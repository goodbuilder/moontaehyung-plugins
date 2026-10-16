# Workflow coordination

Choose the smallest relevant workflow, not a mandatory sequence. Reuse active requirements,
authorization, decisions and evidence. Explicit user instructions control scope. Do not repeat
interviews, create a second approval gate, or bypass an applicable existing approval requirement.

| Skill | Responsibility |
|---|---|
| risk-adaptive-blueprint | Project-level branching decisions, risk forecasts, earliest prevention points and pivot gates; not routine implementation. |
| architecture-decision-record | Durable rationale and evidence for material choices and their supersession; not a second implementation approval. |
| create-gui | New operator GUI requirements and product workflow; use design-boundaries for substantial architecture decisions. |
| modify-gui | Existing GUI scope, preservation and impact; use maintain-boundaries for structural changes. |
| design-boundaries | Responsibilities, interfaces, state/resource ownership and lifecycles; reuse product requirements. |
| maintain-boundaries | Preserve boundaries during changes; redesign only the necessary scope. |
| verify-check | Acceptance criteria, small implementation steps, handoffs and complete workflow verification. |
| rca | Explain intended-versus-observed task gaps, including technical failures, and propose corrective actions. |
| auto-subagents | Select and coordinate bounded delegation; the calling workflow retains domain decisions, records and final acceptance. |
| update-architecture | Refresh the architecture reader only when explicitly requested. |
| auto-skill-manager | Check project skill coverage, search publicly only for confirmed gaps or explicit user requests, and recommend candidates with provenance; changes stay behind the configured manager's approval gates. |
| Zotero | Search Zotero, verify reference metadata and recommendation evidence, export BibTeX, insert citations, and import verified records. |

Use one decision record and one verification ledger per change. If a GUI workflow already owns
requirements, verify-check reuses them and asks only about missing consequential conditions.
Routine implementation choices do not require another interview. Known local errors do not need
RCA; unclear or repeated failures may. RCA recommendations neither authorize implementation nor
prove recovery. Boundary design is not runtime verification. Return to verification after a fix.

Do not invoke GUI workflows for unrelated backend work or expand a change into a global refactor.
Preserve update-architecture's explicit-only policy; other skills do not automatically invoke it.
For material choices, follow the [minimum sufficient change policy](minimum-sufficient-change.md).
Boundary changes also follow the [architecture refresh contract](architecture-refresh.md), recording
impact without automatically refreshing the external reader.

## Canonical instruction owners

The common architecture procedure lives in design-boundaries and maintain-boundaries. Common
implementation verification lives in verify-check. GUI references contain only operator-facing
mapping and acceptance supplements; do not expand them back into independent copies of those
procedures. Shared minimum-change policy remains authoritative for complexity decisions.

Compare content and provenance before importing a personal skill copy; modification timestamps alone
are not a version order. Update this packaged source first and synchronize personal installations
only when requested, adapting local links while preserving invocation policies.

## Delegation owner

auto-subagents owns shared delegation decisions and coordination. verify-check,
maintain-boundaries, and rca route suitable independent investigations to that skill.
Reuse assignments across workflow handoffs instead of dispatching duplicate work.
The calling workflow retains its criteria, domain judgment, authorization, and existing
record; delegated work does not introduce another interview, approval gate, or ledger.

## Implementation decision owners

For each material choice, use one owner: create-gui or modify-gui for GUI-facing
implementation/tooling, and design-boundaries for structural choices. One task may have
several different decisions, but a skill handoff does not start the same comparison again.
Maintain-boundaries flags invalidated assumptions; verify-check turns them into checks and
returns unresolved or contradicted choices to their owner. Without a separate planning
workflow, the coordinating agent resolves only the missing material choice within scope.
Reuse the existing plan, authorization, and decision record; read the shared policy once
when needed, not again for each participating skill.

## Risk-adaptive planning and ADRs

Use risk-adaptive-blueprint when exploring consequential project-level alternatives or reacting
to a material change in risk. A selected material decision is documented by
architecture-decision-record using linked D-/R-/G- IDs. Routine code changes should not
produce either artifact by default. Existing decision owners (GUI workflows or
design-boundaries) still own the technical choice, while ADR owns the historical record;
verify-check retains the acceptance ledger, and rca owns evidence-backed analysis of
observed misses. Avoid creating duplicate approvals, interviews, or decision records.
