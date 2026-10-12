# Persistent GUI Interview Playbook

## Operating rhythm

Interview one primary decision at a time. A useful turn has this shape:

1. Recover the current phase and relevant decisions from `docs/`.
2. Explain why the next decision matters in one or two sentences.
3. Ask one concrete question. When useful, give a recommendation plus alternatives and tradeoffs.
4. After the answer, resolve contradictions or ambiguity about that topic.
5. Write the answer, rationale, consequences, and remaining uncertainty to the owning document, decision log, and state file.
6. Ask the next question only after the durable update succeeds.

Do not impose a question count or deadline. Several days of deliberate interviewing is expected for device-rich or safety-relevant applications. Avoid asking questions whose answer can be learned from the repository or authoritative documentation.

Phrase every user-facing question as an operating situation, observable result, or understandable tradeoff. Keep the technical translation in the documents. If a technical choice has no material effect on cost, safety, data, workflow, deployment, or future options, make and document the recommendation instead of asking the user to choose terminology they do not need.

## Phase order

The phases are a coverage map, not a rigid script. Revisit earlier phases when later answers expose a conflict.

### 1. Context and intent

- Who operates the system, where, for how long, and under what pressure?
- What physical or business outcome does the application control or observe?
- What currently fails, costs time, or creates risk?
- Which existing systems, code, protocols, and terms are authoritative?

### 2. Scenarios and scope

- Walk through startup, preparation, normal operation, intervention, completion, and shutdown.
- Identify personas, permissions, non-goals, v1 boundaries, and later capabilities.
- Define completion using observable operator and system outcomes.

### 3. Inputs, devices, and data

- Enumerate devices, services, files, streams, protocols, update rates, units, clocks, identifiers, and data ownership.
- Decide discovery, connection, authentication, configuration, simulation, recording, retention, and provenance.
- Distinguish source state, derived state, command intent, and verified outcome.

### 4. State and command model

For every important command, decide:

- visible name and operator intent;
- prerequisites and permission;
- enabled/disabled presentation versus backend rejection;
- idempotency and concurrency;
- progress, success postcondition, failure evidence, timeout, retry, cancel, and rollback;
- resulting state, persisted evidence, audit record, and recovery action.

Use a transition table for workflows with three or more states. Ask scenario questions such as “What should happen if the connection drops halfway through this command?”

### 5. Information architecture and layout

- Rank information by operator decision importance, frequency, urgency, and persistence.
- Decide navigation, workspace ownership, inspector/diagnostics, tables, plots, camera/map surfaces, dialogs, keyboard paths, and multi-monitor behavior.
- Specify target resolutions, scaling, localization, numeric precision, units, and empty/loading/stale/degraded/error states.

### 6. Visual and interaction system

- Convert the traditional mechanical workstation direction into semantic tokens and measurable density.
- Decide emphasis, status vocabulary, icon/text use, focus, contrast, reduced motion, confirmation rules, dangerous commands, and alarm acknowledgement.
- Do not rely on color alone or make healthy status visually dominant.

When the visual direction remains open, invite—do not require—the user to provide 2–5 screenshots or other visual references as the primary question for that turn. Ask what they like and dislike in each reference; do not assume that every repeated trait is intentional. If references are provided, compare hierarchy, information density, navigation, typography, color, component treatment, and status/alarm presentation. Identify common patterns, conflicts, and details that are product-specific or incompatible with the approved workflows.

Turn the analysis into a short set of transferable, testable visual principles and show the synthesis to the user for confirmation. Treat every inferred preference as a proposal until accepted, then record the references, stated likes/dislikes, accepted principles, and rejected interpretations in `docs/08-design-system.md` and the decision log. Do not copy a referenced product or let a screenshot override workflow, safety, accessibility, target hardware, or dynamic-content stability. If the user has no references, continue from workflow and domain evidence without blocking the interview.

### 7. Architecture and delivery

- Select framework, supported OSes, packaging, offline/online assumptions, updates, logging, configuration, secrets, persistence, migration, performance budgets, and observability.
- Decide GUI-thread boundaries, worker lifecycle, resource owners, adapters, simulation/fake strategy, and shutdown order.
- For CPU/GPU workloads, decide target hardware profiles, per-workload latency/throughput priority, concurrency and queue limits, GPU memory ownership, overload/backpressure, fallback, telemetry, and thermal/power constraints. Ask for measurable budgets rather than arbitrary utilization percentages.

### 8. Verification and approval

- Turn each workflow and failure case into an evidence-backed acceptance criterion.
- Identify what can be automated, simulated, visually inspected, or only validated with hardware/field operation.
- Review contradictions, assumptions, risks, non-goals, implementation phases, and the approval scope.

## Ambiguity handling

Label statements using these meanings:

- **Fact:** supported by repository, device, protocol, or authoritative source evidence.
- **Decision:** explicitly accepted by the user.
- **Proposal:** recommended but not accepted.
- **Assumption:** temporarily used and still requires confirmation.
- **Open:** unresolved and assigned a next action.

If two accepted decisions conflict, stop progression on that dependency, document the conflict, and ask the smallest question that resolves it. Do not silently reinterpret the older decision.

## Pause and resume

On pause or end of session:

- write the current phase and status;
- record the last completed decision and exact next question;
- list documents a new session must read;
- retain unresolved questions with priority and blocking impact;
- state whether implementation remains prohibited.

On resume, cite the recovered decisions in a short recap and ask the stored next question. If the repository changed after the last interview update, inspect the change and flag only decisions it may invalidate.
