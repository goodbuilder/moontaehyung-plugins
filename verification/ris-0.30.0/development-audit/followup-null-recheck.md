# Independent follow-up: malformed record corrections

The original `independent-audit.md`, `strategy-negative-results.json` and `findings-results.json` remain historical evidence. Both reported malformed-record errors are now independently rechecked as corrected within the tested scope.

- Findings: `python3 .../development-audit/audit_findings_after_null_fix.py` reran the complete independent frozen-question, missing-record, owner revision receipt, missing fact/limitation, disposition, final output, unchanged/stale draft, direct-edit and malformed canonical-null controls. All assertions passed. Canonical null now returns managed error exit 2 without a traceback, preserving exact malformed bytes. See `findings-results-after-null-fix.json`.
- Strategy: the same synthetic same-project plan with a strategy JSON `null` now returns exit 2 and `Malformed originating strategy record fields`, without traceback or file modification. See `strategy-negative-results-after-null-fix.json`, including the exact public CLI command and result.

These controls verify managed failure and preservation of malformed local data. They do not establish authenticated reviewer independence, scientific completeness or wider schema-fuzz coverage. No producer code was changed by the auditor; no sealed data, actual research, credentials or external calls were used.

# M5 implementation verification (self-verification)

`python3 -m pytest skills/ris/tests/test_learning.py -q`: 18 passed in 1.14s after project integration and adaptive lesson additions. New public CLI project control uses a disposable synthetic manual-policy project, binds to the canonical CONTEXT preimage SHA256, checks permission and stale CAS rejection, preserves prior content in existing history, stores attributed intent/hypotheses/observations/constraints/decision, rejects agent claims of user decisions, and changes the canonical current question only with exact user acceptance plus the dedicated goal approval flag. No profile environment is provided or profile file created.

Public lesson command executed: `python3 skills/ris/scripts/ris.py learning lesson --mode assist --requested --concept uncertainty --dimension-view '{"schema":1,"consent":"general-concepts-only-v1","concepts":{}}'`. Result was teaching=true, weakest dimension=definition, synthetic interval arithmetic [8,12] from 10±2, explicit limits, practice [17,23] from 20±3, ability NOT_ASSESSED, profile_access=false, profile_updated=false. Tests also verify delegated and absent lesson request suppress teaching, supplied dimension progress changes focus, and extra project-history fields are rejected. These are scaffolds rather than measured learning outcomes.

Combined current integration command: `python3 -m pytest skills/ris/tests/test_learning.py skills/ris/tests/test_findings.py skills/ris/tests/test_strategy.py -q`: **35 passed in 17.73s**. Follow-up inspected implementation identities are captured in `followup-code-hashes.json`.
