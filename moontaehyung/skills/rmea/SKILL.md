---
name: rmea
description: Perform Risk Mode and Effect Analysis to identify potential risk modes, their causes and impacts, existing controls, response priorities, and residual risk. Use for structured prospective risk assessment; use FTA for logical combinations producing a specific failure.
---

# Risk Mode and Effect Analysis

## Method and scope
Use RMEA here to mean Risk Mode and Effect Analysis. This label has varying usage: state this definition and the selected assessment rules, and preserve a supplied organizational method rather than claiming a universal RMEA standard. Relate the analysis to the active risk plan if one exists.
If the user means a different expansion or requires formal FMEA compliance, clarify the method before rating; do not relabel this generic workflow as a certified FMEA procedure. For ambiguous routing, use an available analysis-router.

## Process
1. Define the objective, system or process boundary, operating conditions, assessment horizon, and acceptance authority.
2. Identify risk modes by process step or component. Record causes, local and overall effects, affected assets, and existing prevention and detection controls.
3. Define anchored scales for severity, likelihood, and detection difficulty before rating. Make score direction explicit: a larger detection-difficulty score means harder detection. Separate measured data, estimates, and unknowns; never fabricate failure frequencies.
4. Rate each risk with its evidence and uncertainty. State the prioritization rule. If using a product score, retain the component ratings and do not treat multiplication of ordinal ratings as a measured probability or expected loss. Escalate severe consequences separately rather than hiding them behind a low product.
5. Specify prevention, detection, containment, or mitigation actions, owners, dates, and effectiveness checks.
6. Reassess residual risk. Distinguish predicted residual ratings from ratings supported by completed controls and verification. Record acceptance as proposed unless the responsible authority has accepted it.
7. Check coverage against functions, requirements and operating phases; merge duplicate modes while preserving distinct causes/effects. Review common resources and interacting risks, referring a specific combination question to FTA only if needed. Detection ratings concern detection before the relevant harm; distinguish later alarms. Reassess after verified controls, incidents, changed conditions, or invalidated assumptions. Preserve the previous ratings, method version and history.

## Output contract
For a small analysis, show the table in chat. When a file is needed, default to an XLSX workbook using an available spreadsheet workflow; honor explicit format requests. Use a Markdown or CSV fallback only if the workbook cannot be produced, and disclose the fallback.

Workbook sheets: Method (scope, definitions, scales, thresholds, assumptions); Risk Register; Actions (linked by risk ID); Evidence where needed. Preserve formulas for derived priorities and explain them; do not hardcode calculated results.
Use the project's existing anchored scales and acceptance rules where available. When absent, state provisional scales before applying them; do not treat invented thresholds as organizational policy. Recalculate the workbook with a supported spreadsheet workflow, check representative priorities and blank/unknown inputs, and inspect the rendered register for usable widths, filters and clipping. Preserve manually maintained owners and actions on updates.

Risk Register columns:

| ID | Step or component | Risk mode | Causes | Effects | Existing controls | Severity | Likelihood | Detection difficulty | Evidence and uncertainty | Priority and rationale | Action IDs | Residual ratings and status | Acceptance status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Actions must include owner, deadline or trigger, and verification. Leave unknowns explicitly unknown rather than assigning a neutral score. Summarize the highest priorities and unresolved assessment gaps above or alongside the workbook.

## Completion
Material risks have controls or proposed actions, explicit residual-risk status, and acceptance responsibility. Producing the register does not implement controls or authorize risk acceptance.
