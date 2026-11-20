# RIS role gate (pilot: `research-map`)

Opt in per project: add `role_gate_profile: "research-map"` to `.ris/project.yaml`, then copy
`templates/role-gate/claude-settings.local.json` to `.claude/settings.local.json` and
`templates/role-gate/codex-hooks.json` to `.codex/hooks.json`, setting `RIS_SCRIPTS` to this
`scripts/` directory. Codex requires its hook-trust approval. Roll back by removing the setting and hooks;
`.ris/role-gate/` records stay.

Flow: the prompt hook starts a run (skip a turn with `RIS-SIMPLE` on its first line). For each task run
`ris.py gate assign --task ID`, put the printed `RIS_ASSIGN ...` line in the agent prompt, and have the agent end
with `RIS_RESULT {json}` (run_id, task_id, token, input_hash, status, evidence, artifacts, blocking).
For Codex builds that emit `collaborationspawn_agent`, use the updated Codex hook template.
The Coordinator includes the exact RIS_ASSIGN line in the original spawn message and sets
`task_name` to the returned `codex_task_name` and `fork_turns: "none"`. The task name is
derived from the assignment token so the hook can validate a call whose message is opaque. The pre-tool hook validates the original call without changing its
arguments. The gate requires the matching successful tool response, observed role, and assignment
token in the worker's result before binding its agent ID. Run gate assign again after a failed
spawn to obtain a fresh token. Refresh and review the project hook configuration after updating.
Tasks in order: RG-RESEARCH, RG-PLAN, RG-DESIGN, RG-VERIFY, RG-AUDIT. Tokens are single-use; a result is accepted
only if its call was observed. `ris.py gate verdict` shows what is missing; `state update` to COMPLETE and the
`Stop` hook use the same judge. After 2 identical no-progress Stop blocks auto-continue stops and the run stays
incomplete. Changing canon or HTML after delivery invalidates the verdict.

Binding rules (verified against real Claude Code sessions): a task counts only when the call used the
role's own agent type (`moontaehyung:researcher`, …; `general-purpose` or an unknown type is refused), the
spawned agent's real id is bound to that call (from the tool response), and the result comes from that same
id. A result sent early by `SubagentStop` is held until the id is bound. Start phrases: `/ris`, `$ris`, `RIS`
as the first word of the prompt; a sentence that merely mentions RIS does not start a run. Only the session that
started a run is gated; `ris.py gate release` hands the run to the next session. With the pilot on, `COMPLETE`
is refused even when no gate record exists. Gate tasks are mirrored into `.ris/state.json`.
Snap Firefox for the engineer task needs its profile and the HTML copy under `~/snap/firefox/common/`.
