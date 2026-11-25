# RIS 0.26.0 study reporting and hypothesis revisions

The RIS behavior baseline is the locally installed 0.24.0 skill. Its 180 regression tests passed
before this change. The shared plugin source was at `1190579` (0.25.0), which included a separate
Faust addition. The user selected a combined local deployment.

| Workflow | Acceptance condition |
| --- | --- |
| Read the numerical conclusion | The first result summary derives counts, units, thresholds and verdicts from the registered calculation. A reported value remains attributable to its source. |
| Combine mandatory metrics | Show an overall verdict only under an explicit combination rule. Distinguish a criterion flip with an unchanged overall result, an overall flip, and unavailable evidence. Preserve the user's choice. |
| Add a new explanation during a study | Record its motivation and prospective prediction. Reopening the previous revision shows the hypotheses that existed at the time. |
| Split and test hypotheses | Preserve the parent and unaffected history. Subsequent observations evaluate the active hypotheses. A motivating observation on its own does not confirm a prediction made afterward. |
| Resume in a fresh process | A later session can recover the revised hypothesis set, actual evidence, and next discriminating test from the same study. |

## What the checks exercise

- In the earlier correction study, the historical interpretation at revision 3 said three
  searches and 100% empty. A read-only projection recovered the captured four searches and
  75% empty. With an explicitly previewed all-required rule the search-count result changed
  from fail to pass, the empty-share result stayed fail, and the aggregate stayed fail.
  A later measurement in the integrated test changes the aggregate to pass.
- The integration test added two children of an existing hypothesis and one additional
  explanation. It retained the user's earlier selection, rejected a stale edit, accepted
  an identical retry, and reopened the historical evidence and result at its original revision.
  The prospective test could support the new hypothesis only after a separate measurement.
- An independent reviewer reproduced a failure where a fresh, unrelated metric could make
  recycled evidence look new. The fix scopes the comparison to inputs supporting each
  hypothesis. Reusing renamed bytes for a linked metric is rejected even with an unrelated
  fresh metric present. A new input genuinely linked to that hypothesis is accepted.
  Matching locators with no original digest also cannot gain independence merely by being
  fingerprinted for the first time. A program cannot establish scientific independence from
  file identity alone.
- A complete, bounded study workflow was exercised with 22 fresh CLI processes. An initial
  pre-freeze attempt exposed a mismatched reporting-function signature. After integration
  the candidate passed on a new project. A separate test-harness assertion was corrected
  to recognize the actual direction of a threshold change (`fail_to_pass`).

## Version comparison on RIS engineering research

The research question was whether the real released `check` helper can establish a pilot
requirement of three distinct search **families** and two beyond-snippet source reads.
Separate workers used 0.24.0 or the feature candidate on the same staged evidence. Both saw
the same actual software measurements and source material, with no private research histories.
Later packets were withheld until the preceding answers were saved. The follow-up experiment
used predeclared, operator-coded families; both helpers were executed on the same project
inputs. The two helpers correctly returned the same structural counts for the one-family
and three-family conditions. This experiment did not change the meanings of `check`'s counts.

The study distinguishes the quality of the user-facing judgment from continuity of its
evidence. A correct recommendation can be reached manually in either version. A revisioned
amendment additionally makes its introduction point, motivation, active predictions and
subsequent evidence inspectable in the study. A controlled local replay is not a measurement
of human labor savings or general field accuracy.

An independent reviewer scored the anonymized first answers on all three visits. Both arms
met the oracle on visits 1 and 2. Both correctly reported the held-out counts on visit 3.
Neither clearly returned both case-specific decisions required under the supplied codebook.
Each received the same corrective request. Under that codebook, one family plus two reads
fails the pilot rule, while three families plus two reads meets it. Whether the tool's output
alone establishes breadth is a separate question. The release guidance now makes that distinction
explicit. This small comparison demonstrated no first-answer accuracy advantage.

In the observed baseline study the hypothesis IDs stayed fixed, with the subsequent explanation
documented in prose. The candidate retained the original hypotheses in historical views, split
one explanation into named children and recorded a separate held-out observation. All four
revisions of an actual 0.24.0 numerical study also reopened with their original stored fields.
A rule bound at revision 5 did not appear in revisions 1–4. The three-visit engineering replay
used a frozen feature draft; the final source and installed helpers are also checked through
the independent CLI scenario.

## Reproduction

Run `python3 -m pytest -q skills/ris/tests` at the plugin root. The source suite passed all 206
RIS tests; the separately included Faust suite passed 21 tests. The source helper, Claude manifest
and historical snapshot checks passed. File hashes establish package identity, not scientific
validity of a claim or independence of a new experiment.
