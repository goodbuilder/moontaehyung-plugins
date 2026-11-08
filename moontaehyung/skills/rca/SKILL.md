---
name: rca
description: "Investigate actual important failures, recurring defects, and unexplained outcome gaps using causal hypotheses, supporting and contrary evidence, and corrective-action checks. Use AAR for overall retrospectives and FTA for modeled failure combinations; obvious local errors need no formal RCA."
---

# Root Cause Analysis

Explain an actual failure using evidence rather than merely a plausible story. Own the incident timeline, causal hypotheses, contrary evidence, confidence, and corrective recommendations. An overall sustain/change retrospective belongs to [AAR](../aar/SKILL.md).

## Establish the failure question

Reuse the baseline and acceptance evidence from the request, AAR, or verify-check; capture only missing context:

- intended outcome and observable acceptance criteria;
- constraints, dependencies, and deadline or scope limits that affect success;
- assumptions that could change the result.

Use the user's wording where possible. Do not turn inferred preferences into requirements. Ask a focused question only when an ambiguity blocks a sound definition of success; otherwise state a reasonable assumption and continue. Keep the baseline in the conversation or task notes; do not create a separate file unless requested.

## Investigate

State the specific expected-versus-observed gap and account for user-directed scope changes. Do not start a general completion review or analyze a successful task for hypothetical failure. Already confirmed causes and obvious local fixes do not require a fresh investigation.

When a meaningful miss needs substantial independent evidence investigations, use
[auto-subagents](../auto-subagents/SKILL.md) to choose and coordinate delegation.
Seek evidence that could disprove each hypothesis as well as support it. Keep causal
synthesis, confidence, and corrective recommendations here; delegation does not authorize
fixes. If the companion skill is unavailable, investigate locally.

For meaningful misses, analyze causes in this order:

1. State the gap between expected and observed results.
2. Reconstruct only the relevant events and decisions from available evidence.
3. Separate the direct failure mechanism from contributing conditions and deeper process causes. Distinguish facts from hypotheses and state confidence.
4. Identify the earliest evidence-supported point where a different check, clarification, decision, or action could have prevented or reduced the miss. If it cannot be established, mark it unresolved.
5. Recommend a small, concrete corrective action tied to the cause, plus a verification that would show it worked.

Prefer explanations that can be supported by logs, diffs, outputs, user corrections, or other task evidence. Do not assign blame, claim causation from timing alone, or fill evidence gaps with a plausible story. If evidence is insufficient, say what remains unknown and what minimal evidence would resolve it.

## Report

Keep the investigation proportional. Include the failure definition, relevant timeline, hypotheses and their supporting/refuting evidence, causal conclusions and confidence, unresolved questions, and corrective actions with effectiveness checks. Distinguish containment from recurrence prevention and proposed from implemented or verified actions. Do not change project files, workflows, or settings solely because the analysis recommends it.

## Method boundaries

When a defined failure requires AND/OR combination analysis, use [FTA](../fta/SKILL.md) as a bounded supporting method; modeled paths are not proof of the incident cause. For consequential ambiguity between workflows, return the question to the active coordinator using [analysis-router](../analysis-router/SKILL.md). Workers must not recursively route or delegate. Reuse an existing comparison instead of starting it again. Return authorized repair checks to verify-check; pass lessons to AAR without duplicating its report.

## Bundled workflow coordination

Read the [skill routing contract](../../references/skill-routing.md) when combining these workflows.
Reuse the active requirements, authorization scope, and evidence record; do not repeat interviews
or create a second approval gate or ledger.
