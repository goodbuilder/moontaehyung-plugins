# GUI Project Documentation Contract

The target project's `docs/` directory is both the specification and persistent interview state. Preserve compatible existing documents; add missing sections or map the contract to existing files rather than overwriting user content.

## Document roles and default layout

Use this layout for a substantial new project. Existing equivalents or a compact combined
specification may fulfill these roles; record the mapping in the index/resume state. Keep
scope, accepted contracts, approval, evidence, and next action discoverable. Do not generate
empty files for inapplicable layers. The initializer provides the full layout when needed.

```text
docs/
├── README.md
├── 00-product-vision.md
├── 01-operator-workflows.md
├── 02-requirements-and-scope.md
├── 03-information-architecture.md
├── 04-workspace-layout.md
├── 05-device-and-data-contracts.md
├── 06-state-and-command-model.md
├── 07-error-recovery-and-safety.md
├── 08-design-system.md
├── 09-architecture-and-implementation.md
├── 10-testing-and-validation.md
├── 11-deployment-and-operations.md
├── approval-summary.md
├── open-questions.md
└── interview/
    ├── state.md
    └── decision-log.md
```

Use extra documents or ADRs only when a decision needs substantial independent rationale. Keep one authoritative home for each fact; link instead of duplicating details.

## Ownership

- `00`: users, environment, problem, outcomes, principles, glossary.
- `01`: current and target end-to-end operator workflows, including normal, repeated, startup/shutdown, maintenance, degraded, error, recovery, interruption, and next-day resume scenarios.
- `02`: functional/non-functional requirements, v1 scope, non-goals, acceptance boundaries.
- `03`: entities, navigation, feature/workspace ownership, hierarchy, terminology.
- `04`: screen regions, target displays, responsive/multi-monitor rules, detailed workspace layouts, and dynamic-content geometry stability.
- `05`: devices, protocols, services, files, schemas, rates, units, clocks, feature and shared-resource ownership, provenance.
- `06`: feature public state/command/event contracts, state machines, permissions, concurrency, postconditions.
- `07`: hazards, feature failure isolation, degraded modes, alarms, recovery, retries, cancellation, shutdown safety.
- `08`: product-specific visual rationale, anti-template rejection criteria, semantic tokens, density, typography, components, accessibility, status presentation, and dynamic-content formatting/stability.
- `09`: technology, reuse and qualitative complexity budget, justified new boundaries/dependencies, threading, resource budgets, required persistence, packaging, phased plan.
- `10`: acceptance matrix and one slice ledger for applicable automated/simulated/manual evidence, including links to complexity decisions and residual conditions. Share this ledger with verification work.
- `11`: supported platforms and hardware profiles, install/update/configuration/logging/backup/field operations.
- `approval-summary`: user-facing outcome, workflow, failure behavior, preserved scope, performance priorities, risks, and approval request in plain language; link to technical detail rather than duplicating it.
- `open-questions`: unresolved questions only, with owner, priority, blocking impact, and next action.
- `interview/decision-log`: chronological accepted decisions and changes.
- `interview/state`: machine- and human-readable resume checkpoint.

## State schema

Keep this compact YAML block at the top of `docs/interview/state.md` and explanatory notes below it:

```yaml
---
schema: create-gui-interview-state-v1
status: interviewing
phase: context-and-intent
updated: YYYY-MM-DD
last_completed: "What was durably decided"
next_question: "One exact question to ask next"
read_next:
  - docs/00-product-vision.md
blocking_questions: 0
implementation_allowed: false
approval:
  state: not-requested
  scope: null
  recorded_at: null
---
```

Allowed `status` values are `interviewing`, `paused`, `awaiting_approval`, `approved`, `implementing`, and `verifying`. `implementation_allowed` remains `false` until explicit approval is recorded. Do not treat a phase label, generated plan, prior implementation request, or pause as approval.

## Decision log entry

Each accepted decision records:

```markdown
## D-YYYYMMDD-NN — Short title

- Status: Accepted | Superseded
- Area: workflow | scope | device-data | state-command | layout | design | architecture | verification | deployment
- Decision: ...
- Rationale: ...
- Consequences: ...
- Simpler alternative and reason, when material: ...
- Present limit and revisit trigger, for a deferral: ...
- Supersedes: none
- Evidence: user answer, repository path, or authoritative link
```

When a decision changes, append a new entry and mark the old entry superseded; do not rewrite history.

## Update discipline

After each substantive answer:

1. update the owning field document;
2. append or supersede the decision-log entry;
3. remove resolved items and add newly exposed items in `open-questions.md`;
4. update `state.md` last, including the exact next question and `read_next` list.

This order ensures a resumed session never advances beyond durable domain documentation.
