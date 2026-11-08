---
name: project-plan
description: Design or revise consequential project plans with branching choices, quality gates, fallback routes, and evidence-based switch criteria. Coordinate specialist risk or option analysis only when needed; standalone risk registers belong to RMEA, weighted alternative evaluation to MCDA, and material architectural decision history to ADR.
---

# Project Plan

## Goal and boundary
Maintain a **decision graph** rather than a single fixed roadmap. Connect desired outcomes and success criteria to choices, testable assumptions, risk triggers, escape routes, and earliest preventable failure points. A blueprint proposes options; it does **not** silently authorize high-impact changes.

## Inputs
- Goal and non-goals; constraints; current project stage; environments and stakeholders.
- Existing requirements, code, incidents, ADRs and evidence, when available.
- If sources are unavailable, flag unknowns explicitly; do not invent empirical incident frequencies.

## Analysis boundaries
Own the execution decision graph, milestones, gates and fallback routes. Use existing adequate analyses first. Request [RMEA](../rmea/SKILL.md) only for a material need to systematically compare risk modes and controls; [FTA](../fta/SKILL.md) for a defined failure-combination question; and [MCDA](../mcda/SKILL.md) for unresolved trade-offs across credible alternatives. These methods own their detailed registers/models/matrices; reference their IDs and versions rather than duplicate them in the blueprint. Do not run all methods as mandatory planning stages.

When choosing the method is consequentially ambiguous, use [analysis-router](../analysis-router/SKILL.md); it may ask auto-subagents to compare candidates independently. Reuse completed comparisons and return only new unresolved questions to the coordinator. Follow user-selected methods and existing domain decision owners. A routine local fix needs none of this planning workflow.

Use existing outcome/decision references when handing investigations to auto-subagents. Keep the
question, required evidence, returned findings and unresolved consequential branches in this plan;
auto-subagents owns who performs the work and when. Update affected nodes when new alternatives
or dependencies are found. Do not shape the decision graph around agent headcount or remove a
branch merely because it has no worker assignment.

## Workflow
1. **Frame:** Summarize purpose, inputs, process, outputs, and highest-risk failure outcomes. Separate verified facts, assumptions, and inferences.
2. **Decompose:** Discover unresolved questions from the goal, constraints, actual workflow and evidence. Build outcome elements (`O-###`) with success criteria, connect decisions to the outcomes they support, and build decision nodes (`D-###`), milestones (`M-###`), and gates (`G-###`). For each candidate, assume it is selected and identify the prerequisites and subsequent decisions it introduces. First map the breadth of distinct credible approaches; then recursively expand every viable alternative through its own consequential downstream decisions, including alternatives not yet selected. Do not stop after the first comparison or first actionable task. Follow [gates and branching rules](references/gates-and-branching.md) for expansion and stopping rules. Every high-impact decision needs a baseline, a credible fallback, and a reversible exit if possible.
3. **Analyze:** Forecast each option under explicit conditions using the same comparison criteria: expected result, required resources, follow-up decisions, evidence, uncertainty and verification. Do not sum incomparable metrics or invent unexamined combination effects. Preserve forecasts separately from subsequent observations. For every branch describe preconditions, benefits, costs, dependencies, failure modes, affected assets, reversibility, and an earliest prevention point. Use pre-mortem and RCA hypotheses; do not label untested hypotheses as root causes.
4. **Measure:** Specify leading indicators, measurement source, observation window, thresholds, and owners. Mark numerical thresholds *provisional* until calibrated. Qualitative safety invariants (e.g. never delete unmanaged user files) override weighted scores.
5. **Gate:** For each milestone write verifiable acceptance criteria, failure response, hold/rollback actions, and route to an alternative. A gate must not depend on undocumented intuition.
6. **Link ADRs:** For material architectural selections/changes (boundaries, interfaces, dependencies or deployment), create/update an ADR using the `architecture-decision-record` skill. Use the ordinary append-only decision history for other research choices. Reference applicable ADR IDs from decision nodes; do not duplicate decision rationale across artifacts.
7. **Show the decision graph:** Present consequential choices visually by default, without waiting for a chart request. Show the current question, comparable options, recommendation with reason, user decision points, and verification/fallback paths. Investigate the full credible option landscape before ranking. Group options for a readable overview and retain the complete candidate inventory in the expandable map; overview size is not an investigation limit. Explain search coverage, distinct mechanisms, rejected candidates and unexplored frontier. Deepen all viable branches rather than only the recommended one. For the agreed interactive workflow, use the bundled renderer and [graph contract](references/graph-contract.md) to produce a standalone HTML map from canonical Markdown. See [forecast protocol](references/forecast-protocol.md). Compact Mermaid/text is a fallback when HTML cannot be generated; report the limitation. Do not deliver only graph source that the user cannot readily view. Keep a single canonical plan with a versioned structured graph and append-only history; generate views from it. Create separate risk/decision artifacts only as needed, linking specialist-owned records; use [blueprint template](assets/blueprint-template.md) and [risk register template](assets/risk-register-template.csv). For an exported graph, Graphviz DOT plus rendered SVG is an option. Preserve existing artifact version and history.
8. **Review:** Run the checklist below and explain which choices remain unverified. New evidence triggers review of relevant nodes, not a wholesale rewrite.

## Exploration and visualization
Default to autonomous breadth-first discovery followed by recursive multi-stage investigation of viable branches before requesting selection; follow an
explicit user-picked branch on request. Reuse prior answers. Treat downstream feasibility, data, method, integration, validation and fallback choices as part of the current comparison when they affect achievable outcomes. A short answer or a small overview is not an exploration-completion criterion. Follow the coverage and frontier rules in references/gates-and-branching.md.
The map separates a read-only component-option catalog from candidate composition/comparison in distinct views. Show all options per component with forecasts/evidence in the catalog; display each candidate as a bundle across component rows in the candidate matrix. Browsing the catalog must not change candidate choices; matrix cells open the corresponding candidate/component editor. The map also supports folding, shared-node navigation, side-by-side alternatives, candidate bundles and hypothetical selections. Keep candidate choices independent: one reusable option may belong to many candidates. Use multiple selection for compatible choices within a candidate; reserve single selection for actual mutually exclusive alternatives. Do not partition choices into disjoint candidate pools. See the graph contract for candidate references and legacy compatibility.
Browser state is exploratory, never acceptance. Unexplored branches need further agent investigation;
copy their stable IDs into the conversation. After an authorized milestone, update Markdown/history,
mark affected downstream assumptions for review, regenerate HTML and report the source revision.

## Decision-node contract
Every `D-###` must specify: question, alternatives (at least two unless impossible), current default, assumptions, evidence, owner, expected benefit, cost, failure mode, reversibility, early warning metric, switch threshold, fallback route, linked ADR and last-reviewed date.
Keep detailed records behind the overview; label unavailable evidence and not-yet-applicable fields instead of inventing values. Distinguish recommendation, provisional assumption, and confirmed selection.

## Resolve unknowns without excessive questions
Classify each material unknown as **investigate**, **experiment**, **assume and proceed**, **user decision**, or **defer**. Record the resolution owner, affected node, and when the answer becomes necessary.
- Investigate facts available from code, documentation, configuration, or existing evidence directly.
- Resolve feasibility and performance uncertainty through an appropriately scoped probe within existing authorization; planning does not authorize costly or consequential experiments.
- For low-impact, reversible implementation details, choose a reasonable default and label the assumption and reconsideration trigger.
- Ask the user about goals, priorities, acceptable tradeoffs, or commitments that require their intent only when the answer materially affects the current plan and is needed now. Reuse prior answers and permissions.
- Investigate consequential downstream choices on unselected viable paths conditionally, without confirming them. Defer only details that cannot yet be usefully analyzed; give the exact missing prerequisite, why further investigation cannot resolve it now, and the reopening action. An unselected parent alone is not grounds to defer.
When asking, mark the decision in the graph and give concrete options, consequences, and a recommendation with its reason. Group closely related questions; do not require the user to complete the entire tree. Continue independent investigation while awaiting an answer, but do not finalize a dependent branch or treat silence as approval. Update the graph after answers or new evidence, preserving decisions and their rationale.

## Non-negotiable safeguards
- Never convert an unknown probability into a claimed failure rate. Prefer severity × likelihood bands with confidence labels and sensitivity analysis over unsupported precise expected values.
- Never optimize an unsafe route simply because its numeric score is high.
- Minimize irreversible actions. Specify containment for data leaks; rollback cannot undo leaked data.
- Switch thresholds must mention the exact observation window and evaluation mechanism.
- A decision log is append-only; supersede decisions rather than erasing them.
- For software systems, distinguish design tests, simulated failure injection, and actual deployment evidence.

## Quality check
- Every critical risk points to an earliest prevention point, detection signal, immediate containment, and fallback.
- Every high-impact node has ≥2 considered alternatives or a documented impossibility.
- Each critical branch has measurable gate criteria and a named accountable role.
- Decision graph has no dead-end failure route unless explicitly `STOP/ESCALATE`.
- ADR references resolve; assumptions vs verified observations are labeled.
- Choices, compatible parallel work, and observed gate outcomes are visually distinct; shared subdecisions are linked rather than duplicated.
- Material unknowns have resolution routes; only current decisions requiring user intent are asked.
- The overview makes the current position, recommendation, pending user decisions, and next verification visible.
- Coverage includes distinct approach families, all viable paths have consequential downstream expansion, and each terminal/unexplored frontier has a substantive stopping reason and next action. Overview folding is not pruning research. Review the graph audit output without padding nodes to silence warnings.

## Optional integration
Use Hooks or scheduled checks only to collect evidence or request re-evaluation. Do not authorize installs/deletions automatically. Trigger blueprint review on gate failure, changed constraints, repeated incident, new dependency, or material external change. Respect user confirmation rules for any write to live systems.
