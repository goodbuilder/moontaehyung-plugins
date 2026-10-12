# GUI boundary design handoff

Use [design-boundaries](../../design-boundaries/SKILL.md) for common ownership, dependency,
interface, lifetime and enforcement rules. This document adds only the operator-GUI mapping.

Derive capability boundaries from approved operator scenarios. Ask which capabilities must remain
usable when another fails; do not ask users to choose dependency-injection or event-bus patterns.
Record screen ownership in the mapped UI document, source/resource ownership in the data document,
commands and feedback in the state/command document, failure isolation in the recovery document,
and design decisions and tests in the existing architecture and verification documents.

Preserve GUI-specific Qt parent/thread roles, live-update geometry, focus/selection and resource
budgets from their dedicated contracts. Boundary design must support those outcomes without adding
product features or duplicating the requirements interview, approval summary or evidence ledger.
