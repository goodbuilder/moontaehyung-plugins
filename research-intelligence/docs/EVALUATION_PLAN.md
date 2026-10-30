# Evaluation Protocol — P0 draft

## Purpose

Separate research quality from throughput and from packaging success. Test the actual workflows, not merely generated file counts. All numerical thresholds are provisional until calibrated on an independent benchmark corpus.

## Reference set design

Build at least 12 representative topic tasks (suggested initial set, not yet labeled gold):
- Established domains (3): classical stereo triangulation, Kalman filtering for navigation, battery state-of-charge estimation.
- Emerging/narrow domains (3): lightweight onboard visual landing-site selection, cross-modal drone fault diagnosis, uncertainty-aware small-data aerial object localization.
- Cross-domain topics (3): RTK-assisted visual reconstruction, robotics safety assurance with machine learning, multi-sensor condition monitoring.
- Ambiguity/adversarial topics (3): SfM vs multi-view reconstruction grouping; stereo-vs-sensor-fusion false alternatives; publication counts vs proven customer demand.

Include hard constraints and exploration budgets in fixtures. A qualified human reviewer and/or independently sourced review papers/textbooks must create reference subtopic/edge labels before comparing RIS outputs. Keep benchmark labels outside the prompt seen by the tested generator; prevent label leakage.

## Sampling and evaluation

1. Freeze task inputs, execution mode, model/tool versions, retrieval time and limits.
2. Capture run/branch/query/source IDs, generated graph, excluded candidates, claims, approval requests, database and export artifacts.
3. Score topic validity, topic recall, edge accuracy, paper metadata, claim support and reference locators using a documented rubric.
4. Double-review a sample of ambiguous labels; record disagreement instead of manufacturing consensus.
5. Score independent attempts, regressions and a matched human-only workflow where possible; report confidence intervals or caveats.
6. Compare quality and time together, with gate violations as separate hard fails rather than a composite score alone.

## Unit and integration test candidates

- E-001: Topic -> child -> grandchild + multiple-parent relationship preserved across save/reload.
- E-002: SIFT aliases and SfM synonyms reused; broader 'multi-view reconstruction' not incorrectly collapsed.
- E-003: Invalid relation type or dangling foreign key rejected.
- E-004: Zotero duplicate source ID/DOI not duplicated after retries.
- E-005: Abstract-only evidence cannot be marked full-text-verified.
- E-006: Nonexistent DOI, mismatched author/year, and fabricated locator rejected/flagged.
- E-007: Two contradictory empirical claims remain separate, conditions and source passages visible.
- E-008: Zotero offline or Obsidian write failure leaves consistent task/sync journal, retries idempotently.
- E-009: User-owned non-RIS Markdown or Zotero records remain untouched.
- E-010: Approval denied/absent for deletion, paid service, external publication or scope change causes no side effect.
- E-011: Restart after cancellation resumes pending tasks without duplicated external writes.
- E-012: Re-running same topic reuses prior evidence and identifies newly changed claims.
- E-013: Market data labels observed contract separately from proxy, hiring, patent count and speculative forecast.
- E-014: Source text containing 'ignore previous instructions' cannot alter authorization rules.
- E-015: Plugin registration and discovery work in verified host environment, separate from mock run.

## Test status and evidence template

Test ID / requirement ID / input+conditions / expected outcome / actual observation / PASS|FAIL|BLOCKED|NOT_RUN / source&artifact location / environment+commit / limitations / follow-up.

## Workflow examples

Normal: given a topic and scoped policy, retrieve or synthesize candidate child concepts, check valid evidence, persist canonical graph and Zotero pointer, project to RIS/ Obsidian folder, read back, then re-run without duplicates.

Failure: a valid DOI is indexed but PDF/full text is not available; metadata may be marked checked, while the claim remains abstract-only or blocked. A failed Obsidian projection must not lose authoritative state or mark the export completed. A user-requested deletion outside RIS scope must not proceed without approval.
