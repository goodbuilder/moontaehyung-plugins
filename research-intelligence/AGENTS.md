# RIS-scoped instructions for Codex

Scope: research-intelligence/ only. Do not edit the existing moontaehyung plugin, shared marketplace, or global instructions without a separate change request.

Read docs/REQUIREMENTS.md, docs/ARCHITECTURE.md, docs/ROADMAP.md, docs/DEFINITION_OF_DONE.md, and docs/EVALUATION_PLAN.md before substantial implementation. Preserve user-approved policies in README.md.

## Implementation practices

- Prefer Python with uv, ruff, typed interfaces, and pytest when implementation begins; check current tooling/docs before locking versions.
- Choose the smallest working vertical slice. Reject speculative frameworks, premature MCP abstractions, and duplication of the bundled Zotero helper. Record major choices in ADRs.
- Keep AI proposals separate from deterministic validation and persistence. All persisted graph nodes/edges require stable identifiers, provenance, review status, and schema validation.
- No claim is VERIFIED merely because an LLM asserted it, a Zotero record exists, or an abstract mentions it. Keep bibliographic identity, abstract relevance, and full-text claim support separate.
- Do not silently merge concepts on semantic similarity; uncertain merges require review. Distinguish IS_A, PART_OF, RELATED_TO, ALTERNATIVE_TO, DEPENDS_ON, and SUPPORTS / CONTRADICTS claims.
- Never fabricate citations, DOI, paper metadata, experiment results, market sizes, or literature completeness.
- Preserve user constraints. The agent may rank and defer investigations but may not change research goals, make paid purchases, or publish personal data without approval.
- Never delete or modify pre-existing research content outside RIS-owned areas. Write operations inside the configured RIS scope must be logged, reversible when practical, and idempotent.
- Do not persist tokens/secrets, user's Zotero PDFs, Obsidian vault, or personal SQLite databases in Git.
- Prefer independent read-only subagent investigation; assign non-overlapping write scopes. A coordinating owner validates/commits changes. Do not spawn unnecessary agents.
- For each phase, define input, process, output, invariants, failure cases, evaluation evidence, and explicit PASS/FAIL/BLOCKED/NOT_RUN.
- Separate mock/unit passes from local application integration passes. Neither can be substituted for the other.
- Before phase advancement, inspect actual test artifacts, address blocker/critical failures, and report unresolved risks. Treat numerical targets as proposed until baseline calibration and review.
- Follow repo's existing relevant verify-check, rca, architecture, and Zotero guidance as references where available, without creating a runtime dependency on the other plugin.
