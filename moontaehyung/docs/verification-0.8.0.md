# 0.8.0 packaging and installation verification — 2026-10-16

## Scope

Added the existing `auto-skill-manager` instruction skill to the `moontaehyung` plugin.
The skill instructions were copied byte-for-byte from codex-skill-manager 0.3.0.
The plugin package version advanced from 0.7.0 to 0.8.0.

## Changes

- Added `skills/auto-skill-manager/SKILL.md` and `agents/openai.yaml` display metadata.
- Updated plugin metadata, the README skill inventory, and the routing contract for twelve skills.
- Preserved the existing codex-skill-manager package and its copy of this skill.
- Added no hooks, MCP servers, executable code, or runtime dependencies.

## Static checks

- Plugin manifest parsed as JSON and declares version 0.8.0 with `./skills/`.
- The package contains twelve skill directories.
- All 51 files in the previous 0.7.0 skill tree remain byte-identical.
- The new `SKILL.md` has SHA-256 `b788b4a99ded3c651c760bf26b77ded90c922807aa09e7fc3a99612a1dc5c9b0`.
- `git diff --check` passed.
- No test suite was run for this instruction-only packaging change.

## Runtime installation

The user approved installation. `codex plugin add moontaehyung@moontaehyung-local --json`
returned version 0.8.0 and installed path
`/home/moontaehyung/.codex/plugins/cache/moontaehyung-local/moontaehyung/0.8.0`.
A subsequent `codex plugin list` reported `moontaehyung@moontaehyung-local` as
`installed, enabled 0.8.0`. The installed skill file matched the local source byte-for-byte.

The installed package came from the configured local marketplace checkout. No other plugin
was removed or disabled.
