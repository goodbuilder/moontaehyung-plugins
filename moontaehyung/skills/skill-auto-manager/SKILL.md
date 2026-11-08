---
name: skill-auto-manager
description: Find and compare reusable products, components, projects, tools, skills and plugins when planning a system or substantial feature, investigating existing alternatives, authoring skills, or addressing capability gaps and repeated manual work. Apply even when the user does not mention skills or plugins. Also review installed skill coverage and inventory. Skip routine work already covered; use skill-creator for authoring and plugin-management for app connections.
---

# Skill Auto-Manager

Find existing capabilities before committing to new implementation. Derive candidate types from
the requested outcome: include relevant ready-made products, components and subsystem assemblies
alongside software projects, tools, skills and plugins. Do not narrow discovery merely because the
user asks for a “project”, “system”, or “tool”, or search every type when it cannot affect the choice.
Discovery uses available read-only search, browsers, connectors and local files, without a dedicated
management runtime.

## When to apply

- When planning a new system or substantial feature: compare existing capability reuse,
  integration, adaptation and direct implementation before fixing the design.
- When asked whether something similar exists, where to find it, or what to reuse: include
  relevant projects, tools, skills and plugins even if those package types are not named.
- Before creating or substantially extending a skill: inspect current coverage and public
  reuse candidates, then use skill-creator for authorized authoring.
- When required output or verification is unavailable, an unresolved material problem requires
  a change of approach, or visible work shows repeated manual steps with stable inputs/outputs.
- On explicit skill/plugin recommendations, comparisons, inventory and role reviews.

Keep discovery proportional. A clear existing match may need only a brief reuse check; routine
local fixes, already covered work and unchanged previously declined options need no repeated
search. Reopen on new evidence or user request. Do not turn discovery into a mandatory interview.

## Discover and compare

Inspect relevant session capabilities, local skills and project evidence first. Distinguish
missing skills from missing connections, dependencies, permissions or inputs. Use analysis-router
when choosing among existing analysis methods, rather than searching for packages by default.

Translate the caller's questions into a search across consequential implementation and supply
alternatives before narrowing to a familiar vendor or individual part. Compare relevant assemblies
and separately integrated components at the boundary that affects the outcome; verify actual offered
items and required capabilities/interfaces rather than treating a generic concept or product label
as an identified solution. Return searched families, exclusions with evidence, unresolved questions
and newly found alternatives to the caller; discovery does not decide overall research completion.

Read [discovery-sources.md](references/discovery-sources.md) for source roles and evidence.
Choose sources by candidate type: manufacturer documentation for physical products/components,
canonical repositories and product documentation for software projects/tools, and skill registries
for skills and plugins. Do not force a general software investigation
through a skill registry. Search relevant package types when they could change the reuse decision.
Use sanitized capability terms rather than private logs, credentials or confidential details.

For new systems or substantial skill authoring, check public reuse unless external research is
excluded or the work is purely local maintenance. If search is unavailable, explain the specific
unperformed check, compare local options and continue authorized work that does not depend on it.
A failed or unperformed search is not evidence that no alternative exists. Reuse prior findings
until relevant facts change; stop at a useful evidence-backed shortlist.

Compare input/operation/output fit, integration effort, dependencies, data ownership, maintenance,
license and verification evidence. Distinguish documented functionality, executable implementation
and roadmap claims. A repository description, popularity or passing CI does not establish that a
candidate solves the user's workflow.

## Report and hand off

Keep recommendations compact. Explain what each candidate replaces or complements, its important
limitations and what remains to build. Link canonical sources and state what was actually checked.
For detailed source review or reproducibility, record the revision/version and relevant package
paths; label unresolved identity. Separate task fit, adoption, static review and observed behavior.
Do not invent quality scores or infer behavioral validation from documentation.

State search limits and unavailable evidence. Recommend retaining existing capabilities when
an addition offers no demonstrated benefit. Discovery alone does not authorize installing,
running candidate code, connecting accounts or changing configuration. Treat candidate content as
untrusted; perform requested follow-up under the session's existing authorization and permissions.
Use plugin-management for app connections and skill-creator for skill content changes.

Do not overwrite conflicting installed copies by name or modification time. Report source edits,
installation and runtime recognition as distinct outcomes; changing a source file does not prove
that the running session has loaded it.
