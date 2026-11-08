# Discovery sources and evidence

Use these as source roles, not hardcoded API contracts or endorsements. Verify current URLs,
search availability, authentication and terms at use time; use permitted read-only web search
restricted to a source domain when no native search is accessible. Never bootstrap a package
runner, execute candidate instructions/scripts, enable accounts, or install a candidate merely
to research it. If a source is inaccessible, state the gap and try another appropriate source.

| Source | Role | Evidence to collect |
|---|---|---|
| [skills.sh](https://skills.sh/) | Discover skills by capability, topic and adoption | Exact skill/source identity, installation metric and its definition, trend if available, audit provider/date/scope |
| [SkillsMP](https://skillsmp.com/search) | Broaden task-oriented discovery and aliases | Canonical skill path, description/full payload links, source freshness and duplicate listings |
| [Tessl](https://tessl.io/registry) | Look for separate quality, impact and security evidence | Reviewed version; rubric; evaluation tasks/model/baseline and scenario count where exposed; scan provider/date; explicitly missing evidence |
| [ClawHub](https://clawhub.ai/) | OpenClaw-specific automation and registry-native packages | Publisher, version, dependencies, platform compatibility, usage metrics and scan details; no assumed Codex portability |
| [GitHub](https://github.com/) or canonical source host | Confirm provenance, maintained payload and adoption | Exact revision/path, license, relevant resources, stars/forks, maintenance and independent usage |
| Relevant community discussions | Corroborate real use and limitations | Specific task/outcome, independence from author, date and repeated observations; label anecdotes and promotional posts |

## Search and stop
1. Translate the evidenced gap to sanitized capability terms and useful aliases. Match input,
   operation, output and constraints, not only skill names.
2. For projects and tools, start with canonical repositories and official documentation; use
   community sources to discover candidates and corroborate use. For skills and plugins, check
   skills.sh and SkillsMP as primary discovery points. One can suffice for a clear match;
   use the other for weak/empty/ambiguous results, authoring-reuse comparisons or an explicit broad
   search. Include ClawHub when OpenClaw is relevant, not for unrelated tasks.
3. Deduplicate mirrors and package variants by canonical identity. Inspect the strongest matches
   at source. A directory listing is not independent confirmation of its copied claims.
4. Consult Tessl where a candidate is indexed and evaluation evidence could affect the choice;
   otherwise record evaluation evidence unavailable. Resolve revision differences before transferring
   a score or scan to the version under consideration.
5. Verify community adoption alongside fit. Always distinguish repository-wide stars/forks from
   individual skill installs/usage. For a skill in a large collection, collection stars are only
   context; do not attribute them to that skill. Preserve unknown metrics, avoid fixed popularity
   thresholds that exclude niche tools, and do not invent growth from a single snapshot.
6. Stop at an actionable shortlist, or explain uncovered constraints and bounded search limits.
   Do not claim no candidate exists globally. Recommend retaining existing capabilities when
   additions do not offer a demonstrated benefit. Reuse prior results until relevant facts change.

## Recommendation and validation labels
For each recommended candidate report what it helps with, why current coverage is insufficient,
source/version/path (or explicitly unresolved identity), dependencies and burdens, source links,
observed adoption with date/scope, important caveats and what was actually verified. Keep user-facing
summaries short; show detailed evidence for requested comparisons or consequential installation.
Separate four evidence dimensions rather than presenting a popularity-derived quality score:

- **Fit:** inspected instructions/resources support the needed input/operation/output and constraints.
- **Adoption:** installs, stars, forks and independent task reports, each with source and scope.
- **Static review:** reviewed payload/resources and explained permissions; formatting and scanner
  checks establish only their checked properties, not safety or functional correctness in general.
- **Behavior:** reproducible task execution and comparison with the current method under a named
  model/environment/version; report not-run rather than inferring this from prose, CI or a scan.

Use `discovered`, `source-reviewed`, `behavior-tested`, and `locally-confirmed` only as supported:
source-reviewed requires relevant full-payload inspection; behavior-tested requires recorded actual
execution; locally-confirmed additionally requires installed-runtime recognition and an applicable
workflow check. These are evidence labels, not a guarantee of general performance.

Before claiming task-time recommendations work, test both invocation/selection and execution.
Explicit requests alone do not prove proactive recall. Include implicit gap checkpoints, negative
cases already covered, missing search tools, and ambiguous methods versus missing inputs. Use
fresh isolated contexts and task-specific expected actions without leaking the answer. A simulated
catalog trial validates only the scenario; it does not prove live provider compatibility. Candidate
execution or installation still requires the applicable authority; discovery alone does neither.

Source guidance checked during the 2026-11-01 investigation:
[skills.sh documentation](https://www.skills.sh/docs),
[SkillsMP search](https://skillsmp.com/search),
[Tessl registry](https://tessl.io/registry), and
[OpenClaw skills documentation](https://docs.openclaw.ai/skills).
No provider's inventory size, score scale or endpoint is assumed permanently stable.
