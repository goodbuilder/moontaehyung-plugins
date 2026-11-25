# Helper operations

The helper is Python standard library only. It is an implementation tool for the agent; the user
need not memorize these commands. Replace `<helper>` with this skill's `scripts/ris.py` path and
always select an explicit project root. These examples use schema v2's default
`research_dir: .ris/research`; existing schema v1 projects keep their configured
`research_dir: research` until the user explicitly requests a layout migration. It does not use the
legacy RIS workspace or database.

```bash
python3 <helper> --project <root> init --name <name> --goal <goal>
python3 <helper> --project <root> check
python3 <helper> --project <root> context --include .ris/research/findings/<file>.md --max-chars 20000
python3 <helper> --project <root> record --kind finding --title <title> --body-file <draft-file>
python3 <helper> --project <root> explore --question capacity --kind query --via web --text "<search query>"
python3 <helper> --project <root> explore --question capacity --kind read --via full --text "<source and passage>"
python3 <helper> --project <root> explore --question batch-size --reuse R-0001
python3 <helper> --project <root> check --question batch-size
python3 <helper> --project <root> context --question batch-size
python3 <helper> --project <root> context --read R-0001
python3 <helper> --project <root> summarize --body-file <four-section-body>            # first time
python3 <helper> --project <root> summarize --body-file <body> --expected-hash <sha256>   # later
python3 <helper> --project <root> propose .ris/research/CONTEXT.md --expected-hash <sha256> --body-file <draft-file>
python3 <helper> --project <root> state init --goal-ref .ris/research/CONTEXT.md --active-plan-ref .ris/research/plans/main-plan.md
python3 <helper> --project <root> state read
python3 <helper> --project <root> state update --expected-hash <sha256> --body-file <complete-state.json>
python3 <helper> --project <root> migrate-layout                          # preview only
python3 <helper> --project <root> migrate-layout --apply                   # apply reviewed mapping
python3 <helper> --project <root> migrate-layout --include-handoff         # preview moving freeform handoff
python3 <helper> --project <root> migrate-layout --include-handoff --apply # apply and move that handoff
```

- File inputs to the RIS CLI, including request bodies and metric definitions, belong to
  the selected project. Use project-relative names, absolute names inside that root, or
  supported stdin from an authorized source. Stage public inputs explicitly. Nested RIS
  projects and private identity directories are outside the selected research scope.
- `init --dry-run` reports planned files without creating anything.
- `init` re-run on a valid project preserves IDs and existing content. If managed entry files
  exist without config, it stops for adoption review. It does not scan/copy the whole repository.
- Schema v2 defaults to `research_dir: .ris/research`; schema v1 uses `research_dir: research`.
  Existing v1 projects need no migration to open and keep their root `HANDOFF.md` unless migrated.
  `migrate-layout` is preview-only without `--apply`. A root handoff with matching `project_id` and
  `kind: handoff` metadata moves automatically. An unowned or mixed root handoff stays in place;
  links it contains into the relocated `research/` tree are rebased in place and listed in the
  preview. If it has no such link, it remains byte-identical. To move a freeform legacy RIS handoff,
  preview with `--include-handoff`, then apply with `--include-handoff --apply`. Other unrelated root
  files remain untouched.
- Unowned or foreign mixed notes within the research tree, collisions, and symlinks fail before files
  move. Preflight inspects up to 20,000 tree entries, 8 MiB per text asset and 128 MiB of text in total.
  It rebases supported inline Markdown and HTML links. Check wiki links, raw paths and inbound links
  from other project files separately. If an interrupted migration leaves its journal, rerun `migrate-layout --apply` to
  recover only when no external edits conflict with the journal.
- `--attach-agents` is optional root-instruction integration, not a default. Use it only when
  explicitly requested; it appends a marked block and preserves an exact preimage of existing
  `AGENTS.md` in `.ris/history`. `attach --dry-run` previews this separately. It does not install
  skills globally. Existing root `AGENTS.md`/`CLAUDE.md` files remain project-owned.
- The versioned config uses scalar YAML fields with JSON-quoted values. Names with Korean,
  punctuation and quotes are supported. Arbitrary hand-written YAML structures need explicit
  support; this narrow format avoids a runtime dependency and unsafe YAML evaluation.
- `record` creates a UTF-8 Markdown draft under the kind's folder. `--related` accepts managed IDs
  in this project. `--body-file -` reads stdin. It does not rewrite INDEX/CONTEXT automatically.
- `context` returns hashes and text for selected notes, character budget/omissions and clear
  preparation/observability limits. Default selection is INDEX and CONTEXT, plus the active plan.
  If `.ris/state.json` exists, the snapshot includes its validated orchestration bookkeeping and
  references; linked evidence contents are not read by the state field.
- `context --question <ID>` reads the project's exploration log and returns entries for that
  question in event order. Queries include their channel and text. Reads include their R-ID,
  original time, locator, recorded scope and reuse status. Reused reads appear when the question
  linked them, with the U-ID, link time and original question ID (null for unassigned reads).
  An empty list with `total_entries: 0` means the log has no matching activity. The view reports
  the log path, its SHA-256 when present, and any skipped malformed rows. Source locators are
  returned as text for the next researcher to follow.
  The character budget covers complete entries, measured as compact JSON characters. When
  `omitted_entries` is positive, rerun with `--max-chars` equal to `characters_required`
  to retrieve all entries from that log revision. Use plain `context --include <path>` to read
  a project note separately.
- `explore` appends one row to `exploration/log.md` under the configured research directory (under
  `.ris/research/` in the schema v2 default; created on first use, without changing init templates).
  Kinds: `query` (channel label such as web, zotero, code) and `read` (scope: snippet, abstract,
  full, code, data). IDs `Q-0001`/`R-0001` are assigned under the write lock. It stores only the query or
  source identity and, when given, a stable question or decision ID. Use 1–64 ASCII letters, digits, underscores,
  periods, colons or hyphens, starting with a letter or digit. Keep the same ID when a question
  resumes. A single read can serve several decisions. To reuse it, link the existing R-ID with
  `explore --question <id> --reuse <R-ID>`. This records the association without adding another
  source opening. Cite the original locator and preserve its read scope. With `check --question <id>`,
  inspect the activity for that question and the sources it reuses. The ordinary project's total
  includes past activity and older unassigned entries. A zero for a scoped count describes the
  recorded activity. It does not establish that a search would be fruitless.
  `check` also flags duplicate IDs
  (error) and malformed rows (warning); it does not judge query quality or comprehension.
- `context --read R-0001` lists the original question, when recorded, and every question
  that explicitly reused that particular read. Use it to locate assessments worth reviewing
  after a correction. Separate reads of the same document can have separate IDs.
- When the selected question has an authorized [recovery ledger](recovery-operations.md),
  `context --question ID` also reports its node status, count and ledger revision. Read
  `recovery read` for its scoped lineage, deliveries and decisions. An absent node supplies
  no evidence about the number of historical requests.
- For multi-session investigations use the [study workflow](study-workflow.md). `context --study ID`
  reads the canonical study and its saved evidence links. A character cap applies to whole sections;
  increase it to `characters_required` to recover all sections of the same revision.
  `study results ID --format markdown` renders the stored numerical criteria and their combined
  verdict when a rule exists. `study amend ID --expected-revision N --body-file FILE` revises
  the hypotheses or prospective test within the same study. See the [amendment example](study-amendment.md).
- `summarize` writes `exploration/summary.md` under the configured research directory (under
  `.ris/research/` in the schema v2 default) from a body with exactly four non-empty sections
  (탐색한 접근 계열, 기각·보류한 후보와 이유, 미탐색 프런티어, 검수 요청), at most 6000 characters. It rejects
  any `Q-`/`R-` ID absent from the work log, computes the statistics block itself (project totals,
  per-question new queries, new reads and explicitly reused reads, unassigned activity, log position
  covered, rejected/deferred bullets citing no log ID), and updates an existing summary only with the current
  hash, preserving identity and the previous bytes in `.ris/history`. `check` warns when the summary is behind
  the log or missing, and errors on a cited ID that does not exist. It cannot judge whether a summary line is
  true; bullets must carry their IDs on the same line to be counted as evidenced.
  In the exclusions section use `[기각]` for a rejected option, `[보류]` for an unresolved option,
  or `[사용자 결정]` with a Markdown link to the user's recorded selection. `summarize` and `check`
  show the basis of each item in `exclusion_basis`. A query-only rejection prompts review.
  A read or reuse ID carries its actual scope, including snippet-only reads. A linked decision
  identifies a reported selection; the reviewer interprets its authority and relevance.
- `propose` writes a JSON change candidate in `.ris/proposals`, tied to a base hash and project ID.
  It preserves the original. Candidate merge is an explicit editing task, not automatically approved.
- `check` detects managed ID collisions, wrong project identity, missing entry files/directories,
  missing related IDs, simple Markdown link issues, malformed RIS instruction blocks, and invalid
  orchestration state when `.ris/state.json` exists. Wiki links, academic correctness, semantic
  contradictions and external source availability are not validated.
- `state init` creates optional run bookkeeping with the project's existing `project_id`. `state read`
  returns the state and its SHA-256 preimage. `state update` validates a complete replacement against
  [state-schema.json](state-schema.json), checks project/run identity and the expected hash, stores the
  exact previous bytes in `.ris/history`, and refreshes `updated_at`. It does not store prompts,
  findings, evidence text, decision graphs, or forecast content. Task dependencies must reference
  existing task IDs and remain acyclic; artifact references must resolve inside the project.
  The update preserves a preimage and checks for intervening edits, but it is not an atomic merge
  with Obsidian or another editor.
- All commands output JSON for the agent. Exit 0 = success, 1 = check found errors, 2 = operation
  refused/invalid. Symlink-managed paths and parent traversal are rejected. An explicit root itself
  may be resolved from a user's link; paths underneath it may not escape.

## Recording locations

- `<research_dir>/literature/`: verified bibliographic/source notes and reviews, with Zotero links when available.
- `<research_dir>/concepts/`: explanations, worked examples, user-reported understanding and unresolved questions.
- `<research_dir>/plans/`: project-plan's branches/gates/fallbacks. Link specialized analysis artifacts rather than copy.
- `<research_dir>/findings/`: observed outputs, provenance, interpretations, limitations, failures and next actions.
- `<research_dir>/decisions/`: choice/rationale and supersession links. Existing project ADR locations stay canonical.

`<research_dir>/INDEX.md` is navigation. `<research_dir>/CONTEXT.md` is current state, not the only
evidence store. In schema v2 these are `.ris/research/INDEX.md` and `.ris/research/CONTEXT.md`.
`.ris/project.yaml` carries UUID, schema/template versions, `research_dir` and the recording policy.
Project files can be versioned in Git; `.ris/proposals` and history may contain private drafts and
need the same review as research notes before publication. Never add blanket Git ignore or sync
rules silently.

## Workflow configuration and guarded updates

```bash
python3 <helper> --project <root> configure --expected-hash <config-sha256> --recording-policy milestones --exploration-mode autonomous --active-plan .ris/research/plans/<plan>.md
python3 <helper> --project <root> update .ris/research/CONTEXT.md --expected-hash <note-sha256> --body-file <complete-updated-markdown>
```

Read current bytes and compute SHA-256 before either command. `configure` preserves project identity
and unrelated settings, saves the preimage, and rejects stale hashes. New projects default to significant changes. Existing projects retain their configured recording scope. Exploration defaults to autonomous when absent. Guided exploration can be task-local.
`update` accepts the complete note, preserves ris_id/project_id/kind/created and saves exact original
bytes in `.ris/history`. It rejects stale bases. Neither operation provides an atomic cross-editor merge.
`propose` remains a non-destructive alternative, with no implicit application.
The active plan must be a project-owned managed Markdown note under `<research_dir>/plans` (under
`.ris/research/plans` in the schema v2 default). `context` includes it within the existing character
budget and reports omissions. Details/current node live in that plan.
When recording a milestone, append the event/rationale to the canonical plan, update relevant links and
CONTEXT, regenerate the Archify HTML with RIS-mode working files under `.ris/`, and refresh the
layout-appropriate handoff under the [shared RIS output contract](shared-outputs.md), then run
`check`. For schema v2, this is `.ris/HANDOFF.md`; for an unmigrated schema v1 project, preserve
the existing root `HANDOFF.md`. Report partial completion rather than implying a multi-file
transaction. These helpers do not automatically infer acceptance or watch conversations.

Command arguments and persisted state artifact references are project-root-relative (for example,
`.ris/research/plans/main-plan.md`). Links authored inside Markdown are relative to the Markdown
file's own directory. In `.ris/HANDOFF.md`, link to `research/plans/main-plan.md`; do not prefix
that handoff link with `.ris/`.
