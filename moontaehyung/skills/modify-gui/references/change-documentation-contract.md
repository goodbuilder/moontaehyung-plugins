# Change Packet Documentation Contract

Keep stable product truth in the project's existing documentation. Keep one modification's investigation, decisions, approval, and evidence under a unique packet:

```text
docs/changes/<change-id>/
├── state.md
├── change-brief.md
├── current-behavior.md
├── workflow-impact.md
├── ui-quality-and-stability.md
├── impact-analysis.md
├── frontend-contract.md
├── backend-contract.md
├── integration-flow.md
├── decisions.md
├── implementation-plan.md
├── approval-summary.md
└── verification.md
```

Use `YYYYMMDD-short-slug` as the default change ID. The initializer adds a numeric suffix rather
than overwriting an existing packet. This is the full packet layout for substantial changes.
A small explicit change may use a combined existing document with the same scope, approval,
evidence, and resume roles. Record that mapping; do not create empty files for unaffected layers.

## State schema

Keep this YAML block at the top of `state.md`:

```yaml
---
schema: modify-gui-change-state-v1
change_id: YYYYMMDD-short-slug
status: interviewing
mode: unclassified
updated: YYYY-MM-DD
baseline_ref: null
last_completed: "Change packet initialized"
next_question: "What operator-visible outcome should change?"
read_next:
  - docs/changes/YYYYMMDD-short-slug/change-brief.md
affected_product_docs: []
blocking_questions: 0
source_changed: false
implementation_allowed: false
approval:
  state: not-requested
  scope: null
  conditions: []
  recorded_at: null
---
```

Allowed statuses are `interviewing`, `paused`, `awaiting_approval`, `approved`, `implementing`, `verifying`, and `completed`. `implementation_allowed` is false until explicit packet-scoped approval and returns to false on material scope expansion.

## Document ownership

- `change-brief`: operator outcome, motivation, scope, non-goals, acceptance summary.
- `current-behavior`: observed baseline, version/worktree context, docs/code/test/runtime conflicts, reproduction steps.
- `workflow-impact`: current and proposed workflows, preserved/changed steps, decisions, handoffs, artifacts, interruption/recovery, completion, next actions, training impact, and workflow-derived regression scope.
- `ui-quality-and-stability`: existing product-specific visual language, affected components/tokens, anti-template rejection audit, dynamic formatting/extent/update contracts, accessibility, and before/after geometry/focus/selection/scroll evidence.
- `impact-analysis`: affected layers/callers, reuse candidates, justified additions, ownership, invariants, resource impact, compatibility, migration, rollback, risks.
- `frontend-contract`: controls, inputs, payloads, visible states, focus/accessibility, errors and recovery actions.
- `backend-contract`: commands, validation, owners, state, concurrency, worker CPU/GPU budgets and backpressure, timeouts, device/service behavior, persistence.
- `integration-flow`: action-to-postcondition traces and transition tables.
- `decisions`: chronological decisions, alternatives, rationale, consequences, supersession, and concrete limits/revisit triggers for deferred optional work.
- `implementation-plan`: approved slices, dependencies, file map, stopping conditions.
- `approval-summary`: user-facing outcome, changed and preserved behavior, failure/degradation handling, performance priority, risks, and approval request in plain language.
- `verification`: one shared slice ledger, exact commands and tested revision, results/environment, relevant resource/load evidence, KEEP / REMOVE / DEFER findings, and residual conditions. Link decisions without duplicating evidence.

## Update order

After each substantive interview answer or implementation discovery:

1. update the affected product document if a lasting accepted contract changed;
2. update the owning packet document;
3. append or supersede the decision entry;
4. update impact, plan, or verification as applicable;
5. update `state.md` last with exact `next_question` and `read_next` paths.

Never overwrite creation interview state in `docs/interview/`. Never use one change packet to store decisions from an unrelated modification.
