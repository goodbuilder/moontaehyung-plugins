---
name: ris
description: Initialize or resume project-local research, align the agent with the user's background, organize source-backed learning and branching plans, and record findings or handoffs in Markdown for Obsidian. Use for RIS requests and research continuity in initialized projects. Do not initialize unrelated projects or record every conversation automatically.
---

# RIS — project-local research continuity

The existing CLI agent is the interface. Research Markdown lives inside the selected project and
is readable in Obsidian. An optional generated HTML map is a local reading artifact; no daemon, central database, separate chat interface or mandatory
MCP server is required. Keep code/data/results where the project already owns them and link them.

## Establish the project and recording scope

Identify the exact project from the user's request and current repository. Pass its root explicitly
to every helper invocation; never use a global active-project selection. If multiple projects are
plausible, ask before dependent reads/writes. Work in the user's existing project; do not assume
that the current tooling repository is the research target.

For an initialized project, read `.ris/project.yaml`, `research/INDEX.md`, `research/CONTEXT.md` and
applicable project instructions first. Inspect linked records only as required for the task.
Summarize current understanding, important uncertainties and the next step briefly. Distinguish
what the user previously stated from what the current agent has actually read and can establish.

For a requested initialization, use the bundled standard-library helper:

```bash
python3 <this-skill>/scripts/ris.py --project <project-root> init --name <project-name> --attach-agents
python3 <this-skill>/scripts/ris.py --project <project-root> check
```

Use `--dry-run` if an initialization preview is requested. Existing research entry files are never
silently adopted or overwritten. On a collision, inspect the existing layout and propose mapping
or adoption; do not force a reset, rename user files or invent an empty research history. The
AGENTS block is a short entry point, not a duplicate of the skill. Existing instructions and their
precedence remain intact. Read helper details only as needed in [operations.md](references/operations.md).

## Align the outcome and lead exploration

Read existing context before asking. Extract the desired deliverable, success criteria, user knowledge,
constraints, preferences and prior decisions; distinguish stated intent from inferred intent. Ask only
material gaps that affect the current result. Do not make users restate facts available in the project.
Default to autonomous broad and deep exploration: survey distinct credible approach families before
ranking, then recursively investigate the consequential decisions introduced by every viable route.
A first comparison or first executable task is not completion. Display a compact overview while retaining
the full candidate inventory, expanded paths and explicit unexplored frontier in the HTML map. A user request to follow a
specific branch switches the active task to guided exploration; persist that preference only if asked.
Research autonomy covers investigation and planning, not costly experiments or implementation commitments.
See [research exploration](references/research-exploration.md) for trend evidence and recording triggers.

## Research coverage and delegation

The coordinating agent retains the research questions, required evidence and completion judgment.
Keep consequential questions in the existing plan or conversation; project-plan owns their branching
structure. When delegation is useful, use available auto-subagents for allocation and coordination.
Provide concrete questions, needed evidence, dependencies and any need for independent investigation;
retain the same coverage when working locally or when delegation is unavailable.

Before recommending, trace returned evidence and unresolved items to the questions. Check both the
correctness of proposed routes and missing consequential alternatives; one check does not establish
the other. Incorporate newly discovered questions into the existing plan and continue or bound their
investigation. Unassigned work and exhausted worker capacity do not make a question complete.

## Investigate, teach and plan

Reuse available skills; do not merge their procedures into a large mandatory sequence.

- Literature: use the user's Zotero skill/connection when available, plus appropriate external
  sources. Keep DOI/item identity, source locator, retrieval date and actual review scope. Search
  failure or limited access is not evidence that no prior work exists. A missing connector does
  not prevent reading existing verified notes; never invent references or install a connector silently.
- Learning: separate prior user knowledge, reported understanding, worked-example reproduction,
  application and validation. Offer `teach-me` for a requested real calculation/method lesson;
  inspect actual formulas/code and state units, assumptions, source and execution limits. Default
  to Markdown; create HTML only when requested. The lesson's creation is not proof of understanding.
- Planning: use `project-plan` for consequential branches, quality gates and fallbacks. Write its
  canonical plan to `research/plans/` and link it from CONTEXT. For this agreed workflow, generate
  an interactive HTML map using that skill’s renderer; keep Markdown as authority. Read the installed
  skill’s contract rather than guessing a sibling path. If unavailable, disclose it and preserve the
  readable plan without claiming the map was generated. Use specialist review, verification, RCA/AAR or ADR only when their actual task warrants it.
- Reuse: use skill-auto-manager to investigate existing projects/tools/skills before substantial
  new implementation when available. Read shared references through the installed skill's path,
  not assumed sibling paths. A file on disk is not proof of runtime availability.

## Record at the user's chosen boundary

`recording_policy` defaults to `manual`, because the user has not agreed to continuous automatic
recording. Persist results when the user requests recording/organization/handoff or authorizes a
specific output as part of the task. If a milestone policy is later explicitly adopted, follow it.
Do not log every conversation, infer consent to private-history scanning, or fabricate session events.

A research record should separate question/purpose, methods/conditions, observations, interpretation,
limitations, source/version/locator, and next action. Link existing artifacts, including unsuccessful
or partial results. Preserve stable `ris_id` and `project_id`; use related IDs only within this project.
Use the helper to create a new draft note, or use a specialist skill's existing canonical artifact
without making duplicate reports. Keep the relevant INDEX/CONTEXT links consistent when that update
is authorized. No extra user approval gate is introduced for already authorized record keeping.

Before changing an existing note, read its current bytes and preserve its identity. The helper's
`propose` creates a separate revision candidate and never replaces the source. For a requested direct
edit, show/inspect a narrow diff, preserve a preimage, re-read for external edits and stop on conflict;
Obsidian does not honor RIS's cooperative locks. Do not claim an atomic cross-editor merge. Do not
silently replace a confirmed decision; append its new rationale and link the superseded state.

For the agreed milestone workflow, record confirmed goals, explicit selections/changes, and established
verification results without a repeated permission gate. A recommendation or a hypothetical HTML choice
is not user acceptance. Existing projects keep their policy; adopt `milestones` only within the selected,
authorized project using `configure`. Do not initialize the tooling repository as a research target.
Use `update` for authorized note edits with a preimage hash; it preserves identity and a backup.

## Resume and hand off

Use `context` for a bounded snapshot of entry notes plus explicit project-local selections. Report
omitted files and why. This does not read their linked PDF/code, deliver the snapshot to another
session, establish comprehension, or expose the agent's internal context. Follow important links
before making claims about those sources.

When a handoff is requested, propose/update CONTEXT with current question, established knowledge,
current decision and conditions, active plan and current node, exploration mode, rejected/deferred approaches and reasons, unresolved questions,
next actions, and source links. Keep detailed findings in their original notes. Another agent
should be able to resume using only this project, the shared skill, and accessible original sources.

Run `check` after changes to managed research structure and report broken links, identity conflicts
and unperformed validation. Human edits remain Markdown-first; formatting checks do not validate
research claims. Do not claim a skill is live merely because its source or installation link exists.
