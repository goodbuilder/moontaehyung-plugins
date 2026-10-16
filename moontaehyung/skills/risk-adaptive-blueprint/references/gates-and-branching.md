# Practical branching rules

- A gate has `PASS`, `HOLD`, `PIVOT`, and `STOP` outcomes. `HOLD` collects evidence; `PIVOT` uses a mapped alternative; `STOP` freezes hazardous changes and escalates.
- Score candidate branches only after rejecting branches that break hard constraints.
- Prefer low-cost, reversible probes before committing to irreversible integrations.
- For uncertain numerical risks, describe plausible low/base/high scenarios and whether the preferred branch changes across them.
- Do not infer causation from a single post-incident correlation. Name candidate causes, observable discriminating tests and counterfactual prevention points.
- Preserve linkage: risk `R-###` → choice `D-###` → gate `G-###` → ADR-####.
