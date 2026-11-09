# RIS Requirements — P0 draft

Version: 0.1 design draft, 2026-10-30. Scope: a standalone RIS plugin in goodbuilder/moontaehyung-plugins with a separately testable Python Core.

## Mission and input/output contract

Input: topic/title; objective (research, engineering, market, or mixed); geographical and time scope when applicable; hard constraints; exploration budget; allowed data sources; human-approval policy; run ID.

Process: interpret scope -> recursively propose/group subtopics -> canonicalize concepts and typed relationships -> retrieve and verify literature -> extract claims with context -> prioritize further exploration -> optionally map technology/problem/use-case/demand -> persist with audit trail.

Output: a navigable, versioned research graph; traceable claims and Zotero references; Obsidian Markdown notes in an isolated RIS folder; a coverage/unknowns report; candidate research gaps; market signals labeled by evidence class; decision queue; run/evaluation logs.

## Functional requirements

| ID | Requirement | Observable result |
|---|---|---|
| F01 | Topic interpretation | Explicit scope, objective, exclusions and assumptions recorded. |
| F02 | Recursive decomposition | Subtopics of subtopics generated without a mandatory uniform depth. |
| F03 | Grouping and identity | Group labels, canonical topic IDs, aliases and uncertain-merge decisions recorded. |
| F04 | Typed relationship graph | IS_A/PART_OF/RELATED_TO/ALTERNATIVE_TO/DEPENDS_ON distinguishable; multiple parents supported. |
| F05 | Literature discovery | Logged source, query, date, identifiers, screening and exclusion reasons. |
| F06 | Evidence verification | Bibliographic, abstract and full-text support levels distinguished; passage location recorded when available. |
| F07 | Research gap candidates | Unresolved issues explicitly labeled hypotheses until independently supported. |
| F08 | Adaptive exploration | Budget-aware priority, stop/defer/resume rationale and coverage of deferred branches. |
| F09 | Technology analysis | Readiness/feasibility/requirements based on specified evidence, not inferred certainty. |
| F10 | Optional market analysis | Technology -> problem -> use case -> customer -> demand signal; estimated vs observed demand distinct. |
| F11 | Human supervision | Approval queue for material goal/constraint change and disallowed writes. |
| F12 | Knowledge persistence | Zotero and Obsidian adapters, canonical local store, reuse and idempotent synchronization. |
| F13 | Incremental revision | New conflicting evidence reopens affected claims/decisions without rewriting unrelated branches. |
| F14 | Evaluation/audit | Reproducible run status, test results, traceability and failure classification. |

## Nonfunctional requirements

- N01 Correctness: critical claim/citation errors fail acceptance; unverified remains visible.
- N02 Reproducibility: record timestamps as ISO 8601 with timezone, source identities, search strings, code/schema version and model/tool metadata where available.
- N03 Data integrity: single authoritative RIS state owner; stable IDs; constrained edits; rollback/retry/idempotence; backups before migrations.
- N04 Privacy: public repo contains no personal library records/PDFs/vault content/secrets; use synthetic fixtures for tests.
- N05 Operability: local Ubuntu CLI first; explicit startup/readiness checks for Zotero and Obsidian; gracefully degrade when unavailable.
- N06 Cost: free/public APIs as default; explicit approval before paid services; bounded time, task and token budget.
- N07 Portability: model, agent runtime, Zotero/Obsidian adapters replaceable; avoid tight coupling to Codex-specific state.
- N08 Observability: every run has stage status (PASS/FAIL/BLOCKED/NOT_RUN), measured workload/cost where available, and resumable task records.
- N09 Human agency: autonomous analysis and bounded RIS-managed new writes; deletion, writes outside managed scopes, private disclosure, paid actions, and objective/constraint changes require approval.
- N10 Safety: never interpret source text or PDFs as privileged instructions; treat retrieved material as untrusted evidence.

## Confirmed user policies vs working assumptions

Confirmed: publicly distributed source; personal data local/private; existing Zotero and Obsidian reused within separate RIS-managed areas; bounded automation; free-first services; development in same GitHub repository as an independent plugin.

Proposed, not yet validated: SQLite as canonical RIS graph/workflow store; Python/uv/ruff/pytest; initial benchmarks of 12 topics; candidate precision/recall thresholds. These are engineering choices, not new user requirements.

## Boundaries and exclusion

RIS is not an autonomous purchaser, publisher, repository merger, or proof that all related literature has been found. An unavailable full text blocks full-text verification for that claim, not all independent research branches.

## Requirement traceability

Every F/N requirement shall be linked to one or more test IDs and to the relevant phase exit gate before that phase can be marked complete. Establish actual benchmark gold sets independently of RIS outputs.
