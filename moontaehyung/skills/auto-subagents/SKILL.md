---
name: auto-subagents
description: Assess and coordinate useful parallel work and subagent delegation across tasks, including investigation, implementation, and verification, when independence and expected benefit justify the overhead.
---

# Auto Subagents

Own delegation only. The calling workflow keeps requirements, authorization, domain
decisions, records, and final acceptance. Reuse its current plan and evidence.

## Choose the execution method

At the start of each task and when its scope changes, assess whether independent work can
run concurrently: investigation, non-conflicting implementation, testing, or review. Identify
dependencies, file ownership, shared resources, critical-path impact, and integration overhead.
Use parallel tool calls for independent small checks. When permitted and useful, automatically
delegate bounded independent work with native subagents while the coordinator continues a
different critical-path task. Include implementation and verification, not only investigation.
Handle short or inherently sequential work locally when delegation would add overhead, and
serialize dependent changes or conflicting resource access. Do not manufacture tasks to fill
agent slots. System, developer, user, and tool restrictions take priority; this skill cannot
enable delegation when a higher-priority instruction or the environment prohibits it.
If delegation is unavailable or disallowed, continue locally without seeking extra
delegation permission or installing another execution system.

## Dispatch bounded work

- Keep one top-level Coordinator for the overall RIS run. A Planner, Researcher, Engineer, or Auditor may
  coordinate bounded leaf work inside its assigned scope when the runtime supports it, but the
  Coordinator retains cross-role dependencies and final acceptance. Reuse active assignments and
  relevant completed evidence across skill handoffs; do not spawn the same investigation again.
- Assign concrete questions from the task, not fixed personas. Provide the question,
  relevant paths and facts, applicable contracts, allowed actions, and expected evidence.
  Identify work already covered or assigned elsewhere so workers can avoid duplicate checks.
  Distinguish observations from hypotheses and request contrary evidence when relevant.
  Use a compact brief and the minimum sufficient history; do not omit governing constraints.
- Allocate work to cover the calling workflow's required scope and depth sufficiently. Choose
  headcount from the need for independent investigation/review, task dependencies, parallel benefit
  and integration overhead, within configured limits; do not use a fixed default headcount.
  Preserve configured model, reasoning, and speed choices; do not change them just to delegate.
  Instruct each spawned worker to finish its assignment without further delegation. Custom RIS
  specialists are orchestration roles, not leaf workers; they may request bounded leaf assignments
  through this Skill. Do not assume nested delegation is available in every client or configuration.
  If it is unavailable, return the concrete delegation briefs to the top-level Coordinator.
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

Keep each question linked to its responsible worker or the parent and its returned evidence.
Return unanswered questions, newly identified alternatives and capacity constraints to the calling
workflow; do not silently reduce its scope or declare domain completion from assignment completion.
Reallocate or finish locally when sufficient; the calling workflow owns any scope change.

Check the returned evidence, not just the subagent's completion message. Resolve conflicts
from evidence rather than majority vote. Narrow an incomplete follow-up or finish locally;
avoid repeated spawning or retries without new information. Recheck only what is missing,
contradictory, or invalidated by changes.

Resolve required assignments before dependent work or final completion. Keep unresolved
or unexecuted criteria visible. Propagate cancellation to this workflow's active assignments;
leave unrelated agents alone. Choose assignments without asking the user to define roles
or approve each spawn, while preserving existing scope and tool permissions. The parent
owns synthesis, integration, and the original task's final acceptance.
