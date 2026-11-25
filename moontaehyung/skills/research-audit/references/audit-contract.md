# RIS audit contract

## Status

- `PASS`: the assigned audit scope was inspected and no material defect remains.
- `FAIL`: at least one material, correctable defect remains.
- `BLOCKED`: a material criterion cannot be resolved with available evidence or authorized actions. State the missing input or capability and its effect.
- `NOT_RUN`: the audit did not happen. Do not convert an unavailable Auditor into a pass.

An overall status is not a vote. Record which artifacts and claims were actually inspected. A partial audit may return `BLOCKED` or `NOT_RUN`; state the inspected scope.

For a governed RIS finding, freeze each separable decision question and its required evidence
axes with `findings obligate` before inspecting the producer result. Compare inspected sources
to the observed output, actual return, integration and exact final answer. Check the authorization,
origin and revision at each boundary. Document whether decisions changed because of new evidence,
user contribution or unverified inference. Accept only the inspected question and revision.
If no separate context or trusted release boundary exists, preserve the concern as HOLD and
describe the available self-check. A different value of `specified_by` cannot establish independence.

## Blind scope and independent context

Use this protocol at a consequential decision, a material scope change, and an exhaustive or
acceptance claim. Scale depth to consequence; ordinary factual checks need no ceremony.

1. Give the Auditor the original user objective, HARD constraints, authorized actions, relevant
   domain evidence and environment/resource limits. Initially withhold producer conclusions,
   proposed answer, coverage checklist, release map and seeded-defect labels. Do not remove
   facts necessary to understand the problem merely to create blindness.
2. Independently reconstruct decision-sensitive questions, credible mechanism and solution
   families, exclusions needing support, dependencies, acceptance/failure conditions and unknown
   frontier. Include questions absent from the producer's ontology. Freeze this initial input
   manifest and reconstructed scope with revision/hash and timestamp in the authorized audit
   record before the release map is disclosed. Never overwrite this baseline after disclosure.
3. Release the producer artifacts and coverage map. Compare both directions: every reconstructed
   consequential question has a supported disposition; every producer conclusion has a justified
   scope and evidence chain. Record omissions, newly discovered questions, and justified scope
   changes as deltas. Exhaustive means every relevant family has an evidenced disposition or an
   explicit unresolved boundary, not that every imaginable fact was inspected.
4. Inspect the ten domains below, including cross-domain dependencies and contrary evidence.
   Uninspected consequential scope prevents an unqualified PASS. A clean case may PASS; do not
   manufacture a defect or reward a longer list of immaterial questions.

Independence is an observed property. Use a fresh context without the producer's private reasoning,
answer or answer-key history; record the session/worker identity, supplied-input manifest and when
producer artifacts were released. A new role name or a separate prompt in the same contaminated
context is insufficient. Check actual tool/file capabilities: permitted input paths, readable output
paths, write restrictions, network and shared state. Prefer a read-only input snapshot and separate
output location with runtime-enforced denial of canonical writes; verify the boundary with a harmless
probe outside protected records. Record both observed allows and denies. Separate directories,
worktrees, instructions and claimed role identities alone do not establish filesystem isolation.
Do not probe secrets or protected data. If fresh context or enforcement cannot be obtained, report
that exact limitation and any feasible partial checks; do not claim a blind independent acceptance.

## Ten integrity domains

For each domain record inspected artifact/claim revisions, evidence, finding or justified
non-applicability, uncertainty and decision impact. The domains extend the standing checks rather
than replacing them. They are coverage prompts, never an answer key or fixed ceiling.

1. **Problem Integrity:** original outcome, HARD constraints, decision-sensitive questions, user
   authority, inferred versus explicit requirements, measurement meaning, and material scope changes.
2. **Coverage:** credible mechanism and solution families, contrary evidence, unsupported exclusions,
   unexpected consequential questions, unresolved frontier and evidenced stopping boundaries.
3. **Causal Integrity:** decisive links, rivals, interactions, changed/absent-cause predictions and
   executed bidirectional causal/solution investigation as specified below.
4. **Evidence Integrity:** source identity, passage/locator, actual review scope, access limits,
   claim support, revision, absence versus missing evidence, and recomputable quantities with units,
   baselines, variable roles, assumptions and error; never replace unknowns with fabricated precision.
5. **Feasibility:** dependencies, resources, actual capability versus design budget, costs,
   comparable conditions, sequencing and resource boundaries.
6. **Composition:** compatible combinations, interfaces, interactions, dependency closure and
   preservation of viable alternatives; component plausibility does not establish system feasibility.
7. **Forecast Integrity:** conditional forecasts versus observations, derivations, sensitivity,
   calibration limits and uncertainty that could reverse a recommendation.
8. **Strategy Integrity:** decision sequencing, discriminating investigations, acceptance/failure
   criteria, fallback, reversibility and whether valuable feasible work remains at closure.
9. **Recovery Integrity:** failure detection, containment, checkpoints, retry safety, dependency
   invalidation, canonical-owner rework and re-audit through consistent artifact revisions.
10. **Completion Integrity:** outcome and acceptance evidence, static/controlled/real evidence
    distinctions, preserved audit history, residual boundaries, actual context/file independence,
    host intervention and unsupported completeness or autonomy claims.

## Causal integrity

For each mechanism that could change the decision, trace the original phenomenon, measurement
chain and conditions. Inspect support for each decisive link, including adverse cases and plausible
rival or interacting causes. Check whether the claimed intervention changes the cause, transmission
path or outcome under those conditions. Recompute a decision-sensitive quantity when possible.
Separate observed effects from hypothesized mechanisms.

Compare predictions under a changed or absent cause. Could the available observations or proposed
test distinguish the alternatives? Record residual uncertainty and its effect on feasibility,
recommendation and stopping. To credit bidirectional exploration, trace a cause-originated solution
inquiry and an option-originated causal inquiry through their triggers, subsequent actions, evidence
and resulting revisions. Inspect whether unchanged findings still apply. When a connection was
unnecessary or could not be investigated, report that scope or boundary explicitly. A list of
possible links supplies no execution evidence. Check whether a valuable, feasible investigation
remained at closure.

## Audit record

Use an existing authorized audit record; this contract creates no permission to record private
conversations or alter frozen evidence. Capture at least:

```yaml
audit_id: audit-001
revision: 1
trigger: consequential_decision | scope_change | acceptance
subject_revision: "artifact revision/hash"
original_input_manifest: "paths, revisions/hashes, authorized scope"
blind_scope_snapshot: "immutable reference and freeze timestamp"
producer_release: "manifest and disclosure timestamp after scope freeze"
reviewer_context: "identity, prior exposure, observed fresh-context boundary"
isolation: "actual tool/file allows, denies, probes and limitations"
domain_dispositions: "all ten: inspected references, findings or justified non-applicability"
prior_audit: "superseded audit/finding references, if any"
rework: "owner, corrected revisions, invalidated dependencies, re-audit evidence"
status: PASS | FAIL | BLOCKED | NOT_RUN
uninspected_scope: "remaining consequential questions and effect"
```

## Finding fields

Each material finding contains:

```yaml
id: A-001
severity: critical | high | medium | low
scope: research | evidence | plan | forecast | causal
reference: .ris/research/plans/main-plan.md#D-001
evidence: "Specific source passage, artifact content, calculation, or missing required item"
impact: "How this changes feasibility, comparison, or the final claim"
required_correction: "Smallest concrete change or investigation that resolves the defect"
owner: researcher | engineer | planner | coordinator
re_audit: "The exact corrected claim, node, or scope to inspect again"
residual_uncertainty: "What remains unknown after the correction"
```

Use references to canonical artifacts and external sources; do not copy a second research report into the finding. Distinguish a missing source from evidence that the claim is false. Do not report style preferences as material defects.

The example path is the schema v2 default. In a schema v1 or explicitly migrated project, cite the
actual configured canonical path instead; a layout migration does not make old audit references
invalid or authorize rewriting unrelated records.

## Rework boundary

Preserve an audit chain: audit ID and revision, original input/scope snapshot, released producer
snapshot, findings, owner corrections with changed artifact revisions, invalidated dependencies,
re-audit assignment and inspected evidence, final disposition, and residual boundaries. Corrections
must be made by the canonical owner, not silently patched by the Auditor. Freeze superseded
findings as history and link their resolution; do not erase a FAIL to obtain a clean latest report.
A material scope change triggers a new blind reconstruction for the changed decision using a fresh
uncontaminated reviewer where possible; disclose prior exposure if only a partial re-audit is feasible.

The Coordinator routes each finding to its canonical owner and reopens only affected tasks plus dependencies invalidated by the correction. Unaffected evidence and plan nodes remain valid unless the finding explains why they depend on the defect. Re-audit the corrected scope. If no new evidence, discriminating analysis, corrected input, or changed assumption is available, retain `BLOCKED` with the specific limit rather than repeating work.
