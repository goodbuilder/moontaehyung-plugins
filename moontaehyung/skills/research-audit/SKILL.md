---
name: research-audit
description: Independently audit RIS research coverage, evidence quality, causal integrity, plan feasibility, and conditional forecasts before project pre-analysis is accepted.
---

# Research Audit

Use this workflow for an independent audit of a substantial RIS project pre-analysis. Read the original goal and constraints, canonical research notes, the active Project Plan, and the evidence cited for material claims. Do not rely on the Coordinator's preferred conclusion as an answer key.

For substantial pre-analysis, retain the four standing checks and add the fifth when causal claims affect the outcome.

1. **Coverage:** credible approach families, viable alternatives, unsupported exclusions, contrary evidence, and unresolved frontier.
2. **Evidence:** source identity and locator, actual review scope, claim support, calculations and assumptions, access limitations, and missing evidence.
3. **Plan feasibility:** dependencies, resource assumptions, decision sequencing, verification gates, failure detection, containment, fallback, and reversibility.
4. **Forecast integrity:** comparable conditions, source or derivation, uncertainty, false precision, sensitivity to assumptions, and separation of forecasts from observations.
5. **Causal integrity:** when the conclusion depends on a mechanism or intervention, trace the
   decisive causal claims and cross-direction investigations using the [audit contract](references/audit-contract.md#causal-integrity).
   A factual lookup can leave this area outside scope with a reason.

Return one status: `PASS`, `FAIL`, `BLOCKED`, or `NOT_RUN`. Use `PASS` only when no material failure remains in the assigned scope. Use `FAIL` for a material, correctable defect; `BLOCKED` when a material question lacks an available discriminating action or evidence source; and `NOT_RUN` when the audit was not performed.

For each material finding, follow [the audit contract](references/audit-contract.md). Identify the smallest correction, its canonical owner, and what needs re-audit. Do not make canonical edits. Do not ask for generic additional research when a concrete gap can be stated.

This Skill does not replace `reviewer` for manuscript/report/presentation review, Project Plan for the decision graph, or `verify-check` for executable verification. An audit recommendation does not authorize an experiment, purchase, deployment, or external change.
