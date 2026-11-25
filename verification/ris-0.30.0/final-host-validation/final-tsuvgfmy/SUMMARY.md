# Final frozen source: offline native-host checks

Archive: `a5bf0f1249e5b5b4e9dd77544acbe87e4417b7a8531a59fc91f13d4086cd5b82`.
Supplied manifest: `485648ec3d3d9f526c0eb522a5f32b32a208b05a3fb6029e538a9532a4a13e93`.
All **417** product files match the manifest exactly. Only `skills/ris/scripts/ris_views.py` differs from the preceding candidate. Extracted files remained unchanged after metadata and registration probes. Prior evidence is preserved.

Codex 0.172.0: offline initialize, skills/list and config/read succeed. RIS is an enabled repo-scope skill (pluginId=null); all five explicit role config paths are exposed. This proves project-skill discovery and role configuration acceptance, not marketplace enrollment or role execution.

Claude Code 2.1.331: native plugin validation PASS. Actual process-level initialize-control response registers **all five namespaced product agents and 25 namespaced product slash commands**, including `moontaehyung:ris`. No user input/turn was sent. `agents --json` returns empty background-session list, which is not role inventory.

The earlier `plugin details` Agents(0) observation is resolved: matched 0.29 baseline and candidate both register five roles through process initialization; a known-good default-location control reports Agents(1) in catalog details, while a known-good explicit-file-path control reports Agents(0), yet both register the role in initialization. This reproduces a catalog inventory omission for explicit agent paths rather than a product packaging failure. No source fix or candidate variant is necessary. Existing declared role model strings are returned as metadata; model availability and execution remain untested.

Authoritative compatibility basis: [official plugin manifest reference](https://code.claude.com/docs/en/plugins/manifest-reference.md) accepts agent Markdown-file paths/arrays, and [official Agent SDK reference](https://code.claude.com/docs/en/agent-sdk/typescript#sdkcontrolinitializeresponse) documents agents and slash commands in the initialization response and allows reading initialization before the first turn. No schema workaround was applied.

Both host environments have disposable HOME/work directories, read-only exact product mounts, cleared environment and no network namespace access, real-user HOME, credentials or user configuration. **Model requests/user turns/provider calls: 0**. Only temporary host state was writable. Current four-development-session ceiling, ten-million cache-inclusive-token target, 94% pre-stop and included-only preconditions are unchanged; no session allowance was consumed. Full authenticated model-host isolation, included-only charge blocking, role execution, E2E/REAL/user validation and holdout remain NOT_RUN.

Evidence: `host-results.json`, `claude-initialize-registration.json`, `final-receipt.json`; exact scripts `verify_hosts.used.py` and `claude_initialize_only.used.py`. Matched controls: `../claude-registration-2xuxaxl7/registration-results.json` and `catalog-control-comparison.json`. The prior candidate's unresolved-discovery summary is superseded by these native process-level registration results.
