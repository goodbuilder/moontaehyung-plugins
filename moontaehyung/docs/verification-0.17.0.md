# 0.17.0 local plugin release — 2026-11-07

## Payload and authority

This release packages the current authorized local source, including existing 0.15/0.16 work and
research-map changes. It renames risk-plan to project-plan and bundles RIS. It does not publish,
push, commit, remove the standalone RIS skill or modify research projects.
The Git marketplace previously supplied moontaehyung@moontaehyung-local 0.14.0. This local update uses
a clean release snapshot at LLM_Skill/releases/0.17.0, keeping the same marketplace and plugin IDs.
The previous Git registration is https://github.com/goodbuilder/moontaehyung-plugins.git,
ref feat/risk-adaptive-blueprint-adr. Returning to Git updates requires re-registering that source.

## Preparation evidence

- PASS: 41 helper/graph regression tests, isolated pytest plugins and explicit scope.
- PASS: 20 skill entrypoints pass quick_validate; Project Plan and RIS included.
- KNOWN EXISTING EXCEPTION: Zotero frontmatter uses uppercase `name: Zotero`, identical to the
  installed 0.14.0 source. The lowercase-only authoring validator flags this. Preserve its existing
  public invocation identity; it is outside this rename. Verify runtime discovery independently.
- PASS: graph/source preservation and separate component/catalog versus candidate workflows were
  browser-tested; see verification-research-map.md. No new code changes in this release step.
- PASS: manifest version/name, 21 skill directories, renamed/new skill presence, no risk-plan directory.

## Installation and readback

Use supported `codex plugin marketplace add <release-root> --json`, then
`codex plugin add moontaehyung@moontaehyung-local --json`. Snapshot user config before installation;
change only this marketplace source and this plugin's existing enabled entry. Do not edit plugin
cache files manually. Check default CLI readback, payload hashes and fresh skill discovery.
The external-write sandbox authorization applies to user config/cache changes.

Actual installation/verification receipts and packaging checksums are stored alongside the release
snapshot, outside the immutable plugin payload. Treat a receipt as successful only after CLI readback
and payload checks pass. Current conversations may retain old instructions; source installation alone
does not replace already-loaded context or prove model research quality.
