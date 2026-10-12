---
name: verify-check
description: Split substantial code or behavior changes into small, independently verifiable steps, verify their handoffs, and validate the original user workflow. Use for multi-step or cross-layer implementation, fixes, and reviews; scale checks to risk. Use rca when failures need deeper cause analysis.
---

# Verify Change

Break a requested change into slices that can be proven independently, then carry each slice
from its contract through implementation, failure behavior, and evidence. The purpose is change
verification, not a mandatory workflow for standalone investigations. Decomposition is internal:
do not require separate user requests or approval at each step. Continue within existing
authorization; this skill does not authorize additional system or external changes.

Read the shared [minimum sufficient change policy](../../references/minimum-sufficient-change.md)
before evaluating implementation choices. Scope the review to the requested behavior and
affected callers. For review or diagnosis, report findings; source edits and new persistent
records require authorization from the task or existing project workflow.

## Operating rules

- Establish the source of truth before editing: specification, existing contract, schema, user
  acceptance rule, or observed artifact. Record which one governs each slice.
- Build a slice map before making broad edits. Include dependencies and the smallest observable
  output for every slice.
- Define slices by independently verifiable behavior or a contract, not file count or layer alone.
  A coherent slice may span several files. If failure would leave several unrelated changes as
  possible explanations, split it further. Do not split a small fix merely to create more steps.
- Before editing a slice, define inputs, expected outputs, invariants, and verification methods.
  Do not weaken criteria to fit the implementation. Record user-directed scope changes or
  evidence-backed corrections to mistaken criteria explicitly.
- Do not rely on a failed or unverified prerequisite as though it passed. Continue independent
  work and investigation of the failure; block only work that requires that prerequisite to pass.
- Treat a round-trip test as internal consistency only. It is never the sole proof for a boundary
  format or an external device behavior.
- Use an independent oracle whenever possible: a raw/golden fixture, published schema, captured
  device response, alternate calculation, or hand-checked expected bytes. Do not derive both the
  expected value and the actual value through the same function under test.
- Test negative paths deliberately: malformed input, missing endpoint, timeout, retry, duplicate
  event, cancellation, partial success, stale state, and recovery where they apply.
- Preserve unrelated worktree changes. Do not claim hardware, network, or production behavior is
  verified when only a mock or unit test was run. Tie material evidence to the code version,
  runtime configuration, and session that produced it; current state does not prove past state.

For substantial work spanning multiple slices, maintain a durable audit ledger in the project's existing
change or verification documentation. Prefer an existing change packet's `verification.md`; if
none exists, create the smallest project-relative verification record needed for the work rather
than leaving the history only in chat. Append an entry after every completed, failed, blocked, or
not-run slice and immediately after discovering a defect or contract mismatch. Do not rewrite
earlier observations into the intended outcome; record status changes and superseding evidence.

Use the compact slice record below as the ledger; do not maintain duplicate planning and evidence
reports. Link commands, artifacts, and logs rather than copying large outputs. For small changes,
concise task notes and a final verification report suffice; do not create a documentation packet
by default. Preserve failed observations and append their resolution.

Persist material results before relying on a prerequisite or ending the work session. A required
`FAIL`, `BLOCKED`, or `NOT_RUN` prevents claiming that criterion passed, but does not prevent
investigating it or continuing independent work.

When a slice changes an architecture-facing owner, dependency, state/data/lifecycle boundary,
coordinate/time contract, persistence artifact, or user-visible architecture document, read the
shared [architecture refresh contract](../../references/architecture-refresh.md). Do not run
`$update-architecture` automatically. Unless the user explicitly requests that skill, record only
its `NOT_REQUESTED` status, risk, affected node IDs, reason, and suggested command in the ledger.

## Sequential workflow

### 1. Establish requirements and completion criteria

Before decomposition, turn the request into observable outcomes and identify consequential gaps.
A short prompt does not require a long interview, but a detailed implementation plan cannot repair
a mistaken understanding of the desired result.

- Separate explicit user requirements, existing contracts supported by code/docs/tests, and agent
  assumptions. Existing behavior is evidence, not automatically the desired behavior. Do not turn
  an inferred preference into a requirement or let legacy behavior override an explicit request.
- Identify scope, relevant actors and state transitions, and what observable result would satisfy
  the request. Separate required outcomes from optional improvements.
- Resolve questions from the conversation and available project evidence first. Ask concise,
  focused questions only when competing interpretations materially change scope, user-visible
  behavior, data preservation, external effects, or the meaning of completion. Do not ask the user
  to decide routine implementation details or reconfirm previously established requirements.
- Express completion as conditions, actions/inputs, expected results, and a way to observe them.
  Replace vague terms such as "stable" or "fast" with criteria supported by the user's intent or
  an established contract. Do not invent time limits, tolerances, or repetition counts and present
  them as agreed requirements. Label proposed test parameters as proposals or engineering choices;
  ask when they determine whether the user's goal is met.
- State low-impact assumptions and proceed when reasonable. If an answer is required to determine
  consequential behavior, keep the question pending and defer only dependent decisions or edits.
  Continue independent inspection, reproduction, and other authorized work. Silence is not agreement.
- Summarize material interpretations before broad edits, without requiring blanket plan approval.
  For substantial work, keep the outcome, requirement sources, acceptance criteria, and unresolved
  questions in the existing task record. Give criteria short IDs where useful for linking steps
  and final evidence. Do not add a second requirements document when an existing one suffices.

Define the final check of the original user workflow at the outset; component tests must not
become the completion criterion for a request that requires working integration. If requirements
change, update the affected criteria and dependencies explicitly and reassess affected evidence.

For substantial work, reuse the chosen approach and its rationale from the conversation or
existing task record, and turn assumptions affecting acceptance into focused checks. If a
material choice is unresolved, or fresh evidence invalidates it, return only that question
to its planning owner under the [implementation-choice policy](../../references/minimum-sufficient-change.md#choose-an-implementation). In standalone work,
resolve that narrow choice within the current task. Do not repeat settled comparisons or
block work solely because a separate decision document is absent.

### 2. Build the slice map

Consider the relevant boundaries below. They are prompts, not mandatory separate slices:

1. Contract: inputs, outputs, units, field order, schema, invariants, and ownership.
2. Pure logic: calculations, transformations, selection rules, and validation gates.
3. Boundary adapter: commands, serialization, parsing, device/API calls, and response mapping.
4. State and concurrency: lifecycle, ACK/readback, timeout, retry, cancellation, and mutual
   exclusion.
5. Persistence and evidence: files, event records, recovery, provenance, and migration.
6. UI and workflow: controls, payloads, statuses, overlays, approval, fallback, and edit paths.
7. Integration: the full path across layers and interactions with existing behavior.
8. Documentation and operations: commands, configuration, limitations, and operator guidance.

For every selected slice, write a compact record and update it with results:

```text
ID / observable goal:
Prerequisites:
Change scope / governing contract / requirement source:
Acceptance criteria: input -> expected output; invariants
Verification method / independent evidence:
Result: PASS | FAIL | BLOCKED | NOT_RUN
Evidence: command or action, artifact, environment/version where relevant
Complexity finding, if material: KEEP | REMOVE | DEFER / reason / revisit trigger
Remaining uncertainty / next action:
```

### Delegate independent verification

For substantial independent checks or failure investigations, use
[auto-subagents](../auto-subagents/SKILL.md) to choose and coordinate delegation.
Keep acceptance criteria, independent oracles, source/environment identity, the existing
verification ledger, and the final workflow check here. Subagent completion alone is not
PASS. If the companion skill is unavailable, carry out the same verification locally.

### 3. Implement and verify one coherent slice

Inspect existing behavior and tests. For fixes, establish a baseline or reproduction when feasible;
state when reproduction is unavailable. Implement one coherent slice, then run its focused check
before relying on it in dependent work. Choose checks proportional to risk. Add regression coverage
when it meaningfully detects the defect and protects a fragile or consequential contract. Avoid
tests that merely mirror implementation or wording. Reversible presentation-only changes may need
visual inspection rather than new automated tests. Follow stricter project requirements.

For positional or serialized data, explicitly record frames, axis order, aliases, signs, offsets,
types, byte order, units, and inactive fields. Assert raw bytes or parse an independently constructed payload. For asynchronous
work, test the command sequence and lifecycle separately from the UI. For persistence, test the
written artifact and recovery independently from the in-memory object, including reopening the
saved artifact when required by the user workflow.

### 4. Verify cross-layer handoffs

Passing component checks does not prove the connections work. After prerequisite slices pass,
exercise the relevant transitions in the real chain:

```text
user action or input
  -> controller/facade payload
  -> worker or adapter
  -> external response / result
  -> state transition
  -> persisted evidence
  -> UI status or recovered state
```

At each arrow, check names, units, IDs, provenance, error propagation, and whether an approval or
fallback gate was bypassed. Ensure the expected readback is not generated from the same faulty
encoder or parser as the actual value. A selected GPU setting or a running service does not prove
GPU decoding; verify an actual decoded frame and its backend when that is the required behavior.

### 5. Handle failures and validate the original workflow

For a clear local error, repair it and rerun affected checks; a separate RCA is unnecessary.
When the cause is unclear, the same failure recurs after a fix, or evidence across layers
contradicts itself, use `rca` for hypothesis comparison, causal explanation, and corrective options.
If unavailable, perform a proportionate evidence-based analysis and state its limits. Pass the
unmet criterion, expected versus observed behavior, reproduction conditions, relevant changes,
and existing evidence. Reuse evidence rather than collecting it again without a reason.

`verify-check` owns expected behavior, observed failure boundaries, and verification after changes.
`rca` owns why the failure happened and what would prevent recurrence. Recommendations are not proof
of repair or authority for extra changes. After an authorized fix, return to the failed slice and
its affected integration checks.

Run the original requested user workflow, including relevant failure and recovery transitions.
Select likely failures such as stale state, partial writes, cancellation, reconnect, or shutdown;
do not require an exhaustive generic checklist. Run affected regression checks and all
project-required checks. Do not repeat the whole suite at every slice. Broaden or repeat testing
only for changed dependencies, failures, unresolved risks, or explicit project requirements.
Keep warnings and skipped tests visible.

### 6. Review complexity and report evidence

Apply KEEP / REMOVE / DEFER to actual findings in the affected diff. Check duplicate helpers,
unused paths, speculative flexibility, new dependencies, and migration layers against real
consumers and required failure behavior. A no-findings pass needs only a short note. For an
authorized simplification, rerun affected checks and preserve evidence of any changed contract.
Defer only optional work, with its limit and revisit trigger recorded; never bury required
failed verification as technical debt.



Report the slice statuses from the durable ledger, exact commands, relevant artifacts or file
links, and any unverified boundary. Distinguish `PASS` in a mock/unit environment from field or
hardware verification.
Reconcile evidence with every important original acceptance criterion. A successful command,
component test, or service status alone cannot certify a user-visible runtime result.

PASS applies only to the criteria and environment actually checked. FAIL means an observed
criterion was unmet; BLOCKED means verification cannot proceed because of a concrete missing
prerequisite; NOT_RUN means a check has not been executed. Record the reason for either latter
status. If the real environment is unavailable, state the exact unverified boundary.

Do not claim full completion while a required criterion is failed or unverified. Continue authorized
independent work and report remaining prerequisites without inventing approval gates. Keep the final
report proportional to the task and reference the ledger rather than repeating it.

KEEP / REMOVE / DEFER describes design decisions, not verification status. Accepting a residual
condition can amend scope but never turns missing evidence into PASS. Reuse the active GUI packet
or its mapped verification document; on resume, recheck evidence invalidated by later changes.

### Task summary for later workflow review

When closing or handing off work, retain the original outcome and observed conditions,
then summarize disposition, verification links, rework,
and user corrections separately from scope changes. Reuse the existing ledger/task notes;
small or read-only tasks do not need an extra documentation packet. For substantial records
or measurement questions, read the [work-evidence contract](../../references/work-evidence.md). Link later regressions
to the original task rather than hiding them behind its first completion status.

Record only available time/usage with its source, interval, and agent coverage. Final-turn
usage may arrive after this reply; mark it pending or unavailable as appropriate, never
estimate missing numbers or block completion for analytics. Do not launch monitoring or
inspect broad session histories. cli-usage-review may join completed usage and compare
multiple tasks later when requested; do not invoke a full review after each task.

## Domain routing

Read [slice-patterns.md](references/slice-patterns.md) when the change involves a device or
protocol boundary, asynchronous capture, UI-to-backend flow, or session evidence. Use the patterns
as prompts for the slice map, not as a reason to add irrelevant tests.

## Bundled workflow coordination

Read the [skill routing contract](../../references/skill-routing.md) when combining these workflows.
Reuse the active requirements, authorization scope, and evidence record; do not repeat interviews
or create a second approval gate or ledger.
