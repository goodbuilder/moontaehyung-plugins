import * as validators from './generated-validators.mjs';
import { throwDiagnosticError } from './diagnostics.mjs';
import fs from 'node:fs';
import path from 'node:path';

// "/nodes/3/label" reads much better as "/nodes/3 (id: "router") /label" for the
// LLM fixing the JSON; resolve the nearest enclosing element's id or label.
function annotatedPath(instancePath, data) {
  if (!instancePath) return { path: '/', identity: null };
  let node = data;
  let hint = null;
  for (const seg of instancePath.split('/').slice(1)) {
    if (node == null || typeof node !== 'object') break;
    node = node[/^\d+$/.test(seg) ? Number(seg) : seg];
    if (node && typeof node === 'object' && !Array.isArray(node)) {
      const tag = node.id ?? node.label;
      if (tag != null) hint = String(tag);
    }
  }
  return { path: instancePath, identity: hint };
}

function annotatePath(instancePath, data) {
  const annotated = annotatedPath(instancePath, data);
  return annotated.identity != null
    ? `${annotated.path} (id/label: ${JSON.stringify(annotated.identity)})`
    : annotated.path;
}

function formatErrors(errors, data) {
  return errors.map((e) => {
    const where = annotatePath(e.instancePath, data);
    const detail = e.params && Object.keys(e.params).length
      ? ' ' + JSON.stringify(e.params)
      : '';
    return `  ${where} ${e.message}${detail}`;
  }).join('\n');
}

export function validateSchema(diagramType, data) {
  const validate = validators[diagramType];
  if (!validate) {
    throw new Error(`validateSchema: unknown diagram type "${diagramType}"`);
  }
  const schemaData = diagramType === 'tree' ? validateTreeDocumentLinks(data) : data;
  if (!validate(schemaData)) {
    const diagnostics = validate.errors.map((error) => {
      const annotated = annotatedPath(error.instancePath, data);
      const subject = {
        diagramType,
        path: annotated.path,
        ...(annotated.identity != null ? { identity: String(annotated.identity) } : {}),
      };
      const evidence = {
        keyword: error.keyword,
        expected: error.schema,
        ...error.params,
      };
      const supportedFixes = {
        additionalProperties: [`remove unsupported property ${JSON.stringify(error.params?.additionalProperty)}`],
        required: [`add required property ${JSON.stringify(error.params?.missingProperty)}`],
        type: [`use ${JSON.stringify(error.params?.type)} at ${annotated.path}`],
        enum: [`choose one of the allowed values`],
        pattern: [`match the required pattern ${JSON.stringify(error.params?.pattern)}`],
        minimum: [`use a value ${error.params?.comparison || '>='} ${error.params?.limit}`],
        maximum: [`use a value ${error.params?.comparison || '<='} ${error.params?.limit}`],
        minItems: [`provide at least ${error.params?.limit} item(s)`],
        maxItems: [`provide at most ${error.params?.limit} item(s)`],
        minLength: [`provide at least ${error.params?.limit} character(s)`],
        maxLength: [`provide at most ${error.params?.limit} character(s)`],
      }[error.keyword] || [];
      return {
        code: `schema/${error.keyword}`,
        severity: 'error',
        message: `${annotatePath(error.instancePath, data)} ${error.message}`,
        subject,
        evidence,
        supportedFixes,
      };
    });
    throwDiagnosticError(
      `${diagramType} schema validation failed:\n${formatErrors(validate.errors, data)}`,
      diagnostics,
    );
  }
}

// Tree's optional document links are validated here and removed only from the
// generated-schema copy. The bundled validator predates this tree-specific
// extension; keeping the original object intact lets the renderer consume the
// links after the rest of the diagram passes the standalone schema check.
function validateTreeDocumentLinks(data) {
  if (!data || typeof data !== 'object' || !Array.isArray(data.nodes)) return data;
  const fail = (path, message, evidence = {}) => {
    throwDiagnosticError(`tree document-link validation failed: ${message}`, [{
      code: 'tree/document-link-invalid',
      severity: 'error',
      message,
      subject: { diagramType: 'tree', path },
      evidence,
      supportedFixes: ['use a relative Markdown document path and a non-empty display label'],
    }]);
  };
  const relativeMarkdownPath = (value) => {
    if (typeof value !== 'string' || !value || value.length > 1024 || value !== value.trim()) return false;
    if (/[\\%?#:\u0000-\u001f\u007f-\u009f]/u.test(value) || value.startsWith('/')) return false;
    if (!/\.md$/i.test(value)) return false;
    const segments = value.split('/');
    let descended = false;
    for (const segment of segments) {
      if (!segment || segment === '.') return false;
      if (segment === '..') {
        if (descended) return false;
        continue;
      }
      descended = true;
    }
    return descended;
  };
  const nodes = data.nodes.map((node, index) => {
    if (!node || typeof node !== 'object' || Array.isArray(node) || node.links === undefined) return node;
    const path = `/nodes/${index}/links`;
    if (!Array.isArray(node.links) || node.links.length < 1 || node.links.length > 5) {
      fail(path, 'links must contain between 1 and 5 entries.', { count: Array.isArray(node.links) ? node.links.length : null });
    }
    node.links.forEach((link, linkIndex) => {
      const linkPath = `${path}/${linkIndex}`;
      if (!link || typeof link !== 'object' || Array.isArray(link)) fail(linkPath, 'each link must be an object.');
      const keys = Object.keys(link);
      if (keys.some((key) => key !== 'label' && key !== 'href')) fail(linkPath, 'links may contain only label and href.', { keys });
      if (typeof link.label !== 'string' || !link.label.trim() || link.label.length > 140) {
        fail(`${linkPath}/label`, 'label must be a non-empty string of at most 140 characters.');
      }
      if (!relativeMarkdownPath(link.href)) {
        fail(`${linkPath}/href`, 'href must be a safe relative Markdown path; absolute paths, schemes, query strings, fragments, encoded separators, and traversal after entering the target path are refused.', { href: link.href });
      }
    });
    const { links: _links, ...schemaNode } = node;
    return schemaNode;
  });
  return { ...data, nodes };
}

export function validateTreeDocumentLinkTargets(data, outputPath) {
  if (!data || !Array.isArray(data.nodes) || !outputPath) return;
  const links = data.nodes.flatMap((node, nodeIndex) => (node?.links || []).map((link, linkIndex) => ({ nodeIndex, linkIndex, ...link })));
  if (!links.length) return;

  const researchRoot = findResearchRootForOutput(outputPath);
  const hasParentTraversal = links.some(({ href }) => String(href).split('/').includes('..'));
  if (!researchRoot) {
    if (hasParentTraversal) {
      failTreeDocumentTarget('/nodes', 'parent-relative document links require an output under research_dir/plans so the research-root boundary can be checked.', { outputPath });
    }
    return;
  }

  const rootReal = fs.realpathSync(researchRoot);
  const outputDirectory = path.dirname(path.resolve(outputPath));
  for (const link of links) {
    const pointer = `/nodes/${link.nodeIndex}/links/${link.linkIndex}/href`;
    const target = path.resolve(outputDirectory, link.href);
    if (!isWithinPath(researchRoot, target)) {
      failTreeDocumentTarget(pointer, 'document link resolves outside the research root.', { href: link.href, researchRoot });
    }

    const relativeTarget = path.relative(researchRoot, target).split(path.sep).join('/');
    const basename = path.basename(target);
    const canonicalStudyName = /^study-[A-Za-z0-9][A-Za-z0-9_-]{0,63}\.md$/.test(basename);
    if (canonicalStudyName && relativeTarget !== `decisions/${basename}`) {
      failTreeDocumentTarget(pointer, 'a canonical study link must resolve directly under research_dir/decisions/.', { href: link.href, resolved: relativeTarget });
    }
    if (relativeTarget.startsWith('decisions/study-') && canonicalStudyName) {
      let stat;
      let targetReal;
      try {
        stat = fs.lstatSync(target);
        if (stat.isSymbolicLink() || !stat.isFile()) throw new Error('target is not a regular file');
        targetReal = fs.realpathSync(target);
      } catch (error) {
        failTreeDocumentTarget(pointer, 'canonical study target must be an existing regular file.', { href: link.href, reason: error.message });
      }
      if (!isWithinPath(rootReal, targetReal)) {
        failTreeDocumentTarget(pointer, 'canonical study target resolves outside the research root.', { href: link.href, researchRoot });
      }
    }
  }
}

function findResearchRootForOutput(outputPath) {
  let current = path.dirname(path.resolve(outputPath));
  while (true) {
    if (path.basename(current) === 'plans') {
      const candidate = path.dirname(current);
      const decisions = path.join(candidate, 'decisions');
      try {
        if (fs.statSync(decisions).isDirectory()) return candidate;
      } catch {}
    }
    const parent = path.dirname(current);
    if (parent === current) return null;
    current = parent;
  }
}

function isWithinPath(root, target) {
  const relative = path.relative(root, target);
  return relative === '' || (!path.isAbsolute(relative) && relative !== '..' && !relative.startsWith(`..${path.sep}`));
}

function failTreeDocumentTarget(pointer, message, evidence = {}) {
  throwDiagnosticError(`tree document-link target validation failed: ${message}`, [{
    code: 'tree/document-link-target',
    severity: 'error',
    message,
    subject: { diagramType: 'tree', path: pointer },
    evidence,
    supportedFixes: ['use the map_node_link href computed for this plan and keep its target under research_dir/decisions/'],
  }]);
}
