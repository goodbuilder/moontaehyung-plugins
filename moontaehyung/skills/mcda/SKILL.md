---
name: mcda
description: Compare alternatives using Multi-Criteria Decision Analysis with explicit criteria, scales, weights, evidence, and sensitivity analysis. Use for consequential trade-offs across multiple criteria; record architectural decisions in an available ADR workflow when appropriate.
---

# Multi-Criteria Decision Analysis

The default supported method is additive weighted-value comparison, not every MCDA technique. Use another method only when its assumptions and procedure can be justified; identify it explicitly. For ambiguous routing use an available analysis-router.

## Process
1. Define the decision, credible alternatives, baseline where relevant, and decision owner. Reuse stated user priorities; do not invent preferences or treat silence as selection.
2. Confirm feasible alternatives and separate mandatory constraints from compensable criteria. Exclude or conditionally hold alternatives that fail mandatory constraints before calculating scores; superior scores cannot offset a mandatory failure. Identify dominated options and justify retaining any in the detailed comparison.
3. Define distinct criteria, performance measures, score directions, and anchored value scales. Check double-counting and interactions. Use a justified method; for additive weighted scoring, explain its suitability and limitations.
4. Gather raw performance data with sources and uncertainty. Define the transformation from raw measures to comparable value scores, explaining nonlinear thresholds or saturation where relevant. Do not mix units directly or disguise missing data as average performance. For missing consequential inputs use justified bounds or defer ranking and identify the measurement needed.
5. Elicit or state provisional weights with their rationale. For additive scoring, weights reflect the value of moving across each criterion's defined performance range, not just abstract importance. Normalize weights consistently and show the aggregation formula. Keep stakeholder preferences separate unless an aggregation rule is agreed. Without confirmed preferences, present provisional scenarios rather than an unconditional winner.
6. Evaluate alternatives and vary plausible weights and uncertain inputs, including switching thresholds for leading contenders. Identify rank reversals, ties, and conditions under which a different alternative wins. Match displayed precision to evidence. Do not call a recommendation robust without sensitivity evidence or a defined plausible variation range.
7. Recommend an alternative with trade-offs, unresolved evidence, and reconsideration triggers. Distinguish analytical recommendation from an authorized final decision. Use an available ADR workflow when an architectural decision record is in scope.

## Output contract
For a small comparison, provide the matrix and sensitivity findings in chat. When files are needed, default to an XLSX workbook with traceable formulas plus a short Markdown report. Use an available spreadsheet workflow and honor explicit format requests. Disclose any fallback if workbook generation is unavailable.

Workbook sheets: Scope and Constraints; Criteria and Weights; Raw Data and Sources; Scores; Sensitivity. Preserve calculation formulas and make raw values, transformed scores, assumptions, and missing values distinguishable. Do not fabricate inputs to complete the matrix.
Use a supported spreadsheet workflow to recalculate formulas, check weight totals and score directions, compare representative totals with an independent calculation, and ensure missing inputs do not silently become zero. Inspect rendered tables for clipping and readability. Preserve input sources, analysis version and prior decisions when updating.

Display matrix:

| Criterion | Scale and direction | Weight | Alternative A | Alternative B | Alternative C |
|---|---|---|---|---|---|

Adapt the number of alternatives to the actual decision. Label the result recommendation-ready, conditional comparison, or ranking deferred for missing inputs. Include total scores, ranks and sensitivity results only where inputs and calculations justify them. Otherwise provide the constraint table, known performance, missing inputs and resolution plan without fabricated totals. Where sensitivity can be calculated, show scenarios, changed inputs, winner, and switching conditions.

The report leads with the recommendation and its status, then explains decisive trade-offs, evidence quality, sensitivity findings, and what could change the selection.

## Completion
For a recommendation-ready result, trace the recommendation from evidence through value scales and weights to calculations and examine ranking stability. A conditional or deferred result instead identifies why ranking is unjustified and what evidence or preferences would resolve it. Mandatory constraints and uncertainty remain visible in every status. A highest score alone is not a sufficient conclusion or authorization to implement the choice.
