# Bounded local coordination

`ris_coordination.py` projects the existing task graph and claims one task through
`ris.update_state` CAS. It adds no daemon, state schema, provider call, account setting,
model transport or approval requirement. `.ris/state.json` v1 remains the only task authority.
Existing task IDs, dependencies, invalidations, owners, attempts and artifact references are reused.

## Workflow

Use an existing approved scope/priority artifact and a current local accounting snapshot.
The snapshot is an input artifact, not a second state store or proof of provider accounting.
Store each snapshot at a new immutable path; never overwrite a snapshot referenced by a claim.

```sh
python3 skills/ris/scripts/ris.py --project /path/to/project coordinate --envelope accounting-001.json
python3 skills/ris/scripts/ris.py --project /path/to/project coordinate --envelope accounting-001.json --claim TASK-ID --expected-hash CURRENT_STATE_SHA256
python3 skills/ris/scripts/ris.py --project /path/to/project coordinate --mode concise
```

Projection is read-only. Claim changes exactly the selected existing task to IN_PROGRESS,
increments attempt only for a bounded retry, and appends an envelope reference with its
SHA256 locator. Existing `update_state` preserves the prior state in history and serializes
competing state writes. The returned claim is a local reservation receipt; `dispatched=false`
and `execution_authority=false`. It does not authorize or execute an external effect.
The caller must dispatch at most once through its already authorized controlled dispatcher,
check the returned state hash immediately before dispatch, and enforce its actual tool/model
limits. Reusing a dispatch receipt is not prevented by this module; there is no dispatcher here.

Every claim consumes its source state hash. All competing claims from that snapshot fail
CAS or stale-accounting checks. Refresh accounting after every state change before claiming
another task. Existing IN_PROGRESS task grants count as held demand ceilings; earlier grants
and completed/failed/cancelled grants count as spent ceilings. Fresh accounting cannot report
less. No refund or unobserved actual consumption is invented. Unknown legacy IN_PROGRESS
reservations stop dispatch until reconciled by the existing state owner. This conservative
policy can overcount actual usage; settlement/refund needs an explicit future contract.

## Accounting input contract

A JSON envelope has exactly these fields:

```json
{
  "schema_version": 1,
  "project_id": "same project UUID",
  "run_id": "same authoritative run ID",
  "state_sha256": "exact current raw state bytes SHA256",
  "approval_context": {"path": "existing-approved-scope.md", "sha256": "exact artifact SHA256"},
  "priority": {"quality": "user-defined priority", "cost": "user-defined ceiling", "time": "user-defined priority"},
  "task_order": ["existing-task-id"],
  "resources": {"tokens": {"unit": "cache-inclusive-token", "limit": 100, "spent": 10, "reserved": 0, "known": true}},
  "demands": {"existing-task-id": {"tokens": 20}},
  "decision_blocks": {},
  "external_effects": {},
  "recoveries": {}
}
```

`task_order` lists every task exactly once; it is explicitly supplied rather than an invented
numeric quality/cost/time score. `priority` is preserved verbatim in projection and receipt.
All tasks explicitly demand every resource (including zero); every resource has an explicit
unit and finite nonnegative known quantities. Unknown/stale/overdrawn accounting fails closed.
Exhausted resources prevent any positive demand for that resource. Independent local work with
explicit zero model-token demand can continue if all its other resource demands fit.

`decision_blocks` maps every existing pending-user-decision artifact reference to the exact
affected existing task IDs. USER_DECISION without known scope cannot dispatch. A scoped
pending decision stops affected work and dependent work; unrelated ready work can continue.
The module neither answers a user decision nor changes its scope or the run status.

`blocked_scopes` is an optional envelope map from every current `blocked_items.ref` to a
nonempty list of affected existing task IDs. Scoped holds block those tasks and their dependent
work while preserving independent ready work. A BLOCKED run without blocked-item records, or
blocked items without complete explicit scope, withholds all claims until reconciled. This
metadata does not rewrite a run status or resolve the hold.

`external_effects` optionally maps existing task IDs to
`{"status":"UNKNOWN","evidence":{"path":"effect-log.md","sha256":"..."}}`.
PENDING and UNKNOWN quarantine that task and dependent work; CONFIRMED_DONE prevents duplicate
execution of that task; CONFIRMED_NONE allows the ordinary task policy. Missing effect entries
mean no effect is declared by the caller, not that the module independently observed none.
No uncertain call is retried automatically.

`recoveries` optionally maps a failed task ID to
`{"failure_kind":"internal_exploration","max_attempts":2,"evidence":{"path":"existing-recovery-policy.md","sha256":"..."}}`.
Allowed failure kinds are internal_exploration and transient_tool. A FAIL task below the
recorded maximum can be selected as recover without another user prompt, provided dependencies,
invalidations, effects and resources allow it. This is deterministic detection/claiming under
existing recorded policy, not an actual autonomous research repair. Invalidated tasks are not
silently revalidated. Dependency validity is recursive, so stale ancestors cannot be hidden
behind a PASS child. Audit BLOCKED work is not dispatched.

Artifact paths stay inside the current project and hashes are checked. Hash equality proves
local byte consistency; it does not establish the truth of claimed accounting or semantic
approval. Callers must supply genuinely authorized, trusted accounting. The module does not
read credentials, inspect provider settings, police uncontrolled external clients or prevent
paid-credit consumption. Host filesystem/model isolation remains an independent requirement.
External non-cooperating artifact writers can bypass project locks: before/after claim
checks withhold a receipt if the envelope changes, leaving any committed IN_PROGRESS claim
held for reconciliation. This is fail-closed local admission, not a multi-file transaction.

Use `ris.py --project PROJECT coordinate` through the normal CLI. Claims pin their resource snapshot in the existing task artifact references.

## Verification and limits

Run `python3 -m pytest skills/ris/tests/test_coordination.py -q`.
Tests exercise local initialization → graph setup → accounting snapshot → projection → CAS
claim → stale retry rejection using the actual RIS runtime, including competing claims.
S20 coverage: detect known failed exploration, select bounded recovery and preserve attempt.
S23 coverage: quarantine unknown external effects, prevent retry, retain independent work.
S28 coverage: exhausted/unknown/stale/held/spent accounting cannot allocate more of a constrained
resource; explicit zero-demand independent local work remains eligible. State remains
unchanged on rejection. S29 coverage: concise mode needs no initialization, orchestration state or accounting envelope,
reads no project state and starts no
role, claim, recording or provider action. These are local contract checks, not complete
product S20/S23/S28/S29 acceptance or live-model/REAL/holdout validation.

For a blocked run, `blocked_scopes` may map each existing blocked-item reference to its
affected task IDs. A complete mapping permits independent work. A global or ambiguous
hold withholds all claims. A zero-demand task can proceed on a known exhausted resource
if it meets its other constraints. Trusted admission still precedes every chargeable action.
