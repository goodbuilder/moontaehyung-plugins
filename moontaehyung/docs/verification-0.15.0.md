# Verification 0.15.0

## Scope and source

Source checkout: goodbuilder/moontaehyung-plugins, branch
`feat/risk-adaptive-blueprint-adr`, base commit
`2834176087fbc388f64325bf0c427b47b5b3838f`.

Added aar, rmea, fta, mcda and analysis-router with UI metadata. Narrowed existing RCA to
actual causal investigation; linked risk-plan, ADR and verify-check to specialist owners;
kept auto-subagents generic and unchanged from the base revision. Analysis-router owns the
complete fresh-context candidate-method comparison protocol and uses general delegation.
Updated shared
routing, README and manifest to 0.15.0 (20 skills). No scripts, hooks, MCP servers or new
executable dependencies are introduced by this change.

## Checks and evidence

- PASS: `python3 .../skill-creator/scripts/quick_validate.py <skill>` for all ten added or
  changed skills: aar, rmea, fta, mcda, analysis-router, rca, risk-plan,
  architecture-decision-record, verify-check, auto-subagents.
- PASS: manifest JSON, version and count of 20 skill entrypoints; YAML parsing for all ten
  affected skill UI files. Existing invocation policies are preserved; the five new skills
  allow implicit invocation.
- PASS: relative Markdown targets in the affected skills, shared routing and README after
  this verification record was added; `git diff --check` for tracked changes.
- Earlier synthetic trials: isolated RCA and FTA workers received the same incomplete
  dual-network video incident. Both withheld unsupported causation; FTA contributed a
  conditional failure-combination model. See the router's
  [initial evaluation](../skills/analysis-router/references/evaluation.md) for setup and limits.
  That RCA trial used the pre-change installed RCA; it is not a behavioral regression test
  of every revised instruction.
- Context-aware behavioral checks selected AAR for an explicit retrospective and deferred
  MCDA ranking for missing measurements/preferences. These were local/contextual smoke
  checks, not independent comparative benchmarks.
- Read-only fresh-context integration review examined the package diff, workflow boundaries
  and metadata. It confirmed the three routes above by inspection and found a missing
  README verification target, resolved by adding this record. This is design review rather
  than production or artifact-generation verification.

## Unverified boundaries

- No real project case, generated workbook, spreadsheet recalculation, SVG rendering or
  large-tree solver was exercised. The instructions require their checks when such outputs
  are actually requested.
- RMEA is explicitly the declared generic Risk Mode and Effect Analysis method, not a claim
  that the user's intended terminology or any formal FMEA compliance has been established.
- Installed plugin caches and personal skill directories are unchanged. Live activation,
  runtime discovery, committing and publishing are NOT_RUN. Source integration is not proof
  that a running session recognizes the new version.
- Unrelated bundled skills and historic verification records were not rewritten or retested.

## Responsibility correction

The initial integration put a boundary-comparison section in auto-subagents. Following user
review, that section was removed: the complete method-comparison protocol belongs to
analysis-router. Auto-subagents is byte-identical to the base revision and has no router
dependency. The router defines candidates, isolation, comparison criteria, execution limits,
and synthesis; it delegates only the generic worker coordination mechanics. Shared routing
and README reflect this direction. Focused validation and relative-link checks were rerun.

## Skill discovery update

Skill Auto-Manager now has observable checkpoints before skill authoring, at missing required
outputs/verification, at an unresolved approach change, and at evidenced repeated manual gaps.
It checks local coverage first, discovers through skills.sh/SkillsMP, consults Tessl for available
evaluation evidence, includes ClawHub for OpenClaw needs, and verifies canonical identity and
adoption separately. Source roles are conditional, not a mandatory all-provider sweep.
Read-only discovery continues without the manager CLI; managed search/application retains its
existing capability-ID, sandbox and approval requirements. No installed cache was edited.

Validation:
- PASS: YAML parsing, preserved frontmatter fields, UI description length/default prompt,
  plugin manifest JSON, affected relative links and whitespace checks.
- The standard quick validator rejects the existing top-level `capabilities` manager extension
  in both base and revised Skill Auto-Manager. The extension was retained for compatibility.
  A temporary validation copy excluding only that unchanged extension passes; this is not a
  claim of unmodified standard-schema conformance.
- A fresh-context read-only reviewer exercised six simulated scenarios: new authoring with
  missing CLI; routine typo; missing XLSX dependency; inaccessible ClawHub; monorepo stars
  without skill evidence; and external access unavailable. Expected actions preserved local
  reuse, bounded discovery, truthful status and no implicit installation. Two fallback wording
  ambiguities were clarified. This is instruction-level scenario review, not live proactive
  recall, provider integration, candidate execution or installed-runtime verification.
