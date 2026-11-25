# Independent development audit

Auditor: development subagent /root/human. This agent implemented the learning module and optional teach-me additions, so those portions are self-verification rather than an independent code audit. Simulation, isolation, findings, strategy/recovery and shared integration were read and tested independently of their implementers. No producer files were changed during this audit. Baseline is main, 007ee7ff2d727e813ba59584abc80e7b1c002e74, with uncommitted collaborative changes. Inspected file hashes are recorded separately; owners were actively changing files, so this is a scoped observation rather than a frozen release approval.

## Findings

1. **Confirmed, corrected and independently rechecked:** simulation output exhaustion originally returned FAILED even though the operating-system file size budget caused EFBIG. Original simulation-results.json preserves that result. After the owner fix, the same independent CLI controls in simulation-results-after-output-fix.json classify it BUDGET_EXHAUSTED. Model errors remain FAILED. No remaining defect identified in that tested distinction.
2. **Confirmed malformed-record boundary defect:** a same-project strategy section containing syntactically valid JSON null caused strategy-search to raise uncaught AttributeError at item.get, producing stderr traceback rather than a managed invalid-record response. See strategy-negative-results.json. Owner was notified; this report does not yet claim a corrected verification.
3. **Confirmed malformed-ledger boundary defect:** replacing the canonical findings JSON block with null causes inspect to raise uncaught AttributeError in parse(value.get). The malformed bytes remain unchanged. See final control in findings-results.json. Managed recovery/error response remains incomplete; no authority escalation was demonstrated.
4. **Minor diagnostic gap:** isolation model-workspace preflight does not enumerate directory symlinks when os.walk(followlinks=False) skips them. This does not enable model execution: eligibility is always false and accurately states clean model-host context is unverified. Namespace execution itself rejected the synthetic sibling symlink escape.

## Executed controls and results

Simulation: actual public CLI spawned a numerical Python process in a namespace (returned y=6, namespace pid=2, Python 3.10.12). Frozen case/model input hashes matched before and after execution. Input rewrite attempt failed read-only. Synthetic sibling file, host home and host environment sentinel were unavailable. Wall/CPU budget controls returned BUDGET_EXHAUSTED; after the fix output exhaustion did too. Model exception, invalid/nonfinite/empty output failed. Invalid case, outside-project input and outside-project symlink were rejected before execution. Result explicitly requires a separate validation check. This establishes executed bounded synthetic computation, not scientific correctness, real research quality or a clean LLM host.

Boundary controls: original selected bytes succeeded; deterministic between-selection input revision change was rejected; oversized model rejected; missing bubblewrap failed closed. Input receipts are SHA256 snapshots, not user-provided CAS preconditions. Simulation is read-only with respect to project state and does not commit a result, so ledger-write CAS is not applicable there. Findings mutation uses expected revision plus project lock and atomic exact-byte preimage checks.

Findings public CLI: froze a timing question before any finding; missing record blocked delivery. Missing manual recording authority, stale ledger revision, wrong owner label, stale accepted-finding revision, owner transcript missing the fact, owner transcript missing a limitation, self-review resolution and absent disposition were all rejected. Correct owner transcript and integration succeeded. Missing final fact and missing final limitation blocked delivery; complete exact passages succeeded. Unchanged draft receipt was current; altered draft receipt was stale. Direct narrative edit blocked writes; exact-byte review saved full preimage, set nodes UNVERIFIED, invalidated obligations and removed delivery. Malformed canonical null produced the defect above without overwriting bytes.

The reviewer and owner fields provide declarative role consistency and self-review label rejection. They do not authenticate separate human/process identities or independently verify scientific evidence. The final delivery receipt explicitly says exact transport with no semantic/scientific validation; this audit agrees with that limited scope.

Existing tests executed:

- python3 -m pytest skills/ris/tests/test_learning.py skills/ris/tests/test_isolation.py -q: 18 passed in 0.82s. Learning coverage is self-verification; isolation coverage is independently reviewed.
- python3 -m pytest skills/ris/tests/test_knowledge.py skills/ris/tests/test_strategy.py skills/ris/tests/test_recovery.py skills/ris/tests/test_delivery.py -q: 71 passed in 9.70s.
- python3 -m pytest skills/ris/tests/test_findings.py -q: 5 passed in 8.00s (owner was evolving finding receipts; independent workflow was then adapted to the current required revision and transcript contract).

## Reproduction artifacts

- audit_simulation.py and simulation-results.json: initial CLI controls and raw commands/stdout/stderr.
- audit_simulation_after_fix.py and simulation-results-after-output-fix.json: same controls after output-classification fix, preserving original evidence.
- audit_simulation_boundaries.py and simulation-boundaries.json: deterministic source-revision/size/no-namespace controls.
- audit_findings.py and findings-results.json: independent full canonical workflow and all CLI command results.
- strategy-negative-results.json: malformed strategy reproducer result and traceback.
- inspected-code-hashes.json: scoped code identities observed at report creation.

## Scope and gate judgment

CONFIRMED: the listed synthetic normal/failure/omission/stale/namespace flows executed. Scoped transport and bounded local simulation checks pass except the two malformed-record response defects still requiring correction/recheck. ASSUMED: trusted host protects runtime code and provisions global-profile access outside worker namespaces. UNKNOWN: authenticated independent reviewer identity, scientific completeness, causal benefit of stored strategies and clean model-host isolation. NOT_RUN: real provider/LLM execution, real research experiments, cost-bearing tools, scientific-domain expert evaluation and user UX validation. No FR/NFR or G0-G8 global PASS/READY judgment is made from these lower-layer results. No sealed evidence, credentials, real profiles or existing project data were accessed; no external calls, installs, commits or push occurred. Synthetic temporary projects were created only for verification and automatically removed.
