# Maintaining the moontaehyung plugin (RIS skill and agents)

Read this only when asked to change the RIS skill, its references, helper scripts or role agents.

## One source, two installed copies
- The only editable source is the plugin directory of the `moontaehyung-local` marketplace:
  `~/plugins/moontaehyung`. Codex and Claude Code both install from it.
- Installed copies live under `~/.claude/plugins/cache/` and `~/.codex/plugins/cache/`. They are
  overwritten on update. Never edit them; a change made there is lost and desynchronizes the tools.
- `~/plugins/moontaehyung-claude` is a retired fork. Do not edit it.
- If the source cannot be found or is not writable, report that instead of editing an installed copy.

## Changing it
1. Edit only under `~/plugins/moontaehyung`. Keep content tool-neutral; tool-specific wording
   belongs in `agents/*.toml` (Codex) and `agents/claude/*.md` (Claude Code).
2. Change a role in both agent formats so they stay equivalent.
3. No symlinks inside the plugin tree: Codex drops them and absolute ones break in the cache.
4. Run `python3 skills/ris/scripts/ris.py --help` and `python3 -m pytest -q skills/ris/tests`. The suite includes `test_plugin_sync.py`: equal manifest
   versions, both agent formats per role, no symlinks. Roles listed as known drift there are xfail(strict);
   when you reconcile one, delete its entry so the guard stays meaningful.
5. Raise `version` in both `.codex-plugin/plugin.json` and `.claude-plugin/plugin.json` to the same value.
6. Deploy: `claude plugin uninstall moontaehyung@moontaehyung-local` then `claude plugin install
   moontaehyung@moontaehyung-local` (a same-version `update` is skipped), and
   `codex plugin add moontaehyung@moontaehyung-local`. Start a new session in each tool.
7. Check the installed copy equals the source: `diff -rq --exclude=__pycache__ ~/plugins/moontaehyung <cache>/<version>`.
