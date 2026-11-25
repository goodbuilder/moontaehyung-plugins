# Reproducing a recorded number

Use a metric when a count, ratio or threshold from a CSV or JSONL file could change a research
decision. Identify the input revision, population of rows, unit and decision threshold. If the
report states a number, copy that number into `reported` before checking it. Omit `reported`
when no number was given. Keep the author's original claim and its locator. Qualitative findings
continue to use the standard [study observation](study-workflow.md).

## Define once

This definition counts an empty-result search in the numerator and every search in the
denominator. An empty list is an observed value. A missing field leaves a different question open.
Save the JSON below as `empty-search.json` for this example.

```json
{
  "id": "empty-search-share",
  "format": "jsonl",
  "operation": "ratio",
  "where": {"operation": "search"},
  "numerator_where": {"result_ids": []},
  "unit": "percent",
  "threshold": {"op": "le", "value": "70"}
}
```

For a count use `"operation":"count"`, `"unit":"rows"` and the population filter `where`. For a
ratio choose `fraction` or `percent`. Equality filters name top-level fields. Use strings for CSV
cells, including identifiers with leading zeroes. Thresholds support `lt`, `le`, `eq`, `ge`, and
`gt` and use the metric's unit. The counted rows define the result; establish whether the input
uses comparable sampling, event definitions and units before interpreting two runs.
Threshold comparisons use exact arithmetic. For a repeating ratio, the result also supplies the
exact fraction and identifies the rounded display value. Register a reported decimal or exact
fraction in the declared unit. Keep an explicitly approximate statement in the finding with its
precision when no exact claim was made.

All examples are subcommands of `python3 <skill>/scripts/ris.py --project <root>`. Data inputs
are paths inside the explicitly selected project. Definition and packet filenames are read from
the invoking working directory unless absolute. Each data input is bounded to 64 MiB. Use the
same definition to compare runs; the difference is the second value minus the first:

```text
metric run --definition empty-search.json --input logs/baseline.jsonl --compare-input logs/variant.jsonl
```

If two of four searches are empty in the baseline and three of four in the variant, the results
are 50% and 75%. Only the baseline meets the chosen maximum of 70%. These are example data
and a test threshold. Select the actual threshold from the study criteria.

## Record the observation

On `study observe`, add `--metrics-file metrics.json` alongside the ordinary observation body.
The file is a JSON array. Each entry contains its `input` and either a definition object or
a project-relative `definition_file`. For example, use
`{"definition_file":"empty-search.json","input":"logs/variant.jsonl","reported":"75"}`
to capture the same rule used in the two-run comparison. The normalized rule is stored in the
observation so a later edit to the separate rule file does not change the historical calculation.
Add `reported` to compare the result with a stated number, and `hypotheses` to name the existing
hypothesis IDs the number bears on. For example, a report stating three searches can be checked
with this entry:

```json
[
  {
    "definition": {"id":"all-searches","format":"jsonl","operation":"count","where":{"operation":"search"},"unit":"rows","threshold":{"op":"ge","value":"4"}},
    "input": "logs/variant.jsonl",
    "reported": "3",
    "hypotheses": ["coverage"]
  }
]
```

With four actual searches, the result disagrees with the reported three and crosses the example
threshold. Review the linked hypothesis and the recommendation at that observation's revision.
An observation with an incorrect reported number is useful evidence and can be retained alongside
the calculation. Record a revised interpretation with a new observation when warranted. An
explicit user choice follows its own decision history.

## Rerun or reuse

In a fresh session, select the registered definition by study, revision, observation and metric ID.
For example, to apply the same selection rule to a later run:

```text
metric run --study search-gap --revision 2 --observation trace-1 --metric all-searches --input logs/later.jsonl
knowledge assess search-gap --revision 2 --observation trace-1 --target followup --verify-evidence
context --study search-gap
```

The first command compares the new calculation with the pinned observation. The second checks
the original source bytes and reproduces the registered calculations for the selected knowledge
item. Read file identity, numeric agreement, threshold impact and scientific review separately.
A changed file can still yield the same count. A zero denominator or an unavailable required
field leaves the ratio indeterminate. `context --study` shows outstanding checks on the latest
observations for each recorded definition. It uses saved results when resuming.

Version 0.24 reads qualitative studies written by 0.23. Resume studies that contain the new
metric records using 0.24 or later.

## Present the decision

`study results STUDY --format markdown` produces the user-facing criterion table and summary
from the stored measurement revision. Use that output when answering instead of retyping
numerical findings. It identifies the reported value, the computed value, the threshold in the
metric's unit and the resulting criterion verdict. Cite the original report when explaining
a discrepancy. A historical observation may contain an earlier interpretation.

Set `result_rule` only when the study or user explicitly defines a combination of mandatory
metrics. For example, `{"mode":"all","metric_ids":["all-searches","empty-search-share"]}`
requires both to pass. An `any` rule requires one to pass. Include all the required metric IDs,
including a required metric with no measurement yet. State any separate qualitative requirements.
Check that every metric measures the intended criterion: distinct query strings, for example,
are a different quantity from distinct research approaches.

With no saved rule the output shows separate criterion verdicts. A read-only preview such as
`study results search-gap --all all-searches empty-search-share` applies the specified scenario
to that view. It does not record a user choice or change the study rule. Use `--revision N` for
an as-of view. Compare the reported and reconstructed overall result separately from changes
between successive observations. A known failure settles an all-required rule even when
another criterion is unknown. Conversely an all-required rule with only passes and unknowns
remains unresolved.

When two experimental conditions are being compared, record their separate observations
and scopes in the same study. Apply the same user-specified rule to each using
`study results ID --revision N`. Report both case verdicts before assessing the overall
method. A family count assigned under a supplied codebook, for example, can settle a pilot
criterion under that codebook while independent coding remains useful for external validation.
