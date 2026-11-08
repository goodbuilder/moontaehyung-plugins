# Helper operations

The helper is Python standard library only. It is an implementation tool for the agent; the user
need not memorize these commands. Replace `<helper>` with this skill's `scripts/ris.py` path and
always select an explicit project root. It does not use the legacy RIS workspace or database.

```bash
python3 <helper> --project <root> init --name <name> --goal <goal> --attach-agents
python3 <helper> --project <root> check
python3 <helper> --project <root> context --include research/findings/<file>.md --max-chars 20000
python3 <helper> --project <root> record --kind finding --title <title> --body-file <draft-file>
python3 <helper> --project <root> propose research/CONTEXT.md --expected-hash <sha256> --body-file <draft-file>
```

- `init --dry-run` reports planned files without creating anything.
- `init` re-run on a valid project preserves IDs and existing content. If managed entry files
  exist without config, it stops for adoption review. It does not scan/copy the whole repository.
- `--attach-agents` appends a marked block and preserves an exact preimage of existing AGENTS.md
  in `.ris/history`. `attach --dry-run` previews this separately. It does not install skills globally.
- Config version 1 uses scalar YAML fields with JSON-quoted values. Names with Korean, punctuation
  and quotes are supported. Arbitrary hand-written YAML structures need explicit support; this
  narrow format avoids a runtime dependency and unsafe YAML evaluation.
- `record` creates a UTF-8 Markdown draft under the kind's folder. `--related` accepts managed IDs
  in this project. `--body-file -` reads stdin. It does not rewrite INDEX/CONTEXT automatically.
- `context` returns hashes and text for selected notes, character budget/omissions and clear
  preparation/observability limits. Default selection is INDEX and CONTEXT, not all research.
- `propose` writes a JSON change candidate in `.ris/proposals`, tied to a base hash and project ID.
  It preserves the original. Candidate merge is an explicit editing task, not automatically approved.
- `check` detects managed ID collisions, wrong project identity, missing entry files/directories,
  missing related IDs, simple Markdown link issues and malformed RIS instruction blocks. Wiki links,
  academic correctness, semantic contradictions and external source availability are not validated.
- All commands output JSON for the agent. Exit 0 = success, 1 = check found errors, 2 = operation
  refused/invalid. Symlink-managed paths and parent traversal are rejected. An explicit root itself
  may be resolved from a user's link; paths underneath it may not escape.

## Recording locations

- `literature/`: verified bibliographic/source notes and reviews, with Zotero links when available.
- `concepts/`: explanations, worked examples, user-reported understanding and unresolved questions.
- `plans/`: project-plan's branches/gates/fallbacks. Link specialized analysis artifacts rather than copy.
- `findings/`: observed outputs, provenance, interpretations, limitations, failures and next actions.
- `decisions/`: choice/rationale and supersession links. Existing project ADR locations stay canonical.

`research/INDEX.md` is navigation. `research/CONTEXT.md` is current state, not the only evidence store.
`.ris/project.yaml` carries UUID, schema/template versions and the recording policy. Project files
can be versioned in Git; `.ris/proposals` and history may contain private drafts and need the same
review as research notes before publication. Never add blanket Git ignore or sync rules silently.

## Workflow configuration and guarded updates

```bash
python3 <helper> --project <root> configure --expected-hash <config-sha256> --recording-policy milestones --exploration-mode autonomous --active-plan research/plans/<plan>.md
python3 <helper> --project <root> update research/CONTEXT.md --expected-hash <note-sha256> --body-file <complete-updated-markdown>
```

Read current bytes and compute SHA-256 before either command. `configure` preserves project identity
and unrelated settings, saves the preimage, and rejects stale hashes. Existing project defaults remain
manual; exploration defaults to autonomous when absent. Guided exploration can be task-local.
`update` accepts the complete note, preserves ris_id/project_id/kind/created and saves exact original
bytes in `.ris/history`. It rejects stale bases. Neither operation provides an atomic cross-editor merge.
`propose` remains a non-destructive alternative, with no implicit application.
The active plan must be a project-owned managed Markdown note under research/plans. `context` includes
it within the existing character budget and reports omissions. Details/current node live in that plan.
When recording a milestone, append the event/rationale to the canonical plan, update relevant links and
CONTEXT, regenerate its HTML, then run check. Report partial completion rather than implying a
multi-file transaction. These helpers do not automatically infer acceptance or watch conversations.
