---
name: architecture-decision-record
description: Create, amend, supersede, and audit Architecture Decision Records (ADRs) documenting architectural choices, alternative options, evidence, trade-offs, risk ownership, consequences, and reversal triggers. Use when a technical decision is proposed, accepted, revisited, or reversed; pair with risk-adaptive-blueprint for branching project plans.
---

# Architecture Decision Record (ADR)

## Goal
Capture *why* an architectural choice was made at a point in time, including rejected options and explicit conditions for revisiting it. Do not rewrite history to make prior decisions look correct.

## When to activate
- Choice changes a system boundary, interface, dependency, security posture, deployment model, or maintenance contract.
- A project gate passes or fails and a blueprint branch is selected.
- An incident or new evidence invalidates a previously accepted assumption.
- Do not create ADRs for trivial code formatting or reversible routine edits unless user requests it.

## Procedure
1. Identify decision scope, date (ISO 8601), decision owner, and relevant blueprint IDs (`D-###`, `R-###`, `G-###`).
2. Gather evidence. Label facts, assumptions, hypotheses, and unresolved uncertainties. Link specific sources; never cite a source not inspected.
3. Compare baseline plus at least one credible alternative. Document costs, failure modes, reversibility, compatibility, security and opportunity costs. Include 'do nothing' if material.
4. State the decision and concrete reason; express conditional decisions with their conditions.
5. Declare consequences: what becomes easier, harder, what risk remains, and what tests are needed. Define trigger metrics, time window, and exit/supersession strategy.
6. Assign status from `proposed`, `accepted`, `rejected`, `deprecated`, `superseded`; do not call a decision `accepted` without user/project authority.
7. Write `docs/adr/ADR-NNNN-short-slug.md` with `assets/adr-template.md`; allocate monotonic ID after scanning existing files. Avoid overwriting. If replacing an accepted decision, create a **new** ADR and mark old one superseded with backlinks; preserve original content.
8. Update blueprint links and decision index, if in scope. Run checklist and identify unresolved validation.

## Required fields
ID, title, status, date, context, problem/decision question, constraints, options and trade-off table, decision and rationale, evidence/assumptions, consequences, risks and mitigations, validity/reevaluation triggers, reversal or migration plan, related ADRs, linked blueprint nodes, owner.

## Safety and integrity
- ADR is a record, not an implementation authorization.
- Distinguish hypothetical examples from actual deployments.
- Do not fabricate measured performance gains or issue reports.
- Never silently delete rejected options, conflicts or old ADRs.
- Decision chosen under high uncertainty should remain `proposed` pending designated gate.

## Quality check
- Could a teammate reconstruct why the choice was made without chatting with the author?
- Is the competing option represented fairly, with costs and benefits?
- Are failure symptoms observable and is the alternative actionable?
- Are the blueprint ID links bidirectional?
- Is status internally consistent with approval evidence.
