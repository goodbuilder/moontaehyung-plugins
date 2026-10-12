# Moontaehyung Codex plugins

A personal Codex plugin marketplace with the moontaehyung plugin and its bundled skills.

## Install from a local checkout

From this repository root, run:

    codex plugin marketplace add .
    codex plugin add moontaehyung@moontaehyung-local

Start a new Codex chat or CLI session after installation so it loads the bundled skills.

## Repository layout

- .agents/plugins/marketplace.json registers the local marketplace.
- moontaehyung/ contains the plugin manifest, skills, shared references, and documentation.
- .backups/ is kept outside version control; Git history tracks source revisions.

See moontaehyung/README.md for the individual skills and their workflows.
