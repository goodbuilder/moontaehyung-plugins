---
name: ris
description: Answer research questions, explain concepts, compare alternatives, assess feasibility, and continue source-backed work at the depth the outcome requires. Use project context when relevant; initialize or persist project records only when requested or included in the task.
---

# RIS — outcome-driven research and continuity

RIS turns a research question into a useful, evidence-backed result and carries it forward when
project context matters. Work in the conversation by default. Project Markdown is a continuity layer;
Obsidian can read it. Authorized research plans include Markdown, an interactive HTML map, and a
project-root HANDOFF.md. Use the existing project records for continuity.

The main thread is the Coordinator. It owns user questions, assignments, dependencies,
integration, and completion. At the start and after material scope changes, identify the needed
roles using the [role workflow](references/role-workflow.md) (completion check for projects with `role_gate_profile`: [role gate](references/role-gate.md)) and delegate to available, permitted
specialists. Apply this rule even to one question. Handle work that requires no specialist directly.
If a needed role cannot be assigned, continue locally and report the reason, coverage, and any
verification or independent audit that did not run.

## Select the project and recording scope

Handle standalone questions in conversation without requiring a project or initialization. When the
request depends on a project, identify it from the request and current repository; pass its root
explicitly to helper invocations. Do not assume the tooling repository is the research target. If
multiple projects are plausible and the choice affects dependent reads or writes, ask which one.

For an initialized project, read .ris/project.yaml, research/INDEX.md, research/CONTEXT.md and
applicable project instructions before project-dependent work. Follow only links needed for the
question. Distinguish prior user statements from what has actually been read and verified.

Initialize a project only when requested. Use the bundled standard-library helper:

    python3 <this-skill>/scripts/ris.py --project <project-root> init --name <project-name>
    python3 <this-skill>/scripts/ris.py --project <project-root> check

Use --dry-run for a requested preview. Existing research entry files are never silently adopted or
overwritten. On a collision, inspect the layout and propose a mapping or adoption; do not force a
reset, rename user files or invent an empty research history. When setup includes custom agents,
use the [agent setup guide](references/agent-installation.md). Read helper details only as needed in
[operations.md](references/operations.md).

## Explore, ask, and continue

Use the request, corrections and relevant project context to derive the deliverable, success criteria,
constraints, known facts and prior decisions. Keep this working boundary in the conversation or an
already authorized canonical plan; do not require a separate setup interview or tracking file. Ask
task-grounded question rounds as described below.

When the user explicitly invokes RIS, perform initial exploration even for a narrow technical
question. Scale it to the request: checking the relevant source, code, or existing evidence and
looking for a condition that could change the answer may suffice. Then decide whether a user
question or conditional exploration is needed.

1. **Initial exploration:** Make a targeted first investigation. Read enough relevant evidence, compare
   the main credible approaches or resolve named terms, and identify which unknowns could change the
   result. If a material uncertainty requires user input, ask a concise, preferably batched set of
   questions grounded in those findings. Use
   the interactive question tool when available. For each question, state what is known, the reasonable
   assumptions or options, and why the answer matters. Do not stop at a generic decomposition, ask
   about facts that evidence can establish, or present a provisional ranking as final when user intent
   could change it.
2. **Conditional exploration:** After the user answers, continue from the confirmed scope. For each
   material unknown that remains, create bounded sub-branches under plausible assumptions or user
   choices. Investigate the evidence, dependencies and consequences of those branches far enough to
   make their differences clear. Do not ask as soon as a branch appears; continue the independent
   investigation and collect the remaining user-owned questions for a later, preferably batched,
   question round. Use the interactive question tool when available. Give options, conditional
   consequences and a reasoned default where useful.

Repeat conditional exploration if an answer or new evidence reveals another consequential unknown.
Resolve questions that evidence can answer, state safe assumptions, and keep low-impact possibilities
out of scope. Honor user exclusions; do not research or ask about them unless the user reopens them
or evidence shows that they invalidate the conclusion. If initial exploration leaves no material
user-owned uncertainty, answer directly and state any material assumption. If the user asks to
proceed without questions, give conditional results wherever an unresolved choice matters.

Scale investigation to the decision impact and requested result. Consider credible alternatives and
counter-evidence that could change the conclusion; do not recursively enumerate every conceivable
route by default. Widen scope when a correction or finding exposes a related omission, and explain
why it matters. A progress update is not completion: continue useful authorized work until the
completion criteria are met or a concrete evidence, intent, permission or resource boundary remains.
Research and planning do not authorize implementation, paid execution or real experiments.

See [research exploration](references/research-exploration.md) for question timing, conditional
branches, evidence and completion checks.

Before presenting a decision map, state the question each branch answers. Keep independent
choices on separate axes. Use parent-child links only for actual dependencies.

For a RIS decision tree about an established project goal, use that goal as the root even when
HTML is the only requested deliverable. Read the tree guidance in the
[shared output contract](references/shared-outputs.md) before drafting. Identify the decisions
and prerequisites needed to achieve the goal, and place user-specified scenarios under the
decision question they answer. Before delivery, verify that the root matches the user's goal
and that each necessary decision is represented, with unresolved choices marked.

## Use evidence and specialist skills when they help

Reuse available skills without merging them into a mandatory sequence.

- **Literature:** Use the user's Zotero skill or connection when available, alongside appropriate
  external sources. Keep source identity, locator, retrieval date and actual review scope. Search
  failure or limited access is not evidence that no prior work exists. Do not invent references or
  install a connector silently.
- **Learning:** Explain ordinary concepts directly. Use teach-me when the user requests a worked,
  hand-reproducible calculation or method lesson. Inspect actual formulas or code for such lessons
  and state units, assumptions, sources and execution limits. A lesson's creation does not establish
  understanding.
- **Planning:** Use project-plan when the outcome needs a durable plan with gates and fallbacks.
  Planner orders the work and links gate outcomes to decisions. Engineer supplies feasibility
  assessments, verification methods and acceptance criteria. Researcher supplies the evidence
  and alternatives for the Research Map (연구 지도). Ground the first question round before
  finalizing the plan and bound it to the confirmed outcome. Planner owns the authorized canonical
  plan. The Coordinator integrates results and keeps the entry links and handoff current.
- **HTML:** Use Archify for the interactive Research Map and Research Plan views as specified by
  the [shared output contract](references/shared-outputs.md). Use Designer for substantial layout
  or interaction work. Generate the views from the saved Markdown and keep HANDOFF.md current.
- **Independent audit:** Use research-audit when requested or when independent scrutiny materially
  improves a consequential conclusion. Keep manuscript/report/presentation review with reviewer and
  executable checks with verify-check. Do not call a local self-review an independent audit.
- **Reuse:** Use skill-auto-manager before substantial new implementation or at a concrete capability
  gap when available. A file on disk is not proof of runtime availability.

Before handing work to a specialist, pass the requested outcome, bounded scope, constraints,
questions, relevant evidence, canonical owner and recording permissions. Check returned evidence;
do not treat a completion message as proof.

## Deliver and record at the user's chosen boundary

Match the answer to the request: provide the result or recommendation, key evidence, conditions,
uncertainty and unresolved decisions. Distinguish verified facts, inference, assumptions, estimates
and unperformed validation. For practical use, investigate the inputs, dependencies, procedures and
verification that could change the result. Avoid padding with counts of sources, branches or tool calls.
Compare the deliverable with the active completion criteria before ending.

The project recording_policy defaults to manual. Persist findings when the user requests recording,
organization or handoff, or authorizes a specific project output as part of the task. Do not log every
conversation, infer consent to private-history scanning, or change a project's recording policy.
Existing projects keep their policy; follow an explicitly adopted milestone policy when present.

A research record should separate question and purpose, methods and conditions, observations,
interpretation, limitations, source/version/locator and next action. Link existing artifacts, including
partial or unsuccessful results. Preserve stable ris_id and project_id; use related IDs only within
the same project. Reuse a specialist's canonical artifact instead of making duplicate reports.

Before changing an existing note, read its current bytes and preserve its identity. For a requested
direct edit, inspect a narrow diff, preserve a preimage, re-read for external edits and stop on
conflict; Obsidian does not honor RIS cooperative locks. Do not claim an atomic cross-editor merge.
Keep CONTEXT's current-state sections current; move superseded claims to marked history or link their
records. Keep INDEX links consistent when the update is authorized. Do not rewrite unrelated notes.
Use the helper's guarded update when appropriate; read [operations.md](references/operations.md).

Use context for a bounded snapshot when resuming or handing off; report omitted files and why. It does
not read linked PDFs or code. Follow important links before making claims about them. A .ris/state.json
file is optional bookkeeping for a coordinated run; it does not replace canonical findings or plans.

When resuming an authorized plan, read HANDOFF.md if present, then open the linked canonical plan.
For a handoff outside that workflow, summarize the current question, confirmed criteria, established evidence,
active assumptions and branches, decisions and conditions, unresolved user questions, next actions and
source links. Keep detailed findings in their original notes. Run check after changing managed research
structure and report broken links, identity conflicts and unperformed validation. Formatting checks do
not validate research claims. Do not claim a skill is live merely because its source exists.
