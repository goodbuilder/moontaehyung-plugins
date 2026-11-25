# RIS audit contract

## Status

- `PASS`: the assigned audit scope was inspected and no material defect remains.
- `FAIL`: at least one material, correctable defect remains.
- `BLOCKED`: a material criterion cannot be resolved with available evidence or authorized actions. State the missing input or capability and its effect.
- `NOT_RUN`: the audit did not happen. Do not convert an unavailable Auditor into a pass.

An overall status is not a vote. Record which artifacts and claims were actually inspected. A partial audit may return `BLOCKED` or `NOT_RUN`; state the inspected scope.

## Finding fields

Each material finding contains:

```yaml
id: A-001
severity: critical | high | medium | low
scope: research | evidence | plan | forecast
reference: .ris/research/plans/main-plan.md#D-001
evidence: "Specific source passage, artifact content, calculation, or missing required item"
impact: "How this changes feasibility, comparison, or the final claim"
required_correction: "Smallest concrete change or investigation that resolves the defect"
owner: researcher | planner | coordinator
re_audit: "The exact corrected claim, node, or scope to inspect again"
residual_uncertainty: "What remains unknown after the correction"
```

Use references to canonical artifacts and external sources; do not copy a second research report into the finding. Distinguish a missing source from evidence that the claim is false. Do not report style preferences as material defects.

The example path is the schema v2 default. In a schema v1 or explicitly migrated project, cite the
actual configured canonical path instead; a layout migration does not make old audit references
invalid or authorize rewriting unrelated records.

## Rework boundary

The Coordinator routes each finding to its canonical owner and reopens only affected tasks plus dependencies invalidated by the correction. Unaffected evidence and plan nodes remain valid unless the finding explains why they depend on the defect. Re-audit the corrected scope. If no new evidence, discriminating analysis, corrected input, or changed assumption is available, retain `BLOCKED` with the specific limit rather than repeating work.
