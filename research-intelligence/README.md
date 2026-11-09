# Research Intelligence System (RIS)

Status: **P0 design draft; no RIS runtime/plugin installed yet.**

RIS is a research, technology, and optional market intelligence system. A user supplies a topic, objectives, constraints, and an automation policy. RIS recursively discovers subtopics, verifies literature and claim-level evidence, builds an inspectable topic graph, autonomously allocates a bounded exploration budget, and maintains knowledge across runs.

## Project placement

- This directory will become an **independently installable plugin** in the existing goodbuilder/moontaehyung-plugins marketplace.
- Do not change the existing moontaehyung plugin or marketplace entry during P0.
- Existing Zotero, auto-subagents, verify-check, rca, and design-boundaries skills are integration/reuse candidates, not mandatory internal dependencies.
- RIS Core owns persistent state and deterministic validation. Skills guide workflows; agents perform reasoning; adapters interact with external systems.

## Approved user policies (2026-10-30)

1. Open-source code in the public repository; keep personal research data, PDFs, vault contents, database files, and credentials out of Git.
2. Reuse the existing Zotero library and Obsidian vault, but isolate RIS-owned records in a managed Zotero collection and Obsidian folder. Actual identifiers/paths are local setup inputs.
3. Permit bounded automatic writes **only inside RIS-managed areas**. Require approval for deletion, modifications outside the managed scope, public release, paid actions, and material goal/constraint changes.
4. Prefer free/public research APIs. Paid API or service use requires explicit approval.

## P0 artifacts

- docs/REQUIREMENTS.md — functional/nonfunctional requirements and authorization.
- docs/ARCHITECTURE.md — proposed domain, state, and adapter boundaries.
- docs/ROADMAP.md — P0–P7 staged delivery and dependencies.
- docs/DEFINITION_OF_DONE.md — success gates and proposed numeric targets.
- docs/EVALUATION_PLAN.md — benchmark protocol, failure tests, and measurement.
- docs/ADR/ADR-0001-hosting-and-boundaries.md — approved placement and preliminary architecture decision.
- AGENTS.md — scoped Codex execution guidance.

## Next implementation slice

Create a P1 local-first vertical slice on a separate, reviewable change: topic -> subtopic/claim -> mock evidence -> SQLite state -> managed Obsidian Markdown projection -> repeat/recovery tests. Add live Zotero only after adapter read/write safety is tested. Do not treat these documents as evidence of working integration.

## Non-goals for v1.0

An exhaustive universal ontology; guaranteed discovery of every paper; a fully automatic systematic review; independent claims that inferred market demand is measured demand; a web UI; unrestricted background monitoring or automatic deployment.
