import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import vm from 'node:vm';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { validateSchema } from '../renderers/shared/validator.mjs';

const skillRoot = path.resolve(fileURLToPath(new URL('..', import.meta.url)));
const renderer = path.join(skillRoot, 'renderers/tree/render-tree.mjs');
const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'archify-tree-doc-links-'));
const keepArtifacts = process.env.ARCHIFY_KEEP_TEST_ARTIFACTS === '1';
let keptOutputPath;

try {
  const planDir = path.join(tempRoot, 'research', 'plans');
  const decisionsDir = path.join(tempRoot, 'research', 'decisions');
  fs.mkdirSync(planDir, { recursive: true });
  fs.mkdirSync(decisionsDir, { recursive: true });
  const notePath = path.join(decisionsDir, 'study-S-001.md');
  const outputPath = path.join(planDir, 'research-map.html');
  const candidatePath = path.join(tempRoot, 'candidate.json');
  fs.writeFileSync(notePath, '# Canonical study note\n', 'utf8');

  const candidate = {
    schema_version: 1,
    diagram_type: 'tree',
    meta: { title: 'RIS Research Map' },
    nodes: [
      { id: 'goal', label: 'Research goal' },
      {
        id: 'recommendation',
        parent: 'goal',
        label: 'Recommended method',
        sublabel: 'Recommendation from the current study snapshot',
        links: [{ label: 'S-001 · revision 3 snapshot', href: '../decisions/study-S-001.md' }],
      },
    ],
  };
  fs.writeFileSync(candidatePath, JSON.stringify(candidate, null, 2) + '\n', 'utf8');

  validateSchema('tree', candidate);
  const targetUrl = new URL(candidate.nodes[1].links[0].href, pathToFileURL(outputPath));
  assert.equal(targetUrl.href, pathToFileURL(notePath).href, 'relative study link resolves to the canonical note');
  assert.equal(fs.existsSync(new URL(targetUrl)), true, 'resolved canonical note exists');

  for (const href of [
    'https://example.test/study.md',
    'javascript:alert(1).md',
    '/research/decisions/study-S-001.md',
    '//example.test/study.md',
    '../decisions/../../outside.md',
    '../decisions/%2e%2e/outside.md',
    '../decisions/study-S-001.md#section',
    '../decisions/study-S-001.html',
  ]) {
    assert.throws(() => validateSchema('tree', {
      ...candidate,
      nodes: candidate.nodes.map((node) => node.id === 'recommendation'
        ? { ...node, links: [{ label: 'Unsafe', href }] }
        : node),
    }), /document-link validation failed/, `unsafe link is rejected: ${href}`);
  }

  const rendered = spawnSync(process.execPath, [renderer, candidatePath, outputPath], {
    encoding: 'utf8',
    timeout: 30000,
  });
  assert.equal(rendered.status, 0, `tree renderer exits successfully: ${rendered.stderr}`);
  assert.equal(fs.existsSync(outputPath), true, 'generated map HTML exists');
  const html = fs.readFileSync(outputPath, 'utf8');
  assert.match(html, /data-node-document-links="\[\{&quot;label&quot;:&quot;S-001 · revision 3 snapshot&quot;,&quot;href&quot;:&quot;\.\.\/decisions\/study-S-001\.md&quot;\}\]"/);
  assert.match(html, /id="focus-document-links"/);
  assert.match(html, /function renderDocumentLinks\(node\)/);
  assert.match(html, /link\.href = entry\.href/);
  const serializedLinks = html.match(/data-node-document-links="([^"]+)"/);
  assert.ok(serializedLinks, 'generated map stores links on their recommendation node');
  const linksJson = serializedLinks[1]
    .replaceAll('&quot;', '"')
    .replaceAll('&amp;', '&')
    .replaceAll('&lt;', '<')
    .replaceAll('&gt;', '>')
    .replaceAll('&#39;', "'");
  class MockElement {
    constructor(tagName) {
      this.tagName = tagName;
      this.children = [];
      this.attributes = {};
      this.hidden = false;
      this._textContent = '';
    }
    set textContent(value) {
      this._textContent = value;
      this.children = [];
    }
    get textContent() { return this._textContent; }
    setAttribute(name, value) { this.attributes[name] = value; }
    appendChild(child) { this.children.push(child); }
  }
  const selectedNode = { getAttribute: (name) => name === 'data-node-document-links' ? linksJson : null };
  const renderedLinks = new MockElement('div');
  const helperStart = html.indexOf('function safeRelativeMarkdownPath(');
  const helperEnd = html.indexOf('function renderSourceEvidence(id)', helperStart);
  assert.ok(helperStart >= 0 && helperEnd > helperStart, 'generated map includes the document-link viewer code');
  const viewerHelpers = html.slice(helperStart, helperEnd);
  vm.runInNewContext(`${viewerHelpers}\nrenderDocumentLinks(node);`, {
    document: { createElement: (tagName) => new MockElement(tagName) },
    documentLinks: renderedLinks,
    node: selectedNode,
  });
  assert.equal(renderedLinks.hidden, false, 'selected recommendation exposes its document link');
  assert.equal(renderedLinks.children.length, 1, 'selected recommendation creates one clickable anchor');
  const anchor = renderedLinks.children[0];
  assert.equal(anchor.tagName, 'a');
  assert.equal(anchor.href, '../decisions/study-S-001.md');
  assert.equal(anchor.attributes['aria-label'], 'S-001 · revision 3 snapshot');
  const clickedTarget = new URL(anchor.href, pathToFileURL(outputPath));
  assert.equal(clickedTarget.href, pathToFileURL(notePath).href, 'click target resolves to the canonical study note');
  assert.equal(fs.readFileSync(new URL(clickedTarget), 'utf8'), '# Canonical study note\n', 'resolved target is readable');

  const nestedPlanDir = path.join(tempRoot, 'research', 'plans', 'nested', 'deeper');
  fs.mkdirSync(nestedPlanDir, { recursive: true });
  const nestedCandidatePath = path.join(nestedPlanDir, 'candidate.json');
  const nestedOutputPath = path.join(nestedPlanDir, 'research-map.html');
  const nestedCandidate = {
    ...candidate,
    nodes: candidate.nodes.map((node) => node.id === 'recommendation'
      ? { ...node, links: [{ label: 'S-001 · revision 3 snapshot', href: '../../../decisions/study-S-001.md' }] }
      : node),
  };
  fs.writeFileSync(nestedCandidatePath, JSON.stringify(nestedCandidate, null, 2) + '\n', 'utf8');
  const nestedRender = spawnSync(process.execPath, [renderer, nestedCandidatePath, nestedOutputPath], {
    encoding: 'utf8',
    timeout: 30000,
  });
  assert.equal(nestedRender.status, 0, `nested plan link renders successfully: ${nestedRender.stderr}`);
  assert.equal(fs.existsSync(nestedOutputPath), true, 'nested research map HTML exists');
  const nestedTarget = new URL('../../../decisions/study-S-001.md', pathToFileURL(nestedOutputPath));
  assert.equal(nestedTarget.href, pathToFileURL(notePath).href, 'nested relative study link resolves to the same canonical note');

  const escapingCandidatePath = path.join(nestedPlanDir, 'escaping-candidate.json');
  const escapingCandidate = {
    ...nestedCandidate,
    nodes: nestedCandidate.nodes.map((node) => node.id === 'recommendation'
      ? { ...node, links: [{ label: 'Escaping', href: '../../../../outside.md' }] }
      : node),
  };
  fs.writeFileSync(escapingCandidatePath, JSON.stringify(escapingCandidate, null, 2) + '\n', 'utf8');
  const escapingRender = spawnSync(process.execPath, [renderer, escapingCandidatePath, path.join(nestedPlanDir, 'escaping.html')], {
    encoding: 'utf8',
    timeout: 30000,
  });
  assert.notEqual(escapingRender.status, 0, 'parent-relative target outside research root is refused');
  assert.match(escapingRender.stderr, /document link resolves outside the research root/);
  keptOutputPath = outputPath;
} finally {
  if (!keepArtifacts) fs.rmSync(tempRoot, { recursive: true, force: true });
}

console.log('tree document link checks passed');
if (keepArtifacts && keptOutputPath) console.log(`test map: ${keptOutputPath}`);
