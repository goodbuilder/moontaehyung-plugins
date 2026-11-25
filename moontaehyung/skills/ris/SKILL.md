---
name: ris
description: Initialize or resume project-local research, align the agent with the user's background, organize source-backed learning and branching plans, and record findings or handoffs in Markdown for Obsidian. Use for RIS requests and research continuity in initialized projects. Also use for explicit requests to diagnose or improve the RIS skill or its role instructions. Do not initialize unrelated projects or record every conversation automatically.
model: claude-fable-5-2
effort: medium
---

# RIS — project-local research continuity

The existing CLI agent is the interface. Research Markdown lives inside the selected project as
ordinary local files. In the schema v2 default, `.ris/research` is dot-prefixed and may not appear
in the parent Obsidian vault's navigation or Vault API; see [Obsidian's Vault API guidance](https://docs.obsidian.md/Plugins/Vault).
The paired Archify HTML map is a local reading artifact; no daemon, central database, separate chat interface or mandatory
MCP server is required. Keep code/data/results where the project already owns them and link them.

For autonomous RIS pre-analysis, the main thread coordinates the run. The optional `planner`,
`researcher`, `engineer`, `designer`, and `auditor` custom agents have separate responsibilities; their templates and
installation steps are in [agent installation](references/agent-installation.md). This Skill owns
project-local continuity, source records, and Researcher evidence workflow. Project Plan owns the
canonical decision graph and forecasts. The Coordinator owns overall run acceptance. If custom
agents are unavailable, continue the work that can be done locally and report which independent
capability did not run.

## Classify the request first

Choose one mode from the request and project state, say it in one line, and load only what that mode needs.
An explicit request about the RIS skill, plugin or its role instructions goes to
[maintenance](references/maintenance.md) and the plugin source. An explicit request about
an application goes to that application. When the target is genuinely ambiguous, ask once
before inspecting or changing either project.

- **Resume**: initialized project and a request to continue. Read the entry notes and report; no exploration.
- **Record / hand off**: a stated recording, organization or handoff request. Use the record and handoff sections.
- **Initialize**: a stated request to start a project. Preview with `--dry-run`, then initialize.
- **Explore**: a research question whose answer needs approach families, evidence or a plan. This mode
  carries the breadth discipline, the work log and the summary below.
- **Narrow answer or meta question** (a factual lookup, or a question about improving RIS itself): answer
  directly with sources where used. The discipline scales down; do not run the full inventory.
  For a short request to choose among options, also use the [choice guidance](#carry-research-through-to-a-usable-result).
- **Not an initialized project**: do not initialize the tooling repository. Explore without a log, say
  that no work log exists, and offer a project root. The exploration evidence is then the conversation only.

## Establish the project and recording scope

Identify the exact project from the user's request and current repository. Pass its root explicitly
to every helper invocation; never use a global active-project selection. If multiple projects are
plausible, ask before dependent reads/writes. Work in the user's existing project; do not assume
that the current tooling repository is the research target.

For an initialized project, read `.ris/project.yaml`, resolve its `research_dir`, then read that
directory's `INDEX.md` and `CONTEXT.md` plus applicable project instructions. Schema v2 defaults
to `.ris/research`; schema v1 projects keep using their configured `research` directory. Do not
create a parallel root `research/` tree. Inspect linked records only as required for the task.
Summarize current understanding, important uncertainties and the next step briefly. Distinguish
what the user previously stated from what the current agent has actually read and can establish.

For a requested initialization, use the bundled standard-library helper:

```bash
python3 <this-skill>/scripts/ris.py --project <project-root> init --name <project-name>
python3 <this-skill>/scripts/ris.py --project <project-root> check
```

Use `--dry-run` if an initialization preview is requested. Existing research entry files are never
silently adopted or overwritten. On a collision, inspect the existing layout and propose mapping
or adoption; do not force a reset, rename user files or invent an empty research history. Schema v2
creates managed research under `.ris/research/`. Existing schema v1 projects continue to use
`research/` until the user explicitly requests `migrate-layout`; that command previews by default,
and only `migrate-layout --apply` applies the reviewed mapping. Initialization and ordinary writes
do not migrate files or move the legacy root `HANDOFF.md`. The
AGENTS block is a short entry point, not a duplicate of the skill. Existing instructions and their
precedence remain intact. Read helper details only as needed in [operations.md](references/operations.md).

## Align the outcome and lead exploration

Read existing context before asking. Extract the desired deliverable, success criteria, user knowledge,
constraints, preferences and prior decisions; distinguish stated intent from inferred intent. Ask only
material gaps that affect the current result. Do not make users restate facts available in the project.
In Explore mode, survey distinct credible approach families before
ranking, then recursively investigate the consequential decisions introduced by every viable route.
Before ranking any approach, read
[research exploration](references/research-exploration.md#exploration-breadth-discipline) in full; the
summary below only names the obligations and does not replace it:
1. Split each decisive unknown by source kind (measure, derive from what is at hand, construct, estimate
   from the process), then add a branch that negates the premise all candidates share.
2. Read each condition at its stated scope; reject only on a stated constraint or quantified evidence.
3. Look up every named product/standard/tool/dataset in primary sources, one search naming its variant
   or version each, and show a per-entry table.
4. Search before ranking: several distinct recorded queries, including practice and adjacent fields.
5. Run a second gap pass; revisit options rejected on assumption.
6. Give a fragment-combination table and the unknowns still open.
7. For each option dismissed as insufficient alone, state and test the minimal complement.
8. Build the resource-by-unknown matrix; no resource left in only its default role unmentioned.
9. After a goal-meeting candidate, counter-search for materially different principles or resources;
   recompute borderline options under varied assumptions before rejecting.
10. Before "not found", run two differently worded queries or open a primary source.
11. Open primary text for top candidates and every ranking-deciding figure.
12. Work the frontier: investigate the top three unexplored items before returning.
**Return checklist:** run through items (a)-(k) in the reference before returning; `check` counts the
mechanical parts (distinct queries, sources opened beyond a snippet, summary structure) and warns, but
cannot judge completeness or understanding.
A first comparison or first executable task is not completion. Display a compact overview while retaining
the full candidate inventory, expanded paths and explicit unexplored frontier in the HTML map. A user request to follow a
specific branch switches the active task to guided exploration; persist that preference only if asked.
Research autonomy covers investigation and planning, not costly experiments or implementation commitments.
See [research exploration](references/research-exploration.md) for trend evidence and recording triggers.

**Exploration work log.** In an initialized project, while running the exploration above, append one
line per search query and per source actually opened. Use the question or decision ID from
the active plan or working context with `explore --question ID`. Choose a short stable ID
when the question has none. Supply the query and channel or the source locator and read
scope as described in [operations](references/operations.md). Record activity as it occurs.
For an earlier read that applies to another question, link its existing read ID to that
question and cite its locator. At a checkpoint, `summarize` derives the question's new activity
and reused reads from the log. Write what the evidence changes in the summary body; use
`check --question ID` when inspecting a particular question.
Older entries without an assignment remain unassigned until a relevant link is established.
The log contains self-reported search activity and source locators. Keep conversation text
and analysis out of it. The project’s recording policy still applies.
Do not claim a read beyond the logged scope (a `snippet` is not a read of the source).

**Exploration summary (the human-readable layer).** The user reviews the summary, not the log.
Refresh it with `summarize` at each checkpoint: when one approach family's investigation ends,
and always before returning results, handing off or stopping. Read the current summary first
(its hash comes from `context`), carry forward anything a human added, then submit the whole body.
The body has exactly four sections, each non-empty (write `없음` if none): 탐색한 접근 계열 /
기각·보류한 후보와 이유 / 미탐색 프런티어 / 검수 요청. One short line per item, with the log IDs
(`Q-0003`, `R-0002`) that support it on the same line. Keep it to one screen (6000 characters); if
items must be dropped, keep the highest priority and state how many were omitted. Put in 검수 요청
only what needs the user's judgment: a rejection without evidence, a conclusion resting on one source,
a "not found" with too few queries, a preference or risk choice, a checklist item not met. Do not write
the statistics block; the helper computes it from the log. Mark exclusion items with `[기각]`,
`[보류]` or `[사용자 결정]` so the reader can distinguish a query-only deferral from an unsupported
rejection. Link the recorded selection for a user decision. The summary is the agent's own account and
is not an independent audit; the log IDs are what let a reader or the Auditor verify a line.

## Carry research through to a usable result

For substantial research, the Researcher derives a coverage boundary from the assigned question,
requested outcome, constraints, and existing context. Keep it in the conversation or canonical
plan; no extra interview or file is required. Read the completion checks in [research exploration](references/research-exploration.md#completion-and-recommendation-checks)
before recommending or ending the research assignment. The Coordinator owns overall RIS completion;
the Researcher reports whether research coverage is adequate or explicitly bounded.
When evidence affects a choice, use [evidence behind a recommendation](references/research-exploration.md#evidence-behind-a-recommendation).

When the user asks for a choice, explain the recommendation, reasons to defer or exclude
alternatives, what could reverse the recommendation, and the next available action. Use
the stated acceptance conditions and tie each observation to its candidate and conditions.
Distinguish an open requirement from a prerequisite the user or current decision record
explicitly marks satisfied. Cite the latter to its own source and reopen it if the scope
changes or contrary evidence appears. A measurement of one criterion can leave another
established premise intact. A threshold establishes eligibility. If several options
pass, rank them only on an expressed preference or explain the remaining choice.
For a single fact, give the fact and its source. Only the user makes a selection.
For changed evidence, follow the
[correction procedure](references/research-exploration.md#apply-a-correction-to-the-decisions-that-used-it).

Treat a correction as evidence to recheck related omissions across the active scope, not just patch
the latest answer. A progress report is not a stopping point: continue authorized, useful work until
the research result is supported or the remaining work is genuinely blocked. A missing specialist
Skill does not block reasoning RIS can perform itself; state which specialist artifact or capability
remains unavailable.

## Research coverage and delegation

The Coordinator owns cross-role task routing and overall completion. At intake and after a material
scope change, identify the needed roles using the [role workflow](references/role-workflow.md) (when
each role is called, what it owns and returns, and how Engineer, Planner and Researcher hand off) and
delegate to available, permitted specialists. The Researcher owns the assigned
research questions, required evidence, and research-coverage judgment. The Engineer owns feasibility,
resource fit and the verification method and acceptance criterion for each consequential claim; the
Designer renders the Archify HTML from the saved Markdown revision. Keep consequential questions
in the existing plan or conversation; project-plan owns their branching structure. When delegation is
useful, use available auto-subagents for allocation and coordination. Provide concrete questions,
needed evidence, dependencies, and the need for independent investigation; retain the same coverage
when working locally or when delegation is unavailable. Treat spawned investigation workers as leaves;
if a specialist cannot delegate in the current runtime, return bounded worker briefs to the Coordinator.

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
- Planning: use Project Plan for consequential branches, quality gates and fallbacks. Follow the
  [shared RIS output contract](references/shared-outputs.md) for authorized plan deliverables.
  Update canonical Markdown and deliver its Archify guided exploration tree and layout-appropriate
  handoff (`.ris/HANDOFF.md` for schema v2; the existing root `HANDOFF.md` for unmigrated schema v1).
  Store final RIS plan/map HTML beside the canonical plan under the configured `research_dir`.
  Keep RIS-mode Archify working files and diagnostics inside `.ris/`; do not write them to a
  project-root `.archify/`. Use Project Plan for the Markdown and graph checks. Use Archify for RIS HTML,
  including when the installed Project Plan instructions show its own render command.
- Independent RIS audit: for an autonomous pre-analysis, use `research-audit` when the Auditor is
  available. Keep manuscript/report/presentation review with `reviewer`, and executable checks with
  `verify-check`. Do not call a local self-review an independent audit.
- Reuse: use skill-auto-manager to investigate existing projects/tools/skills before substantial
  new implementation when available. Read shared references through the installed skill's path,
  not assumed sibling paths. A file on disk is not proof of runtime availability.

For multi-stage research, follow the [frontier completion check](references/research-exploration.md#run-the-next-investigation-before-closing-the-branch) before reporting research complete.

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

For a requested multi-session study, or a later visit that supplies only a raw result log, read the
[study workflow](references/study-workflow.md) and the current canonical study before interpreting
the result. If an observation suggests a new explanation, amend the same study before testing
its prediction. Preserve the earlier evidence as the origin of the idea. For a decision-bearing count, ratio or threshold from CSV or JSONL, use the
[metric workflow](references/metric-workflow.md) to record how the rows were selected and replay
the calculation. Use the generated `study results` summary or table for numerical statements
in the answer. Explain the meaning and limits separately. Combine numerical criteria only
under an explicit rule that represents the actual requirements. A proxy metric can leave a
mandatory criterion unresolved. When the user asks about several test conditions, give the
verdict for each under the user's rule and the stated evidence assumptions. Then say how far
those results generalize. Additional checks proposed by the researcher affect confidence unless
the user adopts them as mandatory criteria. A managed study is opt-in; `recording_policy` remains manual. Its evolving hypothesis
assessment and provisional recommendation belong in `decisions/study-<ID>.md` under the configured
research directory. Link to it from the plan, CONTEXT, applicable HANDOFF and map instead of
maintaining duplicate mutable recommendations. Preserve any confirmed user selection and its
history in the existing canonical records. Follow the [shared output contract](references/shared-outputs.md#managed-studies)
for links and rendered snapshots.

Before changing an existing note, read its current bytes and preserve its identity. The helper's
`propose` creates a separate revision candidate and never replaces the source. For a requested direct
edit, show/inspect a narrow diff, preserve a preimage, re-read for external edits and stop on conflict;
Obsidian does not honor RIS's cooperative locks. Do not claim an atomic cross-editor merge. Do not
silently replace a confirmed decision; append its new rationale and link the superseded state.

Within authorized recording scope, keep CONTEXT's current-state sections current rather than
appending corrections beneath stale active instructions. Move superseded claims to a clearly marked
history section or link their existing records; preserve IDs, evidence, and prior decisions. INDEX
should point to the current plan and result. Do not change recording policy or rewrite unrelated
project notes merely to satisfy this convention.

For the agreed milestone workflow, record confirmed goals, explicit selections/changes, and established
verification results without a repeated permission gate. A recommendation or a hypothetical HTML choice
is not user acceptance. Existing projects keep their policy; adopt `milestones` only within the selected,
authorized project using `configure`. Do not initialize the tooling repository as a research target.
Use `update` for authorized note edits with a preimage hash; it preserves identity and a backup.

## Resume and hand off

When resuming a specific question or decision, run `context --question <ID>` with the same
project root and the ID used by `explore`. If the user names the topic in words, resolve its
existing ID from the plan, context or question IDs in `check`. The question snapshot contains
the logged queries and source locators, including reads explicitly reused for that question.
Use the recorded read scope when citing
a source. If entries were omitted, repeat with `--max-chars` set to `characters_required`.

Use `context` for a bounded snapshot of entry notes plus explicit project-local selections. Report
omitted files and why. This does not read their linked PDF/code, deliver the snapshot to another
session, establish comprehension, or expose the agent's internal context. Follow important links
before making claims about those sources.

For autonomous runs, `.ris/state.json` may hold run status, task ownership/status, gate status, and
references to canonical artifacts. Use the helper's `state` commands to read or update it with a
preimage hash. Keep findings, decision graphs, forecasts, and source content in their existing
canonical records; state is bookkeeping, not a second research store. Existing projects without a
state file remain valid.

For an existing plan, read the handoff path for that layout: `.ris/HANDOFF.md` for schema v2, or
the existing root `HANDOFF.md` for a schema v1 project that has not completed an explicitly applied
layout migration. Follow its link to the canonical Markdown and verify both against current files.

Do not attach Coordinator instructions to the project's root `AGENTS.md` or `CLAUDE.md` by default.
That optional integration is available only when explicitly requested; preserve existing project
instructions and treat the root files as project-owned.

When a handoff is requested, propose/update CONTEXT with current question, established knowledge,
current decision and conditions, active plan and current node, exploration mode, rejected/deferred approaches and reasons, unresolved questions,
next actions, and source links. For a managed study, link its canonical record for the evolving
assessment and recommendation rather than copying them; keep explicit user selections distinct.
Keep detailed findings in their original notes. Another agent
should be able to resume using only this project, the shared skill, and accessible original sources.

Run `check` after changes to managed research structure and report broken links, identity conflicts
and unperformed validation. Human edits remain Markdown-first; formatting checks do not validate
research claims. Do not claim a skill is live merely because its source or installation link exists.

## Changing this skill

To modify RIS (this skill, its references, scripts or role agents), edit only the plugin source
directory and never an installed cache copy; follow [maintenance](references/maintenance.md).
