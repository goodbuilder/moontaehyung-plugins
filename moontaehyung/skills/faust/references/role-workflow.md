# RIS specialist roles

The main RIS thread coordinates the work. It owns the research question, active constraints,
user question rounds, assignment boundaries, overall conclusion, and updates to the canonical
records. Record confirmed user choices separately from provisional recommendations. The five
specialists below are optional. The main thread can perform short or closely coupled work directly.

## Responsibilities and handoffs

| Role | Call when | Owns and returns |
| --- | --- | --- |
| **Researcher** | A conclusion depends on evidence that needs a bounded investigation. | Findings and alternatives for the Research Map. Return the affected decision and option IDs, source locators and inspected scope, contrary evidence, conditions under which the result changes, and material gaps. |
| **Engineer** | A candidate's feasibility, resource fit, implementation, or verification is uncertain. | Technical configurations, interfaces, budgets, conditional forecasts, and the method and criterion that would verify each consequential claim. Return comparable assumptions, calculations or observed results, dependencies, and failure conditions. Perform checks only within the user's authorized scope. |
| **Planner** | Independent work, prerequisites, or result-dependent choices need sequencing. | The structure of the Research Plan. Use Researcher evidence and Engineer's criteria to place the work, identify what can run in parallel, and link each gate to the choice it informs. Return the proposed work order, required inputs, pass/fail or inconclusive routes, fallbacks, and affected graph IDs. |
| **Designer** | The HTML needs substantial layout, interaction, or navigation work. | Archify HTML and its derived tree specification from the approved Markdown revision. Keep goal, constraints, decision IDs, statuses, and prerequisites aligned. Check node details and navigation between the Research Plan and Research Map when both exist. Return artifact paths, source revision, checks performed, and any rendering limits. |
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

## Coordinate by investigation stage

- During initial exploration, use available evidence first. Call Researcher for a material gap
  and Engineer when feasibility determines what to ask. The main thread asks only questions
  that require material user input, after the initial evidence has been gathered.
- After the first answer, assign consequential assumption branches as needed. Reuse common
  evidence and investigate what changes across branches. Planner uses the results to sequence
  dependent work. Collect later user questions after their practical consequences are clear.
- Once a recommendation is concrete enough to inspect, Auditor can challenge the consequential
  claims. Route source issues to Researcher, technical criteria or feasibility issues to Engineer,
  and missing prerequisites or result paths to Planner. Recheck the findings and their affected
  dependencies after a correction.
- For authorized file outputs, the main thread incorporates accepted results into Markdown
  and refreshes the handoff. It can render a straightforward HTML update through Archify
  directly. If delegated, Designer uses the saved Markdown revision and the
  [shared output contract](shared-outputs.md). The main thread checks the HTML against the latest
  plan before delivery and routes presentation defects to Designer.

## Assign and integrate work

Give each specialist the applicable role instructions, an outcome and question, affected stable
IDs, current constraints, relevant evidence and paths, expected result, and allowed actions.
For existing files, include the relevant source revision or snapshot. Reuse completed assignments.
Keep assignment scope proportional to the decision and have requests for other roles go through
the Coordinator. Use a named role whose instructions match these boundaries, or give the same
scoped brief to a permitted generic worker. Apply the current session's delegation permissions.

Route unresolved user choices to the main thread with evidence and conditional consequences.
Specialists propose updates by stable ID. The main thread serializes canonical Markdown and
handoff writes. Designer may write assigned derived artifacts within the authorized scope.
When a user correction or concurrent edit changes an input, recheck the affected IDs before
applying returned results, and regenerate only the affected views from the saved Markdown.

If a named role is unavailable, continue authorized work that can be performed directly.
Label independent audit work as `NOT_RUN` when it could not be delegated. Report any required
evidence, check, or artifact that remains unavailable. Record run bookkeeping in the existing
optional RIS state only when that workflow is already in use.
