# RIS Architecture — proposed P0 design

## Purpose and boundary

Create a local-first, independently installable research-intelligence plugin while preserving the existing moontaehyung plugin. Host instructions do not own the research database.

## Logical layers

1. Client: Codex CLI and one RIS entry skill; later optional UI.
2. Workflow: topic exploration, literature research, evidence audit, optional market analysis and bounded multi-agent coordination.
3. Core: typed graph, claim/evidence registry, decision policy, task scheduler, evaluation logic, schema and permission validator.
4. Persistence: SQLite transaction owner (proposed), durable run log and migration tool.
5. Adapters: Zotero local/API; Obsidian scoped Markdown; academic metadata sources; later optional MCP. External connections may be absent without invalidating core tests.

Dependency direction: entry/agents -> core contracts -> adapters; core imports no Codex/Zotero/Obsidian APIs. Deterministic validation must precede authoritative writes.

## Data ownership

- Zotero: authoritative external bibliographic library and PDF attachments; RIS persists item keys/verified metadata snapshots/provenance, not PDFs.
- RIS store: canonical IDs, graph relations, claim evidence links, task state, decisions, approvals, sync journal, provenance and version.
- Obsidian: human-readable projection of RIS state in a configured RIS/ folder; avoid manually editing user-owned notes outside this area.
- Git repository: source code, schemas, synthesized test fixtures and reviewable decisions; never live vault or personal DB content.

## Candidate relational entities

Topic(id, canonical_name, aliases, scope, review_state);
Relation(id, source_topic_id, target_topic_id, relation_type, status, provenance);
Paper(id, doi_or_other_id, zotero_item_key, metadata_check_level, source);
Claim(id, text, context, state, topic_id);
Evidence(id, claim_id, paper_id_or_source_id, locator, verification_level, support_or_contradiction, checked_at);
Task(id, run_id, topic_id, status, priority, budget, reason);
Decision(id, topic_id, alternatives, criteria, rationale, approval_state, revisitation_trigger);
Run(id, started_at, ended_at, config_snapshot, stage_result);
SyncJournal(id, target_system, operation_id, target_id, status, retry_state).

Additional objects for market mode: Problem, UseCase, CustomerSegment, DemandSignal, MarketEvidence with observation date, geography, type, confidence and source. No market size without method and underlying data.

## Identity / graph rules

- Topic names are not IDs; aliases may map to one concept, but uncertain equivalence remains separate pending adjudication.
- IS_A (taxonomy), PART_OF (compositional), DEPENDS_ON (prerequisite), ALTERNATIVE_TO (decision context), RELATED_TO (noncommittal) are different semantics.
- A topic may have multiple parent relationships and cross-links. Preserve rejected edges and their reasoning for audit.
- Never equate citation order with influence or publication volume with demand.
- Claims are atomic, time- and context-scoped and linked to evidence passages. Verification level must be explicit (library record / metadata checked / abstract checked / relevant full text checked / independently reproduced).

## Workflow and failures

Input -> run/config snapshot -> planner -> bounded candidate topics -> independent research workers -> claim/evidence review -> deterministic graph validation -> SQLite transaction -> sync journal -> Zotero managed collection / Obsidian managed folder -> final readback + evaluation report.

For external writes, persist intent and operation ID before attempting side effects; use idempotent reconciliation to avoid duplicates on restart. A database transaction cannot atomically commit across Zotero and Obsidian; report partial-sync state and retry safely. Do not mark cross-system sync complete solely from a local success response.

On cancellation, preserve last valid state and active task statuses. If a service is down, independent discovery may continue while affected export tasks remain BLOCKED. Require authorization before deleting/overwriting existing user content.

## Integration strategy

P1: mock adapters, local SQLite, Markdown projection in a synthetic test vault. P3/P4: inspect existing Zotero skill's interface and integrity rules for reuse. Live integration only after sandbox-mode adapter tests and explicit configuration. Obsidian official CLI or file adapter should be selected based on tested environment, not assumed.

## Architecture risks / revisit triggers

1. Shared-plugin code reuse causing runtime coupling -> use stable adapter contracts; extract common library only for verified reuse needs.
2. Ontology drift / semantic duplicate explosion -> concept registry and manual review for ambiguous merges.
3. Poor source authenticity -> layered evidence verification and independent evaluation set.
4. Human approval bottlenecks -> batch decision queue; continue unrelated tasks.
5. Cross-system sync failure -> journal, retries, readback, reconciliation.
6. Premature framework complexity -> implement vertical slice and justify any new infrastructure with a failing test or measured need.

All design choices are proposals until P1 engineering validation; record consequential changes in ADRs.
