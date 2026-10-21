# 0.11.0 verification and scope

- Replaces `skills/update-architecture` with the upstream Archify 3.2.0 skill package from `tt-a1i/archify`, pinned to commit `208acba8d412335185b2056fedf54b3405df43fb`.
- The upstream distributable contains 200 files (17,812,933 bytes); the plugin adds one local `agents/openai.yaml`. The MIT license, third-party notices, and JetBrains Mono license are retained.
- Static review found local artifact writes, optional child-process use for preview/browser checks and opening an explicitly requested artifact, and a bounded GET to Archify's fixed update-manifest URL. The update check records metadata in the user cache and does not install updates itself.
- Requires Node.js 18 or later. The package says no install is required in the skill folder; its renderer and schemas are bundled. Optional browser/opening paths depend on locally available tools.
- Preserves the shared project architecture-refresh contract and updates live skill routing. Historical verification records naming `update-architecture` remain unchanged.

## Checks

- Archify `SKILL.md` validation on source and installed copy — PASS.
- Plugin JSON manifest parse, Archify local Markdown links, and `git diff --check` — PASS.
- Plugin contains 13 skill folders; Archify is present, `update-architecture` is absent, and `reviewer` remains present — PASS.
- Codex plugin CLI installed version `0.11.0` at `/home/moontaehyung/.codex/plugins/cache/moontaehyung-local/moontaehyung/0.11.0` — PASS.
- Skill Manager runtime recognition — NOT_RUN: its adapter rejects the installed Codex CLI `0.163.0` as unsupported (adapter was built for `0.162.1`). The plugin CLI reported the installed path and the installed cache contents were checked directly.
- Upstream Archify scripts and tests were not executed during static package review.
