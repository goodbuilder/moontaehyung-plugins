---
name: fta
description: Perform Fault Tree Analysis of a defined undesirable event using AND/OR logic, event definitions, minimal cut sets, and mitigations. Use for prospective failure-path analysis or incident hypotheses; an FTA alone does not establish the actual cause of an incident.
---

# Fault Tree Analysis

Support qualitative static coherent AND/OR trees by default. Order-dependent failures, repair, switching behavior, or noncoherent logic require an explicit suitable model or a stated limitation; do not silently flatten them into static gates. For ambiguous routing use an available analysis-router.

## Process
1. Define the top event precisely, including observable failure criteria, system boundary, operating mode, and time horizon.
2. Decompose sufficient causal conditions using OR (any input suffices) and AND (all inputs are required). Verify the logic against the system behavior. Document missing prerequisites and dependencies.
3. Stop at basic events that can be investigated or assigned controls. Mark undeveloped events and analysis limits. Give repeated occurrences of the same event one identity; examine common-cause failures and shared resources.
4. Derive minimal cut sets: the smallest combinations sufficient to produce the top event. Remove duplicate and nonminimal combinations. Check representative combinations against the tree. If exhaustive enumeration is impractical, state the algorithm, bounds, and omissions; label the result partial.
5. Identify single points of failure and consequential combinations. Map each to prevention, detection, or mitigation and an appropriate verification.
6. Quantify only when event probabilities, time bases, and dependency assumptions are supported. For independent inputs, AND uses a product and OR uses one minus the product of complements. Do not apply independence formulas to dependent or repeated events, or sum overlapping cut-set probabilities as an exact result. Qualitative analysis is valid when data are absent.
7. Trace gate conditions to system evidence and check completeness against interfaces, shared resources and operating modes. Treat intentionally undeveloped branches as unknown, not verified basic events. For small trees derive Boolean expressions and check cut-set sufficiency and minimality; for larger trees use a suitable solver or label the result partial. Keep event IDs consistent across the diagram, dictionary and calculations. Do not equate failure rates with probabilities or mix mission-time and demand-based data; if quantitative results are given, disclose input uncertainty and influential assumptions.

## Output contract
For a small analysis, show a readable diagram and tables directly in chat. When files are needed, default to an SVG fault-tree diagram plus a Markdown report; honor explicit format requests. Use an available diagram workflow or renderer and visually inspect exported diagrams for legibility, clipping, and gate labels. If rendering is unavailable, deliver a clearly labeled source/text fallback.

The report contains scope and top event; assumptions; an event dictionary (ID, definition, type, evidence, status); a readable diagram; minimal cut sets; mitigations; uncertainties and undeveloped branches. Include a quantitative section only when justified, with inputs, sources, equations, units/time bases, and assumptions.
If system structure is unverified, label the tree provisional and its cut sets conditional on named assumptions, or defer cut-set derivation and list the structural evidence needed. Never fabricate a complete tree to satisfy the output contract.

| Cut set | Failure meaning | Evidence or assumption | Prevention or mitigation | Verification |
|---|---|---|---|---|

Distinguish modeled possibilities from event paths confirmed by incident evidence. Connect findings to an existing risk register or RCA without duplicating its records.

## Completion
Gate logic and event identities have been checked, important minimal cut sets and single failure points are reported, and analysis limits are visible. A diagram alone is insufficient; proposed mitigations remain proposals until implemented and verified.
