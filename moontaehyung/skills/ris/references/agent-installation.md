# RIS custom agent setup

Use the [shared role workflow](role-workflow.md) for responsibilities and handoffs.
The source ships Codex TOML templates in `agents/` and Claude Markdown templates in
`agents/claude/`. Copy only the authorized roles to the appropriate agent directory.

Use this procedure only for an authorized custom-agent installation. Ordinary research does not
require installation or a fixed roster. Preserve higher-priority delegation restrictions and configured
model choices; template defaults do not authorize changing them.

| Client | Templates | Project directory | Personal directory |
| --- | --- | --- | --- |
| Codex | `agents/{researcher,engineer,planner,designer,auditor}.toml` | `<project>/.codex/agents/` | `~/.codex/agents/` |
| Claude Code | `agents/claude/{researcher,engineer,planner,designer,auditor}.md` | `<project>/.claude/agents/` | `~/.claude/agents/` |

Review same-named files before copying and merge deliberately. Preserve configured models.
For every assignment, give the selected agent the actual path to the shared role workflow.
For Designer, also give it the shared output contract and the saved plan revision.

Use the [Coordinator guidance](../../../templates/ris-coordinator-AGENTS.md) in the
project's instructions as needed. The RIS helper's `--attach-agents` flag adds the RIS
guidance block to AGENTS.md. Register custom agents separately for the chosen client.
After setup, validate the installed files and open a fresh session. Check discovery of each
installed role and relevant skill, then give each role a bounded smoke assignment to verify
that it can be invoked and return the expected shape. Report file installation, discovery, and
successful invocation separately.

The Coordinator applies the session's actual tool and delegation limits. An Auditor's
read-only instructions set its work scope. Enforce read-only access separately where
required. Route requests for other RIS roles back to the Coordinator.

See OpenAI's [Subagents documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents) for agent locations, file fields, model configuration, and inherited permissions.
