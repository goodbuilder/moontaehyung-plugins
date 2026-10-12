# Workflow Change Analysis

Treat the current operator workflow as a compatibility contract until the user approves a change. Do not infer the workflow from screen layout alone.

## Recover the current workflow

Use product documents, code, tests, runtime observation, saved artifacts, logs, and operator explanation to record:

- workflow ID, operator, goal, trigger, prerequisites, permissions, frequency, urgency, and duration;
- ordered actions and system feedback, decisions, branches, confirmations, handoffs, waits, and concurrent work;
- devices/data, produced artifacts, success evidence, completion, and next action;
- manual shortcuts, workarounds, fallback paths, and differences between documented and actual practice;
- rejection, timeout, disconnect, partial success, failure, cancellation, retry, restart, and resume.

When evidence conflicts, document the conflict and ask which outcome is intended. Preserve unrelated working paths.

## Propose the workflow change

Show current and proposed flows in plain language. Mark preserved, added, removed, reordered, or automated steps and explain changes to decisions, handoffs, artifacts, timing, permissions, error/recovery, training, and operating procedures.

Improve workflow only within the requested and approved outcome. Do not use a GUI change as permission to rewrite business policy, safety procedure, roles, data retention, or unrelated workflows. Keep a manual/fallback path unless its removal and replacement failure behavior are approved.

## Approval and regression

Trace changed workflow steps to screens, commands, state transitions, backend postconditions, feature owners, data/artifacts, and tests. Walk through normal, degraded, error/recovery, interruption/resume, completion, and next-action scenarios before approval.

Verification must execute the proposed workflow end to end and rerun preserved alternate, manual, failure/recovery, and adjacent critical workflows. A screen-level test does not prove the workflow, and a backend unit test does not prove the operator can complete it.
