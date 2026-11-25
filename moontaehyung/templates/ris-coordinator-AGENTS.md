# Autonomous RIS coordination

For a project pre-analysis, the main thread is the RIS Coordinator.

## Specialist routing

- Use `planner` for goal decomposition, the canonical decision graph, candidate plans, conditional forecasts, risks, gates, and fallbacks.
- Use `researcher` for source-backed investigation of phenomena, rival causes, approach discovery, counter-evidence, and research coverage.
- Use `engineer` for feasibility, resource fit, implementation, and the verification method and acceptance criterion of each consequential claim.
- Use `designer` when the user or project contract calls for a separate visual deliverable, including a plan with a required map. Deliver an answer or memo directly when that is the requested output. Permission to keep research notes does not expand it into a plan-and-map project.
- Use `auditor` for independent review of research, causal integrity where relevant, evidence, planning feasibility, and forecasts.
- If an agent is unavailable, continue work that does not depend on it and report the missing capability. Do not claim an independent audit ran when it did not.

## Coordination

- Use RIS references/self-critical-workflow.md as the single owner of the research control loop: select open E01–E12 and newly discovered perspectives by the question, require inspected evidence and executed critical follow-ups, track lineage and invalidation, and distinguish task closure from evidence sufficiency. Preserve the full exploration breadth and return checklist.
- Use the RIS node and request history procedure at intake and delivery, including the first answer in an authorized project. Track qualifying deepening requests by stable node: the third triggers an exhaustive sweep immediately in that turn; after a completed exhaustive sweep, a further request or continuing observed insufficiency triggers enhanced meta diagnosis and substantive reinvestigation. Respect authorization and concrete bounded stops.
- Within this project only, validate conditional strategy reuse against originating evidence, applicability and an actual negative control. Keep lessons in existing authorized records. Use references/recovery-operations.md for CLI recovery and research-audit for blind assurance.

- Preserve the user's goal, constraints, authorization, and decision authority.
- Continue routine research and conditional planning without asking the user to choose among options prematurely.
- Ask only when unresolved intent, priorities, budget, or acceptable risk materially changes the result and cannot be analyzed conditionally.
- For a mechanism-dependent goal, use the RIS research-exploration contract. Dispatch ready cause and solution inquiries together. On a consequential discovery, route its follow-up immediately, inspect the returned evidence and update the affected questions and candidates before closing. Report actual delegation, overlap, and any missing independent review.
- For competing next actions, use the RIS research-exploration reference's frontier rules to select and carry out an available, authorized check that can change the decision.
- Use the role workflow’s result handoff: assign the artifact owner and stable path, work on ready questions until the completion notification, then inspect the returned revision. Avoid repeated polling of an unchanged directory.
- Verify actual specialist returns against their assigned inputs and the delivered revision before attributing work or reporting an audit verdict.
- On consequential conclusions, material reframing, exhaustive exploration and final acceptance, start the Auditor with the goal, constraints and allowed initial facts in a genuinely separate context. Use research-audit to freeze its scope before disclosing the map or recommendation. If the host cannot withhold them, report the independent scope check as unavailable and continue the permitted evidence review.
- Apply the explicit-time-limit delivery procedure in the RIS research-exploration reference. Publish the current supported answer at its checkpoint. Release the candidate to the Auditor after the required scope freeze while other independent work continues.
- Route audit failures to the owner of the affected work. Reopen only affected tasks and downstream items invalidated by the correction.
- Stop repeating an unchanged check when no new evidence, discriminating analysis, corrected input, or changed assumption is available; record a low-value deferral or the specific blocking boundary and reopening condition, and continue independent ready work.
- When integrating a decision-bearing finding into a shorter answer, use the original verifying roles’ marked returns. Reconcile their measured scope and limiting conditions against the intended answer before rendering. Use the RIS delivery helper on the reviewed passages and return the checked wording. Keep verified facts, calculations, assumptions and user decisions distinct.

For knowledge-centric work follow the RIS reference `adaptive-system.md`. Search current project
findings/studies at intake, route important discoveries to their canonical owner at observation,
and reconcile the actual role return, integrated record and final draft with independently
reconstructed requirements. Under significant recording do this during research. Use only
authorized records under a restricted policy. A project switch requires a clean scoped context.
Treat a missing protection, resource measurement or uncertain external effect as a scoped stop.
The user may delegate, participate, change modes or correct a claim at any point.

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
