# ADR-0001: Autonomous RIS specialist agents

- **Status:** proposed
- **Date (ISO 8601):** 2026-11-10
- **Owner:** User / plugin maintainer
- **Blueprint links:** N/A — the plugin source has no canonical Project Plan for this proposal
- **Supersedes / Superseded by:** none

## Context and decision question

The current RIS Skill already supports broad source-backed research, continuity, project-local
Markdown, branching plans, and interactive maps. It also assigns research coverage and completion
judgment to the coordinating agent. This concentrates research, planning, whole-run completion, and
review in one context. The proposed change asks whether RIS should split those responsibilities
across persistent Codex agent roles while preserving the existing Skills and canonical artifacts.

## Constraints and decision drivers

- Keep the existing CLI agent as the interface and project Markdown as the research authority.
- Reuse `ris`, `project-plan`, `auto-subagents`, and existing analysis Skills.
- Keep project identity, recording policy, user decisions, and authorization boundaries intact.
- Make independent audit a distinct role; do not claim independent validation when it did not run.
- Store orchestration bookkeeping without copying findings, sources, forecasts, or the decision graph.
- Do not imply plugin installation automatically registers custom agents.

## Options considered

| Option | Benefits | Costs and risks | Reversibility | Evidence quality |
| --- | --- | --- | --- | --- |
| A — keep one coordinating agent and the current Skills | No agent installation step; existing workflow is available in one session | Research, planning, overall completion, and self-review share context; independent audit is not represented as a separate role | High; current setup remains available | Current plugin Skill and routing sources inspected |
| B — main-thread Coordinator plus Planner, Researcher, and Auditor TOML templates | Clear role ownership and separate contexts; preserves current Skills and project-local records; supports a genuine independent audit when the Auditor runs | Requires project/user agent installation; more token and coordination cost; Auditor instructions do not isolate permissions; nested specialist delegation needs runtime confirmation | High; remove templates and continue with the existing Skills | Current plugin sources and official Codex custom-agent/plugin documentation inspected |
| C — build a standalone RIS application, service, or database | Could provide a custom interface and centralized orchestration | Adds runtime, persistence, maintenance, and migration work despite existing CLI and Markdown workflow | Medium; migration away could strand new state | Not investigated because it conflicts with the established project-local direction and was not needed to answer this decision |

## Decision and rationale

Proposed: use option B. Keep the main Codex thread as the Coordinator; use `planner`, `researcher`,
and `auditor` as optional custom agents. Retain existing Skills as the canonical methods and
artifacts. Add `research-audit` for general RIS audit findings. Treat `.ris/state.json` as optional
run/task/gate bookkeeping and artifact references only. Ship agent TOMLs as plugin templates and
document copying them to `.codex/agents/` or `~/.codex/agents/`; do not claim plugin installation
registers them.

The proposal remains `proposed`, not `accepted`: source templates are being prepared, but a fresh
Codex session has not demonstrated discovery, delegation, or independent audit behavior.

## Evidence, assumptions, and uncertainties

- **Verified:** the current package has RIS continuity, Project Plan, Auto Subagents, and specialized analysis Skills. The current RIS Skill owns broad exploration and continuity; Project Plan owns the canonical decision graph and forecasts.
- **Verified:** Codex documents custom agent TOMLs under project `.codex/agents/` or personal `~/.codex/agents/`, requires `name`, `description`, and `developer_instructions`, and states that custom agents inherit parent permissions. [OpenAI Subagents documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- **Verified:** Codex plugin packages include Skills and optional assets; agent templates require separate registration. [OpenAI plugin packaging documentation](https://developers.openai.com/plugins/build/plugins)
- **Assumed:** separate role contexts will improve coverage and audit independence enough to justify their added token and latency cost. Evaluate with realistic runs before tuning model settings.
- **Unknown:** whether the installed client/configuration permits specialist agents to spawn leaf workers. Use Coordinator-mediated leaf delegation if it does not.
- **Unknown:** live agent discovery, end-to-end state-helper behavior, audit defect recall, forecast calibration, token cost, and latency.

## Consequences and residual risk

- Researcher owns research coverage for an assigned investigation; Planner owns the canonical plan and forecasts; Auditor challenges both; Coordinator owns cross-role routing and overall acceptance.
- Existing project plans, source records, review workflow, and manual recording default remain in place.
- Installing the three agent templates and merging the Coordinator block into project `AGENTS.md` are explicit setup actions. They do not alter the plugin user's project automatically.
- The optional state helper validates project references and task dependencies, but it cannot verify the truth of referenced research or forecast claims.
- The Auditor's no-edit instruction is behavioral. A parent session's write permissions remain inherited.

## Re-evaluation / exit contract

- **Leading signal + source:** agent discovery and observed behavior in a clean Codex session; later, seeded audit outcomes and historical project forecasts.
- **Observation window:** initial installation smoke test, then representative RIS runs; no numeric sample size is set until the evaluation set is defined.
- **Trigger:** agents are not discoverable, independence is not achieved, audit/rework duplicates work, or measured token/latency cost outweighs demonstrated coverage benefit.
- **Containment:** do not claim an independent audit or completed autonomous run when a required agent did not execute.
- **Fallback:** keep the Coordinator and existing Skills; use Coordinator-mediated leaf delegation or local sequential work and label the audit `NOT_RUN`/`BLOCKED` when appropriate.
- **Review date:** after the first runtime discovery/delegation smoke test.

## Verification

- [x] Competing options and risks recorded
- [x] Official agent registration and permission behavior linked
- [ ] Decision owner reviewed
- [ ] Runtime discovery/delegation behavior observed
