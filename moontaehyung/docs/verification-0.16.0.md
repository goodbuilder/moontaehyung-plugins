# Verification 0.16.0 — RIS bundle

## Scope

Added `skills/ris` from the user's locally implemented project-local RIS skill under
`RIS/skills/ris`. This is the existing CLI agent + shared skill + per-project Markdown design.
No new web interface, database, MCP server, external service, hook or background process is introduced.
Python 3.10+ and Unix `fcntl` are required by the helper. Pytest is a test-only dependency.

Manifest 0.16.0 declares 21 skill entrypoints. README and shared routing describe ownership
between RIS, risk-plan, teach-me, Zotero and other existing specialist workflows.
The helper tests are bundled so path relocation can be tested against the packaged payload.

## Checks

Executed checks:
- Standard skill frontmatter validation and UI metadata.
- Manifest JSON, version, entrypoint count and local reference resolution.
- Bundled helper's behavioral tests from the package location.
- Clean temporary-project CLI initialization/check/context without dependencies or central state.
- Whitespace validation of affected source changes.

## Limits

These checks cover deterministic file operations, not independent model-based skill selection,
academic correctness, actual external source retrieval or user understanding. Actual implicit recall
and a new CLI agent session remain NOT_RUN. Existing project data are untouched.

Installed plugin caches, user plugin configuration and the standalone ~/.agents/skills/ris link
are not changed. The existing standalone skill remains independently recognized. A later plugin
installation must verify bundled recognition and resolve duplicate copies deliberately; source
presence or a passing test is not installation, activation, committing or publishing.

The existing local RIS app/source is retained; this bundled payload is self-contained and does
not depend on a desktop checkout path. Existing uncommitted 0.15.0 work is preserved.

## Results

- PASS: `skill-creator/scripts/quick_validate.py skills/ris` -> valid.
- PASS: bundled `skills/ris/tests/test_project.py` -> 16 passed.
- PASS: manifest 0.16.0, 21 entrypoints, implicit-invocation metadata and local RIS references.
- PASS: a new temporary project initialized with preserved AGENTS rules, checked and read as a
  prepared context through the packaged script; no SQLite created and no server launched.
- PASS: `git diff --check` on the source checkout.
- NOT_RUN: live plugin install/activation, standalone-copy cleanup, actual model workflow and publishing.
