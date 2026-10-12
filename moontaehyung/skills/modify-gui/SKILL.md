---
name: modify-gui
description: Modify an existing stateful desktop operator GUI and the backend behavior directly required by that GUI through persistent change interviews, impact analysis, explicit approval, implementation, and end-to-end regression verification. Applies to hardware-backed, simulation, replay, and data-driven operator applications; do not route tiny isolated presentation fixes or backend work unrelated to a user-visible GUI contract here.
---

# ModifyGUI

Change an existing operator application without losing its proven behavior, user-owned work, or operational contracts. Own the full user-visible vertical slice when required: interaction, frontend validation, controller/service boundary, directly coupled backend work, state and persistence, and final presentation.

## Scope boundary

Classify the request before interviewing or editing:

- **frontend-only:** layout, styling, presentation, accessibility, or interaction without changing the backend contract;
- **backend-coupled:** a user-visible workflow spanning GUI and its directly required command, worker, external source/service, state, or persistence behavior; this is the primary mode;
- **backend-only GUI contract:** backend behavior whose observable result, state, or error contract is consumed by the GUI;
- **out of scope:** backend infrastructure, pipelines, algorithms, databases, or operations with no direct GUI contract. Handle these as ordinary backend work or a more suitable workflow.

Small, fully specified text, color, spacing, or isolated bug fixes normally do not need this skill. If the user explicitly invokes it, keep the change packet and approval process proportional rather than manufacturing a long interview.

For review or diagnosis only, inspect the existing records and report findings. Do not
initialize a packet, edit files, or request implementation approval unless the user asks to
proceed with a change.

Read the shared [minimum sufficient change policy](../../references/minimum-sufficient-change.md)
before selecting an implementation. Trace affected callers and public contracts, reuse suitable
existing behavior, and record the reason for material new abstractions, dependencies, settings,
or workers in the existing impact/decision record. Preserve the requested outcome and fix causes
at their owner; a small diff is not sufficient if sibling callers still fail.

Hardware is only one kind of runtime boundary. Apply the same analysis to simulation clocks, replay sources, generated data, network services, and virtual resources. If there is no existing desktop workflow or user-visible GUI contract, use a more suitable workflow.

Read [references/scope-and-impact.md](references/scope-and-impact.md) for classification and product-document routing.

## Start or resume

1. Resolve the repository root and inspect repository instructions, current changes, documentation, launchers, dependencies, source, tests, and relevant runtime evidence. Preserve user-owned modifications and do not assume a clean worktree.
2. Identify the active change packet under `docs/changes/` or its mapped equivalent. If the user names one, use it. Otherwise resume the single record whose state matches the requested change; if several remain ambiguous, ask which one without modifying source.
3. To resume, read the packet's `state.md`, every path under `read_next`, its current-behavior and decision records, then relevant code and tests. Briefly report the recovered baseline and ask the stored `next_question` without repeating settled questions.
4. For a new change, read [references/change-documentation-contract.md](references/change-documentation-contract.md). Reuse an appropriate existing record or choose a descriptive lowercase hyphenated slug. Use `scripts/init_gui_change.py --root <repository-root> --slug <slug>` for a substantial new packet; a small explicit change may use a combined record with scope, approval, evidence, and resume state.

The packet is durable memory for a change that may span days. After every substantive answer, update the affected product document or packet document, append the decision, update open questions, and write `state.md` last. Always preserve the exact next question and `read_next` paths before the conversation can end.

## Audit record integration

Use the packet's `verification.md` or mapped equivalent as the single slice ledger, including
when `verify-check` participates. Record observed facts, commands/artifacts, environment,
status, and next action after meaningful checkpoints and when a defect or mismatch is found.
Link KEEP / REMOVE / DEFER decisions and revisit triggers rather than copying the evidence.
Persist prerequisite results before dependent work. Update current product documents for accepted
contract changes; keep unresolved findings in the packet with their status.

## Architecture refresh boundary

Read the shared [architecture refresh contract](../../references/architecture-refresh.md) only when
the changed workflow affects an architecture-facing owner, dependency, state/data/lifecycle
boundary, coordinate/time contract, persistence artifact, or user-visible architecture document.
Do not invoke `$update-architecture` or regenerate the HTML automatically. If the user has not
requested a refresh, record the small `architecture_refresh` status with risk, affected node IDs,
and the suggested explicit command. Use `NOT_APPLICABLE` for changes with no architecture-facing
impact.

## Establish the baseline

Do not design from the request alone. Record:

- current commit or other discoverable version identity and relevant pre-existing worktree changes;
- the current affected operator workflows as actually performed, including hidden prerequisites, manual workarounds, alternate paths, interruption/resume, errors/recovery, artifacts, and next actions;
- the current design system/component vocabulary and dynamic-state geometry, focus, selection, scroll, table-column, dock/splitter, and window behavior across representative and boundary values;
- observed current behavior, including inputs, visible states, backend postconditions, persistence, errors, and shutdown;
- authoritative product documents and mismatches among docs, code, tests, and runtime behavior;
- owners of devices or other external inputs, sockets, workers, queues, files, settings, simulation clocks, replay cursors, and sessions;
- the current feature dependency map, public cross-feature contracts, shared mutable state/resources, and observed failure isolation when the change may affect coupling;
- baseline worker topology and representative CPU, GPU, accelerator-memory, queue, throughput, latency, GUI-responsiveness, and overload evidence when resource allocation may change;
- existing tests and the smallest reproducible baseline commands.

Treat a documentation/code mismatch as an unresolved contract, not permission to choose whichever is convenient. Do not rewrite unrelated code or normalize architecture merely because it would be cleaner.

For an inherited monolith or legacy panel, map affected state/resource owners before changing the shell. Preserve proven behavior through characterization checks and avoid duplicating its resource owner. A migration-only facade needs exit criteria and consumer coverage; a stable public adapter may remain when it provides a real boundary. Do not remove a layer merely because it has one implementation.

## Conduct the change interview

Read [references/change-interview.md](references/change-interview.md), [references/nontechnical-interview.md](references/nontechnical-interview.md), and [references/workflow-change-analysis.md](references/workflow-change-analysis.md). Ask one primary question per turn, grounded in the baseline and prior decisions. A substantial cross-layer change may intentionally take several days. Assume the user is not a programmer unless they request technical depth.

Determine the intended operator outcome, preserved behavior, exact scope, frontend contract, backend contract, state transitions, failure/recovery behavior, migration and compatibility, deployment implications, and evidence needed for acceptance. For each important command, trace:

```text
operator action
  -> frontend validation and payload
  -> controller/service/worker boundary
  -> external or domain result
  -> state and persistence
  -> visible success, rejection, or recovery
```

Do not infer authority for a framework migration, backend rewrite, schema migration, protocol change, dependency upgrade, or unrelated cleanup. Propose those separately with their cost and risk when genuinely necessary.

For simulation or replay changes, include the affected clocks, reset/epoch transitions,
input/seed identity, and truth-versus-estimate contracts. Verify the required repeatability
within stated tolerances; do not add time controls, replay, or fault-injection features solely
to satisfy a generic checklist.

Ask the user to decide observable outcomes, preserved behavior, priorities, safety, acceptable degradation, and failure scenarios. Do not ask them to select module boundaries, event mechanisms, thread/queue design, schemas, test architecture, or resource scheduling. Investigate those and recommend a design in plain language.

If the request changes worker concurrency, CPU/GPU placement, accelerator use, media/inference load, queues, process priority, or responsiveness under load, read [references/worker-resource-changes.md](references/worker-resource-changes.md). Treat allocation policy, observability, overload/fallback, and target-environment verification as part of the approved GUI contract. Do not tune from a single utilization snapshot or hard-code a percentage without a measurable service objective.

If the change crosses capabilities, touches shared state/resources, introduces a new feature, or risks wider regression, read [references/feature-boundary-changes.md](references/feature-boundary-changes.md). Produce the before/after dependency and ownership impact internally. Ask scenario questions about what must continue working when another capability fails rather than asking the user to choose code architecture.

Read [references/ui-authenticity-and-stability-changes.md](references/ui-authenticity-and-stability-changes.md) whenever visible UI, text, dynamic data, conditional controls, tables, plots, status, navigation, or layout may change. Preserve the application's product-specific visual language; do not insert generic AI/SaaS card, pill, gradient, glow, glass, oversized-heading, or decorative-dashboard patterns without an approved operator purpose. Treat geometry, focus, selection, and scroll stability under live updates as functional compatibility.

## Implementation options for substantial changes

After establishing the baseline and before fixing a substantial change's implementation
plan, use the [implementation-choice policy](../../references/minimum-sufficient-change.md#choose-an-implementation). Compare retaining the current approach,
a bounded replacement, and suitable existing tools for the affected workflow. Own the
GUI-facing choice and pass material structural questions to design-boundaries with settled
constraints intact. Keep the comparison within the requested change; small fixes and still-valid
prior choices do not need a new tool survey or framework proposal.

## Qt Designer for Qt Widgets

Use Qt Designer only after Qt Widgets has been selected for the project, when visual
editing helps with stable forms such as settings pages or dialogs. Qt Quick/QML and
non-Qt projects keep their own tooling. Preserve the chosen Qt version, Python binding,
and existing UI structure; do not migrate a framework or convert an entire UI just to
adopt Designer.

Within the authorized implementation scope, keep `.ui` files and required resources in
the repository as the layout source of truth, with a reproducible loading or generation
step. Use the matching binding's loader or generator; keep custom logic outside generated
files. Retain state and command handling with their existing owners, and use placeholders
for custom views where useful. Codex may author `.ui` files directly; manual Designer
editing is optional.

Use the existing verification workflow to check resizing, signal connections, and dynamic
states in the running application. Designer preview alone is not completion evidence.

## Documentation and approval gate

Use the existing `docs/00`–`11` product documents as shared truth when present. Read only the subset relevant to the change, plus packet state; a full redesign may require all of them. Keep change-specific history under `docs/changes/<change-id>/`.

When an accepted change alters a lasting product contract, update both its numbered product document and the change packet. The packet explains why and how the contract changed; the product document describes the current accepted product. Do not leave two competing truths.

Before source edits, present:

- baseline and preserved invariants;
- affected workflows before and after, preserved/manual/fallback paths, changed decisions/handoffs/artifacts, retraining impact, and workflow-derived regression cases;
- before/after visual rationale, component/token reuse, dynamic format/extent/update contracts, and geometry/focus/selection/scroll stability evidence for affected UI;
- approved outcome, included and excluded scope;
- affected frontend, backend, data, state, persistence, deployment, and documentation boundaries;
- baseline and proposed CPU/GPU worker budgets, concurrency/backpressure policy, overload/fallback behavior, and target-environment acceptance limits when affected;
- transition and failure behavior;
- file/component impact map and migration/rollback needs;
- phased implementation plan and end-to-end verification matrix;
- durable audit-ledger location, update cadence, and slice status convention;
- risks, assumptions, and unresolved field conditions.

Write the packet's `approval-summary.md` in plain language and link its claims to the detailed technical packet. Set packet state to `awaiting_approval` and wait for explicit user approval using that summary. During the interview only documentation changes are permitted. Approval of one packet does not authorize other packets or unrelated cleanup. Conditional approval must be recorded and reflected in the plan before implementation.

## Implement the approved vertical slice

After approval, record scope and time and set `implementation_allowed: true`. Use
[maintain-boundaries](../maintain-boundaries/SKILL.md) to assess the actual owners and dependencies,
preserve state identity and lifecycle contracts, and limit structural changes to this scope.
If a materially new boundary needs design, use design-boundaries within the same packet.
These helpers do not reopen settled requirements or create another approval gate.

Use [verify-check](../verify-check/SKILL.md) for step ordering, prerequisite checks, implementation
and integration evidence. Pass the approved workflow IDs and existing `verification.md`; do not
copy its generic procedure into a second plan. This skill remains responsible for operator
behavior, visual compatibility, scope and approval state.

Preserve Qt callback/thread affinity, GUI responsiveness, approved resource budgets and truthful
visible state. A click or emitted signal is intent, not proof of backend completion. Historical
views retain their source/session context rather than silently displaying current global state.

If implementation exposes a material requirement, destructive migration or scope expansion,
document the change and return the affected work to the applicable approval process. Existing
user authorization remains valid for its scope.

## Verify and close

Use verify-check's results and [references/vertical-slice-verification.md](references/vertical-slice-verification.md)
for the GUI-specific acceptance review. Exercise affected and preserved adjacent operator flows
through the real entry point. Compare visible states, interaction, layout stability and recovery
against the approved baseline; do not infer those from domain tests alone.

Close the packet only when every approved criterion passes or the user explicitly accepts a
named residual condition. Missing evidence remains unverified. Update affected product documents,
mark the packet completed, record implementation identity, and retain unresolved field limitations.
Use the existing decision and evidence records; do not run another generic verification procedure.

## Bundled workflow coordination

Read the [skill routing contract](../../references/skill-routing.md) when combining these workflows.
Reuse the active requirements, authorization scope, and evidence record; do not repeat interviews
or create a second approval gate or ledger.
