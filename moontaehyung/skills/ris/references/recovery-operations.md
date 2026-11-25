# Public recovery continuity CLI

`python3 <skill>/scripts/ris.py --project <root> recovery read` is read-only and works with project layout schema 1 and 2. It returns the current `hash` (literal `missing` before first write), ledger revision, stable nodes, full semantic history and recorded request outcomes. Missing history is **unknown**, never an inferred zero.

Apply one explicitly classified event from a UTF-8 JSON file or use `--body-file -` to read standard input. Supply only the documented operational fields. For example,

```sh
python3 <skill>/scripts/ris.py --project <root> recovery apply \
  --expected-hash <hash-from-read> --body-file event.json --record-authorized
```

Under manual recording policy, use `--record-authorized` only when the user has authorized this recording. The flag asserts authority; it does not obtain authority, change project policy, or authorize research/external actions. Without authority, keep the same continuity information in the conversation and do not write. Milestones policy permits recording within its authorized scope.

All events require a stable `id`. Exact event retries return the original outcome, even with a stale CAS hash. Reusing that ID for changed content is rejected. All new events require the current hash. Writes use the existing project lock, managed no-symlink paths, preimage comparison and atomic publishing. Concurrent cooperating CLI writers serialize; external tools bypassing the lock can still race in the existing comparison/replace interval. Do not edit the ledger outside this CLI.

## Event bodies

Create a node with explicit semantic scope and applicable conditions:

```json
{"id":"event-001","operation":"create","history_complete":true,"node":{"id":"Q-main","label":"Main question","scope":"Which design meets the stated goal?","conditions":"Existing goal revision and hard constraints"}}
```

Only set `history_complete:true` when the complete history is known and has no earlier deepening requests. Omit it for imported, legacy or uncertain history: count stays `null`. Node IDs are independent of labels and cannot be reused, including retired IDs.

Record a delivered answer (a locator in the conversation is acceptable):

```json
{"id":"event-002","operation":"delivered","node_id":"Q-main","result_ref":"conversation:answer-001"}
```

Record a genuine later user request:

```json
{"id":"event-003","operation":"request","node_id":"Q-main","request_id":"turn-003-Q-main","request_ref":"conversation:turn-003","kind":"deepen"}
```

`request_id` is a stable logical request identifier across retries and envelopes. Reusing it with the identical request and a different event ID deduplicates; changed content is rejected. For a turn touching multiple independent nodes, assign one request ID per node. Persist/recover IDs from the conversation or ledger; never mint a new request ID merely because a tool retries or a session resumes.

Kinds: `deepen`, `input-and-deepen` (also requires `input_ref`), `input`, `retry`, `resume`, `explanation`, `render`, `self`, `audit`, `new-goal`. The final eight do not increment. Deepening before any delivered result does not increment. A repeated delivered answer does not reset history. Mixed new input plus a genuine request to deepen uses `input-and-deepen` and increments normally.

After delivery, known counts yield: 1 → `assess_exhaustive`; 2 → `unused_frontier`; 3 and later → `exhaustive_now` immediately. Exhaustive completion must be separately recorded with `operation:"exhaustive-complete"`, `node_id` and `result_ref`. Subsequent genuine deepening yields `meta_recovery`. The helper selects the required action; it does not itself investigate or certify exhaustive coverage. Unknown total history keeps `count:null` and separately increments the known local `observed_count`. Its first, second and third observed genuine requests require `assess_exhaustive`, `unused_frontier`, and `exhaustive_now` respectively; recover missing history in parallel. Unknown prehistory cannot postpone exhaustive escalation indefinitely. Recorded exhaustive completion requires `meta_recovery` even when the total count is unknown.

Resolve an unknown count only from complete evidence with `operation:"reconcile-history"`, `node_id`, integer `count`, and `evidence_ref`. This explicit historical assertion is preserved in the event log; the helper cannot verify conversation completeness. Known counts cannot be overwritten.

## Semantic changes

Rename: `operation:"rename"`, `node_id`, new `label`, and `rationale`. The stable ID, scope, conditions and count remain unchanged. A changed goal or scope is not a rename.

Split: `operation:"split"`, one-element `parents` ID list, two or more `children` node objects (each with new `id`, `label`, `scope`, `conditions`), and semantic `rationale`.

Merge: `operation:"merge"`, two or more distinct `parents`, exactly one child node object, and `rationale`. Parents retire but remain readable in the ledger. Requests must select active nodes explicitly; retired IDs are never silently redirected. Children retain parent IDs; events retain all before/after semantics. Semantic split/merge defaults to unknown historical applicability: children start with unknown total count and zero locally observed requests. The parent counts remain preserved in lineage, and are never silently presented as applicable to a changed scope. Explicit `history_applicability:"preserve"`, supported by the semantic rationale, permits split children to inherit the parent count and merged children to inherit the union of applicable requests when their identities are known. Only use preservation when those historical requests apply to the resulting question under its stated conditions. If that distinction changes recovery action, preserve independent nodes and assess semantic applicability before merging. Delivery/exhaustive state carries only with explicit preserved applicability and when all parents have that state; a changed scope has no automatically delivered or exhaustively investigated result. Changes never alter unrelated nodes.

JSON output is authoritative for this helper; generated prose, rendering, audit and retries do not constitute new user requests. No model classifies language here: the calling workflow is responsible for evidence-backed semantic classification and user authority.

For a merge with explicitly preserved applicability, the helper counts the union of known logical request IDs. Shared ancestors contribute once. If pre-ledger counts prevent reconstructing the overlap, the total stays unknown and the known lower bound still triggers recovery.
