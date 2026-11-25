# M5 final correctness and freeze

Frozen owner files are listed with SHA256 in `learning-final-freeze.json`. No further edits by this owner are pending.

`python3 -m pytest skills/ris/tests/test_learning.py -q`: 21 passed in 1.71s. `python3 .../development-audit/audit_learning_final.py`: 14 registered public CLI controls passed; commands/results saved in `learning-S16-S17-final-results.json`.

S16 content now differs by weakest dimension: definition prerequisite, explanation reasoning, calculation arithmetic, application missing-input decision, limitations counterexample. Fully confirmed views skip basics and offer only a requested transfer task. Delegated/no-request modes suppress teaching. No profile read/write is performed by lessons.

S17 selective erase is hash-bound: one dimension or one concept can be removed without affecting other entries. Disposable public CLI controls confirmed preservation of unselected entries and eventual full cleanup. No real profile was accessed.

Contributions now use `ris.companion('ris_delivery')`, require exact project_id, and hold the project lock from policy inspection through the canonical CONTEXT CAS/history commit. A fresh policy/identity check before commit rejects reduced authority. A deterministic negative control simulated significant-to-manual policy reduction and verified unchanged CONTEXT bytes. Goal changes still require explicit user acceptance plus the dedicated approval flag.

These checks verify deterministic content adaptation and record governance. Actual cognitive improvement, retention, independent transfer and authenticated user competence remain unverified. Historical profile confirmation is user attestation, not a measurement performed by the lesson command. No scientific completeness or global release readiness judgment follows.
