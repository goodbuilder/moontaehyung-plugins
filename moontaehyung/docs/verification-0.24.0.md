# RIS 0.24.0 quantitative evidence verification

The distributed 0.23.0 package matched the source at intake. Its 140 RIS regression tests passed.

## Acceptance cases

| Question | Independent expectation |
| --- | --- |
| Did the variant run perform three searches? | Both prior variant logs have four search events, three of which returned an empty list. A reported total of three conflicts with the source. The empty-result share is 75%. |
| Did the result cross the decision threshold? | The original baseline had two empty searches out of four, or 50%. At a maximum of 70%, the baseline qualifies and the variant does not. Appending one nonempty search to the variant gives three out of five, or 60%, which qualifies. |
| Do exact bytes establish the reported number? | An unchanged file can contain a misreported count. An added unrelated record can change its SHA-256 while leaving the metric value unchanged. The report shows both checks. |
| Is the result unknowable? | A missing filter field in an in-scope row, malformed input or zero denominator for a ratio is indeterminate. No source, study history or user decision is rewritten by verification. |
| Can another session use the rule? | Select the original study revision, observation and metric ID; apply that stored definition to another input. Compare the same definition and unit, preserve the reported claim and recorded revision. |
| Can the researcher stop copying counts? | Refresh a summary with new and explicitly reused reads in separate questions and historical unassigned activity. Each question's tally is derived from the log and reuse does not inflate project openings. Human summary edits retain optimistic concurrency protection. |

The calculator checks explicit numeric claims in registered definitions. Qualitative conclusions,
unregistered prose and the scientific fit of a metric require interpretation.

The final RIS suite passed all 180 tests. An independent CLI exercise with a makerspace dataset
checked a reported count of 3 against an observed 4 where both meet a minimum of 3. It also checked
a 75% to 50% threshold crossing and a zero-denominator result. An exact retry retained one
observation and a conflicting retry preserved the original study. A separate fresh session recorded
the original search-report discrepancy and linked the affected hypothesis without confirming any
user selection. Version 0.23.0 could establish that the input bytes matched for the same erroneous
report; it had no calculation replay.

The study and finding from a project created by 0.23.0 reopened in the new helper, and reusing the
pre-existing qualitative finding returned the original saved bytes. The source CLI help and Claude
plugin manifest validation passed. Run `python3 -m pytest -q skills/ris/tests` from the plugin root.

## Separate breadth-policy trial

Two fresh workers received identical catalogues and case budgets. The only instruction change was
replacing the minimum of three additional alternatives with a counter-search for materially different
options. The rubric was written before the comparison. A separate reviewer graded anonymous answers
against the records actually opened.

| Task | Previous rule, searches / opens | Counter-search rule, searches / opens | Result |
| --- | --- | --- | --- |
| Two approved carriers | 2 / 6 | 2 / 5 | Both found the two eligible carriers and selected the faster one. The candidate omitted a historical transport lookup excluded by the approval record. |
| Open-ended cultural-centre admission | 5 / 7 | 5 / 7 | Both found all four materially different routes and the evidence requiring a low mount for the counter. |

The candidate met the prespecified acceptance rule in this small controlled comparison. The fixed
candidate count was removed. Coverage of consequential alternatives and counterevidence remains
part of Explore. One run per arm and case does not estimate field-wide time savings or recall.
