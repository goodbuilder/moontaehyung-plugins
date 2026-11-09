# ADR-0001: Host RIS as a separate plugin in the existing marketplace

Date: 2026-10-30
Status: Accepted for repository placement and user policy; implementation details are Proposed.

## Context

The repository currently distributes the moontaehyung plugin, including nine workflows and a Zotero helper. RIS requires a persistent graph, recursive exploration, source verification, resumable state and optional market data. Putting all of it inside one SKILL.md or modifying the existing plugin would create substantial coupling.

## Decision

- Use goodbuilder/moontaehyung-plugins as the shared repository.
- Place RIS under research-intelligence/ as a **separate plugin**, not a sub-skill of moontaehyung.
- Preserve existing plugin and marketplace during P0; introduce the RIS manifest and marketplace entry after package validation.
- Propose a Python RIS Core with durable SQLite state and thin AI/CLI/adapters, subject to P1 validation.
- Review existing zotero, verify-check, rca, auto-subagents and design-boundaries rules for reuse, but avoid a hard dependency on the other installed plugin.
- Code public; private library/database/vault/PDFs/credentials never committed.
- Reuse existing user Zotero library and Obsidian vault only inside newly configured RIS-managed areas.
- Allow autonomous new records and updates only in managed RIS scope; any deletion, outside-scope mutation, paid operation, external publication, or objective change needs approval.
- Free-first research sources; paid services not used without approval.

## Considered alternatives

A. Single monolithic RIS skill within existing plugin: low start-up overhead, weak persistence/test boundary.
B. RIS separate plugin in same repo: shared governance, independently testable, chosen.
C. Completely separate repository: strongest release separation, extra coordination; reconsider if distinct release lifecycle warrants it.

## Risks, constraints, validation

- Repository-level co-location must not become implicit runtime dependency.
- Shared Zotero helper may not cover RIS write semantics; validate before adopting.
- Market inputs can be proxies: provenance, geography, observation time and demand type are mandatory.
- P0 documents alone are not proof of runtime functionality or evaluation quality.
- Revisit this ADR if dependency leakage, packaging conflict, or independent release cadence becomes a measured problem.
