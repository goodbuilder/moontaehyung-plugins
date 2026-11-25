# Selected final-passage delivery

Use this narrow helper when compressing decision-bearing findings whose known evidence
limits could disappear from a separate final summary. The finding owner chooses concise,
self-contained paragraphs, in the user's language, containing the result and the
qualifications the user needs. Selection and data extraction remain human/agent work.
The helper neither discovers important facts nor judges scientific or semantic sufficiency.
Do not use it as a general requirement to mark every research note or routine extraction.

In an existing, explicitly selected project Markdown file, surround each user-ready passage
with these exact standalone lines (examples inside fenced code blocks are ignored):

```markdown
<!-- ris:deliver -->
실측 표본은 3개이며 신뢰구간은 아직 계산하지 않았다. 이 결과만으로 양산 성능을 확정할 수 없다.
<!-- /ris:deliver -->
```

The helper only reads. It never creates project configuration, scans notes, records a
ledger, updates recovery state, sends a message, or performs external access. Marking an
existing note is a separate edit subject to that project's recording authorization.
Manual/no-recording work can supply the same marked text through stdin without initializing
RIS or saving a new file.

```sh
python3 skills/ris/scripts/ris.py --project ROOT delivery --source research/findings/result.md
python3 skills/ris/scripts/ris.py --project ROOT delivery --source .ris/research/findings/result.md --source notes/qualification.md
python3 skills/ris/scripts/ris.py --project ROOT delivery --source -
```

Default JSON returns the ordered source paths and byte SHA256 hashes, a composite
`revision`, and passages with stable-in-that-revision IDs, source line locators, and text.
Identical repeated selections are deduplicated; retries do not write or multiply passages.
Source ordering contributes to the revision. The digest pins the selected source bytes,
including unmarked content, rather than a Git commit or the truth of the findings.
Both schema 1 and schema 2 project layouts work; delivery does not read project config.
Every supplied file path must be project-relative and pass the existing `inside` boundary:
no absolute paths, parent traversal, symlink components, or non-regular files. File sources
must have a `.md` extension. Stdin must be the sole source.

To obtain the actual ready-to-send paragraphs, use `--format markdown`. This emits passage
text separated by blank lines, without a machine report. The agent still owns the final
outgoing response and must use the selected text, rather than summarize it again.

```sh
python3 skills/ris/scripts/ris.py --project ROOT delivery --source notes/result.md --format markdown
python3 skills/ris/scripts/ris.py --project ROOT delivery --source notes/result.md --draft-file draft.md --expected-revision DIGEST
```

Check the complete outgoing draft against the revision obtained during selection. A draft
can instead come from `--draft-file -`; source and draft cannot both use stdin. The draft
path is also project-relative. `--draft-file` and `--expected-revision` must be supplied
together. A stale source revision or malformed marker structure fails with exit 2.
Missing passages produce exit 1 and JSON `ok: false` with their IDs, locators, and full
text. `--format markdown` still returns JSON on missing passages, so failure cannot look
like a completed user message. Success exits 0.

The check requires each selected passage to appear as consecutive complete paragraphs in the draft.
It allows ordinary line wrapping and spacing within a paragraph. Place added commentary in a separate paragraph. It preserves punctuation, words,
numbers, and their order; disconnected fragments or a bag of keywords cannot satisfy it.
Do not select code, tables, or text whose meaning depends on exact whitespace. This is a
text-preservation check: a misleading surrounding paragraph, omitted unmarked findings,
an unsupported original claim, or a scientifically incomplete selected passage can still
pass. No independent-science PASS, research-completeness claim, or user-delivery event
follows from this result. After editing any source, select again and review the new revision.

The file read checks detect ordinary replacement during reading; they are not a sandbox
against a malicious concurrent process controlling the project directory. The helper does
not lock owners' files or freeze the project after it returns. Python may maintain its normal
installation-side bytecode cache; no project files or persistent delivery records are written.
