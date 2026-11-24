# moontaehyung plugin source (shared by Codex and Claude Code)

- `moontaehyung/` is the only editable source of the plugin (RIS skill, role agents, other skills).
  Both tools install from it through the `moontaehyung-local` marketplace in this directory.
- Never edit the installed copies under `~/.claude/plugins/cache/` or `~/.codex/plugins/cache/`, and do not
  edit `moontaehyung-claude/` (retired fork). Backups of earlier versions are in `.backups/`.
- Follow `moontaehyung/skills/ris/references/maintenance.md` for the change, version, and deploy procedure.
- Do not commit or push unless asked.
