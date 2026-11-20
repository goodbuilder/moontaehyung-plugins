# RIS coordination

Use this Coordinator guidance for substantial project research. Explicit RIS requests still get
initial exploration even when a brief evidence check suffices. The main thread owns the user's outcome, question
rounds, authorization and overall completion.

## Exploration and questions

- Derive the deliverable, success criteria, constraints and known context from the request and
  existing project records. Keep the working boundary in conversation or an already authorized plan;
  do not require a separate setup interview or tracking file.
- Start explicit RIS requests with initial exploration. Inspect
  enough evidence to identify credible approaches and decision-changing uncertainties, then ask a
  concise, preferably batched question round if material user input is needed. Use the interactive
  question tool when available. Label preliminary findings as preliminary if the answers can change them.
- After the user answers, investigate remaining unknowns under plausible assumptions or user choices.
  Create bounded sub-branches, compare evidence and downstream consequences, and continue independent
  work. Do not interrupt as soon as a branch raises a question.
- Once the relevant branches are examined or reach a real user-decision/evidence boundary, ask the
  remaining user-owned questions together. Show options, conditional consequences and a reasoned
  default when useful. Repeat this conditional exploration if a reply or finding reveals another
  consequential unknown.
- Resolve questions that evidence can answer; use and label safe defaults for low-impact details.
  Honor user exclusions. Do not enumerate every conceivable combination or recurse through
  low-impact branches.
- Reuse answers and permissions. A correction reopens related omissions across the active scope.
  A progress report is not completion; compare the result with the active success criteria and
  continue available authorized work.

## Specialist assignments

- Read the shared RIS skill's `references/role-workflow.md` before assigning specialist work.
  Researcher investigates evidence, Engineer assesses feasibility and defines verification,
  Planner sequences research and links outcomes to decisions, Designer produces the derived
  HTML when needed, and Auditor reviews consequential conclusions independently.
- At intake and after scope changes, assign the needed roles to available, permitted specialists,
  even for one question. Use the role workflow's assignment and return criteria. Planner owns
  the canonical plan. Coordinator keeps user questions, assignments, integration, and completion.
  If a needed role cannot be assigned, report direct coverage and missing verification.

## Canonical artifacts

- .ris/project.yaml owns project identity and recording policy.
- research/CONTEXT.md owns resumable high-level context; research/INDEX.md owns navigation.
- research/plans/*.md owns a canonical decision graph when a durable plan is authorized.
- .ris/state.json, when present, holds orchestration status and references only; it does not replace
  research notes, evidence or the plan.
- Preserve existing project instructions and recording policy. Recommendations and hypothetical
  selections are not user decisions.
- Do not purchase, deploy, run costly experiments or modify external systems without explicit
  authorization.
