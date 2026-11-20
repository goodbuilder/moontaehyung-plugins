# Shared RIS research outputs

Codex and Claude use the guided exploration tree in Claude RIS's `guided-v5/tree.html`
as the reference for the HTML view. For a
research task with an authorized plan deliverable, keep one canonical Markdown plan in the
selected project's existing plan location. In a managed RIS project use `research/plans/<plan>.md`
and put the generated HTML files beside it, with `HANDOFF.md` at the project root.
When both views are needed, generate separate standalone files for the Research Plan and
Research Map. For new Korean artifacts use `<project-goal>-연구 계획.html` and
`<project-goal>-연구 지도.html`. Use corresponding labels in the user's language and
replace characters that cannot be used in a portable filename. Preserve existing paths when
splitting or revising published artifacts where the resulting roles remain clear. Update links
when a path changes. Conversation-only requests and standalone
evidence notes retain their existing recording scope.

The Markdown file is the editable source. Preserve its plan and node IDs and managed frontmatter.
Use the [Project Plan graph contract](../../project-plan/references/graph-contract.md) for the
canonical plan. Include the current question, criteria,
candidate inventory, evidence and forecasts, explored paths, exclusions with reasons, remaining
frontier and next actions. Keep the initial findings and questions, user decisions, and later
assumption branches and consequences in the same plan. For applicable comparisons include the
Claude-style partial-solution combination table, minimal complements and their placement, and
resource-by-unknown matrix. These are output conventions. Use the RIS exploration rules for
question timing and investigation depth.

## Current constraints

Keep a `현재 제약조건` section in the canonical Markdown plan. Distinguish confirmed
constraints, preferences, and provisional assumptions. State their scope and link the source
or decision when available. Link a shared constraints file when multiple plans use it.

Read this section and any applicable linked constraints when starting or resuming work on
the plan, before the initial exploration or the next active branch. Recheck affected constraints
after user corrections or new evidence, and before creating or ruling out branches, making a
recommendation, or regenerating the map. Reuse the current reading within the same work session
until a change or a consequential decision warrants rechecking.

When a constraint changes, update the active section and retain the previous value and rationale
in the plan history. Revisit affected branches. In HTML, show plan-wide constraints at the goal
and option-specific conditions or violations at the relevant nodes. Link the section from the
handoff when a constraint matters for the next action.

## HTML map

Use the [RIS role workflow](role-workflow.md) for authorship and delegation. Planner owns the
canonical plan. Designer produces assigned HTML views from a saved revision and returns the source
revision and output identity. Engineer verifies required rendered behavior on that output when
execution verification is needed. Auditor compares consequential content and status against the
same revision when independent review applies. Coordinator checks the delivery and handoff.
Keep structural changes in the canonical plan, and make presentation changes reproducible in
the renderer or derived specification. Resolve the workflow path beside this file's
source when an installed copy links to the shared output contract.

Check the canonical plan using the graph contract. Generate the standalone HTML beside it
with Archify's interactive tree renderer from a derived tree specification. Use a goal root
with current constraints, then decision questions, mechanism families where useful, and
concrete options. Expand an option into a further question only when choosing it changes the
downstream decision. Show concise evidence on nodes, distinguishing observations, calculations,
forecasts and assumptions. Mark constraint violations and unresolved choices with their reasons.

Place the project goal at the left edge of the research map and expand to the right
(`layout.direction: "right"` in Archify). Use each vertical decision column for parallel
decisions (병렬 결정) that can be made independently of one another. Group alternatives
under their shared decision. Place a decision or task that requires an earlier result or
selection in a column to its right, and name its prerequisite.
Check the rendered columns against the dependencies. If tree layout would align dependent
items with their prerequisites, use a reference to the downstream gate or task instead.

When updating an existing research map, preserve its nodes and stable IDs. When the user selects
an alternative, update its status and expand the requested branch. Keep other alternatives and
their descendants visible with their current status, including unselected and undecided options.
Remove nodes only at the user's request. Before delivery, compare the previous and updated node
IDs and verify that every removal was requested.

After investigating a research-map branch, mark the node that already states each consequential
open question or decision. Preserve its ID and keep its alternatives under it. Add a child node
under the relevant alternative only when the investigation reveals a distinct follow-up question.
Prefix the unresolved node's label with `[Answer needed] ` or
`[Decision needed] ` in English, and `[답변 필요] ` or `[결정 필요] ` in Korean.
State what evidence or input is needed and which choice the answer could change. Use the workspace's
Archify tree renderer with pending-node support and verify that the node outline is dashed.
When resolved, preserve the node ID, record the outcome and evidence, and remove the prefix.
Show a navigable overview with expandable branches and node detail. Scale the tree to the
investigation stage and evidence available. Keep detailed comparisons and source citations in
Markdown and use the same decision IDs in both views. Keep the tree specification derived from
Markdown. Browser interactions do not confirm decisions. Report an unavailable tree renderer
or failed generation as a partial deliverable.

### Preserve investigation and decision dependencies

When execution and alternative comparison both need a view, generate the research plan and the
goal-rooted research map as separate HTML files from the same canonical Markdown. Use
**Research Plan** and **Research Map** as the document headings in English. In Korean, use
**연구 계획** and **연구 지도**. Link both files from the Markdown and handoff. The research plan shows ordered or parallel work, prerequisites, and conditional
next steps based on observed results or gate outcomes. The research map shows decision questions,
concrete alternatives, and their applicability. For example, a load test and its pass/fail routes
belong in the research plan. The comparison of retaining mechanisms belongs in the research map.
Link the relevant test outcome to that choice by stable
decision ID and link the selected route back to its verification work.

For a common task that requires one selected alternative, reference the selection gate from
the research plan and place the task after that gate. For example, compare sensor models in
parallel in the research map. Once a model is selected, investigate its calibration procedure
and verify the installed sensor in the research plan. If calibration method itself requires a
choice, place that question under the selected model in the research map and link it to the plan.

When alternatives share a question, place it once at the narrowest scope that covers them
and refer to it from each applicable alternative by stable ID. Share a criterion across
interfaces when it applies to all of them. Keep results tied to the configuration in which
they were obtained when interfaces, hardware, or conditions differ.

When the alternatives and the shared node appear in the same HTML view, draw a dashed
reference line from each applicable alternative to the single shared node. Distinguish
these lines from the tree's parent-child links. Keep stable-ID navigation in node details.
Verify that each intended source and target is connected, that the lines remain legible,
and that collapsing a branch hides links with hidden endpoints. Use a navigable reference
for a shared node in another view.

On hover in the research map or plan, highlight the hovered node, its tree ancestors up
to the goal, and all visible descendants in its expanded subtree. Also highlight any
visible shared upstream nodes referenced by that highlighted set and the applicable tree
and dashed reference lines. Keep collapsed descendants hidden. Clear the temporary
highlight when the pointer leaves, preserving any selected node and its detail panel.

When the plan has consequential prerequisites, distinguish investigations that can
start independently from decisions that depend on their results. For each such
investigation, name the output that feeds a later decision. In the canonical graph,
give a decision explicit incoming dependencies or a shared gate that names the
required evidence. Mark which inputs are jointly required and which only apply
under a stated condition. When choices constrain each other, compare feasible
bundles at the shared decision. Items discovered together can have different
prerequisites. Group the overview by the actual dependencies of this plan.

In the tree, show independent first investigations as siblings when they are the
current work. Show convergence with one shared decision or gate and identify it by
the same stable ID from each contributing branch. If a reference is plain text,
name its destination and make the shared node findable by that ID. At the shared
node, say which inputs must be available before deciding. Show successors under
their condition or as clearly marked references. A separate options overview may
group alternatives for comparison. Label it as such so it does not imply execution
order. Use this structure only where the plan has these dependencies.

### HTML acceptance check

Before delivery, open the generated HTML and trace a representative route from
independent investigations through any shared gate to a conditional decision.
Confirm that the prerequisites, pass/fail paths, and decision status agree with
the Markdown. When both files exist, open a verification node in the research
plan to see its method and pass/fail criteria, follow its link to the research
map decision to see the candidates and their evidence, and follow the link back
to the relevant verification node. A schema or render pass checks structure.
If browser interaction cannot be checked, inspect the generated hierarchy,
node details, and link targets and report which interaction remains unverified.

The RIS HTML route applies even when the installed Project Plan copy shows its own render
command. Use that skill for Markdown and graph checks and use Archify for the RIS map.

## Handoff

Keep one concise project-root `HANDOFF.md` for the active plan. Create or refresh it when saving
an authorized plan milestone or handing the work off. Use project-relative links and include:

- The current research stage and whether a user answer is pending.
- The canonical Markdown plan and both generated HTML paths when applicable, plus the active
  decision or branch IDs.
- The next concrete investigation or decision and any blocker.
- User questions that still matter, with the condition for asking them later.

Preserve unrelated content if a project already uses `HANDOFF.md`, updating a dedicated RIS section.
Leave detailed evidence, decisions, and branch history in the plan. On resume, use the handoff as
an entry point and check its pointers against the current Markdown and actual files. If they
disagree, continue from the canonical plan and refresh the handoff at the next authorized write.

After an authorized update, regenerate the affected HTML files from the saved Markdown,
refresh the handoff, and report the Markdown, generated HTML files, and handoff paths.
If generation fails, mark the affected file stale or missing in the handoff and report the
specific blocker.
