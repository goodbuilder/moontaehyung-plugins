# 0.17.0 plugin update — 2026-11-07

## Installed state

PASS: moontaehyung@moontaehyung-local updated from 0.14.0 to 0.17.0 and enabled.
Installed path: ~/.codex/plugins/cache/moontaehyung-local/moontaehyung/0.17.0.
Readback uses the default CLI configuration, without source overrides. All 314 packaged files match
release SHA-256 values. A fresh Codex app-server skills/list (forceReload) discovers 21 enabled
namespaced skills from 0.17.0, including moontaehyung:project-plan and moontaehyung:ris; no old
risk-plan entry is discovered. Existing standalone ris is retained intentionally.

## Installation route and configuration

A clean local snapshot is at LLM_Skill/releases/0.17.0. No remote push, publication or commit occurred.
Direct replacement of the existing marketplace source was refused before any mutation. The successful
installation uses supported `codex plugin add` with local-marketplace overrides for that command only.
User config remains byte-for-byte equal to its pre-install backup. The existing Git marketplace
https://github.com/goodbuilder/moontaehyung-plugins.git, ref feat/risk-adaptive-blueprint-adr, is preserved.
Future updates from Git will use the state of that Git branch; these local changes have not been
published there. Repeat the scoped local install route for unpublished local releases.

Preparation text inside the immutable release payload describes a proposed permanent source switch;
it is superseded by the successful route and installation-result.json next to that payload. The
payload itself is unchanged after installation so its checksums remain reproducible.

## Evidence

Release-side receipts: releases/0.17.0/installation-result.json, payload-verification.json,
discovery-verification.json, packaging-manifest.json and preinstall-state.json (paths relative to
LLM_Skill). The config preimage is in the private temporary directory identified by preinstall-state.

- PASS: 41 helper/graph tests before packaging; prior desktop/mobile browser workflow passes.
- PASS: 20 entrypoints pass skill-authoring quick_validate. Existing `name: Zotero` is unchanged
  from 0.14.0 and flagged by its lowercase-only rule; runtime discovery of moontaehyung:Zotero passes.
- PASS: manifest 0.17.0, 21 skill directories, project-plan and RIS present; risk-plan directory absent.
- PASS: all 314 installed payload checksums; no missing/mismatched files; config bytes unchanged.
- PASS: fresh runtime discovery, enabled state and default scoped CLI list.
- Initial verification script used tomllib unavailable on system Python 3.10; changed to exact byte
  comparison, which is stronger for confirming no config mutation. Initial app-server check was
  blocked from its SQLite state runtime by the sandbox; authorized rerun passed.
- An all-marketplace list reported an existing missing CSM manifest. Target-scoped list and fresh
  discovery succeed. No unrelated marketplace repair or permission changes were made.

Current conversations can retain already-loaded instructions. Start a fresh conversation to invoke
moontaehyung:project-plan or moontaehyung:ris with the new instructions. Runtime discovery does not
establish research quality or user understanding; those remain separate validations.
