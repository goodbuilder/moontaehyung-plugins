# moontaehyung

A Codex plugin with twenty-one skills for structured analysis and workflow selection, explainable XLSX workbooks, Archify diagrams and explainers, hand-reproducible computation lessons, research review, risk-aware project planning, development workflows, skill management, and Zotero research.

| Skill | Purpose |
|---|---|
| ris | Resume research through the existing CLI agent using project-local Markdown, Obsidian, source-backed understanding and handoffs. |
| project-plan | Map design alternatives, risks, early warnings, quality gates and fallback paths before committing. |
| architecture-decision-record | Record why an architectural choice was made, and when to revisit or supersede it. |
| create-gui | Define and build new operator GUI workflows. |
| modify-gui | Change existing GUI workflows while preserving their contracts. |
| design-boundaries | Design module responsibilities, interfaces, ownership and lifecycles. |
| maintain-boundaries | Prevent responsibility concentration and hidden coupling during changes. |
| verify-check | Establish acceptance criteria, verify small steps and the complete workflow. |
| analysis-router | Select analysis workflows; compare consequential boundary cases independently through auto-subagents. |
| aar | Review expectations, outcomes, successful practices and sustain/change actions. |
| rca | Investigate important actual failures with causal hypotheses and supporting/refuting evidence. |
| rmea | Assess prospective risk modes, controls, response priorities and residual risk. |
| fta | Model defined failures with AND/OR logic and minimal cut sets. |
| mcda | Compare alternatives with value scales, weights and sensitivity analysis. |
| auto-subagents | Select and coordinate bounded independent work through native subagents. |
| skill-auto-manager | Compare reusable projects, tools, skills and plugins before substantial implementation and at capability gaps. |
| archify | Create validated interactive diagrams or one-page explainers; use the shared contract for requested architecture-reader refreshes. |
| Explain-xlsx | Create formula-traceable XLSX workbooks alongside reportable code-derived numerical results across project domains. |
| reviewer | Review research papers, technical reports, and presentations with evidence-backed criticism and prioritized revisions. |
| teach-me | Teach a real computation with a worked example readers can reproduce by hand. |
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

Version 0.7.0 adds two complementary planning skills: risk-adaptive-blueprint (branching options,
pre-mortem risks, gates and switching conditions) and architecture-decision-record (durable,
linked ADRs). Blueprints remain revisable while ADR history is preserved. Risk discovery is not
authorization to modify live systems. No Hooks, MCP servers, or new runtime dependencies are added.
See [0.7.0 verification](docs/verification-0.7.0.md).

Version 0.8.0 adds Auto-Skill-manager for reviewing current skill coverage and recommending relevant skills or scoped maintenance using available read-only discovery tools. Public discovery remains recommendation-only; discovered candidates are not installed automatically. This adds an instruction-only skill and UI metadata, with no hooks, MCP servers, or runtime dependencies. See [0.8.0 verification](docs/verification-0.8.0.md).


Version 0.8.1 clarifies when public skill discovery runs and how recommendations show coverage, source, match evidence, and review status. Search is skipped when current skills cover the need; incomplete results remain explicit. Recommendations never install candidates. No engine code, Hooks, MCP servers, or runtime dependencies changed. See [0.8.1 verification](docs/verification-0.8.1.md).


Version 0.9.0 renames the public skill identity `risk-adaptive-blueprint` to `risk-plan` while preserving its planning workflow and supporting resources. Invoke it as `$risk-plan`; ADR routing now points to the new identity. This is a skill-name change and does not add hooks, MCP servers, or runtime dependencies. See [0.9.0 verification](docs/verification-0.9.0.md).


Version 0.10.0 adds the reviewer skill for evidence-based review of research papers, technical reports, and presentations. It uses the six-part Korean review format from the personal reviewer instructions and adds no hooks, MCP servers, or runtime dependencies.


Version 0.11.0 replaces the plugin-specific update-architecture skill with Archify 3.2.0 from tt-a1i/archify. It includes validated architecture and workflow diagrams, one-page explainers, and their source package. The shared architecture-refresh contract still governs source authority, explicit reader refreshes, and verification records. See [0.11.0 verification](docs/verification-0.11.0.md).

Version 0.12.0 adds Explain-xlsx for code-derived numerical results. It creates report-first workbooks with live spreadsheet formulas, code-to-cell provenance, and explicit boundaries for calculations that remain code-produced values. It adds no hooks, MCP servers, or runtime dependencies. See [0.12.0 verification](docs/verification-0.12.0.md).

Version 0.13.0 adds reviewer configuration v6 beside the existing reviewer skill. It defines project-neutral review coverage, audits present document elements, and keeps delegated reviewers blind to unassigned reviews or answer keys. The skill reads the bundled configuration; no hooks, MCP servers, or runtime dependencies are added. See [0.13.0 verification](docs/verification-0.13.0.md).

Version 0.14.0 adds the explicit-only Teach Me skill. It teaches a real computation through a hand-reproducible example, stepwise prerequisites, diagrams, self-checks, and a code cross-check. Requested HTML pages use the bundled Archify workflow; no Claude-only helper skills, scripts, hooks, MCP servers, or new runtime dependencies are required. See [0.14.0 verification](docs/verification-0.14.0.md).

Version 0.15.0 adds AAR, RMEA, FTA, MCDA and analysis-router. RCA now focuses on actual causal
investigation; project-plan integrates specialist results; ADR and verify-check reuse their
records. Analysis-router owns isolated candidate-method comparisons and uses the unchanged
general auto-subagents delegation workflow. Explicit method requests
are respected, obvious requests avoid a comparison, and missing facts/preferences cause a
bounded deferral rather than more agents. Simple results stay in chat. Requested or substantial
file deliverables default to Markdown for AAR, XLSX for RMEA, SVG plus Markdown for FTA, and
formula-traceable XLSX plus Markdown for MCDA. RMEA denotes the declared generic Risk Mode and
Effect Analysis workflow, not certified FMEA compliance. FTA defaults to static AND/OR models;
MCDA defaults to additive weighted-value comparison. Spreadsheet/diagram outputs use available
artifact tooling; generation and runtime activation are distinct from writing these skills.
No hooks, MCP servers, or new executable dependencies are added. See
[0.15.0 verification and limits](docs/verification-0.15.0.md).

Skill Auto-Manager compares reusable projects, tools, skills and plugins before substantial
implementation, during alternative searches and at concrete capability gaps. Discovery starts
with local coverage and uses sources suited to the candidate type: canonical repositories and
product documentation for software, skills.sh/SkillsMP for skills, Tessl for available evaluation
evidence, and ClawHub for OpenClaw needs. Search unavailability is reported without blocking
supported local recommendations. Discovery does not install or activate candidates. Popularity,
static checks and actual behavior remain separate evidence dimensions. See the
[discovery source contract](skills/skill-auto-manager/references/discovery-sources.md).


Version 0.16.0 bundles RIS as a project-local research skill. The existing CLI agent is the
interface; no separate web UI, central database, mandatory MCP server or Node runtime is added.
Each project owns `.ris/project.yaml` and `research/` Markdown; the project root can be opened
in Obsidian. The bundled standard-library Python helper initializes/checks projects, prepares
bounded source snapshots, creates draft notes and preserves existing-note changes as proposals.
Recording defaults to manual. Existing files and project identity are preserved.

Use the RIS skill with requests such as “이 프로젝트에 RIS를 초기화해줘”, “현재 이해와 판단을
읽고 연구를 이어가자”, or “이번 결과와 다음 세션 맥락을 기록해줘”. See the
[RIS workflow](skills/ris/SKILL.md) and [helper operations](skills/ris/references/operations.md).
Project-plan owns branching plans; teach-me owns requested worked examples; Zotero owns verified
library operations. RIS links their canonical results rather than rerunning all methods.

This change adds packaged source, not live activation. A pre-existing standalone `ris` may still
be recognized; keep its provenance distinct from the bundled skill and do not remove or retarget
it until the desired plugin installation and discovery are verified. See
[0.16.0 verification and limits](docs/verification-0.16.0.md).

### Research decision maps

RIS now clarifies desired outcomes, surveys source-backed research trends and defaults to broad, recursive
agent-led investigation (guided branches on request). Project Plan connects outcome elements to
alternatives, conditional forecasts, verification and fallbacks. Canonical plans remain Markdown;
its bundled standard-library renderer generates a portable interactive HTML map without a server.
Map previews never confirm decisions. The agreed milestone policy records confirmed goals, choices
and verification results; existing projects retain their recording policy until explicitly configured.
See [graph contract](skills/project-plan/references/graph-contract.md),
[RIS operations](skills/ris/references/operations.md) and [verification](docs/verification-research-map.md).

Autonomous exploration now keeps the full mechanism inventory, expands viable unselected routes through downstream decisions, and reports structural coverage/frontier in the HTML map. Overview size is not an investigation cap.

Candidate bundles now reuse option references across independent candidates. HTML supports candidate switching, cloning, comparison and candidate-local multiple selection for compatible choices; legacy single-choice plans remain readable.

The research map separates **구성요소별 선택지** (read-only catalog with evidence) and **후보 구성·비교** (component-by-candidate matrix and independent editing). Browsing options preserves all candidate choices; comparison cells open the matching candidate/component editor.

### Version 0.17.0 — research planning maps

Renames risk-plan to project-plan. RIS and Project Plan clarify desired outcomes, survey distinct
research approaches and recursively investigate viable alternatives. Canonical Markdown graphs
support reusable option references across independent candidate bundles and decision-local multiple
selection. Portable HTML separates a read-only component-option catalog from candidate composition
and comparison. The Python helper adds guarded updates, project settings and active-plan resume.
See [implementation evidence](docs/verification-research-map.md) and
[local installation verification](docs/verification-0.17.0.md).
