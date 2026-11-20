# Verification — Autonomous RIS coordination

## Scope and completion criteria

This change applies the proposed Coordinator/Planner/Researcher/Auditor architecture to the writable
plugin source under `upstream/moontaehyung`. The personal RIS project at `/home/moontaehyung/바탕화면/RIS`
and the packaged `releases/0.17.0` snapshot were read for comparison and left unchanged.

Completion criteria:

- Role ownership is explicit, and the main thread remains Coordinator.
- Custom agent templates and project Coordinator instructions are available with a documented installation path.
- Research continuity remains project-local and the current completion checks are present.
- Planner retains one canonical decision graph and forecast history.
- Auditor has an independent audit contract with targeted, owner-routed corrections.
- Optional `.ris/state.json` stores statuses and references only and is supported by a guarded helper interface.
- Package docs describe installation separately from runtime discovery and do not claim live activation.

## Baseline and preserved work

- Source checkout: `upstream`, branch `feat/risk-adaptive-blueprint-adr`, `HEAD 2834176` (`feat: publish moontaehyung plugin v0.14.0`).
- The checkout already contained uncommitted v0.15–0.17 package changes before this task. Those files were preserved and extended only where relevant.
- The actual RIS Skill supplied by the user resides outside the writable roots. Its missing completion-check section in the packaged reference was restored in the in-workspace source copy.

## Change slices

| ID | Observable goal | Result | Evidence and limitation |
| --- | --- | --- | --- |
| R1 — role contracts | Three narrow agent TOMLs and a compact Coordinator `AGENTS.md` template exist | TOML syntax `PASS`; runtime discovery `NOT_RUN` | Three TOML files parsed with the installed `toml` module. Discovery still requires a fresh Codex session. |
| R2 — Skill ownership | RIS, Project Plan, Auto Subagents, routing, and forecast protocol assign work without duplicating canonical artifacts | Skill format `PASS`; behavioral evaluation `NOT_RUN` | `quick_validate.py` passed for RIS. Source review of changed Skill and routing files; reviewer Skill and its TOML were left unchanged. |
| R3 — independent audit | RIS audit Skill defines coverage, evidence, feasibility, forecast checks and finding format | Skill format `PASS`; seeded defect recall `NOT_RUN` | `quick_validate.py` passed for `research-audit`; no audit corpus is present. |
| R4 — durable run state | Optional state uses project identity, statuses and local artifact references; helper provides guarded init/read/update/check/context support | Syntax/JSON parse and anchored-plan resume `PASS`; remaining state lifecycle checks `NOT_RUN` | A CLI regression covers state initialization, `check`, context resume, preservation of the anchored reference, and deduplication of the loaded plan. Wider state-update behavior remains unverified. |
| R5 — package setup | Package description, version, and installation guidance describe templates and separate registration | Diff whitespace check `PASS`; package installation `NOT_RUN` | `git diff --check` passed. Plugin manifest is set to `0.18.0`; no release package was built or installed. |
| R6 — review corrections | Resume anchored plans and read UTF-8 plan/HTML files under an ASCII locale | `PASS` | Three regression tests failed before the fix and passed afterward; all 44 helper/graph tests passed. See the review follow-up below. |

## External contract evidence

OpenAI documents custom agent TOMLs in project `.codex/agents/` or personal `~/.codex/agents/`,
requires `name`, `description`, and `developer_instructions`, and states that subagents inherit the
parent's permissions. Plugin documentation describes Skills and optional assets as package contents;
agent registration remains a separate Codex configuration step. See [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
and [Package your plugin](https://developers.openai.com/plugins/build/plugins).

The reviewed Subagents page does not specify a guaranteed nested-specialist delegation contract.
This is a documentation limit, not evidence that nested delegation is impossible. Templates keep the
leaf-worker rule and include Coordinator-mediated fallback; live behavior remains unverified.

## Architecture refresh status

```yaml
architecture_refresh:
  status: NOT_REQUESTED
  risk: MEDIUM
  affected_nodes: [COORDINATOR, PLANNER, RESEARCHER, AUDITOR, RIS_STATE]
  reason: "Role ownership and optional orchestration state changed; the user supplied a design but did not request refreshing an existing Archify reader."
  suggested_command: "Use $archify to create or refresh an RIS architecture reader when requested."
```

## Static checks and not-run work

- `quick_validate.py` reported `Skill is valid!` for `skills/ris` and `skills/research-audit`.
- Python AST parsing passed for `skills/ris/scripts/ris.py`; the three agent TOMLs parsed with the installed `toml` module; the state-schema JSON and plugin manifest parsed; `git diff --check` passed.
- These are format/syntax checks, not behavioral coverage.

- Current helper/graph regression suite: `PASS` — 44 passed after the review corrections below.
- Plugin packaging/installation were not run.
- Agent discovery, specialist-to-leaf delegation, independent audit behavior, and full RIS workflow were not exercised in a fresh Codex session.
- No audit-seeded corpus, historical-project backtest set, or model/cost benchmark exists in this change.
- The ADR remains `proposed`; it has not been accepted by the decision owner.

The P2 runtime and empirical evaluation work remains the next evidence-producing phase. Do not infer
research quality, forecast calibration, or live agent availability from the source files alone.

## Review corrections — 2026-11-10

The initial implementation recorded helper tests as `NOT_RUN`. The supplied reviewer subsequently
reported 41 passing helper/graph tests and two reproduced defects. This follow-up reproduced the
reported failures and one adjacent UTF-8 read failure before changing production code:

| Case | Before correction | Correction and observed result |
| --- | --- | --- |
| `active_plan_ref` ends in `#D-001` | `check` passes, but the `context` CLI returns exit 2 because it treats the fragment as part of the filename | Remove the fragment only from the path used to load the plan. The state retains the full reference; the plan is loaded once even when explicitly included. Regression `PASS`. |
| Re-render Korean HTML with `LC_ALL=C`, `PYTHONUTF8=0`, `PYTHONCOERCECLOCALE=0` | First render passes; second render returns exit 2 with an ASCII `UnicodeDecodeError` | Read the generated-file guard with `encoding='utf-8'`, matching the writer. Both renders pass and the source Markdown bytes remain unchanged. Regression `PASS`. |
| Configure a Korean active plan under the same ASCII locale | `configure` returns exit 2 with an ASCII `UnicodeDecodeError` while reading plan metadata | Read the plan once with explicit UTF-8 before checking its metadata. Regression `PASS`. |

The first locale-test attempt failed during Python's site initialization while decoding a venv
`.pth` file, before reaching either helper. Locale-only child processes now use the same selected
interpreter with `-S`; both helpers use only the standard library. The parent pytest runner remains
the documented RIS venv. The renderer regression probes the child's default encoding and confirms
that it is not UTF-8 before exercising two renders. After this isolation adjustment, all three
regressions failed at the intended application behavior before the fixes.

Focused regressions: `3 passed`. Full relevant suite: `44 passed in 1.14s`, exit 0:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH= /home/moontaehyung/바탕화면/RIS/.venv/bin/python -m pytest skills/ris/tests/test_project.py skills/project-plan/tests/test_graph.py -q -p no:cacheprovider
```

Run from the plugin source root. Tests are in `skills/ris/tests/test_project.py` and
`skills/project-plan/tests/test_graph.py`. No package installation or release snapshot was changed.
Optional browser smoke: `NOT_RUN`; Playwright is unavailable with the documented
`PYTHONPATH=/tmp/teachme_browser_lib`, and the documented Chromium executable is absent.
