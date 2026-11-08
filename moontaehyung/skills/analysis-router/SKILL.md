---
name: analysis-router
description: Select and coordinate AAR, RCA, RMEA, FTA, MCDA, risk planning, ADR, and verification workflows when a request crosses their boundaries or needs multiple analyses. Resolve consequential ambiguity by comparing candidate workflows independently through auto-subagents; skip routing overhead for an obvious local task.
---

# Analysis Router

Own workflow selection, the complete candidate-comparison protocol, and synthesis. The selected methods own their analyses; [auto-subagents](../auto-subagents/SKILL.md) supplies general delegation mechanics only and does not depend on this router. Explicit user choice takes priority. Do not interpret a request for analysis as authorization to implement recommendations.

## Choose the smallest sufficient workflow

| Need | Primary workflow | Distinction |
|---|---|---|
| Learn from completed work, including successes | aar | Overall expectations, observations, sustain/change actions |
| Explain an actual important failure | rca | Evidence-backed causal diagnosis; ordinary obvious fixes need no formal RCA |
| Identify and prioritize prospective risk modes | rmea | Register of modes, effects, controls, actions, residual risk; declare the method definition |
| Explain combinations producing a defined failure | fta | Logical model and minimal cut sets, not proof an incident followed that path |
| Choose between credible options with conflicting criteria | mcda | Explicit value scales, weights, trade-offs and switching conditions |
| Plan consequential branches, gates and fallbacks | project-plan | Integrates analyses into execution routes; does not repeat their tables |
| Record a material architectural choice | architecture-decision-record | Decision history, not another selection or approval process |
| Verify authorized multi-step changes and recovery | verify-check | Implementation and outcome evidence, not another causal report |

Read only the selected skills and genuinely needed companions. Resolve installed skills by the session catalog; the four sibling methods are linked below. Do not assume a named companion is installed. If missing, perform a bounded local equivalent and disclose the limitation; do not install it automatically.

## Boundary procedure
1. State the requested outcome, available evidence, candidate workflows (normally two), and the specific ambiguity. First distinguish missing facts or user preferences from ambiguity about methods: agents cannot invent either.
2. If the distinction is clear from the table, route directly. Use comparison when both candidates are credible and choosing incorrectly could materially change the investigation, decision, or effort. Do not compare every routine request. Before dispatch, define task-specific acceptance questions using the comparison criteria in step 5.
3. Read the available `auto-subagents` skill. It owns delegation mechanics. Give each worker the same immutable source evidence, requested outcome, constraints, allowed actions, and its assigned candidate skill. Each performs that method, not a sales pitch for it. Start fresh contexts without inherited conversation history (use `fork_turns="none"` where supported), and supply a compact brief with governing constraints but without the coordinator's preferred answer or other worker's result. If context isolation cannot be guaranteed, disclose that limitation. Require workers not to delegate or invoke this router.
4. Use read-only execution or separate output directories. Workers may produce draft reports/calculations within the assigned scope but cannot edit source records, accept risk, make a final decision for the user, or take external actions. Normally use two workers, one per candidate, and one comparison round. If delegation is unavailable, compare locally and disclose the loss of independent evaluation.
5. Collect concrete method outputs, supporting/contrary evidence and unresolved uncertainty. Compare useful discoveries, source support, contradictions and omissions, actionable output, unresolved uncertainty, and effort/questions against the predefined acceptance questions. Arithmetic validity and evidence outrank polish, length, or votes. Disqualify unsupported decisive conclusions. Use execution records for time/cost claims; do not invent measurements.
6. Synthesize: select one; sequence complementary methods; consolidate a duplicated step; or defer because evidence/preferences are missing. Inspect cited evidence and calculations. Ask only the missing question that materially changes the result; a third agent is not a substitute for missing input. Follow up only on specific conflicting evidence, not unlimited tournaments.
7. Return one integrated result with the selected route and concise reason. Preserve useful unique findings and unresolved disagreements. Reference worker artifacts instead of producing duplicate canonical registers. Keep a short routing note in existing task notes; create a persistent routing log only when requested or needed for an ongoing project. A single case supports a local choice, not an automatic global trigger edit.

## Ownership and handoffs
Read [references/handoffs.md](references/handoffs.md) for a multi-method analysis or overlap with existing broad RCA/project-plan instructions. Reuse scope, evidence, IDs, permissions and active assignments. Do not recursively route or start the same analysis again under a new skill name.

Sibling methods: [AAR](../aar/SKILL.md), [RMEA](../rmea/SKILL.md), [FTA](../fta/SKILL.md), [MCDA](../mcda/SKILL.md).

## Completion
The chosen workflow answers the user's question or states the specific unresolved blocker. Report comparative execution only if actually performed. Selection, analysis completion, implementation completion and verified effect are separate statuses. Never claim a skill has been activated merely because its files exist.

For maintenance or questions about validation, read [references/evaluation.md](references/evaluation.md); it records initial synthetic checks and their limits, not routing evidence for the current user's case.
