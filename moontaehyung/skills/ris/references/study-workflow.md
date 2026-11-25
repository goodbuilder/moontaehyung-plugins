# Multi-session research studies

A study gives an authorized research project one stable place for its competing predictions,
evidence, current recommendation, explicit user selection and next test. The agent translates the
user's request or result log into the records below. The user can give the goal and observations in
ordinary language. Write the goal, assessment and next action in the user's working language
and preserve original source names, units and locators. Start the record when a multi-session study is requested or recording this
output is otherwise authorized. For a conversation-only analysis, give the assessment in the reply.

## Start with a question that can be resolved

Choose a stable study ID. From the goal and current evidence, state the acceptance criteria, the
conditions under which they apply, and plausible competing explanations. For each hypothesis give
a prediction that would distinguish it. Select an available check whose possible outcomes would
change the assessment. Explain a missing capability or an inconclusive outcome where applicable.
Use an existing authorized log or calculation before proposing a new experiment.

If the user explicitly requires all or any of a set of numeric criteria, record that rule at
the first authorized opportunity with the IDs of the **intended** criteria. Give a required
but unmeasured criterion its own ID. A measured proxy, such as the number of query strings,
can have a separate ID from the required count of distinct research approaches.

All commands below are subcommands of `python3 <skill>/scripts/ris.py --project <project-root>`.
Pass JSON through `--body-file <file>` or use `--body-file -` with standard input. For example, a
researcher investigating a coverage failure could start `study start search-gap --body-file -`
with the following proposal:

```json
{
  "goal": "Explain why the final answer missed a published correction.",
  "criteria": ["Distinguish failure to find the correction from failure to follow a search hit."],
  "conditions": {"index": "catalog-v1", "case": "correction"},
  "hypotheses": [
    {"id":"not-returned","statement":"No search surfaced the correction.","prediction":"Its ID is absent from every returned hit list.","basis":{"kind":"assumption","note":"The initial answer omitted the correction."}},
    {"id":"not-opened","statement":"A search surfaced the correction and the researcher skipped it.","prediction":"Its ID occurs in a hit list and in no successful read.","basis":{"kind":"assumption","note":"This could produce the same final answer."}}
  ],
  "test": {"description":"Trace the correction ID through the run.","method":"Compare returned IDs with successfully opened IDs.","limits":["One run in one index."]},
  "evaluations": {
    "not-returned":{"assessment":"untested","rationale":"The hit lists have not been inspected."},
    "not-opened":{"assessment":"untested","rationale":"The read events have not been inspected."}
  },
  "recommendation":"Hold the choice of remedy pending the trace.",
  "rationale":"Either explanation fits the initial answer.",
  "next_action":"Inspect the hit lists and read events."
}
```

The created revision is 1. Link it with `study-link search-gap`. When a plan exists, supply the
managed plan with `--plan <project-relative-plan.md>` or use the active plan. The stable navigation
links go in CONTEXT, the applicable handoff and the plan. They continue to open the current study
as its revision advances. Preserve human-authored notes around these links. If a link operation
reports a partial update, inspect the named conflict and retry the same command.

When generating a research map beside the plan, attach the current note to the decision node
using the Tree renderer's [local document link](../../archify/renderers/tree/README.md).
Run `study-link` for the map's plan and use the returned `map_node_link` as an item in the node's
`links` array. Its label identifies the actual revision and its href is relative to the plan.
A saved map identifies the revision it describes and opens the current study at the same location.

## Resume with a result

Use `study list` to find the study and `context --study search-gap` to recover its current
recommendation, user choice, predictions, conditions and next action. Follow its canonical path
when a section is omitted by the character budget. Use `study show search-gap --revision 1` to
recover the prediction as it stood before measurement. Open the result itself and identify its
version, location, conditions and limits. Distinguish a missing record from a measured absence.

With an authorized result, call `study observe search-gap --expected-revision 1 --body-file -`.
The body contains a stable observation `id`, `finding`, exact `locator`, `evidence_kind`,
`conditions`, `limitations`, a current `evaluations` entry for each hypothesis, and the updated
`recommendation`, `rationale` and `next_action`. Use `supported`, `contradicted`, `inconclusive` or
`untested` for each assessment, with a reason. The evidence kinds are `source`, `publication`,
`derived`, `assumption` and `unresolved`. Identify an inference as such even when its input is measured.
When another test could distinguish the remaining explanations, supply its `next_test` with
`description`, `method`, `limits` and `predictions` keyed by hypothesis ID. Explain what this
observation settles and what remains open in the reply. An exact retry uses the same observation ID.
If a different observation has advanced the study, read the new revision before submitting the
updated assessment.

When a specific project-local file is the observed input, attach it with
`--evidence-file inputs/run.jsonl` on `study observe`. Repeat the option for multiple explicitly
selected files. The observation records the path and SHA-256 while the original bytes stay
where the project owns them. Preserve the passage, row or run ID in `locator`. A citation
alone leaves the original file unchecked.

For claims calculated from CSV or JSONL, supply `--metrics-file` on the same observation.
The [metric workflow](metric-workflow.md) describes how to record a definition, compare inputs,
reproduce a reported value, and inspect a threshold change. For qualitative findings, keep using
the observation and its evidence locator.

For a purely numerical observation with at least one metric, you may omit `finding`. Use
`study results ID --format markdown` directly for the quantitative part of the user's reply.
The canonical note puts the generated criterion table before the agent's interpretation.
The original reported value stays attributed to its source. Add the implications and limits
in the user's working language. A saved `result_rule`, supplied at study start or amendment,
defines how the specified numerical criteria combine. A separate mandatory qualitative condition
can still leave the research choice open.

Record a choice only when the user actually makes it. For example, `study decide search-gap
--expected-revision 2 --body-file -` accepts a JSON object with `id`, `selection`, `rationale`
and the `locator` of the explicit confirmation. A later recommendation can differ from that
selection. Preserve the user's choice and identify the new evidence that warrants reconsideration.

See [revising hypotheses and tests](study-amendment.md) when an observation suggests a new
explanation, an existing hypothesis needs splitting, or a more discriminating test becomes available.

## Carry one finding into another study

Select a concrete source observation and revision and compare its recorded conditions with the
target study's conditions. This works for failed trials as well as favorable results.

```text
knowledge assess search-gap --revision 2 --observation obs-trace --target followup
knowledge reuse search-gap --revision 2 --observation obs-trace --target followup --target-revision 1 --verify-evidence
context --study followup
```

`assess` is read-only. With authorization to save the reuse, `reuse` writes a finding in the
target project. Inspect the source and target conditions, differences, missing values,
scope limits and evidence type before using it in a decision. An exact recorded scope match
still needs scientific interpretation. Where a condition differs, identify the specific repeat
measurement needed. A negative finding carries the limits of the original failure.
Use `--verify-evidence` to compare the explicitly attached source files with the bytes pinned at
observation time. Report file verification separately from a match between recorded conditions.
Both can succeed while the finding still needs scientific review for this particular use.

By default both studies belong to the selected project. For a specifically requested transfer,
run in the target project and pass `--source-project <exact-source-project>`, the source study,
pinned revision and observation. A fresh session in the target can see the saved provenance
and review status through `context --study`. Reassess before relying on it after a target revision
change. Keep project permissions and the recording policy in force.
