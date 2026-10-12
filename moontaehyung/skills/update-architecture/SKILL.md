---
name: update-architecture
description: Refresh a project's current architecture documents and non-expert HTML reader only when explicitly requested, preserving separate change explanations and verified evidence.
---

# Update Architecture

Refresh the current architecture view of a desktop operator application when the user explicitly
requests an architecture update. This is an external documentation workflow, not an in-app
architecture viewer and not an automatic post-edit hook.

Read the shared [architecture refresh contract](../../references/architecture-refresh.md) before
starting. It defines the manifest fields, novice-reader acceptance criteria, stale-status record,
and audit entry shape.

## Invocation boundary

Use this skill only after an explicit request such as:

```text
$update-architecture Workstation
Workstation 아키텍처 HTML 갱신해
```

Do not invoke it implicitly for every GUI edit. `modify-gui` and `verify-check` may record that an
architecture refresh is needed, its risk, and its affected nodes, but they must not regenerate the
reader unless the user requests this skill. A presentation-only typo or spacing change normally
needs only the ordinary document check unless the user asks for a full refresh.

## Outcome

Leave a truthful, repository-relative current view with these separate layers:

1. a plain-language first-read explanation for someone who does not know the project;
2. visual context, ownership, command/status, lifecycle, and data/evidence maps;
3. a node catalog explaining each architectural and flow/state node;
4. source, owner, input/output, failure boundary, mode, coordinate/time, and provenance references;
5. a separate change explanation describing what changed and why.

The current view is an `as-is` snapshot. Do not turn it into a target architecture, live runtime
dashboard, or generated import graph without explicit scope.

## Workflow

### 1. Establish the refresh baseline

- Resolve the repository root and read applicable `AGENTS.md` files.
- Read the active architecture change packet, its `state.md`, current `verification.md`, and the
  current architecture Markdown/HTML before editing.
- Record the observed revision, dirty-worktree qualification, current reader paths, and the
  change packet or user request that authorizes this refresh.
- Locate an existing project manifest/registry or generator. If none exists, create the smallest
  project-owned structured registry described in the shared contract; do not infer durable roles
  only from imports.
- Preserve Workstation application source, runtime settings, device state, and unrelated changes.

### 2. Update the authoritative facts

Prefer this order of authority:

1. accepted product/contract documents and the current change packet;
2. explicit project architecture registry or manifest;
3. current source and tests for names, callers, owners, persistence, and observed boundaries;
4. runtime evidence when the user explicitly includes live qualification.

For every changed node or edge, keep a stable ID and record its role, owner, inputs, outputs,
failure isolation, source path, and whether it belongs to live hardware, saved-evidence, replay,
simulation, or offline validation. Treat role and ownership as explicit facts requiring review;
AST/import discovery may find candidates but cannot decide their meaning.

Keep layout hints separate from semantics. Use stable groups, ranks, ports, or primary/secondary
views to reduce edge crossings. If a relationship is omitted from a primary map for readability,
represent it in the context map, flow map, table, or catalog and say where it moved.

### 3. Generate the reader and figures

- Keep Markdown or the project registry as the editable source; do not hand-edit generated HTML
  or generated SVG/PNG when a generator exists.
- Generate the external HTML reader, DOT sources, and rendered SVG/PNG figures using repository-
  relative paths and no unnecessary remote resources.
- For Graphviz SVG used by Firefox, prefer the Cairo backend when the ordinary renderer causes
  `viewBox`/transform clipping. Preserve the render command in the figure-source README.
- Embed the beginner explanation before technical metadata, graphs, or code names. Keep technical
  metadata available but collapsed or clearly secondary.
- Link the HTML reader, Markdown source, change explanation, figure source, and representative
  source files from the repository index where the project already has one.

### 4. Verify in proportion to the request

Always run the cheap checks after generation:

- HTML parsing, unique section IDs, local link/image existence, and no accidental remote dependency;
- generated node IDs and edges resolve, source paths exist, and manifest/reader counts agree;
- JavaScript/CSS syntax when the reader has interaction;
- `git diff --check`, the repository portability check, and the smallest relevant documentation
  or project tests.

For an architecture or reader refresh, also open the actual HTML in Firefox (or the project's
documented browser) and check at a normal and narrow width:

- the complete beginner flow is visible and readable;
- the success and insufficient-data branches are understandable;
- each figure is complete, labels are not clipped, and lines do not create avoidable crossings;
- the node catalog exposes role, input/output, ownership/failure, and source without forcing a
  separate image or code file;
- fit/readable controls remain inside the same document and do not create page-level overflow.

If the browser or display is unavailable, record `BLOCKED` or `NOT_RUN` with the exact reason.
Do not call a static parser a visual pass.

### 5. Record the refresh

Append the actual commands, screenshots or visual observations, changed node IDs, generated
artifact identity, environment, status, residual risk, and complexity decision to the active
packet's `verification.md`. Update the separate `explanation.md` with the before/after reader or
architecture delta. Write `state.md` last, preserving the next question and `implementation_allowed`
boundary.

Do not fold the change history into the current architecture document. The current document says
what is true now; the change explanation says what was changed in this refresh.

## Stop conditions

Stop and record an unresolved condition when:

- source, tests, and architecture documents disagree about an owner or contract;
- a proposed layout would hide a required relationship without a second representation;
- a node's role cannot be established from accepted documents, source, or evidence;
- the requested refresh would require application-source, schema, device, or plugin behavior
  changes outside the explicit documentation scope;
- the non-expert completion criterion cannot be verified in the available browser environment.

Ask for direction only when resolving the conflict would materially change the current view or
expand the requested scope. Otherwise leave the fact and next action in the packet.
