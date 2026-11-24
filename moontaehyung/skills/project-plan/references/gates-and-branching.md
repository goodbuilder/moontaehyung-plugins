# Practical branching rules

## Discover and expand branches
1. Trace the goal through the actual workflow, constraints, dependencies and measured bottlenecks. Identify questions whose answers change the route to success.
2. Generate credible alternatives from available mechanisms and resources, existing approaches, and relevant evidence. Include retaining the current approach when viable. Mark speculative candidates as unverified rather than presenting them as established options.
3. For each candidate, ask: what must be true, what must be decided next, what alternative mechanisms can satisfy that requirement, what evidence distinguishes them, and what happens if the requirement fails? Child decisions must arise from these consequences, not an arbitrary branching quota.
4. Label relations explicitly: **CHOOSE** for mutually exclusive alternatives, **AND** for compatible or jointly required work, and **IF** for observed conditions or gate outcomes. A failed test is not a user preference. Keep planned fallbacks distinct from alternatives available now.
5. Reuse stable node IDs when branches share a downstream decision. Connect fallback paths to existing nodes. The underlying structure is a graph; use tree-shaped views only where they preserve these relationships.
6. Reject hard-constraint violations with reasons, then deepen branches with consequential cost, risk, irreversibility, or uncertainty. Avoid enumerating every combination of compatible options; examine interactions that could change feasibility or the recommendation.
7. Use the autonomous coverage/expansion protocol below. A first executable step, a comparison table, an experiment proposal or an unmade user choice is not by itself an expansion boundary. Hypothesize each alternative conditionally and trace the decisions it introduces; mark empirical outcomes unknown rather than pretending the experiment was run. Stop a branch only at a justified frontier and record its reason and next action.

## Present the current decision
Compare options using the same relevant criteria: expected effect, time/cost, major risk and reversibility; use unknown labels when estimates lack evidence. Show a recommendation and rationale separately from confirmed choices. Start with the current decision and enough downstream consequences to assess it, then provide focused views of deeper branches. Include a relation legend, current position, pending questions and verification conditions. When updating, mark rejected or superseded paths with reasons rather than silently erasing the decision history.

## Gates

- A gate has `PASS`, `HOLD`, `PIVOT`, and `STOP` outcomes. `HOLD` collects evidence; `PIVOT` uses a mapped alternative; `STOP` freezes hazardous changes and escalates.
- Score candidate branches only after rejecting branches that break hard constraints.
- Prefer low-cost, reversible probes before committing to irreversible integrations.
- For uncertain numerical risks, describe plausible low/base/high scenarios and whether the preferred branch changes across them.
- Do not infer causation from a single post-incident correlation. Name candidate causes, observable discriminating tests and counterfactual prevention points.
- Preserve linkage: risk `R-###` → choice `D-###` → gate `G-###` → ADR-####.

## Autonomous breadth and depth protocol

### Breadth before recommendation
- Build a candidate inventory across relevant mechanisms, problem formulations, established and recent
  approaches, hybrids, resource-constrained routes, and a viable current/baseline approach. These are
  search lenses, not mandatory options or a numerical quota. Consult multiple relevant primary-source
  channels/families; record coverage and inaccessible/unsearched areas.
- Keep materially different ways of achieving the outcome. Do not offer cosmetic parameter variants
  as independent research directions, collapse a whole family into one unexplained "other", or stop
  discovery when two alternatives suffice for the minimum node schema.
- Before ranking, perform a counter-search for plausible omitted approaches and evidence against the
  leading recommendation. Exclusions require a concrete constraint or evidence, not familiarity.
  A naturally small candidate set is valid only after its search boundary is explained.

### Expand viable alternatives through consequences
- For every viable option, assume it is chosen and ask what must then be obtained, built, decided,
  learned and verified; create the next meaningful questions and their credible alternatives.
- Repeat across successive decision stages until the route from the outcome to validation and an
  actionable next investigation is understandable. Merely listing a sensor/method and a test is shallow.
  Include interacting data, method, integration/deployment, evaluation and fallback decisions where
  applicable; do not force irrelevant stages or duplicate shared subdecisions.
- Develop the strongest alternative and other viable mechanism families, not just the favorite.
  Detail can be uneven where evidence differs, but label the difference. Model both conditional
  probe outcomes and subsequent routes; user selection is needed to commit, not to forecast.
- Recheck the breadth inventory after deepening: a dependency discovered in one branch may expose a
  missing approach elsewhere. Prune only constraint violations, dominated/duplicated routes supported
  by evidence, or explicit user exclusions. Keep reasons and reopening conditions.

### Genuine expansion boundaries
- Terminal: the route is sufficiently specified through relevant downstream choices and verification;
  name what is ready to execute and what would invalidate it.
- Evidence limit: targeted investigation was attempted but a specific inaccessible source or unknown
  measurement prevents a useful distinction; name the attempt, missing fact and next probe. "More
  research needed" and an unselected prerequisite alone are insufficient.
- Intent boundary: an unresolved goal/priority materially changes the alternatives. Show conditional
  scenarios as far as useful, ask the narrow question and continue independent branches.
- Constraint or budget boundary: state the actual constraint or agreed budget, what remains unexamined,
  and the continuation order. Do not silently reinterpret a response-length preference as a research cap.

Report an explicit frontier per unexpanded option (`exploration_frontier` in the graph contract).
The coverage audit makes structural shallowness visible; passing it is not proof of research quality.

## Reuse choices across candidate solutions

Candidates are bundles, not disjoint buckets of options. Construct each plausible combination from
reusable decision/option references. Shared sensors, datasets, techniques or validation approaches
can occur in many candidates; compare the choices that differ without stripping shared choices.
Use single selection only for mutually exclusive options within the same candidate. Use multiple
selection for complementary choices (for example independent validation checks), and check declared
incompatibilities per candidate. Candidate overlap alone is never a reason to reject a candidate.
Keep evidence and option definitions canonical while preserving independent candidate memberships.
