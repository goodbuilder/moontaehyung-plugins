# Persistent Modification Interview

Ask one primary question at a time in the user's working language. Substantial redesigns and device-rich cross-layer changes may take several days; small well-specified changes should remain proportional.

Use operating situations and visible consequences rather than programming terminology. Codex owns technical investigation and recommendation. Ask the user to choose only when alternatives materially affect workflow, safety, data, cost, performance, deployment, or future capability.

## Sequence

1. **Outcome:** What must the operator be able to observe or accomplish afterward?
2. **Baseline:** What happens now, and which docs, code, tests, or runtime evidence prove it?
3. **Preservation:** Which behavior, data, compatibility, performance, and operating procedures must not change?
4. **Workflow before and after:** What the operator does today, what should change, what stays, and how interruption, failure, recovery, completion, and next actions differ.
5. **Scope:** What is included, excluded, deferred, and forbidden cleanup?
6. **Screen behavior:** What the operator enters, sees, can do, cannot do, and uses to recover.
7. **System behavior:** What must actually happen, how success is known, and what happens on delay, rejection, failure, restart, and shutdown.
8. **Feature independence:** What should remain usable when another capability or device fails, slows, or is disabled.
9. **Resources and load:** Which work stays responsive or timely when the computer cannot do everything at full speed, and which degradation or stoppage is acceptable.
10. **Migration and operations:** Existing data/settings, version compatibility, rollout, rollback, logs, and field constraints.
11. **Verification:** Observable acceptance criteria and automated, simulated, visual, and hardware/manual evidence.
12. **Approval:** Summary, impact map, plan, risks, and explicit packet-scoped authorization.

Revisit earlier topics when later evidence conflicts. Do not ask the user for facts discoverable from the repository, runtime, or authoritative documentation.

## Command questions

For every changed command establish:

- operator intent and exact input;
- prerequisites, permission, and presentation when unavailable;
- accepted payload and backend validation;
- duplicate/concurrent behavior and resource ownership;
- in-progress, cancel, timeout, retry, and late-result behavior;
- success postcondition and independent evidence;
- rejection, partial success, failure, and recovery;
- persisted data, audit/provenance, restart behavior, and shutdown interaction.

## Durable turn rhythm

After an answer, resolve ambiguity about that one topic, then record fact/decision/proposal/assumption/open status. Update packet documents and state before asking the next question. On pause, store the exact next question and necessary read paths; pausing never grants approval.

When docs, code, tests, and runtime disagree, present the evidence and ask which behavior is intended. Preserve the conflict in `current-behavior.md` until resolved.
