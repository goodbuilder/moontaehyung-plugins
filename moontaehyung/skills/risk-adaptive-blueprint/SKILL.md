---
name: risk-adaptive-blueprint
description: Design or revise a project's risk-adaptive decision blueprint with branching implementation choices, failure modes, quality gates, fallback routes, and evidence-based switch criteria. Use for project planning, pre-mortems, architecture alternatives, risk-triggered replanning, or converting an RCA into preventive decisions. Pair with architecture-decision-record when a choice is made or revised.
---

# Risk-Adaptive Project Blueprint

## Goal and boundary
Maintain a **decision graph** rather than a single fixed roadmap. Identify choices, testable assumptions, risk triggers, escape routes, and earliest preventable failure points. A blueprint proposes options; it does **not** silently authorize high-impact changes.

## Inputs
- Goal and non-goals; constraints; current project stage; environments and stakeholders.
- Existing requirements, code, incidents, ADRs and evidence, when available.
- If sources are unavailable, flag unknowns explicitly; do not invent empirical incident frequencies.

## Workflow
1. **Frame:** Summarize purpose, inputs, process, outputs, and highest-risk failure outcomes. Separate verified facts, assumptions, and inferences.
2. **Decompose:** Build decision nodes (`D-###`), milestones (`M-###`), and gates (`G-###`). Avoid single-path plans: every high-impact decision needs a baseline, a credible fallback, and a reversible exit if possible.
3. **Analyze:** For every branch describe preconditions, benefits, costs, dependencies, failure modes, affected assets, reversibility, and an earliest prevention point. Use pre-mortem and RCA hypotheses; do not label untested hypotheses as root causes.
4. **Measure:** Specify leading indicators, measurement source, observation window, thresholds, and owners. Mark numerical thresholds *provisional* until calibrated. Qualitative safety invariants (e.g. never delete unmanaged user files) override weighted scores.
5. **Gate:** For each milestone write verifiable acceptance criteria, failure response, hold/rollback actions, and route to an alternative. A gate must not depend on undocumented intuition.
6. **Link ADRs:** For each selected or changed decision create/update an ADR using the `architecture-decision-record` skill. Reference its ID from each decision node; do not duplicate decision rationale across artifacts.
7. **Produce artifacts:** Create `blueprint.md`, `decision-graph.dot` (Graphviz source, if chart requested), `risk-register.csv`, and `decision-log.md` as needed. Use `assets/blueprint-template.md` and `assets/risk-register-template.csv`. If Graphviz is installed, render SVG; if not, provide the DOT as editable source. Preserve existing artifact version and history.
8. **Review:** Run the checklist below and explain which choices remain unverified. New evidence triggers review of relevant nodes, not a wholesale rewrite.

## Decision-node contract
Every `D-###` must specify: question, alternatives (at least two unless impossible), current default, assumptions, evidence, owner, expected benefit, cost, failure mode, reversibility, early warning metric, switch threshold, fallback route, linked ADR and last-reviewed date.

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

## Optional integration
Use Hooks or scheduled checks only to collect evidence or request re-evaluation. Do not authorize installs/deletions automatically. Trigger blueprint review on gate failure, changed constraints, repeated incident, new dependency, or material external change. Respect user confirmation rules for any write to live systems.
