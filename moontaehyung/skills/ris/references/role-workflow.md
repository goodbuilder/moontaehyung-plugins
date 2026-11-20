# RIS specialist roles

The Coordinator owns user questions and decisions, assignments, dependencies, integration, and
completion. Identify the needed roles at intake and after a material scope change. Assign each
needed role to an available and permitted specialist even when the task has one question. Start
independent assignments once their inputs are ready. For a required role that cannot be delegated,
record why, what was covered directly, and which checks are unavailable. Keep confirmed user
choices distinct from provisional recommendations.

## Responsibilities and handoffs

| Role | Call when | Owns and returns |
| --- | --- | --- |
| **Researcher** | A conclusion depends on evidence that needs a bounded investigation. | Findings and alternatives for the Research Map. Return the affected decision and option IDs, source locators and inspected scope, contrary evidence, conditions under which the result changes, and material gaps. |
| **Engineer** | A candidate's feasibility, resource fit, implementation, or verification is uncertain. | Technical configurations, interfaces, budgets, conditional forecasts, and the method and criterion that would verify each consequential claim. Return comparable assumptions, calculations or observed results, dependencies, and failure conditions. Run authorized analyses and checks, returning inputs, settings, reproducible commands or methods, results, and unverified conditions. |
| **Planner** | Independent work, prerequisites, or result-dependent choices need sequencing. | The canonical Research Plan and decision graph. Use Researcher evidence and Engineer's criteria to place the work, identify what can run in parallel, and link each gate to the choice it informs. Return the proposed work order, required inputs, pass/fail or inconclusive routes, fallbacks, and affected graph IDs. |
| **Designer** | The HTML needs substantial layout, interaction, or navigation work. | Archify HTML and its derived tree specification from the saved Markdown revision. Keep goal, constraints, decision IDs, statuses, and prerequisites aligned. Check node details and navigation between the Research Plan and Research Map when both exist. Return artifact paths, source revision, checks performed, and any rendering limits. |
| **Auditor** | The user requests independent review or a consequential conclusion benefits from it. | Scoped independent findings. Check claims against original goals, constraints and sources, including technical feasibility and the ability of a proposed gate to distinguish decisions. If HTML is in scope, check that consequential choices and statuses match the canonical plan. Return status, affected IDs, evidence, impact, and the smallest correction. |

Engineer defines **what a check measures and what result meets the requirement**. Planner decides
**when the check runs and which decision each outcome enables**. Researcher can supply evidence
for both. For example, Engineer defines a load check and its acceptance criterion. Planner puts
that check before the decision it informs and links the alternative routes to its outcomes.

When candidates can use the same stimulus, reference measurement, and environment, Planner
groups them in a shared test and records the run order. Start with a pilot to check the
reference and whether co-installation changes the results. Pair measurements within each run
if interference and added load are acceptable. Otherwise reuse the fixture and alternate or
balance candidate order within comparable conditions. When effects of multiple factors or their
interactions would change a decision, use design of experiments (DOE) to specify factors,
levels, responses, repeats, and run order. Verify the selected alternative in its intended
standalone configuration before drawing deployment conclusions.

Researcher identifies questions and evidence that apply to multiple alternatives and states
their scope. Engineer distinguishes shared acceptance criteria from measurements that must
be repeated for each implementation. Planner places a single shared node and references it
from the affected alternatives. Coordinator checks the scope and dependencies before accepting
the structure. Designer carries the shared node and references into the HTML, draws the
same-view reference lines required by the shared output contract, and checks each endpoint
and navigation target. In both views, verify that hovering highlights the full upstream
path, the expanded downstream subtree, and the applicable shared nodes and lines.
Check that collapsed descendants stay hidden and that the hover clears with a detail
panel open.

## Assignment and return

Give the role an outcome and question, constraints, affected stable IDs, relevant sources and
input revision, output path or format, acceptance criteria, and authorized actions. The return
identifies the input revision, resulting artifact or evidence, checks performed, and unresolved
conditions. Reuse prior work while its inputs and scope still apply.

Planner owns the canonical plan and serializes its writes. Researcher supplies source-backed
findings or counterevidence, Engineer specifies and runs authorized checks, and Designer writes
assigned derived views. Coordinator integrates these results and updates the handoff. Auditor
reviews claims and artifacts independently, reporting blocking findings, affected IDs, and evidence.

Route source or coverage gaps to Researcher, plan or branch defects to Planner, feasibility and
execution issues to Engineer, and rendering defects to Designer. A structural omission reopens
the same class of nodes across the affected scope. Version checks and audit findings against the
inputs and outputs they covered. If an artifact changes, repeat the affected checks for the
delivered revision. Local self-review does not count as independent audit. If independent review
cannot run, record it as NOT_RUN.

## Example workflows

- **Missing follow-up question.** Planner checks comparable branches and identifies the gaps.
  Researcher can investigate evidence in parallel where questions are already known. Planner
  updates the canonical plan with the findings and unresolved criteria. Designer renders from
  that revision. Engineer checks the required interactions on the delivered HTML. Auditor
  samples or checks the full affected class as warranted by the scope. Coordinator closes the
  task after addressing blocking findings.
- **Missing pending outline.** The saved plan already marks the question pending. Designer
  repairs the renderer or its input and rebuilds the map. Engineer checks the visible outline
  on the generated HTML. Reopen plan work only if the source state or scope is also wrong.
