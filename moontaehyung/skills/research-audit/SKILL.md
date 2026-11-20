---
name: research-audit
description: Independently audit substantial RIS research against its outcome, including evidence, consequential coverage, plan feasibility, and conditional forecasts.
---

# Research Audit

Use this workflow when the user requests an independent audit or when independent scrutiny materially improves a consequential RIS result. Read the original goal, active completion boundary and constraints, relevant canonical research and planning artifacts, and evidence cited for material claims. Do not rely on the Coordinator's preferred conclusion as an answer key.

Audit four areas:

1. **Coverage:** whether the research addresses the requested outcome and examines credible alternatives, assumptions, contrary evidence and unknowns that could materially change the result. Judge coverage against the active scope; do not require an exhaustive landscape or low-impact branches. An exclusion the user explicitly stated, with their wording recorded, is supported, not a coverage defect. Before an initial question round, check that the exploration gathered enough evidence to ground material questions. Before a later question round, check that plausible assumption branches and their consequences were investigated first. A branch awaiting a user decision is normal when evidence cannot settle it and its options and consequences are clear; fail it if it could have been resolved by evidence or a safe default.
2. **Evidence:** source identity and locator, actual review scope, claim support, calculations and assumptions, access limitations, and missing evidence.
3. **Plan feasibility:** dependencies, resource assumptions, decision sequencing, verification gates, failure detection, containment, fallback, and reversibility.
4. **Forecast integrity:** comparable conditions, source or derivation, uncertainty, false precision, sensitivity to assumptions, and separation of forecasts from observations.

Return one status: `PASS`, `FAIL`, `BLOCKED`, or `NOT_RUN`. Use `PASS` only when no material failure remains in the assigned scope. Use `FAIL` for a material, correctable defect; `BLOCKED` when a material question lacks an available discriminating action or evidence source; and `NOT_RUN` when the audit was not performed.

For each material finding, follow [the audit contract](references/audit-contract.md). Identify the smallest correction, its canonical owner, and what needs re-audit. Do not make canonical edits. Do not ask for generic additional research when a concrete gap can be stated.

This Skill does not replace `reviewer` for manuscript/report/presentation review, Project Plan for the decision graph, or `verify-check` for executable verification. An audit recommendation does not authorize an experiment, purchase, deployment, or external change.
