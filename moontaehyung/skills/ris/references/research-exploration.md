# Research exploration and completion

Scale this guidance to the requested result. Explicit RIS requests always start with initial
exploration. For a narrow question, check the relevant evidence and any conditions that could
change the answer, then answer directly if no material user input is needed.

## Initial exploration and first question round

Start from the user's request, corrections and relevant project context. Derive the deliverable,
success criteria and constraints; keep them in the conversation or an already authorized plan.

Before asking about material ambiguities, do a targeted first exploration. Inspect enough relevant
sources, existing evidence or calculations to understand the main credible approaches and identify
which unknowns could change the result. Do not stop at a list of possible questions. Also do not
pretend this initial survey is a complete assessment when important assumptions remain.

Ask a concise, preferably batched set of questions informed by what the exploration found. For each
question, include the known evidence, plausible options or the assumption you would otherwise use,
and how the answer could change the work. Use the interactive question tool when available. Ask only
about user-owned intent, priorities, scope or tradeoffs that materially affect the outcome. Resolve
factual questions from available evidence and use a safe default for low-impact reversible details.
Skip the question round when no material user input is needed or when the user asks to proceed
without questions. Complete initial exploration in either case.

## Conditional exploration and later question rounds

Define the decision question before listing its branches. Sibling options must answer the same
question at a comparable level. Identify the prerequisite facts, requirements, candidate mechanisms,
and verification questions. Give each its own place in the plan. Keep independent choices as
separate axes, with a comparison matrix or shared nodes when useful. Make a child branch only
when the parent answer changes its meaning, viable options, or required evidence. If the same
children repeat under several parents, check for an independent axis before expanding the tree.
Put assumptions that could invalidate downstream choices upstream and label them as provisional.

After the user answers, continue from the confirmed outcome and existing evidence. For each remaining
material unknown, identify plausible assumptions or choices and make bounded sub-branches. Investigate
the evidence, dependencies, feasibility and downstream consequences for those branches far enough to
show what differs. A branch may represent a factual uncertainty, an explicit user preference, or a
condition such as a resource limit; label which it is.

Do not ask about a branch as soon as it appears. Continue independent investigation and resolve
questions evidence can answer. Once the consequential branches are sufficiently explored or reach a
real user-decision/evidence boundary, collect the remaining user-owned questions into a later batch.
Use the interactive question tool when available. Give each question its options, conditional
consequences and a recommended default when evidence supports one. Do not ask one question at a time
or make the user enumerate dependencies.

When an answer or new evidence reveals another consequential unknown, continue with the affected
branches and ask about them after their consequences are clear. Honor explicit exclusions. Reopen an
excluded branch only if the user withdraws the exclusion or evidence shows that it invalidates the
result; explain that dependency before investigating.

Keep the branch set proportional to decision impact. Consider plausible alternatives that could
change feasibility or the user's choice; do not enumerate every imaginable combination or recurse
through low-impact details. If the same evidence and assumptions recur without progress, change the
search or decomposition, bound the uncertainty, or report the specific limit.

## Evidence and comparisons

Reuse adequate prior evidence; seek primary sources for unresolved material claims. Browse for current
or fast-changing facts when freshness can affect the conclusion. For substantial literature or trend
work, retain the actual date window, search channels, source identity and locator, retrieval date,
inclusion limits, and whether the abstract, full text, code or results were inspected.

For comparisons, group approaches by the mechanism or problem they address. Compare the criteria
relevant to the outcome, evidence, limitations and open questions. Check contrary evidence and
recent changes when they could reverse a conclusion. Separate publication observations from claims
about a whole field; check preprint and published versions when their differences matter.

Distinguish verified facts, calculations, estimates, scenarios, assumptions, inferences and unknowns.
Search failure or limited access is not evidence that no prior work exists. Counts of sources, options,
branches or tool calls do not establish adequate coverage.

## Completion and recommendation checks

### Continue an existing research map

In an active RIS project with an existing research map, interpret “연구 진행해” as a
request to investigate the active scope until every leaf's immediate parent is a meaningful
research or decision question. Use leaf nodes for its alternatives, evidence, or specific
verification criteria. Continue available investigation before marking a question as needing
an answer or decision. Record the specific missing input, measurement, or authorization at
any real boundary. Preserve existing IDs and prior evidence, and gate downstream work on
the unresolved prerequisite. Update and open the existing HTML map, and verify the immediate
parent of every leaf in the requested scope. This convention does not authorize new
experiments or project initialization.

Before recommending or ending a substantial assignment:

- Compare the answer with the active deliverable, success criteria and constraints.
- Cover the evidence and credible alternatives that could materially change the result.
- For each consequential unknown, state whether it was resolved by evidence, modeled through
  assumptions, assigned to the user, or left at a concrete evidence/resource boundary.
- Continue available investigation that could change the recommendation. Separate it from experiments
  or external actions that are unavailable or unauthorized.
- Check any proposed bundle or route end to end, including dependencies and shared resources. Label
  identified configurations, hypothetical combinations and sensitivity scenarios distinctly.
- Bound unresolved decision-sensitive assumptions and show how they affect the recommendation.
- Report what is established, conditional and unperformed. Give a conditional recommendation when a
  decisive uncertainty remains.
- Stop when the requested scope is satisfied or a specific intent, evidence, permission or resource
  boundary prevents further useful work. Do not continue merely to increase the number of branches.

## Recording and plans

Conversation is the default working record. Persistent recording remains manual unless the selected
project has an authorized milestone policy. Reuse canonical project records; do not create a new file
or plan merely to track a question round.

Use Project Plan for a requested durable plan or when consequential decisions need a graph, gates or
fallbacks. Keep ordinary comparisons and conditional analysis in conversation unless a plan artifact
is part of the requested result. Record confirmed decisions separately from recommendations and
hypothetical branches. Deliver authorized plans with Markdown, HTML, and HANDOFF.md under the
[shared output contract](shared-outputs.md).
