# 0.9.0 risk-plan identity verification — 2026-10-17

## Scope

Rename the exported Moontaehyung skill ID from `risk-adaptive-blueprint` to `risk-plan` and
refine the workflow around evidence-driven branch expansion, CHOOSE/AND/IF relations, progressive
graph views, and explicit routes for unknowns. Update the UI metadata, ADR routing, templates,
README, and plugin version.

## Checks

- The plugin contains twelve skill directories, including `skills/risk-plan/`.
- The ADR skill routes to `$risk-plan`; current README and routing tables use the new ID.
- Templates and the branching reference are retained and updated under `skills/risk-plan/`; links
  from `SKILL.md` point to their package-relative resources.
- No hooks, MCP servers, or new runtime dependencies are added.
- `quick_validate.py` passed for `skills/risk-plan`.
- `csm auto catalog` reported version 0.9.0, twelve skills, no catalog errors, and package digest
  `7fb7629c22a8656fe2cf6116b59aea51aafc85d1927cf6204822f750f4233b07`.
- `git diff --check` passed. No test suite was run; the change is an instruction identity rename.

## Runtime boundary

The package source is version 0.9.0. Codex currently reports the installed plugin as 0.8.0;
this source update does not claim that version 0.9.0 is installed or active.
