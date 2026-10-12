---
name: create-gui
description: Design and build new stateful desktop operator GUI projects through a persistent, multi-session requirements interview, documented approval gate, implementation, and interaction/error-path verification. Applies to hardware-backed, simulation, replay, and data-driven operator applications; do not route ordinary small edits to an established GUI here.
---

# CreateGUI

Create a conventional, information-dense operator application only after its behavior and acceptance criteria have been decided with the user. Treat the project's `docs/` directory as durable interview memory and the approved specification as the implementation contract.

## Applicability and system shape

Treat hardware as one possible external boundary, not as a prerequisite for this skill. The same workflow applies when the runtime consumes simulation state, replay files, generated data, network services, or no external I/O at all. If the project is a CLI, library, or non-operator visualization with no desktop workflow, route it elsewhere.

For a stateful runtime, define the contract before integrating the source: authoritative owners for mutable state and resources, typed input/output and unit/frame/time semantics where relevant, command intent versus observed state, lifecycle boundaries, and the first testable end-to-end workflow. Keep these decisions domain-neutral; project-specific protocols, schemas, and domain rules belong in the project documents.

Architecture reader generation is a separate explicit workflow. Do not regenerate an architecture
HTML on every design or implementation step; record affected owner/contract information and use
`$update-architecture` only when the user explicitly requests the current external reader.

Read the shared [minimum sufficient change policy](../../references/minimum-sufficient-change.md)
before architecture or implementation decisions. In the existing scope/architecture documents,
identify what v1 needs, what can be reused, and what evidence would justify added complexity.
Treat this as a qualitative budget, not a target number of files or classes. Early UI mockups
can test workflow; production logic and state must remain usable independently of widgets.

For a design-document request, make a reviewable draft the first deliverable. After reading
repository instructions and locating the relevant existing documents, write the known scope,
constraints, proposed smallest design, unknowns, and next question to the mapped specification
and resume record. Then refine that draft with the references needed for open decisions.
Do not wait for exhaustive reference reading or environment qualification to record it.
Unverified performance or deployment stays an explicit validation item; design-only work
does not require installing a stack or building a runnable prototype.

## Start or resume

1. Resolve the project root from the user's requested execution location. Do not silently choose another directory.
2. Inspect existing repository instructions, source, dependency files, launchers, tests, and documentation before recommending a stack or asking questions that local evidence can answer.
3. Look for `docs/interview/state.md` or the resume record mapped by the project's documentation index. Read that state, open questions, decisions, and every `read_next` document. Summarize the recovered position and continue from `next_question`; do not repeat settled questions unless evidence conflicts.
4. Otherwise read [references/documentation-contract.md](references/documentation-contract.md) and map its roles to existing documents. Use `scripts/init_gui_docs.py --root <project-root>` when a full new documentation set is useful; it preserves existing files. A small project may use a combined specification with the same decision, approval, and resume information.

Interview state belongs in the target project, never inside this skill. Update it after every substantive user answer, before asking the next question. A conversation may end at any point; leave `last_completed`, `next_question`, `read_next`, open decisions, and blockers accurate enough for a new Codex session to resume without chat history.

## Design handoff

For substantial architecture decisions, use [design-boundaries](../design-boundaries/SKILL.md).
It owns responsibility, interface, state/resource and lifecycle design. Supply the operator
workflows and constraints already collected here; do not repeat the interview or create another
approval process. Record its decisions in the existing architecture/decision documents.
Use [verify-check](../verify-check/SKILL.md) for acceptance traceability, implementation slices,
prerequisites and evidence. This skill owns GUI requirements, product decisions and approval.

## Conduct the interview

Read [references/interview-playbook.md](references/interview-playbook.md), [references/nontechnical-interview.md](references/nontechnical-interview.md), and [references/operator-workflow-design.md](references/operator-workflow-design.md). This is intentionally a multi-day process when the project warrants it. Assume the user is not a programmer unless they request technical depth.

- Ask one primary question per turn. Use short follow-ups only to clarify the current answer; do not send questionnaires or rush toward implementation.
- Ground questions in repository evidence and prior decisions. Offer 2–4 concrete alternatives, implications, and a recommendation when the user would otherwise have to guess.
- Ask the user about operating outcomes, priorities, safety, acceptable degradation, and visible behavior. Do not delegate framework, module, thread, queue, event, schema, or testing-mechanism decisions to them; investigate and translate those technical decisions into plain-language consequences.
- Move from operator goals and real scenarios through scope, data and external inputs, states and commands, failure recovery, layout, design, architecture, deployment, and verification.
- Use scenario walkthroughs to expose missing transitions and failure behavior. Capture terminology conflicts and distinguish facts, decisions, assumptions, proposals, and unresolved questions.
- Let the user pause explicitly. A pause is not approval and must not advance the phase.

Work workflow-first: discover the current real-world process even when it uses paper, spreadsheets, command lines, or multiple applications; then propose and approve the target operator workflows before fixing navigation, screens, commands, feature boundaries, or backend orchestration. Do not automate a broken or unsafe sequence without surfacing an improved alternative.

When simulation or replay is in scope, decide the relevant clock/control modes, input/configuration/seed identity, reset behavior, and truth-versus-estimate separation. Specify required repeatability and tolerances rather than promising determinism from a seed alone. Define pause, step, fault injection, or replay only when the workflow needs them; hardware checks apply only to hardware boundaries.

The default visual direction is a traditional mechanical/engineering workstation: compact, calm, data-first, keyboard-capable, and explicit about status and units. Do not turn that preference into a fixed layout before interviewing the project's operators and workflows.

Read [references/operator-ui-authenticity-and-stability.md](references/operator-ui-authenticity-and-stability.md) before approving the design system or visual implementation. Derive hierarchy, density, components, and wording from the operator workflow and domain rather than an interchangeable AI/SaaS template. Specify stable geometry and interaction for every frequently changing value, status, message, table, plot, and conditional control so live updates do not move surrounding content, focus, scroll position, or click targets.

## Recommend technology

Read [references/technology-selection.md](references/technology-selection.md) when choosing the stack. For a conventional cross-platform desktop operator application with Python-friendly external integration, recommend Python with PySide6 and Qt Widgets unless discovered requirements favor another option. Explain the tradeoff and record the decision; do not select a framework solely because the current example repository uses it.

Before fixing a new GUI's implementation plan, use the [implementation-choice policy](../../references/minimum-sufficient-change.md#choose-an-implementation)
to compare relevant UI authoring tools and component approaches as well as the framework.
This workflow owns GUI-facing choices; design-boundaries owns material structural choices
and reuses the GUI constraints already decided. Keep the recommendation in the existing plan.

Keep external-input and domain logic independent of widgets, define typed state/command boundaries, and keep blocking I/O off the GUI thread. Prefer standard widgets, model/view tables and trees, semantic design tokens, and testable adapters over per-widget styling or direct external calls from click handlers.

When the application has CPU- or GPU-intensive workers, media pipelines, inference, plotting, or concurrent external-input processing, read [references/worker-resource-budgeting.md](references/worker-resource-budgeting.md). Interview and document workload budgets, worker concurrency, queue/backpressure policy, CPU/GPU selection and memory limits, observability, overload behavior, and target-environment evidence before approval. Do not invent fixed percentages or affinity settings without measurement.

When the application contains multiple meaningful capabilities, workers, external inputs, or workspaces, read [references/feature-boundary-design.md](references/feature-boundary-design.md). Design cohesive feature ownership and narrow cross-feature contracts internally. Ask the user scenario questions such as which capabilities must remain usable when another fails; do not ask them to choose an event bus, module layout, dependency injection pattern, or other code structure.

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

## Documentation and clarity gate

Maintain the field-specific documents defined in [references/documentation-contract.md](references/documentation-contract.md). Record each accepted choice in both its owning document and `docs/interview/decision-log.md`; keep rejected alternatives only when their rationale prevents future rework.

The interview is complete only when:

- primary operator workflows and scope boundaries are explicit;
- every critical current and target workflow has actors, triggers, prerequisites, ordered steps, decisions/handoffs, visible feedback, artifacts, completion, cancel/retry/resume, and normal/degraded/error/recovery outcomes;
- every important command has prerequisites, in-progress behavior, success evidence, rejection behavior, timeout/retry/cancel policy, and resulting state;
- external input, simulation/replay, mutable-resource, and data ownership, threading, persistence, shutdown, and deployment boundaries are decided;
- CPU/GPU worker budgets, concurrency, backpressure, overload behavior, and measurable responsiveness/throughput criteria are decided when resource-intensive work exists;
- feature ownership, dependency direction, shared-resource ownership, failure isolation, and independent test/disable behavior are designed when multiple capabilities exist;
- layouts, status semantics, accessibility, target displays, and interaction rules are testable;
- product-specific visual rationale and rejection criteria are explicit, and dynamic text/data has a format, maximum expected extent, overflow policy, update rate, and geometry/focus/scroll stability contract;
- normal, degraded, disconnected, invalid-input, partial-success, recovery, and shutdown scenarios have expected outcomes;
- acceptance criteria and validation environments are observable and feasible;
- design assumptions, review triggers, and the location/update cadence of the durable decision and verification records are explicit;
- no high-impact open question remains hidden behind an assumption.

When the gate is satisfied, produce `docs/approval-summary.md` in plain language, plus the detailed architecture proposal, phased implementation plan, verification matrix, remaining risks, and deliberate non-goals in their technical documents. Update state to `awaiting_approval` and ask for explicit approval using the plain-language summary; make the technical detail available without requiring the user to understand it.

## Approval boundary

Do not create application source code, install dependencies, scaffold the GUI project, or begin implementation before the user explicitly approves the documented specification and implementation plan. Repository inspection and edits under `docs/` are permitted during the interview. If approval is conditional, record the condition, update the affected documents, and return to `awaiting_approval`.

After approval, record its date and scope in the decision log, set state to `approved`, and implement only the approved scope. New material requirements discovered during implementation return to interview mode and require amended approval.

## Implement and verify

After the documented approval, execute the accepted plan using
[verify-check](../verify-check/SKILL.md) for decomposition, focused checks, handoffs, regression
scope and final evidence. Reuse `docs/10-testing-and-validation.md` or its mapped equivalent;
do not create a second ledger or acceptance process.

Use the architecture accepted through design-boundaries. Keep blocking I/O off the GUI thread
and distinguish command intent from observed success. Apply resource budgets and overload behavior
from the approved GUI contract; do not add persistence, replay or workers solely for a checklist.
When implementation changes an established boundary, use maintain-boundaries for that affected
scope without restarting the design interview.

Read [references/verification.md](references/verification.md) for GUI-specific acceptance evidence.
Verify operator workflows through the real entry point and relevant interactions, including
visible state, keyboard/focus and live-update stability. Report evidence in the existing record.
The GUI workflow owns acceptance: every approved criterion needs evidence or an explicitly
accepted residual condition; unrun checks never become PASS. Update product documents and resume
state with observed results and remaining limits.

## Bundled workflow coordination

Read the [skill routing contract](../../references/skill-routing.md) when combining these workflows.
Reuse the active requirements, authorization scope, and evidence record; do not repeat interviews
or create a second approval gate or ledger.
