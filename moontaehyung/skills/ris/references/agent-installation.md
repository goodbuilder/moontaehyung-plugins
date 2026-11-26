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
and merge deliberately; do not overwrite it by name. The templates pin a starting model and reasoning
effort per role; choose an available model if your account or workspace does not provide one of them.

| Role | Codex | Claude Code | Effort |
|---|---|---|---|
| auditor | `gpt-6.2-astra` | `claude-fable-5-2` | high |
| engineer | `gpt-6-luna` | `claude-haiku-5-5` | max |
| researcher | `gpt-6.1-terra` | `claude-opus-5-5` | medium |
| planner | `gpt-6-luna` | `claude-haiku-5-5` | max |
| designer | `gpt-6-luna` | `claude-haiku-5-5` | max |

Start a fresh Codex session after installation. For isolated noninteractive runs, check that
the native delegation tool actually offers the intended role. If a project template is present
but absent from the role selector, an invocation can bind that same reviewed file explicitly,
for example `-c 'agents.researcher.config_file="/absolute/project/.codex/agents/researcher.toml"'`.
Repeat for the required roles and verify their effective settings. Use the selected project's
current definitions when they include user changes.

## Coordinator (main session) model

The role agents carry their own model and effort. The Coordinator runs on the session model, so pin it
separately when runs must be comparable.

- **Claude Code:** the RIS `SKILL.md` frontmatter sets `model: claude-haiku-5-5` and `effort: max`.
  Claude Code applies a skill's model and effort only for the turn that invokes the skill; the session
  model resumes on the next prompt. To hold the same model for a whole session, start it with
  `claude --model claude-haiku-5-5 --effort max`, or set `"model"` in the research project's
  `.claude/settings.json`. The `CLAUDE_CODE_EFFORT_LEVEL` environment variable overrides the skill's effort.
- **Codex:** the frontmatter fields above are Claude Code fields and are not relied on in Codex. Copy
  the profile template once and start RIS sessions with it:

  ```bash
  cp <plugin-root>/templates/ris.config.toml ~/.codex/ris.config.toml
  codex -p ris
  ```

  The profile sets `gpt-6-luna` with `max` reasoning effort on top of the user's base config.

Change the Coordinator model in the frontmatter and the profile template together.

## Optional Coordinator integration (both tools)

Attaching [the Coordinator block](../../../templates/ris-coordinator-AGENTS.md) to the selected
project's `AGENTS.md` (Codex) or `CLAUDE.md` (Claude Code) is optional integration, not part of
default RIS initialization. Do it only when explicitly requested, preserve existing instructions,
and do not replace user or project guidance. Root instruction files remain project-owned.

All custom agents inherit the parent session's permissions, provider, and connected tools. The Auditor's
no-edit rule is behavioral; its definition does not create an isolated read-only permission boundary.
If specialist-to-leaf delegation is unavailable in a client, have the specialist return bounded delegation
briefs to the Coordinator, who can assign leaf work.

See OpenAI's [Subagents documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents) for
Codex agent locations, file fields, model configuration, and inherited permissions.
