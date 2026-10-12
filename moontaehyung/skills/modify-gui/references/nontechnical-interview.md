# Interviewing a Non-Programmer About a Change

The user decides the desired operational change, preserved behavior, priorities, acceptable degradation, safety, data consequences, and approval scope. Codex investigates the existing implementation and owns the technical recommendation.

## Ask about outcomes, not mechanisms

Ask what the operator should observe or accomplish, what must remain available, and what should happen during delay, failure, overload, restart, and recovery. Do not ask the user to select modules, event systems, schemas, workers, queues, thread counts, GPU memory limits, test doubles, or migration mechanisms.

Use one question per turn in this form:

1. Describe a real operating situation.
2. Offer 2–3 choices stated as visible outcomes.
3. Recommend the safest maintainable option and explain the practical tradeoff.
4. Record the user decision and translate it into technical consequences internally.

Example:

> If analysis slows down, should the existing controls remain immediately responsive while results arrive later, or may controls wait to preserve real-time analysis? Recommended: keep controls responsive and show that analysis is delayed.

Codex then derives worker priority, concurrency, queue, and status behavior from the answer.

## Technical responsibility

Inspect code, tests, runtime, documentation, device/API rules, and target hardware before recommending architecture. Make a technical choice without burdening the user when alternatives do not materially change cost, safety, data, workflow, deployment, or future options. If they do, explain only those consequences and ask the user to choose among them.

If the user says “I don't know,” investigate, propose a reversible safe default, and ask whether its visible consequence is acceptable. Never record unexplained technical assent as informed approval.

## Plain-language approval

The packet's `approval-summary.md` contains:

1. what changes and what stays the same;
2. the operator workflow before and after;
3. success, delay, rejection, failure, overload, and recovery behavior;
4. data and compatibility effects;
5. performance priorities and allowed degradation;
6. visual and interaction changes, including whether live text or status can move anything;
7. verification demonstrations;
8. cost, risk, assumptions, rollback, and unverified field conditions;
9. exact approved scope.

Link to the technical packet for optional detail. The user approves the outcome and consequences, not the implementation vocabulary.
