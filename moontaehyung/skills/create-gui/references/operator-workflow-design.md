# Operator Workflow Design

Treat workflow as the source for information architecture, screens, commands, states, feature boundaries, backend orchestration, and acceptance tests. A feature list is not a workflow.

## Discover current work

Document how the job is actually performed today, including paper, spreadsheets, shell commands, multiple applications, verbal handoffs, manual checks, workarounds, and recovery habits. Distinguish official procedure from observed practice and ask which should govern when they conflict.

For each meaningful workflow record:

- workflow ID, plain-language goal, operator/persona, environment, frequency, urgency, and duration;
- trigger, prerequisites, permissions, required devices/data, and readiness evidence;
- ordered operator actions and system responses;
- decisions, branches, confirmations, handoffs, waits, and concurrent work;
- visible progress, stale/degraded state, success evidence, produced artifacts, and next action;
- invalid input, rejection, timeout, disconnect, partial success, failure, cancel, retry, rollback, interruption, restart, and next-day resume;
- completion criteria and what must be recorded for review/audit.

Use scenario walkthroughs with the user; maintain technical state/transition detail internally.

## Design the target workflow

Do not copy the current sequence mechanically. Identify duplicate entry, avoidable switching, hidden prerequisites, unsafe ordering, ambiguous success, dead ends, and recovery that depends on memory. Propose outcome-based alternatives and obtain approval for operational changes.

Keep critical or frequent actions direct and contextual. Keep advanced or rare actions available without crowding the primary path. Do not remove a manual or fallback path until its replacement and failure behavior are approved and verified.

Codex may propose workflow improvements but must not invent business policy, safety authority, permissions, data-retention rules, or required operating procedure. Those consequences require user approval.

## Traceability and gate

Give each critical workflow a stable ID. Trace workflow steps to screens/workspaces, commands, state transitions, device/data contracts, artifacts, feature owners, failure handling, and verification cases. One screen may support several workflows and one workflow may cross several screens; navigation should follow operator tasks rather than mirror backend modules.

Before implementation, walk the user through normal, degraded, error/recovery, interruption/resume, and completion scenarios in plain language. Approval covers the target workflow and its consequences, not merely a list of screens.
