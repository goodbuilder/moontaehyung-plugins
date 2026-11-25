# RIS 0.23.0 research workflow verification

The comparison baseline is the locally installed 0.22.0 plugin. Its distributed files matched the source tree at intake, and all 77 RIS tests passed.

| Workflow | Acceptance |
| --- | --- |
| Run a study across sessions | Start with competing predictions, then use an identified observation to revise the assessment. A fresh process can recover the initial prediction, current rationale, limitations and next action. Replaying the observation preserves a single revision. |
| Maintain one decision record | The plan, context and handoff point to the same managed Markdown study. A recommendation update preserves human decisions and annotations. A rendered map can identify its source. |
| Reuse knowledge | An explicitly selected observation retains its source identity, conditions and limits. Matching, changed and missing conditions have distinct explanations. An imported finding is identifiable after a restart. |

Each area has a separate implementation owner. Integration and local packaging run after the shared study contract is verified.

## Integration observations

- The first fresh-process study creation failed before publication of the new note. The temporary-file writer referenced a missing import during integration. Study and navigation writers were moved to a shared atomic create/replace implementation. Existing-note replacements compare the exact preimage under the project lock. An external editor can still race after the final comparison.
- Source review found that a planned condition could count as observed when assessing reuse. The comparison now identifies planned conditions absent from the actual observation. Exact scope match is an input to scientific judgment.
- The focused evidence-review regressions passed on the integrated CLI. They verify that a search-only rejection prompts review even when another option has a linked source, and that a correction can be traced to the questions explicitly linked to its read ID.
- An intake record from a prerelease build revealed that comparing saved Markdown against the newest renderer could invalidate a sound study after a presentation change. The stored projection and its payload now have a versioned digest. A reader validates the recorded bytes, schema and project identity independently of the current rendering code. The regression changes the renderer and reopens the original record.
- A fresh researcher started a study from the previous synthetic comparison outcome before seeing the execution logs. Its original proposal was retained across the prerelease format repair. A separate session received just the project and the three previously accepted run traces. It found E-017 returned and opened only in the baseline, and correctly bounded the causal interpretation. Its first analysis miscounted three empty variant searches as three total searches. A separate count found four searches per arm. The researcher appended a correction, leaving both the earlier observation and the original predictions accessible. This exercise demonstrates resumption and correction; it also records an actual agent counting error.
- In Firefox the decision node in a nested rendered plan opened the canonical study note by clicking the link emitted by `study-link`. The link showed the snapshot revision and resolved across the two nested plan directories. The rendered file also passed Archify's output check. Evidence was served on loopback.
- A schema 1 migration fixture preserved historical study reads, navigation links, human annotations and a saved finding through conversion to schema 2. Its repeated reuse was idempotent. A generic update could change annotations while a replacement of the managed history was rejected.
- An independent reviewer found that an arbitrary source locator and matching condition strings could display a saved observation as applicable with no further review. The release gate requires separate recorded-condition and source-byte results, explicit scientific review, and a negative test using a source that cannot be verified.
- The source-level CLI attachment probe recorded a file's SHA-256 and compared it at reuse time. It returned `not_checked` without a verification request, `bytes_match` for the same bytes, and `changed` after a rewrite; changed bytes required rechecking. Scientific review remained required in all three cases. Hashing checks identity, not whether a paper or measurement supports the claim.
- The independent cross-feature acceptance run used 61 fresh CLI processes. It verified explicit selection, hypothesis assessments, next-test activation, stale and duplicate revisions, one canonical study, selected-project isolation, and positive and negative knowledge reuse. A later incompatible condition produced a reason for remeasurement while the original observation remained intact.

## Reproduction

Run `python3 -m pytest -q skills/ris/tests` from the plugin root. For map navigation run
`node skills/archify/tests/tree-document-links.mjs`. Archify's shared validator and render/check
commands support the optional node links. Code calling the internal generated schema function
directly bypasses this wrapper.

These checks use synthetic research projects and a previous controlled search experiment. A
serial development baseline, real research labor savings and field accuracy were not measured.

The final source suite passed all 140 RIS tests. The Tree document-link tests, RIS CLI help
and Claude plugin manifest validation passed. The independent acceptance runner completed
231 checks across its 61 fresh processes. A separate reviewer repeated the fictional-locator
and changed-condition probes through the CLI and saved findings; both required further review.
