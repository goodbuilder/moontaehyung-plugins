# RIS custom-agent installation

Faust supplies TOML templates under `agents/`; installing the skill makes its Skills available but does not register these custom agents. Codex discovers project agents from `<project>/.codex/agents/` and personal agents from `~/.codex/agents/`.

For one RIS project, copy the three templates into its project-scoped agent directory:

```bash
mkdir -p <project-root>/.codex/agents
cp <this-skill>/agents/researcher.toml <this-skill>/agents/planner.toml <this-skill>/agents/auditor.toml <project-root>/.codex/agents/
```

Review existing files first. If a destination agent already exists with different instructions, compare and merge deliberately; do not overwrite it by name. For personal use across projects, place reviewed templates in `~/.codex/agents/` instead. The templates use `gpt-6.1-sol` as a starting model; choose an available model if your account or workspace does not provide it.

Append [the Coordinator block](../templates/faust-coordinator-AGENTS.md) to the selected project's `AGENTS.md`, preserving existing project instructions. The template is not a replacement for user or project guidance. Start a fresh Codex session after installation, then confirm the three agent names and relevant Skills are discoverable. A template on disk does not establish runtime discovery.

All custom agents inherit the parent session's permissions, provider, and connected tools. The Auditor's no-edit rule is behavioral; its TOML file does not create an isolated read-only permission boundary. If specialist-to-leaf delegation is unavailable in a client, have the specialist return bounded delegation briefs to the Coordinator, who can assign leaf work.

See OpenAI's [Subagents documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents) for agent locations, file fields, model configuration, and inherited permissions.
