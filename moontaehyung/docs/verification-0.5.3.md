# Work evidence and usage review — 0.5.3

## Scope and work summary

Task: work-evidence-review-20261011. Requested outcome: verify-check records compact task
outcomes; cli-usage-review reviews comparable work and measured costs from bounded sources.
The personal review skill preserves CLI habits and adds requested workflow review. The
packaged verify-check and shared reference are synchronized; the plugin still has eight
skills and does not add cli-usage-review as a new packaged entry.

Disposition: implemented with the checks below. Existing verify-check instructions and
personal/package differences are preserved. The shared record contract has one packaged
authoring source and two identical personal distribution copies. No Workstation application,
authentication, model configuration, monitoring service, or plugin activation changes.

Sources: official Codex skill-evaluation, non-interactive JSONL, App Server, authentication,
and evaluation-practice documentation cited in work-evidence.md. Runtime example fields
were checked against those documents; local Codex reports version 0.162.1. The normalized
usage-summary-v1 format is a local interchange contract, not a claimed official export.

Process: one implementation agent and two independent forward evaluators were used; none
subdelegated. Root review corrected handling of unknown usage properties in duplicate
identity checks and added a sanitized cross-platform timestamp error case. No user correction
or task-scope change occurred during this modification. Total task time and token usage are
unavailable: no bounded complete runtime export was supplied, including subagent coverage.
They are not inferred from tool timings or reported as zero. No monetary estimate is made.

## Structural checks

PASS: official quick_validate.py accepted 19 personal/package skills; all 101 local Markdown
links resolved. Shared record copies are identical. UI metadata stays consistent with the
expanded review scope, preserving default implicit discovery. The helper uses only Python
standard-library modules. Existing verification criteria and unrelated skills remain intact.

## Numerical and input-boundary tests

PASS: python3 -B -m unittest discover -s personal/cli-usage-review/tests -v, 11 tests.
Independent expected values include cumulative 100/30 -> 150/40 -> 180/50 producing 80/20,
and overlapping ten-second agent intervals producing 15 seconds wall span and 20 seconds
summed intervals. Cache/reasoning details are not added again to input/output totals.

Cases cover actual subprocess CLI invocation, the documented exec example, exact duplicates,
ambiguous exports, conflicting identities, ignored extra properties, missing/null/zero and
invalid counts, unknown/subtree scopes, absent cumulative baselines, resets/unordered counters,
mixed forms, overlapping self intervals, partial/invalid timestamps, failed/unfinished turns,
unknown/private formats, empty inputs, explicit regular paths, and sanitized output/errors.
The script emits numeric allowlisted data and fixed labels, not input IDs, paths, raw messages,
reasoning, commands, or malformed lines. Ambiguous aggregates are withheld, not guessed.

## Independent forward checks

Evaluators received isolated fixture requests and raw evidence without expected conclusions.
They did not inspect real history, credentials, network, hardware, or other projects.

| Request | Observed behavior | Result |
|---|---|---|
| Close a small authorized label correction through verify-check | Updated only the label and the existing verification record; preserved historical failed work; recorded unavailable task time/tokens rather than inventing numbers; no extra journal or monitor. | PASS |
| Compare old/new workflow records and explicit usage exports | Included failed/interrupted work, unrun acceptance and later regression; kept user scope growth separate from correction; rejected a savings conclusion with missing child usage and model/scope differences; separated wall span/gaps from summed durations and declined money without billing evidence. | PASS |
| Review a short CLI habit sample | Stayed in habit mode, suggested proportional input-saving options, did not assume repeated tests were wasteful, execute commands, or demand workflow metrics. | PASS |

Root fixture checks confirm that review inputs were unchanged and only the authorized writer
source and existing ledger changed. No new evaluator-generated files appeared.

## Limits

These targeted examples do not establish the framework's real-world savings or guarantee
all future model behavior. No live backend, GUI, or hardware workflow was exercised.
Usage availability/completeness in the active host is not guaranteed. The helper accepts
explicit public exec exports and declared normalized metadata only; it does not crawl
private rollout logs or implement an App Server adapter. Cross-thread CLI aggregation and
unknown/subtree overlaps are conservatively withheld. Normalized identity/scope assertions
require evidence from the input author. Full files are read into memory, so inputs should
be bounded selected exports. Automatic monitoring and task-wide billing attribution are
outside this change.
