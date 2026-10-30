# Definition of Done (DoD) — P0 proposal

## General rule

Never replace evidence with a self-reported completion. Each gate has requirement IDs, scenario ID, observed artifacts, version/environment, and PASS/FAIL/BLOCKED/NOT_RUN. A critical failure or unrun mandatory test prevents PASS.

## Primary outcome KPIs

1. Evidence reliability: audited factual claims whose cited passages actually support the stated claim under its recorded conditions / all audited factual claims. Also report critical fabrication and serious context-omission counts separately.
2. Research coverage: benchmark reference subtopics found / independently curated in-scope reference subtopics. Report precision of generated subtopics and limits of the reference set.
3. End-to-end successful runs: runs completing required stages with verified durable outputs and no unresolved mandatory failure / all eligible benchmark runs. Report mode and environment.

## Diagnostic and safeguard metrics

- Topic precision = true valid generated concepts / examined generated concepts.
- Relation accuracy = valid typed edges / audited typed edges.
- Evidence traceability = claims with retrievable source locator / audited factual claims.
- Metadata accuracy = verified correct bibliographic identities / audited paper records.
- Duplicate rate = confirmed duplicate concepts or source records / all new candidate records.
- Review burden = human-approval requests and active review minutes per completed run; never optimize this at expense of missing mandatory approval.
- Mean time and cost per verified claim and per completed topic, not just total papers.
- Recovery: correct re-run, journal replay, stale results, partial sync and corruption checks.
- Market mode: correctness of observed-vs-proxy-vs-estimated demand labeling.

## Proposed thresholds (NOT measured or user-approved)

These are initial trial targets; ratify after a fixed gold corpus and baseline. They are not evidence of achieved quality.

| Metric | Initial suggested threshold |
|---|---|
| Topic precision | >= 0.90 |
| Core benchmark subtopic recall | >= 0.85 |
| Typed relation accuracy | >= 0.90 |
| Audited key-claim source traceability | >= 0.95 |
| Audited metadata identity accuracy | >= 0.98 |
| Verified graph relations | >= 0.99 |
| Critical fabricated citations, unauthorized destructive writes, disclosed secrets, unrecovered data losses | 0 observed in mandatory test set |
| Mandatory approval-situation detection | all labeled cases in test set |

No universal guarantee is inferred from zero observed incidents. Test power, sample size, and uncertainty need reporting. Quantified performance/cost targets for runtime are intentionally deferred pending baselines.

## Phase gate contracts

- P0: all requirements have acceptance methods and a test-plan ID; authorized policies fixed; open assumptions highlighted. A draft plan alone is not a completed gold dataset.
- P1: schema tests, multiple parents, idempotent re-run, partial-write recovery, scoped non-destructive projection and readback PASS.
- P2: topic hierarchy and grouping accuracy scored against independent labels; nested and multi-parent cases PASS.
- P3: actual metadata identity and source records; search reproducibility; duplicates and missing full text labeled correctly.
- P4: claim-support sampling, contradiction and source-locator audits; no unsupported verified claims in mandatory adversarial test set.
- P5: priority/defer/resume, budget enforcement, approval-policy negative tests, human intervention statistics.
- P6: demand signals with date, geography, provenance and uncertainty; market-off regressions PASS.
- P7: packaging/discovery plus cross-service live validation, failure injection, benchmark suite, privacy review and recovery PASS.

## System acceptance

RIS v1.0 requires F01–F14 traceability, passing applicable mandatory phase gates, actual measured benchmark results against ratified thresholds, and no unresolved critical issue. Document local live integration boundaries honestly. Report improvements against a matched manual baseline when available; do not claim productivity gains without comparative data.
