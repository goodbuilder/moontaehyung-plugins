# 0.4.2 selective subagent verification — 2026-10-10

## Scope and source

Import only the approved `Selective subagent verification` section from the personal
verify-check skill into the packaged verify-check, between slice mapping and implementation.
The imported section SHA-256 is e2638a02377a9e9966ed9d1ea9afacb890fcce921f7f91cae4ca57839f7468e2.

Preserve the plugin's shared minimum-change policy, architecture refresh contract,
KEEP / REMOVE / DEFER fields, workflow coordination, and explicit-only update-architecture
policy. The six other skills, their metadata, references, and scripts remain byte-identical.
The system-provided skill-creator and its local customization are not part of this plugin.

## Verification

- Skill manifests: PASS — all seven bundled skills passed quick_validate.py.
- Plugin manifest, version, skill-directory path, and local Markdown links: PASS —
  version 0.4.2, seven skills, and 50 package-local Markdown links validated.
- Imported section and preservation of other package content: PASS — the imported
  section matches the personal source exactly. Removing only that section reproduces
  the previous packaged verify-check byte for byte. All other existing files except
  the release README and version manifest match the baseline SHA-256 inventory.
- Subagent behavior, time/token savings, and application runtime: NOT_RUN.

Commands: `python3 <skill-creator>/scripts/quick_validate.py <plugin-root>/skills/<name>`
for all seven skills; a Python pathlib/json/re/hashlib inspection checked the manifest,
resolved Markdown links, and compared the complete staged inventory with the baseline.
Checks used a temporary staged copy; application and device execution were not involved.

This is a packaged-source update. Installation, activation, and publishing are not part
of the update. This directory lives outside SASL and has no Git repository; keep the complete
plugin directory together to transfer it to another machine.

Coordinate contract checked: instruction packaging only; no coordinate transforms, axes,
units, saved schemas, or application runtime code changed.
