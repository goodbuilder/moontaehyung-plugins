# RIS specialist roles

The Coordinator brings unresolved choices to the user and owns assignments, dependencies,
integration and completion. The user confirms goals, constraints and final selections. Identify the needed roles at intake and after a material scope change. Assign each
needed role to an available and permitted specialist even when the task has one question. Start
independent assignments once their inputs are ready. For a required role that cannot be delegated,
record why, what was covered directly, and which checks are unavailable. Keep confirmed user
choices distinct from provisional recommendations.

Use the [unified self-critical workflow](self-critical-workflow.md) as the single research
control-loop contract. Coordinator selects and revisits perspectives, maintains stable node identity
and deepening counts, dispatches actual discriminating actions and integrates lineage/invalidation.
Researcher returns evidence and critical follow-ups for each assigned perspective; Engineer tests
feasibility and discrimination; Planner links prerequisites, alternatives and resulting invalidation
to the canonical graph. A completed assignment is distinct from evidence sufficiency. Use the
research-audit skill for blind independent assurance and [recovery operations](recovery-operations.md)
for CLI recovery; neither local self-review nor operational recovery establishes research acceptance.

## Receive a result without polling its files

When another role owns a needed artifact, agree on its stable path or ID at dispatch. Have the
owner return the path, revision or digest, and what changed. The receiving role works on other
ready questions while the owner runs. On a host with completion notifications use that return
to trigger one read and the required checks on the stated revision. A known unchanged file or
directory does not establish readiness. Reopen it when a new revision is reported, the observed
revision differs, or a concrete validation failure warrants inspection. If the host lacks
notifications, make a bounded status check at a dependency or deadline checkpoint. A single
read of the right revision can serve its downstream consumers; preserve each Auditor's independent
evidence inspection and recomputation. Check the clock when making a scheduling or delivery
decision, without a parallel loop of clock and directory probes.

For a finding that another role will compress for a decision, the evidence owner supplies its
selected user-ready passage with the record revision. Follow the
[final passage handoff](self-critical-workflow.md#carry-the-evidence-through-to-the-decision).
The Coordinator owns the outgoing answer and the Auditor owns substantive review.

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

For mechanism-dependent research, use the [causal and solution exploration contract](research-exploration.md#explore-causes-and-solutions-together).
Send a consequential discovery when it can redirect another assignment. Include fact or hypothesis,
locator and conditions, affected question/option/candidate IDs, the new question, required input
and next action. Coordinator assigns or performs that action, checks the resulting evidence, then
routes changes to the owners of affected findings, candidates, gates and audits. Preserve
unaffected results at their applicable revision. Start independent investigations together. Wait
only for the specific input a check needs. Report actual overlapping assignments and unavailable
roles separately from work performed sequentially.

For competing explanations, Researcher returns the observation both explain, the assumptions
where they differ, and an inspected locator or counterexample. Engineer identifies a check
whose possible results separate the candidates, including the conditions that would make it
invalid and the resources needed. If the claim explains a change, use a common baseline
or observe the relevant components directly. A comparison can rank outcomes while leaving
the mechanism unresolved. Planner links each result (including an inconclusive one)
to the decision it would change. If all outcomes leave the same choice, defer that check.
For example, two catalogues can give the same count while one counts titles and the
other counts editions. Inspect a known title with two listed editions under the same
date filter. One entry or two can distinguish the explanations. Different coverage
windows make this comparison inconclusive.

For a requested multi-session study, Researcher states the competing explanations and their
different assumptions; Engineer records structured predictions for each test and the conditions
that make a result supportive, weakening, inconclusive, or inapplicable. Planner selects the next
decision-relevant discriminating test and links each possible outcome to the choice it could change.
On a later visit, the assigned specialist reads the current canonical study before interpreting a
raw result log, checks that its conditions still apply, and identifies what it strengthens, weakens,
or leaves unresolved plus the next discriminating step. Do not infer a user selection from that
interpretation. Record it only when authorized, in the canonical study; use links instead of copies
of its changing assessment or recommendation. See the [study workflow](study-workflow.md) for
commands and the [shared output contract](shared-outputs.md#managed-studies) for record links.

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
the structure. Designer links relevant causal findings from the affected options in existing map details, carries the shared node and references into the HTML, draws the
same-view reference lines required by the shared output contract, and checks each endpoint
and navigation target. In both views, verify that hovering highlights the full upstream
path, the expanded downstream subtree, and the applicable shared nodes and lines.
Check that collapsed descendants stay hidden and that the hover clears with a detail
panel open.

For decision-bearing findings, consult the [integrated research contract](adaptive-system.md).
Pass the question ID at every step, including resume. After a source or case revision, compare
the new data with the original applicability conditions, reopen dependent claims and decisions,
and check their actual use in the answer. An independently frozen evidence obligation can
remain open even when all dispatched tasks have returned.

## Assignment and return

When handing work to a specialist, pass the canonical paths resolved from the project’s
configured research directory and the [shared output contract](shared-outputs.md).

For a Researcher assignment, specify whether the user needs a full exploration or a
bounded evidence check. Name the question to return. When a full investigation delegates
a narrow lookup, the Coordinator retains the remaining breadth and frontier obligations.

Give the role an outcome and question, constraints, affected stable IDs, relevant sources and
input revision, output path or format, acceptance criteria, and authorized actions. The return
identifies the input revision, resulting artifact or evidence, checks performed, and unresolved
conditions. Reuse prior work while its inputs and scope still apply.

Planner owns the canonical plan and serializes its writes. Researcher supplies source-backed
findings or counterevidence, Engineer specifies and runs authorized checks, and Designer writes
assigned derived views. Coordinator integrates these results and updates the handoff. Auditor
reviews claims and artifacts independently, reporting blocking findings, affected IDs, and evidence.

For blind scope reconstruction, give a fresh Auditor only the original goal, constraints and
permitted initial evidence. Identify what its actual tools and inherited context can see. Wait
for its frozen scope before releasing the identified candidate revision and claims for comparison.
Follow research-audit for the required triggers and independence verdict. For a narrower review
of an already exposed claim, identify that limited assignment. Require the actual reviewer's return identifying the material claims
and locators inspected, verdict, and remaining gaps. In the handoff link that return to the
reviewer or host task ID and the reviewed revision. A role assignment, a local check, or an
unattributed status in a note cannot establish an independent PASS. If the host failed to run
the review, record NOT_RUN. If the return or its applicability cannot be verified, state what
is missing and withhold acceptance. Recheck any later material correction.

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
