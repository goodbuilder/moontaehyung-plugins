# RIS custom-agent installation

The plugin supplies five role agents: researcher, planner, engineer, designer and auditor. Installing
the plugin makes its Skills available in both Codex and Claude Code. A template on disk does not
establish runtime discovery; confirm the agent names after installation.

## Claude Code

The agents are listed in `.claude-plugin/plugin.json` (`agents/claude/*.md`) and are registered by the
plugin as `moontaehyung:<role>`. Start a fresh session after installing or updating the plugin and
confirm the five names are available.

## Codex

Codex does not register plugin agents automatically. Copy the TOML templates from the plugin's `agents/`
directory into the project-scoped directory (`<project-root>/.codex/agents/`) for one RIS project, or
into `~/.codex/agents/` for personal use across projects:

```bash
mkdir -p <project-root>/.codex/agents
cp <plugin-root>/agents/{researcher,planner,engineer,designer,auditor}.toml <project-root>/.codex/agents/
```

Review existing files first. If a destination agent already exists with different instructions, compare
and merge deliberately; do not overwrite it by name. The templates for researcher, planner and auditor
use `gpt-6.1-sol` as a starting model; choose an available model if your account or workspace does not
provide it. The engineer and designer templates inherit the session model. Start a fresh Codex session
after installation.

## Coordinator instructions (both tools)

Append [the Coordinator block](../../../templates/ris-coordinator-AGENTS.md) to the selected project's
`AGENTS.md` (Codex) or `CLAUDE.md` (Claude Code), preserving existing project instructions. The template
is not a replacement for user or project guidance.

All custom agents inherit the parent session's permissions, provider, and connected tools. The Auditor's
no-edit rule is behavioral; its definition does not create an isolated read-only permission boundary.
If specialist-to-leaf delegation is unavailable in a client, have the specialist return bounded delegation
briefs to the Coordinator, who can assign leaf work.

See OpenAI's [Subagents documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents) for
Codex agent locations, file fields, model configuration, and inherited permissions.
