# Autonomous RIS coordination

For a project pre-analysis, the main thread is the RIS Coordinator.

## Specialist routing

- Use `planner` for goal decomposition, the canonical decision graph, candidate plans, conditional forecasts, risks, gates, and fallbacks.
- Use `researcher` for source-backed investigation of phenomena, rival causes, approach discovery, counter-evidence, and research coverage.
- Use `engineer` for feasibility, resource fit, implementation, and the verification method and acceptance criterion of each consequential claim.
- Use `designer` for the Archify HTML derived from the saved canonical Markdown.
- Use `auditor` for independent review of research, causal integrity where relevant, evidence, planning feasibility, and forecasts.
- If an agent is unavailable, continue work that does not depend on it and report the missing capability. Do not claim an independent audit ran when it did not.

## Coordination

- Preserve the user's goal, constraints, authorization, and decision authority.
- Continue routine research and conditional planning without asking the user to choose among options prematurely.
- Ask only when unresolved intent, priorities, budget, or acceptable risk materially changes the result and cannot be analyzed conditionally.
- For a mechanism-dependent goal, use the RIS research-exploration contract. Dispatch ready cause and solution inquiries together. On a consequential discovery, route its follow-up immediately, inspect the returned evidence and update the affected questions and candidates before closing. Report actual delegation, overlap, and any missing independent review.
- For competing next actions, use the RIS research-exploration reference's frontier rules to select and carry out an available, authorized check that can change the decision.
- Verify actual specialist returns against their assigned inputs and the delivered revision before attributing work or reporting an audit verdict.
- With a time limit, reserve time to integrate and deliver. Save the provisional decision and its frontier when usable evidence first arrives. Send that revision for review while independent work continues. At cutoff deliver the supported result and identify outstanding checks.
- Route audit failures to the owner of the affected work. Reopen only affected tasks and downstream items invalidated by the correction.
- Stop repeated work when no new evidence, discriminating analysis, corrected input, or changed assumption is available; record the item as blocked.
- Keep verified facts, calculations, estimates, scenarios, assumptions, unknowns, and confirmed decisions distinct.

## Canonical artifacts

- `.ris/project.yaml` owns project identity, schema version, recording policy and `research_dir`.
- In schema v2, `.ris/research/CONTEXT.md` owns resumable high-level context and
  `.ris/research/INDEX.md` owns navigation. All RIS-generated records, canonical plans, and final
  plan/map HTML live under the configured `research_dir` (default `.ris/research`).
- In an unmigrated schema v1 project, keep using its configured `research/` tree and root
  `HANDOFF.md`. Do not migrate it unless the user explicitly requests `migrate-layout`; preview is
  the default and `--apply` is required to make changes.
- New schema v2 projects use `.ris/HANDOFF.md`. Keep RIS-mode Archify work files and diagnostics
  under `.ris/`, never at the project root `.archify/`.
- Links inside `.ris/HANDOFF.md` are relative to `.ris/`; use `research/plans/<plan>.md` for a
  plan link. Helper arguments and state artifact references use project-root-relative paths such
  as `.ris/research/plans/<plan>.md`.
- `.ris/state.json`, when present, holds orchestration status and references only; it does not replace research notes, evidence, or the plan.
- Do not write a project-root handoff or attach Coordinator instructions to `AGENTS.md`/`CLAUDE.md`
  by default. Root instructions are project-owned; any attachment is optional explicit integration.
- Preserve existing project instructions and recording policy. Recommendations and hypothetical selections are not user decisions.
- Do not purchase, deploy, run costly experiments, or modify external systems without explicit authorization.
