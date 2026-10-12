# Interviewing a Non-Programmer

The user is the authority on operations, outcomes, acceptable risk, and priorities. Codex is responsible for discovering and recommending the technical design.

## Decision responsibility

Ask the user to decide:

- who uses the application and what they must accomplish;
- what they see, enter, start, stop, confirm, and recover;
- what must keep working when a device or capability fails;
- whether waiting, retrying, reduced quality/rate, partial operation, or stopping is acceptable;
- what data may be lost, overwritten, delayed, or retained;
- which result is more important when speed, accuracy, responsiveness, cost, or safety conflict;
- deployment and operating constraints they actually know.

Codex investigates and decides or recommends:

- framework, modules, feature boundaries, interfaces, event/signal mechanisms, schemas, threads/processes, queues, resource scheduling, persistence structure, and test architecture;
- exact CPU/GPU worker settings after measuring the agreed hardware/workload;
- file layout, dependency direction, adapters, fakes, and implementation sequence.

Escalate a technical choice to the user only when its consequences materially change cost, safety, data, workflow, deployment, maintainability, or future options.

## Question form

Use one short operating scenario per turn:

1. Explain the situation and why it matters in plain language.
2. Offer 2–3 outcome-based choices when choices help.
3. Put the recommended option first and explain its practical effect.
4. Ask one question.
5. Translate the answer into technical decisions privately and record both the user decision and technical consequence.

Avoid unexplained terms such as module, dependency injection, event bus, schema, thread, queue, backpressure, affinity, context, facade, or mock. If a term is necessary, explain it using the current application before using it.

Example:

> If live video and analysis compete for the computer, should controls and video remain smooth while analysis finishes later, or should analysis remain real-time while preview quality drops? Recommended: keep operator controls responsive and show analysis delay clearly.

Do not ask “How many threads?” or “Which event architecture?” Derive those after the outcome is chosen.

## Handling uncertainty

“I don't know” is a valid answer. Investigate what can be discovered, propose the safest reversible default, state the visible consequence, and ask whether that consequence is acceptable. Keep uncertain technical detail as a proposal or assumption, not a user decision.

## Approval presentation

Keep `docs/approval-summary.md` short and plain:

1. what will be built;
2. how the operator will use it;
3. what success looks like;
4. what happens on delay, failure, overload, and recovery;
5. what existing or planned capability is preserved or excluded;
6. performance priorities and approved degradation;
7. visual character and how changing information remains readable, stable, and comfortable;
8. how acceptance will be demonstrated;
9. cost, risk, assumptions, and remaining field limits;
10. the exact scope being approved.

Link to technical documents for readers who want details. User approval confirms outcomes, tradeoffs, risks, and scope; it does not require understanding code structure.
