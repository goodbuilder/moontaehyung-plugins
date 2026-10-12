# Work evidence for outcome and cost review

This is the shared record contract, not a new journal or approval process. verify-check
records observed work; cli-usage-review compares records when requested. The packaged
reference is the authoring source; personal copies are synchronized distribution copies.

## One task, potentially several executions

Use an existing task/change ID, or a short local ID if none exists. A task may span turns,
sessions, retries, and agents. Record external run/thread/turn IDs only when actually known;
never invent a runtime ID or assign a whole thread to one task without a known boundary.
Keep all relevant attempts, including failed and interrupted ones. Resume the same task
record; append corrections or later regressions with links rather than counting a resumed
or revised summary as a new success. Distinct later repair work can link to the original task.

## Minimal task summary

Reuse the existing verification ledger or task notes. Small changes may use a compact
final/task note; do not create files just for analytics. Read-only tasks keep their write
restrictions. Before substantial work, retain the requested outcome and known comparison
conditions in the existing record. At completion, failure, interruption, or a durable handoff,
append a brief summary of the facts then available:

| Field | Record |
|---|---|
| Task and scope | ID, requested outcome/criteria links, kind and scope; distinguish original scope from later additions. |
| Conditions | Source identity, environment, actually used skills and versions/content hashes, model/settings when observed. Unknown is allowed; current settings do not prove past settings. |
| Outcome | Task disposition and criterion statuses, evidence links, unresolved boundaries, later regressions. Runtime turn completion is not product PASS. |
| Process | Evidence-backed rework and repeated work; useful defect detection is not automatically waste. |
| User involvement | Corrections to wrong results, new scope, required clarification, and authorization requests separately; do not treat every user message or required approval as avoidable friction. |
| Measurements | Sources, execution boundaries, time/token fields actually available, missing data, and agent coverage. |

Do not repeat slice details or large logs. A record may be Markdown; these field names do
not require a separate JSON file or fixed template. A later review may join final usage to
this record in its analysis; it does not silently overwrite historical evidence or write
new files without authorization.

## Measurement semantics

- Separate availability (available, partial, pending, unavailable) from coverage (which
  executions, agents, and interval are included). Pending is appropriate only when a known
  source is expected to provide a later event. Missing values are null/unknown, never zero.
- A final reply cannot reliably include usage that is emitted after that turn completes.
  Record the source and available values; let a later review read completed execution data.
  Do not delay task completion for unavailable analytics or launch another agent to measure it.
- Keep input, output, cache, and reasoning breakdowns with their source definitions. Do not
  add a breakdown again to a total that already includes it. Distinguish per-turn values
  from cumulative snapshots; cumulative intervals need an explicit baseline and boundaries.
- Deduplicate by reliable identities and semantics. Unknown parent/child overlap, conflicting
  records, missing attempts, or uncertain task boundaries must remain visible. Observed
  provided-record totals are not automatically complete task totals.
- Report elapsed wall-clock span separately from summed execution durations. Parallel work
  overlaps; gaps may include user/device/approval waits. Infer neither active work time nor
  waiting categories without evidence. Missing timestamps mean unmeasured duration.
- Tokens and money are separate. Do not price ChatGPT-plan usage as API billing. Monetary
  estimates require an explicit request, known billing mode, applicable rates and date,
  and sufficient usage details; distinguish an estimate from actual billed cost.

## Interpretation

A record is evidence, not proof that a workflow caused an improvement. Keep conditions,
missingness, failures, and contrary outcomes visible. Lower time or token counts alone do
not establish improvement if verification or quality deteriorated. cli-usage-review owns
the comparison procedure. Keep the evaluation's own work separate from measured development
attempts unless explicitly included and labelled.

## Data boundary

Inspect the narrow task/period and explicit record sources requested. Prefer task summaries
and sanitized usage exports. Do not search unrelated histories, read credential stores or
environment secrets, replay commands, or expose private command arguments, raw outputs,
conversation contents, or reasoning text. The usage helper accepts explicitly named exports
and emits allowlisted metadata only; it is not a collector, watcher, or session-log crawler.
No data source is promised to exist in an interactive session. Missing data is a finding.

## Official basis and local choices

- [Skill evals](https://developers.openai.com/blog/eval-skills): outcomes, process, efficiency,
  and captured traces/artifacts provide evaluation evidence.
- [Non-interactive Codex](https://learn.chatgpt.com/docs/non-interactive-mode): exec JSONL
  includes usage in turn.completed; it is distinct from private rollout files.
- [App Server](https://learn.chatgpt.com/docs/app-server): thread/tokenUsage/updated exists,
  but availability to this workflow and aggregation coverage must be established separately.
- [Authentication](https://learn.chatgpt.com/docs/auth): ChatGPT-plan and API-key usage have
  different billing paths.
- [Eval practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices):
  task-specific checks, representative/edge cases, and human feedback improve evaluation.

The two-skill division, record fields, review labels, and conservative aggregation rules are
local design choices. They do not require the Evals API, a custom harness, or continuous review.
