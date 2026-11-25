# Knowledge findings workflow

Use `ris.py --project PROJECT findings inspect --question QUESTION_ID` to resume from the canonical Markdown ledger at the configured `research/findings/knowledge-QUESTION_ID.md` (compatibility `default` question uses `knowledge.md`). This managed note is the single current authority. Nodes live only in `proposals[].finding`; accepted copies are not maintained. Embedded history retains per-node revision deltas, while exact reviewed direct-edit preimages use the existing `.ris/history/<sha256>.md` history area. No parallel database, research execution, or provider call occurs.

Every mutation requires `--input project-relative.json --expected-revision N --idempotency-key unique-operation`. The payload must include the inspected `project_id` and, for nondefault questions, `question_id` matching `--question`. Propagate this stable question ID through every command; unrelated questions never force each other's pending work into delivery. `manual` and `milestones` require explicit `--authorize-record`; only `significant` authorizes this bounded important-record workflow automatically. It does not authorize other services, messages, purchases, or experiments. Missing ledger has revision 0. An identical idempotency retry returns the existing revision; reused keys with changed payloads fail.

Inspect supports `--query text`, `--node-id ID`, `--limit 1..100` (default 20). Responses contain bounded matching nodes and obligations, total counts, revision, direct-edit signal, and delivery hash/freshness. Full history is never returned through ordinary resume. Read the canonical note or history preimages deliberately when historical detail is needed.

## Freeze expected coverage independently

Before producing findings, an independent reviewer should specify the expected questions and their scope:

```json
{"project_id":"PROJECT","obligation":{"id":"timing","question":"What interval is actually supported?","expected_scope":{"topic":"measurement-timing"},"specified_by":"reviewer"}}
```

Use action `obligate`. This creates an OPEN obligation even when no findings exist. `expected_scope` must be a nonempty string map of axes, frozen with the question and reviewer. Creating expected scope from the outgoing draft defeats its purpose. Names are explicit principal assertions; this local CLI does not authenticate independent human or agent identities.

## Propose, record, return, integrate

`propose` takes a `finding` and designated `owner`. A finding contains exactly:

- `id`, `statement`, and `status` (CONFIRMED, ASSUMED, INFERRED, UNKNOWN, NOT_RUN, BLOCKED).
- `conditions` and `axes`, maps of names to strings. Explicitly write unknown rather than zero or an assumed measurement.
- `provenance`, a nonempty array of `{source, locator, revision, limitations}`. The first three fields are nonempty strings; limitations is a string array. Source locators remain assertions until separately checked; use study evidence and raw data replay where actual file analysis is appropriate.
- `relations`, an array of `{kind, target, conditions, evidence}`. Kind is supports/contradicts/depends_on/supersedes; target must already exist and differ from the source; conditions is a string map and evidence a nonempty locator string array. These typed links preserve scope rather than claiming causal proof.

`accept`, `return`, and `integrate` each require `id`, designated `owner`, and nonempty `note`. State transitions are PROPOSED → RECORDED → RETURNED → INTEGRATED. The `return` payload additionally requires `finding_revision` equal to the node's `accepted_revision` and actual `transcript` containing the exact finding statement and every provenance limitation as whole paragraphs. Missing, unrelated or stale transcripts fail; corrected return may be resubmitted with a fresh operation key. Integration checks the returned finding digest. This proves payload transport, not that an authenticated external agent executed a task. Integration notes remain explicit assertions. Updates use a new ID and supersedes relation. This preserves old statements rather than rewriting their history.

`resolve` requires a frozen obligation `id`, its `specified_by` reviewer, unique `finding_ids`, and independent publication paragraph `text`. Each referenced node must be integrated, owned by someone other than the reviewer, and match every frozen expected-scope axis. It becomes CURRENT. This enforces explicit coverage and principal separation; it cannot certify semantic relevance or scientific truth.

`disposition` requires an integrated finding `id`, independent `specified_by`, Boolean `decision_critical`, `disposition`, `reason`, and `condition`. Dispositions are USER_DELIVERY, USED_INTERNAL, EXCLUDED, DEFERRED. A decision-critical finding requires USER_DELIVERY or reviewed DEFERRED. Deferral additionally requires `uncertainty_text` that will be required in the answer. Reviewer classification and reasons remain auditable assertions; they must reflect the actual user's decision.

## Delivery and resume

`deliver` takes project-relative `draft`. It rejects any OPEN or INVALIDATED obligation, pending/unreturned/unverified node, missing independent disposition, or USER_DELIVERY finding without obligation coverage. Required paragraphs are:

- Every current independently specified obligation paragraph.
- Statements and provenance limitations of USER_DELIVERY findings.
- Material uncertainty paragraphs for DEFERRED findings.

USED_INTERNAL and EXCLUDED findings stay in the ledger without forcing whole research notes into the answer. Paragraph matching reuses delivery checking, permits ordinary line wrapping, and detects missing or changed text. It is selected-text transport, not semantic equivalence, fact checking, scientific validation, or a proof that an expected question was truly answered. Do not describe it as such. Delivery records exact draft hash and ledger revision; inspect checks whether that draft still matches.

## Direct edits, impact, and recovery

Edits anywhere in the canonical file cause `direct_edit_pending`. Other writes stop until `review-edit` supplies the exact inspected `file_sha256` and nonempty `reason`. The complete edited UTF-8 preimage is retained verbatim in immutable history, including words before the canonical marker. Review normalizes the managed header but preserves its original edited bytes in that preimage. It marks all edited nodes UNVERIFIED, drops owner receipts and dispositions, invalidates obligations, and removes delivery. Review does not promote user edits into confirmed findings or approval. Reaccept, return, integrate, independently resolve and dispose before delivering again.

Malformed blocks, invalid nodes, or invalid references stop without overwriting the canonical note. Recover deliberately from reviewed history; the CLI never silently replaces malformed files. Source provenance is not automatically fetched, guessed, or upgraded.

Ordinary node transitions invalidate obligations attached to the changed node and its transitive relation dependents. Superseding proposals invalidate the superseded branch. Unrelated obligations remain current. Direct document edits invalidate broadly because arbitrary edits can change the graph or scope itself.

Cooperative writers share the project lock and CAS revision; compare-before-replace detects ordinary external edits, but does not provide a kernel transaction against a hostile concurrent editor. The embedded digest detects ordinary unreviewed edits; a deliberate editor who recomputes it can bypass the signal. This is local governance and provenance, not a tamper-proof store or authenticated multi-principal approval system. Legacy external knowledge records remain on disk but delivery rejects them as retrieval inputs; standalone uninitialized Markdown delivery remains supported.

## Discover earlier findings within this project

At intake for a new question, run `findings search --query "concept or observed issue" --limit 20`. Search scans only canonical `knowledge*.md` files under this project's configured findings directory. It does not change or select the new question's authority. Hits identify their own question, node, revision, note path, short statement excerpt, and explicit source freshness. Follow up with targeted `inspect --question HIT_QUESTION --node-id HIT_ID` before proposing reuse. Same-project discovery never authorizes another project's records.

Search skips malformed, dirty, unverified, and stale/missing explicit project-file evidence. It returns `more`, `scan_complete`, scan counts and bounded skipped reasons, so a capped or partial scan is not reported as exhaustive. At most 200 canonical files are scanned per page; hit limit is 1–100. Citation-only provenance has UNKNOWN reuse status until separately verified. A finding with mismatched frozen expected-scope axes cannot resolve an obligation merely because it appeared in search.

Project-file provenance must explicitly use `source: "file:relative/path"` with `revision: "sha256:FULL_HASH"`. This explicit syntax selects the backing file for hashing; ordinary citations are never guessed as filenames. Inspect and discovery report current/stale/unknown checks, and delivery blocks stale or unavailable explicit backing files. `delivery_current` also becomes false when its exact draft or explicit backing file changes. CURRENT means byte fingerprint agreement, not scientific correctness. External citation checks remain UNKNOWN; no fetch or model run is implied.

Generic context consumers should call `projected_context(api, root, relative, limit=20)`. It returns a bounded clean projection for governed ledger filenames, None for other note kinds, and refuses invalid or pending edited ledgers. This avoids treating whole embedded history or unreviewed text as current working knowledge.

## Preserve actual condition scope

`condition_passage(finding)` derives an exact scope paragraph from actual typed conditions: `Conditions: material=steel; source_temperature=20 C; target_temperature=80 C.` Keys are sorted. It returns None only for an empty conditions map or when every exact `key=value` pair already appears in the statement. Owner return transcripts and USER_DELIVERY drafts must carry this paragraph as well as the finding and its limitations. This treats all explicitly recorded conditions conservatively; it does not invent their importance. An independently reviewed noncritical USED_INTERNAL or EXCLUDED disposition keeps the whole finding internal instead. A decision-critical DEFERRED finding must expose material uncertainty as described above.

For a controlled producer, after `accept`, pin `accepted_revision` in `return.finding_revision`. Build the actual owner transcript from the statement, each provenance limitation, and `condition_passage`, separated by blank lines. Build the outgoing answer from independently specified obligation paragraphs, USER_DELIVERY statements/limitations/condition paragraphs, and DEFERRED uncertainty paragraphs. The helper never claims these string checks certify semantic understanding.

Proposals are never merged automatically. Lexical candidates identify equal normalized statements or high token overlap and show condition/axis equality separately. An exact conditioned duplicate requires `duplicate_resolution: {action: "KEEP_SEPARATE", candidate_ids: [...], reviewed_by: "independent-reviewer", reason: "..."}`. Other potential duplicates or condition conflicts are preserved as explicit candidates, without semantic merging or dropping variants.

For discovery comparison, pass `--target-conditions target.json`, containing `{project_id, conditions}`. Hits expose separate conditions and axes, an inspect locator, and applicability status. MATCH means exact declared known string equality only. CONFLICT means known strings differ. UNKNOWN means missing or unresolved values. Without a supplied target, applicability is NOT_ASSESSED. CURRENT continues to mean evidence byte freshness only, never applicability or scientific truth.

Question IDs follow the existing RIS contract (initial letter/digit, then letters/digits/underscore/dot/colon/dash, at most 64 characters). Filename encoding is reversible; for example `question.case:1` becomes `knowledge-question.case%3A1.md`. Context recognition uses the governed note identity or exact canonical marker as well as its managed path, so an unrelated preexisting user note named `knowledge.md` remains an ordinary note.

Return verification retains only a digest of the supplied transcript, owner receipt, accepted revision and approved fact/limitation/scope passages. Incidental agent transcript text is not persisted. Exact in-statement condition matching uses clear token boundaries (`interval=2` never matches `interval=20`). Current scope transport uses the deterministic exact `Conditions: key=value; ...` format; independently reviewed translated prose is not semantically mapped by this implementation. Preserve source-language values in that paragraph and explain them separately when needed.

Discovery pagination is resumable: when `more` is true, repeat the same query and target-conditions selection with `--cursor NEXT_CURSOR`. The cursor pins the project, query, target condition contents and canonical directory snapshot, and tracks both file and node offsets. Each page visits at most 200 canonical files and 1,000 nodes and emits at most `--limit` hits; later files and later nodes in a large ledger remain reachable. `more` means traversal remains, not that eligible hits are guaranteed. `traversal_complete` distinguishes exhausted traversal from skipped invalid/dirty/stale records; those remain in `skipped`, and make `scan_complete` false. A changed query, target, canonical file set or honest file edit invalidates the cursor with an explicit restart error. Search also checks raw bytes after inspection and checks the snapshot again before returning, so an honest post-inspection edit is never silently combined with an older inspection result. This is an optimistic read snapshot, not a hostile-editor security transaction.
