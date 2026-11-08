# Markdown graph contract v1

A canonical plan is Markdown with exactly one fenced `project-plan` JSON block. Never store a second
editable graph JSON: the renderer embeds the parsed data in the generated HTML. RIS plans retain their
managed frontmatter (ris_id, project_id, kind, created). Keep plan_id stable across revisions.
For autonomous exploration, use [the expanded synthetic example](../assets/research-plan-expanded-example.md) to understand multi-family, multi-stage structure, not as research evidence or a node quota. The smaller research-plan-example.md is only a minimal format/browser fixture, not the expected investigation depth.

Required graph fields: `schema_version: 1`, `plan_id` (unique stable string), `goal`, `nodes`, `edges`.
Optional: `current_node`, `revision`, `sources`, `incompatible`, `candidates`, `current_candidate`.
- Nodes: unique stable `id`, `kind` outcome/decision/milestone/gate, `title`, `status`:
  unexplored/provisional/confirmed/deferred/rejected/superseded. Outcome IDs use O-###, decisions D-###,
  milestones M-### and gates G-###. Node IDs are scoped by plan_id; cross-project records are links.
- Outcomes require `success_criteria`. Decisions require at least two `options` or an
  `alternatives_limit_reason`. Options have unique IDs within a decision and required `title`,
  `forecast`, `conditions`, `resources`, `risk`, `uncertainty`, `verification` strings; `evidence`
  is a list of source IDs (empty means evidence unavailable, explicitly displayed).
- `selection_mode` is `single` (default, mutually exclusive options) or `multiple` (compatible options
  may coexist). `selected` accepts a legacy scalar ID or a list of IDs, checked against this mode.
  It is the legacy recorded decision and requires `selection_reason`; confirmed decisions require it.
  Recommendations remain separate descriptive fields. Optional `revisit_when` and `needs_review`
  describe the trigger/affected assumptions. Preserve history before changing selections/forecasts.
- Edges: `from`, `to`, `relation` CHOOSE/AND/IF. Optional `option` activates the route for a specific
  option at the source node. IF requires `condition`; it is not automatically passed by simulation.
  Shared downstream nodes use one ID. Cyclic fallback routes display as references, not infinite trees.
- `sources` maps IDs to `title`, `locator`, `retrieved` date, `review_scope`. Use verified HTTP(S),
  Zotero/Obsidian links or textual local locators. Local paths are shown as text for portable offline
  reading; the agent follows them from the canonical project. Do not put private content in exports
  beyond the scope already authorized for the plan.
- Optional `observations` per node: list of `date`, `result`, `difference`, `evidence` descriptions.
  Put detailed methods/units/version/conditions in linked findings. Optional `estimates` per option:
  list of numeric `value`, `unit`, `derivation`, `conditions` and `source` ID.
- `incompatible`: list of pairs of [node ID, option ID] tuples. Simulations warn about declared
  conflicts within the active candidate; each recorded candidate is checked independently. Choices
  from different candidates are never combined for conflict checks. Lack of a declared conflict is
  not proof of feasibility. Combinations are not scored.
- Keep append-only dated decision/forecast history in the Markdown body, including prior state,
  reason, authority, evidence, affected nodes and supersession. Backups are additional protection,
  not a substitute for readable history.

```bash
python3 <installed-project-plan>/scripts/project_plan.py --project <root> check research/plans/<plan>.md
python3 <installed-project-plan>/scripts/project_plan.py --project <root> render research/plans/<plan>.md --output research/plans/<plan>.html
```

The renderer requires no RIS install, server, network, Node runtime or third-party Python package.
It validates references and escapes content; it does not validate research truth. It only replaces
an HTML file carrying its generated marker. It shows source hash/time; it cannot watch local files.
After edits, rerender and reload. Copy investigation requests from the map to the agent conversation.
No browser selection writes to the source or creates a confirmed decision.

## Exploration coverage audit

```bash
python3 <installed-project-plan>/scripts/project_plan.py --project <root> audit research/plans/<plan>.md
```

`check` and the HTML header also report unique decision/option counts, expanded option count,
maximum decision stages on shortest outcome paths, and unexplained option frontiers. Counts are
structural diagnostics, not quality scores or minimum quotas. Shared AND children alone do not
show which consequences differ by option: add option-specific routes or an explicit boundary.
Optional `exploration_frontier` entries use `node`, `option`, `reason`, `next_action`. Explain real
terminal/evidence/intent/constraint boundaries; "not yet selected" or "more research needed" alone
is insufficient. The audit validates references and presence, not the truth of these explanations.
Preserve full candidate inventories in the canonical record and group/fold them for readability.

## Candidate bundles and reusable options

A candidate is a complete or partial solution bundle referencing existing decisions/options. Options
are not consumed, assigned a single owner, or globally deduplicated across candidates. The same
[node ID, option ID] may appear in arbitrarily many candidate bundles. Two candidates may share all
but one choice, or initially be identical during exploration. Definitions keep stable IDs; references
repeat. Never force disjoint option pools merely to make candidates look different.

```json
{
  "candidates": [
    {"id": "C-001", "title": "후보 A", "selections": {"D-001": ["rgb"], "D-002": ["public"]}},
    {"id": "C-002", "title": "후보 B", "selections": {"D-001": ["rgb"], "D-002": ["flight"]}}
  ],
  "current_candidate": "C-001"
}
```

Candidate IDs are unique within a plan. Selection values are lists of option IDs; legacy scalar
values are accepted. Each key must be an existing decision; options must exist in that decision.
A single-select decision permits at most one option in each candidate, independently of all other
candidates. Multiple-select decisions permit several distinct compatible options in a candidate.
Declared incompatible pairs remain invalid within one candidate, including multiple selections in
one decision. Repeated IDs within a single selection list are errors, not candidate-reuse limits.
An omitted decision means undecided; it does not inherit a different candidate's choice.

Existing plans without candidates show a default candidate based on legacy node `selected` fields.
The browser maintains overrides per candidate. Adding/cloning/switching candidates does not consume
options or change another candidate. Reset restores only the active candidate's original bundle.
Comparison columns repeat common choices. Clones contain independent selection arrays.
Candidate edits are hypothetical until explicitly recorded through the conversation; the copyable
request includes all current bundles so the agent can persist them to the Markdown graph when asked.
Preserve candidate IDs and prior selections/rationale in append-only history when committing edits.
A candidate combination is a hypothesis, not evidence that all its choices are jointly feasible.

## Separate catalog and candidate views

The HTML opens on **구성요소별 선택지**: every decision axis appears as a component with its full
option inventory, forecasts, evidence and downstream relations. Optional node `component` is a
nonempty display label (for example 데이터 확보); it falls back to the existing decision question.
This is a display label, not a new node identity or an inferred system-module boundary. Existing
outcome nodes and graph dependencies remain intact. Catalog browsing is read-only and independent
of which candidate is active. Its investigation request covers the component rather than silently
including a candidate acceptance request.

**후보 구성·비교** contains candidate switching/add/clone/reset, a matrix of all components against
candidates (including unselected cells), and candidate-local selection controls. Clicking a matrix
cell opens that exact candidate and component. A catalog action can move to the same component in
the candidate editor without changing any choice. Switching views preserves all candidate overrides,
multiple selections and current component. Keyboard arrow/Home/End navigation operates the tabs.
Canonical selection references, legacy compatibility and read-only browser persistence are unchanged.
