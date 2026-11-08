# Research map implementation — 2026-11-07

Authority: accepted conversation plan: autonomous bounded research (guided on request),
outcome decomposition, evidence-backed forecasts, standalone interactive HTML, milestone recording.
Slices: A graph validation/rendering → B RIS configuration/safe updates/resume → C skill contracts,
source synchronization and documentation → D regression and browser workflow.
Completion: outcome→decision traceability, shared/conditional branches, preview distinct from acceptance,
source/history preservation, fresh-session resume, no server/database/runtime CDN.
Approach: Markdown authority with JSON graph block; Python stdlib renderer and embedded JS.
Archify tree requires one parent; a focused graph projection preserves shared decisions without
changing the upstream visualizer or introducing its Node dependency. No automatic numerical aggregation.
Initial status: A/B/C/D NOT_RUN. Original sources and existing dirty worktree preserved.
architecture_refresh: NOT_REQUESTED; risk LOW; affected graph persistence and RIS settings;
no existing architecture reader requested; suggested command: use archify for an architecture reader.

A implemented: Markdown graph v1 parser/validator + portable renderer + synthetic example.
B implemented: project-scoped configure, identity-preserving update with backup/stale rejection,
active-plan bounded resume. C implemented: outcome interview, trend survey, forecast/observation
contracts, milestone semantics; pending source sync and functional checks.

D first run: 26 passed, 1 failed. The failing test counted an ID's textual occurrences and ignored
its extra fallback edge. Replaced that assertion with source-byte preservation and edge equality;
no production behavior was weakened. Browser and source synchronization pending.

D corrected unit run: 27 passed. Explicit invalid absolute output request was refused (expected).
First Chromium launch was blocked by sandbox socket policy; authorized escalated rerun passed.
Chromium file:// workflow verified hypothetical choice, shared-node navigation, back, reset,
active-plan resume and unchanged Markdown; 1280px/390px screenshots inspected, no horizontal overflow.
A further UI pass adds real parent navigation, current-node highlighting and distinct route labels;
copy fallback and these changes will be checked before completion.

Final results:
- PASS packaged helper/graph behavior: 29 tests (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH= /home/moontaehyung/바탕화면/RIS/.venv/bin/python -m pytest skills/ris/tests/test_project.py skills/project-plan/tests/test_graph.py -q`, from package root).
- PASS shared source runner: `PYTHONDONTWRITEBYTECODE=1 ./scripts/test.sh -p no:cacheprovider` → 19 passed.
- PASS RIS and Project Plan quick_validate; graph sample check; git diff --check.
- PASS final optional browser suite: `PYTHONPATH=/tmp/teachme_browser_lib /usr/bin/python3 skills/project-plan/tests/browser_smoke.py --chromium /tmp/teachme_browsers/chromium-1248/chrome-linux64/chrome --output-dir /tmp/research-map-browser-final`.
  Verified keyboard folding, option comparison/hypothetical choice, shared node and parent navigation,
  back/reset, copy or selectable fallback, active-plan snapshot and immutable source. Screenshots:
  /tmp/research-map-browser-final/desktop.png and mobile.png (390px); no horizontal overflow or JS errors.
- Browser copy check initially asserted before async completion; replaced with a completion wait.
  Final browser run PASS; no clipboard behavior was bypassed.
- PASS explicit invalid output paths, stale hashes, identity replacement, dangling active plan,
  duplicate nodes, missing evidence/edges, disconnected decisions, recorded incompatible choices,
  ungrounded numeric estimates, hostile script text and handwritten output protection.
- PASS synchronized 9 shared RIS source/doc/test files with hash preflight and original bytes in
  /tmp/ris-research-sync/preimage-*.bin. Skill payloads match the packaged version.
- Demo: ../../previews/research-map.html from synthetic assets/research-plan-example.md; not real research.

A/B/C/D complete for deterministic implementation and local browser workflow. No selected research
project was initialized; only explicit temporary synthetic fixtures. Existing project IDs/policies,
legacy web code/data, unrelated worktree edits, installed plugin caches and publication state preserved.
NOT_RUN: live model-based implicit discovery, real-topic trend accuracy, live plugin upgrade. The
currently installed plugin cache may still expose risk-plan until a separate update. RIS standalone
symlink points to the synchronized shared source; a fresh session must verify loaded instructions.
KEEP: narrow stdlib graph renderer, one Markdown authority, optional browser test dependency only.


## Autonomous depth correction — 2026-11-07

User evidence: autonomous outputs offer too few choices and too little depth. Contributing instructions:
2–4 overview options, stop at a comparable report/first task, defer unselected paths. These allowed
an early stop; previous file/browser tests did not evaluate autonomous research quality.
Changed RIS and Project Plan to breadth inventory + counter-search + recursive investigation of all
viable paths, conditional exploration before selection, and substantive frontier reasons. Presentation
folding does not cap investigation. No mandatory option/node quotas or invented empirical claims.
Added structural audit and HTML coverage/frontier display. Shared subgraphs render once as navigable
references rather than being recursively duplicated for every option. Expanded synthetic example
contains distinct approach families and multi-stage consequences; this demonstrates structure only.
Verification pending below; installed cache still requires separate update. Live model research quality
must not be inferred from deterministic audit or synthetic graph counts.

Depth correction results:
- PASS: 31 packaged behavioral tests; coverage diagnostics expose unexplained options and remain
  finite for cycles/shared nodes. No hard node-count gate was added.
- PASS: final Chromium smoke test now traverses expanded D-001→D-040→D-041→D-060→D-070→D-080,
  checks all five root options are visible and shared branches do not grow exponentially.
  Desktop/mobile screenshots in /tmp/research-map-depth-browser/expanded-*.png inspected;
  no horizontal overflow or JS errors. Original map folding/preview/copy/resume tests also pass.
- PASS: both skills quick_validate, expanded graph audit, render, git diff --check.
- PASS: RIS shared SKILL.md and research-exploration reference synchronized with preimage/hash checks;
  README updated. Backups /tmp/ris-depth-sync. Shared helper code itself unchanged in this correction.
- Updated workspace previews/research-map.html: synthetic example has 13 decisions, 33 options,
  five decision stages on shortest outcome paths; these counts demonstrate structure only.
- NOT_RUN: independent live-model topic research. Prompt changes and graph diagnostics improve the
  specified behavior but cannot prove a future agent's search breadth or research quality. Installed
  risk-plan plugin cache remains unchanged; source fixes require updating that plugin for live use.

## Candidate option reuse correction — 2026-11-07

User reports options can appear in only one candidate. Existing model has a single global choice
per decision and no independently persisted candidate bundles. Introduce candidates mapping decision
IDs to reusable option references; no global ownership/deduplication constraint. Preserve legacy scalar
selected values. Single/multiple selection is a decision-local semantic rule, never cross-candidate
exclusivity. Candidate previews, cloning, reset and compatibility checks must be isolated.
Slices: model/validation → HTML candidate state/comparison → docs/shared RIS contract → tests/browser.
Acceptance: A and B both contain the same option; changing/resetting A does not alter B; compatible
options coexist within a multiple-select decision; explicit conflicts apply within each candidate;
existing single-select graphs/browser flows remain compatible. Verification pending.

Candidate reuse final results:
- PASS: 40 packaged helper/graph tests, including identical option references in two candidates,
  legacy scalar choices, decision-local multiple selection, per-candidate compatibility, duplicate
  candidate/selection rejection, missing references and invalid modes/current candidate.
- PASS final browser suite in /tmp/research-map-candidates-final: both A/B initially share RGB;
  adding public-data choice to B retains B's flight-data choice and leaves A unchanged; A's conflict
  does not leak into B; resetting B leaves A's edits intact; clone arrays are independent; new blank
  candidate consumes no options; source bytes remain unchanged. Prior folding, deep navigation,
  copy/resume, desktop/mobile and JS-error checks also pass.
- PASS screenshots candidates-desktop.png and candidates-mobile.png visually inspected. Wide
  candidate comparison is contained in its own horizontal scroll region on mobile.
- PASS both skill validators, expanded graph check/render, git diff --check. Existing plans need no
  automatic migration: legacy selected values become the default candidate in the viewer.
- PASS shared RIS exploration reference synchronized with exact preimage/hash checks; backup in
  /tmp/ris-candidate-sync. Helpers/project policy unchanged.
- Demo updated: three candidates share public data/onboard processing; validation supports several
  complementary checks per candidate. Counts and combinations remain synthetic, not empirical claims.
- NOT_RUN: live model candidate generation and installed plugin cache update. Canonical candidate
  edits still require conversational recording; browser edits remain hypothetical.

## Separate components/options from candidate bundles — 2026-11-07

User requests separate presentation. Add two accessible tabs: component-option catalog (read-only
browsing/forecast evidence) and candidate composition/comparison (candidate-scoped edits). The same
shared detail editor moves between panels; browsing components never toggles candidate membership.
All decision axes appear as component rows, including undecided candidate cells. Optional component
labels fall back to existing decision titles; schema/IDs and source records remain compatible.
Acceptance: switching tabs preserves candidate overrides; no candidate controls/selection actions in
library view; candidate table cells open the right candidate/component; legacy graphs, multi-select,
cloning/reset, source preservation and narrow screens continue to work. Verification pending.

First separated-view browser pass found coverage hidden inside the collapsed graph disclosure. Moved coverage outside that disclosure so structural inventory stays visible; rerun pending.


Separated-view final results (supersedes the first browser failure):
- PASS: 41 packaged helper/graph tests, including optional component labels and unchanged memberships.
- PASS final browser suite in /tmp/research-map-separated-final: separate accessible panels, full
  component catalog, no selection buttons/candidate controls in library view, candidate overrides
  survive view switches, catalog→composition transition preserves component and candidate, and
  matrix cells select the intended candidate/component. Arrow-key tab navigation also checked.
- PASS prior deep exploration, independent candidate reuse/multiple-selection/clone/reset, copy,
  snapshot resume and source-byte preservation checks. No JS errors or document horizontal overflow.
- PASS visual inspection of expanded-desktop.png, components-mobile.png and candidates-desktop.png:
  catalog/forecast browsing and composition matrix are distinct. Candidate tables use their own
  horizontal scroll region at narrow widths. Remaining screenshots in the same verification folder.
- Component labels added only to the synthetic example. No existing project records were migrated.
  RIS already delegates visualization to Project Plan; its source/helper contract needed no change.
- Workspace previews/research-map.html regenerated with the two-view template. Installed plugin
  cache remains outside this change; live model research generation is still NOT_RUN.
