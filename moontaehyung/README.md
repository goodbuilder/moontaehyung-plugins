# moontaehyung

A Codex plugin with nine skills for development workflows and Zotero research.

| Skill | Purpose |
|---|---|
| create-gui | Define and build new operator GUI workflows. |
| modify-gui | Change existing GUI workflows while preserving their contracts. |
| design-boundaries | Design module responsibilities, interfaces, ownership and lifecycles. |
| maintain-boundaries | Prevent responsibility concentration and hidden coupling during changes. |
| verify-check | Establish acceptance criteria, verify small steps and the complete workflow. |
| rca | Analyze intended-versus-observed task gaps and propose corrective action. |
| auto-subagents | Select and coordinate bounded independent work through native subagents. |
| update-architecture | Refresh the external architecture reader only when explicitly requested. |
| Zotero | Search the local library, verify reference metadata and recommendation evidence, export BibTeX, insert citations, and import references. |

The Zotero skill is bundled from OpenAI's Zotero plugin v0.1.2 under MIT; see [its license notice](skills/zotero/LICENSE.txt) and [upstream source](https://github.com/openai/plugins/tree/main/plugins/zotero). It uses Zotero Desktop's local API and Connector on 127.0.0.1:23119 with Python's standard library. It distinguishes library records, verified metadata, and checked paper content; unsupported or conflicting details remain unverified. If the local API is disabled, the skill may enable it and restart Zotero when asked to operate the library. Full-text retrieval is request-scoped, and imports are explicit library writes.

Use the [routing contract](references/skill-routing.md) to combine skills without duplicating
interviews, approvals, or evidence. The [minimum sufficient change policy](references/minimum-sufficient-change.md)
keeps additions proportional while preserving required behavior. KEEP / REMOVE / DEFER describes
design decisions; PASS / FAIL / BLOCKED / NOT_RUN describes verification evidence.

Keep the complete plugin directory together, including shared references and each skill's scripts,
templates and metadata. Personal skill copies are independent and not automatically synchronized.

Version 0.4.0 added design-boundaries, maintain-boundaries and rca, and merges the strengthened
verify-check requirements and verification workflow with the existing plugin-specific policies.
Existing GUI workflows and the explicit-only architecture refresh policy are preserved.
No hooks, MCP servers, or new external dependencies are added.

This directory is packaged source, not proof of installation or activation in this session.
See the [verification history](docs/verification.md) and [0.4.0 checks](docs/verification-0.4.0.md).

Version 0.4.1 compares personal skills and Workstation drafts by content, retains the already-merged
latest rules, and routes common architecture/verification procedures to their owning skills.
GUI-specific interviews, approval, visual behavior and acceptance remain with the GUI workflows.
See [0.4.1 comparison and verification](docs/verification-0.4.1.md).

Version 0.4.2 adds selective subagent verification to verify-check. Bounded investigations may
run in parallel when their benefit justifies the extra tokens and coordination; short checks
and known commands stay with the primary agent. Delegation uses compact briefs, usually one or
two subagents, no further delegation, stable inputs, and the existing verification ledger.
The primary agent retains final workflow verification and existing authorization boundaries.
See [0.4.2 update and verification](docs/verification-0.4.2.md).

Version 0.5.0 extracts shared delegation into auto-subagents and connects verify-check,
maintain-boundaries, and rca through package-relative references. Calling workflows retain
their acceptance criteria, domain judgment, records, and authorization. Simple checks remain
local; useful independent investigations can use native subagents without repeated role
assignment. Model/speed configuration and existing GUI/architecture-refresh policies remain
unchanged. See [0.5.0 checks and limits](docs/verification-0.5.0.md).

Version 0.5.1 adds conditional Qt Designer guidance to create-gui and modify-gui for
Qt Widgets forms. Framework selection, existing bindings, and workflow authorization
remain unchanged; Qt Quick/QML and non-Qt projects retain their own tooling. UI sources
and generated/application code have separate ownership, and runtime checks remain required.
See the Qt documentation on [form design](https://doc.qt.io/qt-6/designer-quick-start.html)
and [custom widgets](https://doc.qt.io/qt-6/designer-using-custom-widgets.html).

Version 0.5.2 makes material implementation/tooling choices explicit before the plan is fixed.
Create/modify GUI workflows own GUI choices; design-boundaries owns structural choices.
Maintenance and verification reuse those decisions and reopen only invalidated assumptions.
Small fixes and valid prior decisions avoid repeated comparisons. See
[0.5.2 checks and limits](docs/verification-0.5.2.md).

Version 0.5.3 adds a compact work-summary handoff to verify-check and a shared
[work-evidence contract](references/work-evidence.md). Personal cli-usage-review can compare
those summaries with explicitly supplied usage exports; it is not bundled as a ninth skill.
Unknown usage stays unknown, and task completion does not trigger a mandatory review.
See [0.5.3 verification](docs/verification-0.5.3.md).


Version 0.6.0 adds the OpenAI Zotero skill (v0.1.2, MIT) for local library search, requested full-text reading, BibTeX export, citation insertion, and reference import. It uses Zotero Desktop's local API/Connector and adds no MCP server or Python package.


Version 0.6.1 adds reference-integrity rules to the existing Zotero skill: external references require authoritative metadata checks, recommendations require content evidence, and unresolved fields or mismatches are withheld instead of guessed.
