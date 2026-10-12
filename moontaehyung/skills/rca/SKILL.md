---
name: rca
description: "Compare a task's intended outcome with its actual result, and analyze evidence-backed causes when important expectations are missed. Use for task-level retrospectives or when asked to track expectations through completion; not for general habit analysis."
---

# Task Outcome RCA

Keep the task's intended outcome visible, then compare it with the observed result. When there is a meaningful gap, explain why it occurred and what specific change would reduce the chance of recurrence.

## At task start

Capture a concise baseline from the request and available context:

- intended outcome and observable acceptance criteria;
- constraints, dependencies, and deadline or scope limits that affect success;
- assumptions that could change the result.

Use the user's wording where possible. Do not turn inferred preferences into requirements. Ask a focused question only when an ambiguity blocks a sound definition of success; otherwise state a reasonable assumption and continue. Keep the baseline in the conversation or task notes; do not create a separate file unless requested.

## At completion or interruption

Compare each important acceptance criterion with evidence from the actual deliverable or execution. Mark it met, partly met, unmet, or not verifiable. Account for scope changes the user made while work was underway. If criteria were met, say so briefly; do not manufacture a failure analysis.

When a meaningful miss needs substantial independent evidence investigations, use
[auto-subagents](../auto-subagents/SKILL.md) to choose and coordinate delegation.
Seek evidence that could disprove each hypothesis as well as support it. Keep causal
synthesis, confidence, and corrective recommendations here; delegation does not authorize
fixes. If the companion skill is unavailable, investigate locally.

For meaningful misses, analyze causes in this order:

1. State the gap between expected and observed results.
2. Reconstruct only the relevant events and decisions from available evidence.
3. Separate the direct failure mechanism from contributing conditions and deeper process causes. Distinguish facts from hypotheses and state confidence.
4. Identify the earliest point where a different check, clarification, decision, or action could have prevented or reduced the miss.
5. Recommend a small, concrete corrective action tied to the cause, plus a verification that would show it worked.

Prefer explanations that can be supported by logs, diffs, outputs, user corrections, or other task evidence. Do not assign blame, claim causation from timing alone, or fill evidence gaps with a plausible story. If evidence is insufficient, say what remains unknown and what minimal evidence would resolve it.

## Report

Keep the review proportional to the task. Include the original success criteria, observed outcome, any material gap, evidence-backed cause(s), confidence, and corrective action. For a small successful task, a short confirmation is enough. Do not change project files, workflows, or settings as part of the review unless the user asks to implement the corrective action.

## Bundled workflow coordination

Read the [skill routing contract](../../references/skill-routing.md) when combining these workflows.
Reuse the active requirements, authorization scope, and evidence record; do not repeat interviews
or create a second approval gate or ledger.
