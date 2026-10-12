# 0.4.1 source comparison and deduplication — 2026-10-10

## Source selection

Compared installed personal skills, packaged 0.4.0 skills, and the Workstation boundary drafts.
Hashes and line counts are in [source-comparison-0.4.1.json](source-comparison-0.4.1.json).
These independent directories are not a shared version-control history: newest means the most
complete reconciled content supported by this conversation and the package's change records,
not a modification-time ordering.

| Skill | Selection and reason |
|---|---|
| create-gui | Packaged source retains proportional document mapping, design-first draft, complexity policy and explicit architecture refresh. Personal copy lacks these improvements. Preserve GUI interview/approval/visual rules. |
| modify-gui | Packaged source retains mapped documents, one ledger and proportionate regression/resource policy. Personal copy is an older independent variant. |
| verify-check | 0.4.0 already merges the personal requirement/criteria/decomposition updates with plugin policies. Retain unchanged in 0.4.1. |
| rca | Core content matches personal source; plugin adds coordination. Retain unchanged. |
| design-boundaries | Draft and both installed/package variants have identical core; coordination and reference layout differ. Retain packaged version. |
| maintain-boundaries | Same relation as design-boundaries. Retain packaged version. |
| update-architecture | Packaged only. Preserve bytes and explicit-only policy. |

## Responsibility changes

CreateGUI now delegates common architecture to design-boundaries and generic implementation
verification to verify-check. ModifyGUI delegates structural maintenance to maintain-boundaries
and generic verification to verify-check. Their boundary and verification references are GUI
supplements instead of second copies of common procedures. Existing reference paths remain valid.

GUI requirements, scope approval, interruption/resume, operator behavior, visual stability and
final packet acceptance remain with the GUI workflows. Dedicated resource/visual reference files,
initializer scripts and templates are preserved. No new approval requirement was introduced.

## Verification scope

Structural checks cover all skill manifests, plugin JSON/path, internal links, Python parsing,
and preserved owner skills/scripts/templates. Manual review covers role routing, small-task scope,
existing authorization, and separation of product acceptance from missing verification evidence.
Independent agent behavior evaluation and application runtime tests are NOT_RUN.

This updates packaged source only; personal installations, registration and activation are unchanged.
The plugin lives outside SASL and is not covered by its Git history. Keep the whole plugin directory
for portability. A pre-update backup was made before applying the staged candidate.

Coordinate contract checked: instruction packaging only; no application coordinate transforms,
units, arrays, saved schemas or runtime code changed.

Result: PASS — seven skill validators, 49 local links, manifest path/version, Python parse and byte preservation checks.
