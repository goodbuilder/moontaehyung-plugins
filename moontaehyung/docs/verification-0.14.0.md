# Verification 0.14.0

## Change

Added `teach-me` as an explicit-only Codex skill. The Codex version preserves the worked-example lesson format from the existing Claude skill and replaces its unavailable page-design helpers with the plugin's bundled Archify workflow and inline SVG guidance.

## Verification

- `skill-creator/scripts/quick_validate.py` — PASS.
- Plugin manifest JSON and the skill's `agents/openai.yaml` fields — PASS.
- Package contains 15 skill folders; `teach-me` adds no scripts, hooks, MCP servers, or apps.
- Read-only runtime status shows the installed plugin at 0.13.0 and no recognized `teach-me` skill.
- Live activation is NOT_RUN. The configured Skill Manager's `live-plan` rejected the package with `executable or unsupported bundled resource`. Its package scanner accepts inert Markdown/TOML skill resources; this plugin also bundles executable scripts, HTML examples, SVGs, images, and other assets.

## Scope and limit

The 0.14.0 source package is recorded in the configured marketplace checkout. It is not installed or activated in the Codex runtime, and it has not been committed or published. The existing plugin inventory also reports unresolved Archify resource links; this change leaves them untouched.
