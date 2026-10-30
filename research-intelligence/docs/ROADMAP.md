# RIS Roadmap and Stage Gates

Status: initial architecture proposal. A phase is not complete merely because its documentation or code exists. Observe and record acceptance evidence.

| Phase | Goal | Entry conditions | Exit evidence |
|---|---|---|---|
| P0 Evaluation foundation | Freeze minimum scope, owner permissions, traceable tests and benchmarks | Approved user policy | Requirement-to-test matrix; evaluator rubric; benchmark plan; decisions and open gaps recorded |
| P1 Knowledge foundation | First local end-to-end vertical slice | P0 contract agreed | Stable graph IDs; SQLite transactions; mock evidence; scoped Markdown output; idempotence, rollback and restart tests |
| P2 Topic intelligence | Recursive grouping and typed graph | P1 stable IDs/state | Golden-topic scoring (precision/recall); relationship and semantic-duplicate adversarial tests |
| P3 Literature discovery | Source retrieval, screening and Zotero integration | P1/P2 contracts | Search provenance, verified metadata, duplicate handling, source outage/retry tests |
| P4 Evidence intelligence | Claim-level support, contradiction and gap candidates | P3 metadata integrity | Expert/held-out evidence audit; full-text vs abstract boundaries; unsupported conclusion detection |
| P5 Adaptive exploration | Budgeted autonomous branch selection with approvals | P2/P4 confidence and guardrails | Priority quality; stop/defer/resume; decision queue and approval safety tests |
| P6 Tech + optional market | Technology/problem/use-case/demand links | P4 evidence and P5 policy | Demand-signal class tests; observed-vs-estimated separation; market-disabled mode |
| P7 System validation | Stable end-to-end ris v1.0 and packaging | P1–P6 gates | Multiple-domain test corpus, local live-adapter checks, recovery, privacy audit, plugin discovery test, PR review |

## Milestones

- RIS-MVP: P0–P4 verified; evidence-backed research map (may require manual prioritization).
- RIS-Core: MVP + P5 verified; autonomous bounded exploration with human supervision.
- RIS v1.0: Core + P6/P7 verified; modular market intelligence and tested plugin packaging.

## Sequencing principle

Work on independent stubs in parallel if useful, but do not activate P5 autonomous conclusions until P4 evidence safeguards pass. Each phase has entry/exit gates, explicit PASS/FAIL/BLOCKED/NOT_RUN results, and a record of checked version/environment. Critical failures block claims of completion, not independent investigation.

## First authorized slice

Build only P0 documentation now. P1 code, changes to marketplace.json, local library writes and installing the plugin require subsequent scope-appropriate execution, existing approved managed-area policy, and actual test evidence. Do not change the existing plugin for convenience.

## Known open work after P0

1. Construct 12-topic benchmark candidates and have a human/external reference independently label a gold subset. No benchmark recall claim before that.
2. Derive measurable baseline latency, cost, duplicate rate and stage-level error logs; tune provisional targets.
3. Decide the supported runtime and exact Zotero/Obsidian local adapter behavior from verified versions during P1/P3, not assumptions.
4. Define schema migration, sync idempotence and unauthorized-write negative tests before live integration.
5. Add the RIS plugin marketplace entry only once root manifest and basic skill discovery pass tests.
