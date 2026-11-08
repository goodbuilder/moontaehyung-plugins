# Initial behavioral checks

These are synthetic checks, not evidence about a deployed system or a benchmark proving general effectiveness. No skill installation or production changes were part of these checks.

## Independent RCA/FTA boundary trial

Identical supplied evidence: primary video network link down at 10:00; receiver exit 1 at 10:00:02; no backup logs, failover configuration, stderr, or reproduction data. Question: why did video fail and what should change?

Two fresh-context workers independently read the existing installed RCA skill and the new FTA skill respectively. Neither received the coordinator's expected conclusion or the other's result. Both were read-only and prohibited from delegation and external actions.

Acceptance questions: Is temporal order distinguished from causation? Is unknown backup behavior kept unknown? Are proposed fixes tied to evidence? Does FTA label structural assumptions and avoid invented independence/probabilities? Does either output offer unique useful next steps?

Observed: RCA withheld causal attribution and proposed stderr/configuration/log collection followed by a controlled failover test. FTA also withheld incident attribution, explicitly conditioned a model T = R OR (P AND B), and derived conditional cut sets {R} and {P,B}, identifying a possible common receiver failure point. Neither assumed network independence or fabricated probabilities.

Synthesis: for this incident question, RCA leads; FTA contributes a provisional structural model only if that question matters. This is a one-case routing result, not a universal rule that both methods are always required. No comparative performance, latency, or token advantage was measured.

## Additional contextual smoke checks

A separate context-aware worker checked three cases locally; these checks were not independent blind comparisons. The video case selected RCA with provisional FTA; an explicit post-deployment sustain/change review selected AAR directly; a two-product cost/performance request without measurements or preferences selected MCDA but deferred ranking rather than spawning more agents.

## Review corrections

Read-only review identified and prompted corrections: one owner for AAR table fields; narrow AAR-to-RCA handoff to important unresolved causal questions; handle MCDA feasibility/missing inputs before ranking and permit deferred output; explicitly mark provisional FTA structure/cut sets; require fresh worker contexts for independent comparisons.

Remaining validation limits: no real project cases, workbook generation/recalculation, diagram rendering, large-tree solver checks, or installed-runtime discovery tests have been performed. Existing installed RCA/project-plan/ADR/verification files remain unchanged; the router's handoff contract coordinates their overlap only when loaded.
