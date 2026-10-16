---
name: risk-plan
description: Design or revise a project's risk-adaptive decision blueprint with branching implementation choices, failure modes, quality gates, fallback routes, and evidence-based switch criteria. Use for project planning, pre-mortems, architecture alternatives, risk-triggered replanning, or converting an RCA into preventive decisions. Pair with architecture-decision-record when a choice is made or revised.
---

# Risk Plan

## Goal and boundary
Maintain a **decision graph** rather than a single fixed roadmap. Identify choices, testable assumptions, risk triggers, escape routes, and earliest preventable failure points. A blueprint proposes options; it does **not** silently authorize high-impact changes.

## Inputs
- Goal and non-goals; constraints; current project stage; environments and stakeholders.
- Existing requirements, code, incidents, ADRs and evidence, when available.
- If sources are unavailable, flag unknowns explicitly; do not invent empirical incident frequencies.

## Workflow
1. **Frame:** Summarize purpose, inputs, process, outputs, and highest-risk failure outcomes. Separate verified facts, assumptions, and inferences.
2. **Decompose:** Discover unresolved questions from the goal, constraints, actual workflow and evidence. Build decision nodes (`D-###`), milestones (`M-###`), and gates (`G-###`). For each candidate, assume it is selected and identify the prerequisites and subsequent decisions it introduces. Repeat only where further detail can change a decision. Follow [gates and branching rules](references/gates-and-branching.md) for expansion and stopping rules. Every high-impact decision needs a baseline, a credible fallback, and a reversible exit if possible.
3. **Analyze:** For every branch describe preconditions, benefits, costs, dependencies, failure modes, affected assets, reversibility, and an earliest prevention point. Use pre-mortem and RCA hypotheses; do not label untested hypotheses as root causes.
4. **Measure:** Specify leading indicators, measurement source, observation window, thresholds, and owners. Mark numerical thresholds *provisional* until calibrated. Qualitative safety invariants (e.g. never delete unmanaged user files) override weighted scores.
5. **Gate:** For each milestone write verifiable acceptance criteria, failure response, hold/rollback actions, and route to an alternative. A gate must not depend on undocumented intuition.
6. **Link ADRs:** For each selected or changed decision create/update an ADR using the `architecture-decision-record` skill. Reference its ID from each decision node; do not duplicate decision rationale across artifacts.
7. **Show the decision graph:** Present consequential choices visually by default, without waiting for a chart request. Show the current question, comparable options, recommendation with reason, user decision points, and verification/fallback paths. Start with the relevant overview, usually 2–4 main options when that many are credible; expand the selected or uncertain branches as needed. Use a compact Mermaid or text diagram in conversation, or an interactive view when available and useful. Do not deliver only graph source that the user cannot readily view. Create `blueprint.md`, `risk-register.csv`, and `decision-log.md` only as needed; use [blueprint template](assets/blueprint-template.md) and [risk register template](assets/risk-register-template.csv). For an exported graph, Graphviz DOT plus rendered SVG is an option. Preserve existing artifact version and history.
8. **Review:** Run the checklist below and explain which choices remain unverified. New evidence triggers review of relevant nodes, not a wholesale rewrite.

## Decision-node contract
Every `D-###` must specify: question, alternatives (at least two unless impossible), current default, assumptions, evidence, owner, expected benefit, cost, failure mode, reversibility, early warning metric, switch threshold, fallback route, linked ADR and last-reviewed date.
Keep detailed records behind the overview; label unavailable evidence and not-yet-applicable fields instead of inventing values. Distinguish recommendation, provisional assumption, and confirmed selection.

## Resolve unknowns without excessive questions
Classify each material unknown as **investigate**, **experiment**, **assume and proceed**, **user decision**, or **defer**. Record the resolution owner, affected node, and when the answer becomes necessary.
- Investigate facts available from code, documentation, configuration, or existing evidence directly.
- Resolve feasibility and performance uncertainty through an appropriately scoped probe within existing authorization; planning does not authorize costly or consequential experiments.
- For low-impact, reversible implementation details, choose a reasonable default and label the assumption and reconsideration trigger.
- Ask the user about goals, priorities, acceptable tradeoffs, or commitments that require their intent only when the answer materially affects the current plan and is needed now. Reuse prior answers and permissions.
- Defer details belonging to unselected paths until they become relevant. Revisit them when their prerequisite is selected.
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

## Optional integration
Use Hooks or scheduled checks only to collect evidence or request re-evaluation. Do not authorize installs/deletions automatically. Trigger blueprint review on gate failure, changed constraints, repeated incident, new dependency, or material external change. Respect user confirmation rules for any write to live systems.
