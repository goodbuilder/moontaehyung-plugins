# Analysis ownership and handoffs

This contract coordinates an analysis using the new method skills with existing broader skills. It does not rewrite installed companions or override user instructions, their domain constraints, or permissions.

| Record | Owner | Other workflows consume |
|---|---|---|
| Expectations/outcomes and sustain/change lessons | AAR | RCA receives only the material failure question and evidence |
| Incident timeline, causal hypotheses, supporting/refuting evidence | RCA | AAR summarizes; FTA receives modeled failure question |
| Risk modes, ratings, controls and residual acceptance status | RMEA | project-plan references IDs and action priorities |
| Top event, event dictionary, tree and cut sets | FTA | RCA uses only confirmed incident paths as causal evidence; RMEA links modeled risks |
| Alternatives, value scales, weights, scores and sensitivity | MCDA | Decision owner makes the choice; ADR records it |
| Branches, gates, switch conditions, fallbacks | project-plan | Method reports supply inputs rather than duplicate blueprints |
| Historical choice, rationale, consequences and reversal triggers | ADR | References analysis versions and actual decision authority |
| Implementation checks and verified effects | verify-check | Analysis owners update only claims supported by verification |

Every handoff preserves the question, scope/time horizon, source references and versions, facts versus assumptions, unresolved items, linked existing IDs, permitted actions, and the expected deliverable. Do not fabricate IDs to replace established project records. Track proposed, implemented, and effect-verified actions separately.

Existing RCA may compare expectations and outcomes; reuse that comparison in AAR rather than repeat it. Existing project-plan may already contain risk tables and trade-off analysis; extract or reference adequate results instead of rerunning RMEA/MCDA. Existing ADR may already compare options; run MCDA only if that comparison leaves a material decision unresolved. Existing verification remains the authoritative acceptance record.

One coordinator owns the current route. A method may identify a need for another method but returns that need to the coordinator; workers do not call the router or spawn descendants. Sequence only where one method supplies necessary input to the next. Completion of a report does not authorize fixes, external writes, risk acceptance, or deployment.
