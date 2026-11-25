# Revising hypotheses and tests

Keep the existing study ID when new evidence changes the explanations under consideration.
First record the observation as it was measured. Then use `study amend ID --expected-revision N
--body-file <file>` to propose the new explanation, its origin and a test whose outcomes could
distinguish it. Preserve the initial prediction and previous assessments.

For example, suppose `obs-trace` showed that a correction was missing from the search results
in a study with hypotheses `not-returned` and `not-opened`. The trace motivates two more precise
explanations. A separate held-out correction can distinguish them:

```json
{
  "id": "separate-retrieval-causes",
  "rationale": "The first trace locates the loss at retrieval. It leaves the cause open.",
  "triggering_observation_ids": ["obs-trace"],
  "added_hypotheses": [
    {"id":"terms","parent_id":"not-returned","statement":"Query terms hid an indexed correction.","prediction":"A notice-specific query retrieves it."},
    {"id":"index","parent_id":"not-returned","statement":"The correction was absent from the index.","prediction":"Even an exact notice identifier fails in this index."}
  ],
  "next_test": {
    "description":"Test a separately selected correction in the same index.",
    "method":"Run the topic query and a notice-specific query. Inspect hit IDs and actual opens.",
    "limits":["Conclusions apply to this index revision and the tested notices."],
    "predictions":{
      "terms":"The notice-specific query finds the correction missed by the topic query.",
      "index":"Both queries miss the correction, including its exact identifier.",
      "not-opened":"The topic query already surfaces the correction, but the reader skips it."
    }
  },
  "next_action":"Obtain the held-out trace under the documented conditions."
}
```

For an additional hypothesis, omit `parent_id`. A split links at least two children to an active
parent and retires that parent from new assessments. The old ID and its evidence remain in history.
Repeat the same amendment ID and payload for an exact retry. Reload before retrying a conflicting
edit. To update only the prospective test or an explicit result rule, use an empty
`added_hypotheses` list. Cite earlier observations, or, for an independently supplied reason,
use `basis: {"kind":"independent","locator":"..."}`. Record the source of a changed rule.

Give one predicted outcome per active hypothesis and explain which observations would separate
the alternatives. Identical prediction strings are flagged. Check semantic equivalence as well:
two different wordings may predict the same outcome. If a test distinguishes only a subset,
state which explanations it leaves open and what could separate them later.

For the follow-up, inspect the new measurement and call `study observe` against the current
revision. Cite the new locator and attach the files actually measured where available.
An observation that suggested a hypothesis can motivate the next test. Count confirmation or
contradiction only when the new evidence supports that interpretation. The helper can recognize
some reused evidence; scientific independence also depends on the sampling and study design.
Use `study show ID --revision N` to check what was known before the new hypothesis was introduced.
