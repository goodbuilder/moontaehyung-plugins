# 0.8.1 packaging and installation verification — 2026-10-17

## Scope

Clarify the Auto-Skill-manager public discovery branch and adaptive recommendation output.
No CSM search engine, hook, service, MCP server, or runtime dependency changes.

## Behavior contract

- Inspect project coverage before public search; skip it when current skills cover the need.
- Search project-fit requests only for confirmed gaps; honor explicit alternative-search requests with capability IDs, never raw task text.
- Preserve `complete`, `partial`, `review-required`, and `authentication-required` states.
- Explain candidate fit from matched capability/terms; distinguish standalone skills from parent plugins.
- Keep the default concise; expand source, full digest, bundle, risk, and errors for comparison or staging.
- Do not invent a quality score or install public candidates from search.
- Missing CSM CLI/sandbox remains a configuration error; no tools or PATH are installed/changed.
- Direct plan approval and queued scoped-grant requirements are described separately.

## Static checks

The CSM `auto catalog` command parsed both packages with no package or skill errors. Candidate
digests: CSM 0.3.1 `a7658763c1b2fbef70de73df427b6572a6c4855f4faad6ef6d6cd4703ef0e7d5`;
Moontaehyung 0.8.1 `02943ac0a736cbf11748036296374087cd17adc06cfeb76b904eb890910d8f4d`.
Both Auto-Skill-manager files have digest
`40a0495c5c9482a23e0d84d9164710fad53e3b705e325f0eebe39099fa67c832`. The generic
`quick_validate.py` rejected the existing CSM-specific `capabilities` frontmatter field; the CSM
parser accepts it and reports `skill-management`, so the field was retained. Existing package
skills and scripts were not changed except the Auto-Skill-manager instructions and UI metadata.
No test suite was run because engine and transaction code did not change.

## Runtime and publication

The installed Moontaehyung plugin is updated through the Codex plugin CLI and verified by version,
enabled state, and installed skill digest. Only the current feature branch and the seven reviewed
package files are published. Existing untracked marketplace installation metadata is excluded.
