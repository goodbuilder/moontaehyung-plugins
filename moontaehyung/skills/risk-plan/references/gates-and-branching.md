# Practical branching rules

## Discover and expand branches
1. Trace the goal through the actual workflow, constraints, dependencies and measured bottlenecks. Identify questions whose answers change the route to success.
2. Generate credible alternatives from available mechanisms and resources, existing approaches, and relevant evidence. Include retaining the current approach when viable. Mark speculative candidates as unverified rather than presenting them as established options.
3. For each candidate, ask: what must be true, what must be decided next, what alternative mechanisms can satisfy that requirement, what evidence distinguishes them, and what happens if the requirement fails? Child decisions must arise from these consequences, not an arbitrary branching quota.
4. Label relations explicitly: **CHOOSE** for mutually exclusive alternatives, **AND** for compatible or jointly required work, and **IF** for observed conditions or gate outcomes. A failed test is not a user preference. Keep planned fallbacks distinct from alternatives available now.
5. Reuse stable node IDs when branches share a downstream decision. Connect fallback paths to existing nodes. The underlying structure is a graph; use tree-shaped views only where they preserve these relationships.
6. Reject hard-constraint violations with reasons, then deepen branches with consequential cost, risk, irreversibility, or uncertainty. Avoid enumerating every combination of compatible options; examine interactions that could change feasibility or the recommendation.
7. Stop expansion at an executable and verifiable next step, an explicit user decision, a discriminating investigation/experiment, or a detail deferred until its prerequisite is selected. Do not invent detail beyond the evidence. Reopen the branch when new evidence or a selection warrants it.

## Present the current decision
Compare options using the same relevant criteria: expected effect, time/cost, major risk and reversibility; use unknown labels when estimates lack evidence. Show a recommendation and rationale separately from confirmed choices. Start with the current decision and enough downstream consequences to assess it, then provide focused views of deeper branches. Include a relation legend, current position, pending questions and verification conditions. When updating, mark rejected or superseded paths with reasons rather than silently erasing the decision history.

## Gates

- A gate has `PASS`, `HOLD`, `PIVOT`, and `STOP` outcomes. `HOLD` collects evidence; `PIVOT` uses a mapped alternative; `STOP` freezes hazardous changes and escalates.
- Score candidate branches only after rejecting branches that break hard constraints.
- Prefer low-cost, reversible probes before committing to irreversible integrations.
- For uncertain numerical risks, describe plausible low/base/high scenarios and whether the preferred branch changes across them.
- Do not infer causation from a single post-incident correlation. Name candidate causes, observable discriminating tests and counterfactual prevention points.
- Preserve linkage: risk `R-###` → choice `D-###` → gate `G-###` → ADR-####.
