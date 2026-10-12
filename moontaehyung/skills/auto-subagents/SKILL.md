---
name: auto-subagents
description: Coordinate subagents for substantial exploration, diagnosis, review, or verification when independent work or context isolation justifies the overhead. Keep short tasks and simple commands local.
---

# Auto Subagents

Own delegation only. The calling workflow keeps requirements, authorization, domain
decisions, records, and final acceptance. Reuse its current plan and evidence.

## Choose the execution method

Handle short checks and known commands locally; use parallel tool calls when enough.
Use native subagent tools automatically for bounded investigations whose parallelism,
separate context, or independent review is worth the added tokens and coordination.
Do not manufacture tasks to fill agent slots. User limits and prohibitions take priority.
If delegation is unavailable or disallowed, continue locally without seeking extra
delegation permission or installing another execution system.

## Dispatch bounded work

- Keep one coordinator for the current workflow. Reuse active assignments and relevant
  completed evidence across skill handoffs; do not spawn the same investigation again.
- Assign concrete questions from the task, not fixed personas. Provide the question,
  relevant paths and facts, applicable contracts, allowed actions, and expected evidence.
  Identify work already covered or assigned elsewhere so workers can avoid duplicate checks.
  Distinguish observations from hypotheses and request contrary evidence when relevant.
  Use a compact brief and the minimum sufficient history; do not omit governing constraints.
- Use the fewest useful subagents, usually one or two, within configured limits. Preserve
  configured model, reasoning, and speed choices; do not change them just to delegate.
  Instruct each subagent to finish its assignment without further delegation.
- Prefer read-only investigations and isolated checks. Any edits need an authorized,
  non-overlapping scope. Shared reads are fine; keep inspected inputs stable and serialize
  competing writes or access to devices, ports, and mutable test state.
- Continue different useful work while subagents run. Wait when their results become a
  prerequisite; do not duplicate their investigation while waiting.

## Collect and return evidence

Request a concise answer, supporting and contrary evidence, and unresolved questions.
Link source locations, commands, and artifacts instead of copying raw logs. Include the
source version and environment when results depend on them. Use the calling workflow's
record format when present; do not create a second plan, report packet, or verification ledger.

Check the returned evidence, not just the subagent's completion message. Resolve conflicts
from evidence rather than majority vote. Narrow an incomplete follow-up or finish locally;
avoid repeated spawning or retries without new information. Recheck only what is missing,
contradictory, or invalidated by changes.

Resolve required assignments before dependent work or final completion. Keep unresolved
or unexecuted criteria visible. Propagate cancellation to this workflow's active assignments;
leave unrelated agents alone. Choose assignments without asking the user to define roles
or approve each spawn, while preserving existing scope and tool permissions. The parent
owns synthesis, integration, and the original task's final acceptance.
