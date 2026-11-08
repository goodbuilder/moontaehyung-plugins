# Workflow coordination

Choose the smallest relevant workflow, not a mandatory sequence. Reuse active requirements,
authorization, decisions and evidence. Explicit user instructions control scope. Do not repeat
interviews, create a second approval gate, or bypass an applicable existing approval requirement.

| Skill | Responsibility |
|---|---|
| ris | Coordinate research questions, coverage and completion judgment; own project-local continuity, context handoffs and record locations while preserving specialist decisions/artifacts. |
| project-plan | Project-level branching decisions, risk forecasts, earliest prevention points and pivot gates; not routine implementation. |
| architecture-decision-record | Durable rationale and evidence for material choices and their supersession; not a second implementation approval. |
| create-gui | New operator GUI requirements and product workflow; use design-boundaries for substantial architecture decisions. |
| modify-gui | Existing GUI scope, preservation and impact; use maintain-boundaries for structural changes. |
| design-boundaries | Responsibilities, interfaces, state/resource ownership and lifecycles; reuse product requirements. |
| maintain-boundaries | Preserve boundaries during changes; redesign only the necessary scope. |
| verify-check | Acceptance criteria, small implementation steps, handoffs and complete workflow verification. |
| analysis-router | Choose the smallest sufficient analysis workflow; compare consequential boundary cases independently through auto-subagents. |
| aar | Review overall expected/actual outcomes and processes, successful practices, lessons and sustain/change actions. |
| rca | Investigate actual important or recurring failures using causal hypotheses and supporting/refuting evidence. |
| rmea | Own prospective risk-mode assessment, controls, priorities and residual risk; declare the method definition. |
| fta | Own defined top events, AND/OR models and minimal cut sets; modeled paths do not establish incident causation. |
| mcda | Own multi-criteria value scales, weights, scores, trade-offs and sensitivity; distinguish recommendation from decision. |
| auto-subagents | Select and coordinate bounded delegation; the calling workflow retains domain decisions, records and final acceptance. |
| archify | Create requested diagrams and one-page explainers; use the shared contract when refreshing an existing architecture reader. |
| Explain-xlsx | Trace code-derived quantitative results into reviewable XLSX formulas and source mappings across project domains. |
| skill-auto-manager | Compare outcome-relevant products/components, projects, tools, skills and plugins with source evidence; return alternatives and discovery limits to the caller without adopting candidates or deciding overall completion. |
| reviewer | Review research papers, reports, and presentations when a strict, evidence-based assessment is requested. |
| Zotero | Search Zotero, verify reference metadata and recommendation evidence, export BibTeX, insert citations, and import verified records. |

Use one decision record and one verification ledger per change. If a GUI workflow already owns
requirements, verify-check reuses them and asks only about missing consequential conditions.
Routine implementation choices do not require another interview. Known local errors do not need
RCA; unclear or repeated failures may. RCA recommendations neither authorize implementation nor
prove recovery. Boundary design is not runtime verification. Return to verification after a fix.

Do not invoke GUI workflows for unrelated backend work or expand a change into a global refactor.
Do not invoke Archify as an automatic post-edit architecture refresh. Use it for a requested diagram or explainer, and follow the shared contract for an existing-reader refresh.
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
record; delegated work does not introduce another interview, approval gate, or ledger. The caller
sets required scope/depth and accepts evidence; auto-subagents selects allocation and headcount,
keeps questions connected to evidence, and returns unresolved work or proposed scope changes.

## Analysis selection and ownership

When planning a new system or substantial feature, or investigating similar projects and tools,
use skill-auto-manager to compare reusable projects, tools, skills and plugins. Also use it before
new skill authoring or a substantial skill capability extension, then skill-creator for authorized
authoring. Also check discovery when required output/verification is unavailable, an unresolved
material problem forces an approach change, or visible work shows a repeated manual gap.
This is a capability checkpoint, not mandatory internet research for routine tasks. Use available read-only discovery tools without a dedicated management runtime. Analysis-router selects methods from
the available analysis toolkit; skill-auto-manager discovers reusable capabilities beyond it.

Use [analysis-router](../skills/analysis-router/SKILL.md) when analysis methods overlap or several
are needed. Obvious requests route directly; explicit user method choices take priority. For a
consequential boundary, the router owns the entire comparison protocol: candidate selection,
acceptance questions, fresh-context isolation, normally two executions, and synthesis.
It uses auto-subagents only for general delegation mechanics. Auto-subagents remains reusable
for other investigations and verification and has no dependency on analysis-router.
The coordinator inspects evidence rather than counting votes, then chooses one method, sequences
complementary methods, consolidates overlap, or defers for missing inputs. Workers neither
recursively route nor implement candidate remedies. Reuse existing comparisons and records.

Read the router's [handoff contract](../skills/analysis-router/references/handoffs.md) for shared
input fields and canonical output owners. AAR owns learning from success and failure; RCA owns
unresolved actual causation. RMEA owns the risk register, FTA the logical failure model, MCDA the
evaluation matrix, project-plan the execution graph, ADR the decision history, and verify-check the
implementation/effectiveness evidence. They reference rather than duplicate each other's records.
No report alone authorizes implementation, risk acceptance, or external actions. Completion of
a report, action readiness, implementation, and verified effect are separate statuses.

## Implementation decision owners

For each material choice, use one owner: create-gui or modify-gui for GUI-facing
implementation/tooling, and design-boundaries for structural choices. One task may have
several different decisions, but a skill handoff does not start the same comparison again.
Maintain-boundaries flags invalidated assumptions; verify-check turns them into checks and
returns unresolved or contradicted choices to their owner. Without a separate planning
workflow, the coordinating agent resolves only the missing material choice within scope.
Reuse the existing plan, authorization, and decision record; read the shared policy once
when needed, not again for each participating skill.

## Risk planning and ADRs

Use project-plan when exploring consequential project-level alternatives or reacting
to a material change in risk. A selected material decision is documented by
architecture-decision-record using linked D-/R-/G- IDs. Routine code changes should not
produce either artifact by default. Existing decision owners (GUI workflows or
design-boundaries) still own the technical choice, while ADR owns the historical record;
verify-check retains the acceptance ledger, and rca owns evidence-backed analysis of
observed misses. Avoid creating duplicate approvals, interviews, or decision records.


## RIS research continuity

RIS uses the current CLI agent as its interface and project-local Markdown as its research
record. The coordinating agent retains research coverage and completion judgment. RIS owns project
identity, initialization/format checks, bounded handoff preparation and record organization;
it does not take over specialist analyses or create a separate web application.
Project-plan owns branches/gates/fallbacks, teach-me requested calculation lessons, Zotero verified
source operations, and review/verification/ADR workflows their existing artifacts. Preserve
existing project artifact locations and link rather than duplicate canonical results.
RIS recording defaults to manual until the user explicitly chooses another policy.
