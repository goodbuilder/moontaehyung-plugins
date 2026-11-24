# Faust — stock research with RIS continuity

The existing CLI agent is the interface. Research Markdown lives inside the selected project and
is readable in Obsidian. The paired Archify HTML map is a local reading artifact; no daemon, central database, separate chat interface or mandatory
MCP server is required. Keep code/data/results where the project already owns them and link them.

For autonomous RIS pre-analysis, the main Codex thread coordinates the run. The optional `planner`,
`researcher`, and `auditor` custom agents have separate responsibilities; their templates and
installation steps are in [agent installation](agent-installation.md). This Skill owns
project-local continuity, source records, and Researcher evidence workflow. Project Plan owns the
canonical decision graph and forecasts. The Coordinator owns overall run acceptance. If custom
agents are unavailable, continue the work that can be done locally and report which independent
capability did not run.

## Stock research

Use the existing RIS project format and its recording policy. For equity work,
identify the ticker, exchange, currency, horizon, and evidence cutoff. Compare
company disclosures with market expectations, material peer signals, and price
data appropriate to the session. Label assumptions in scenarios and keep exact
publication and observation times when they affect the analysis.

For retrospective forecasts, freeze pre-cutoff inputs, separate evidence
selection from outcome scoring when useful, and compare predictions against
simple baselines. If using independent forecasters, withhold the outcome and
identify limits to blinding. Do not infer trading or external-action authority
from a research request.

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
precedence remain intact. Read helper details only as needed in [operations.md](operations.md).

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
See [research exploration](research-exploration.md) for trend evidence and recording triggers.

## Carry research through to a usable result

For substantial research, the Researcher derives a coverage boundary from the assigned question,
requested outcome, constraints, and existing context. Keep it in the conversation or canonical
plan; no extra interview or file is required. Read the completion checks in [research exploration](research-exploration.md#completion-and-recommendation-checks)
before recommending or ending the research assignment. The Coordinator owns overall RIS completion;
the Researcher reports whether research coverage is adequate or explicitly bounded.

Treat a correction as evidence to recheck related omissions across the active scope, not just patch
the latest answer. A progress report is not a stopping point: continue authorized, useful work until
the research result is supported or the remaining work is genuinely blocked. A missing specialist
Skill does not block reasoning RIS can perform itself; state which specialist artifact or capability
remains unavailable.

## Research coverage and delegation

The Coordinator owns cross-role task routing and overall completion. The Researcher owns the assigned
research questions, required evidence, and research-coverage judgment. Keep consequential questions
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
  [shared RIS output contract](shared-outputs.md) for authorized plan deliverables.
  Update canonical Markdown and deliver its Archify guided exploration tree and project-root
  HANDOFF.md. Use Project Plan for the Markdown and graph checks. Use Archify for RIS HTML,
  including when the installed Project Plan instructions show its own render command.
- Independent RIS audit: for an autonomous pre-analysis, use `research-audit` when the Auditor is
  available. Keep manuscript/report/presentation review with `reviewer`, and executable checks with
  `verify-check`. Do not call a local self-review an independent audit.
- Reuse: use skill-auto-manager to investigate existing projects/tools/skills before substantial
  new implementation when available. Read shared references through the installed skill's path,
  not assumed sibling paths. A file on disk is not proof of runtime availability.

For multi-stage research, follow the [frontier completion check](research-exploration.md#run-the-next-investigation-before-closing-the-branch) before reporting research complete.

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

Use `context` for a bounded snapshot of entry notes plus explicit project-local selections. Report
omitted files and why. This does not read their linked PDF/code, deliver the snapshot to another
session, establish comprehension, or expose the agent's internal context. Follow important links
before making claims about those sources.

For autonomous runs, `.ris/state.json` may hold run status, task ownership/status, gate status, and
references to canonical artifacts. Use the helper's `state` commands to read or update it with a
preimage hash. Keep findings, decision graphs, forecasts, and source content in their existing
canonical records; state is bookkeeping, not a second research store. Existing projects without a
state file remain valid.

For an existing plan, read project-root HANDOFF.md and follow its link to the canonical Markdown.

When a handoff is requested, propose/update CONTEXT with current question, established knowledge,
current decision and conditions, active plan and current node, exploration mode, rejected/deferred approaches and reasons, unresolved questions,
next actions, and source links. Keep detailed findings in their original notes. Another agent
should be able to resume using only this project, the shared skill, and accessible original sources.

Run `check` after changes to managed research structure and report broken links, identity conflicts
and unperformed validation. Human edits remain Markdown-first; formatting checks do not validate
research claims. Do not claim a skill is live merely because its source or installation link exists.
