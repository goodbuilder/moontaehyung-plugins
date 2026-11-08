# Software architecture explanations

Read only the section that answers the current request. These are authoring choices, not a checklist for every diagram. Reuse the inspected facts and source ranges from [Repository authoring](repository-authoring.md); the project's existing architecture records remain authoritative. Keep the requested medium and scope.

## Choose a C4 view

Use this guidance when C4 is requested or the reader needs different levels of software structure distinguished. Establish the reader's question from the request, conversation and project documents; ask only if a material ambiguity remains.

| View | Reader's question | Show |
| --- | --- | --- |
| System context | What does this system do, and what is outside it? | The system, its users and external systems; label the boundary and exchanges. |
| Container | What runs or is deployed separately, and how does it communicate? | Evidenced executable/deployable units, relevant stores and their interactions. A C4 container does not mean a Docker container. |
| Component | How does a selected executable unit divide its work internally? | Its significant responsibilities, interfaces and dependencies; keep the owning unit clear. |

Choose the smallest set of views that answers the request. A single-view request does not require all three. Do not force a code-level view or turn every package/helper into an independently running unit. If a mixed overview is useful, identify its scope and distinguish the roles rather than silently flattening levels.

Use the existing diagram fields and composition rules. C4 terminology does not introduce schema fields, require a particular renderer, or justify hiding an evidenced control or persistence boundary.

## Explain existing choices

Use this guidance when the reader asks why the architecture has its current shape, or asks about goals, constraints and trade-offs.

- Look for the relevant accepted requirements, ADRs, design notes and change explanations. Use code to establish implementation; code alone does not establish which alternatives were considered or why a decision was made.
- Connect an evidenced goal or constraint to the structural choice, the intended benefit and the cost or limitation. Use a short table or explanation only when it helps the question; do not impose a quality-goal count or invent numeric targets.
- Keep documented intent, plausible interpretation and measured outcomes distinct. A mechanism that could improve reproducibility is not evidence that reproducibility was the original decision rationale or has been demonstrated.
- If rationale is missing, identify that specific unknown. Explain an implementation consequence as an inference when useful; do not fill the gap with a conventional architectural story.
- Link existing decision records instead of duplicating them. Explaining a choice does not authorize creating a new decision, redesigning the system, or initiating an unrelated review workflow.

Keep the conclusion and reasons readable using [Explainer writing](explainer-authoring.md#writing) when a page is requested. Do not turn an ordinary diagram into a report or page merely to fill these topics.

## Explain verification coverage

Use this guidance when verification, reproducibility or handoff is part of the requested architecture explanation.

- Trace an important responsibility to relevant test assertions, fixtures and existing execution evidence. Describe unit, integration or system scope only when the actual boundary supports that classification; a test filename alone is insufficient.
- Identify the real target, mocked or simulated substitutes, test-data source and any boundary left outside the check. Do not infer hardware behavior or full-system coverage from a local fixture.
- Separate tests present in the repository, previously recorded runs, and checks actually performed in this task. State skipped, failed and unknown coverage without treating absent evidence as a failure.
- Explain how test inputs/results relate to the system's source data and artifacts where this matters to reproduction. Reuse existing lineage and ownership guidance rather than drawing a new producer from a file name.
- Artifact/schema/browser checks validate the delivered explanation. They do not demonstrate the described system's correctness, scientific accuracy or runtime behavior.
- Describing the available checks does not by itself require running a suite, starting the application, or contacting hardware. Execute only checks warranted and authorized by the task, and label unperformed verification.

Use a compact responsibility-to-check table or a sourced note if it answers the reader's question. Keep unrelated testing and deployment inventories out of a simple structure diagram.

