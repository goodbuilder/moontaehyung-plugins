# Architecture refresh contract

This contract governs explicitly requested Archify refreshes of an existing project architecture reader and the lightweight status records emitted by `modify-gui` and `verify-check`. It keeps project-specific source authority and verification requirements alongside Archify rendering.

## Archify refresh boundary

Use Archify's `architecture` mode for the visual map and its `explainer` mode only when a one-page explanation is requested. For an existing project reader, establish the project paths and accepted source facts first; do not move or replace established outputs merely to follow Archify's default `.archify/` output folder. The explicit reader-refresh request is separate from ordinary code or GUI edits.

## Separate artifacts

Keep these purposes distinct:

| Artifact | Purpose | Editable authority |
|---|---|---|
| Current architecture Markdown or registry | What the project structure means now | Yes |
| Current architecture HTML | Single external reader for a non-expert and reviewer | Generated from the authority |
| Archify candidate JSON and exported figures | Diagram rendering source and visual maps | Project registry/Markdown is semantic authority; candidate JSON is an editable render input; HTML/SVG/PNG are generated |
| Change `explanation.md` | What changed, why, alternatives, and residual risk | Yes, per change packet |
| Change `verification.md` | Commands, observations, environment, and status | Append-style ledger |

The HTML and Archify candidate are not replacements for the project's semantic source of truth. If the project has no structured registry, an explicitly requested refresh may create the smallest repository-relative one; keep the Archify candidate focused on rendering and links back to accepted facts.

## Minimum node record

Use stable IDs and explicit fields. YAML, JSON, or a project-native equivalent is acceptable.

```yaml
id: OWN-01
name: Measurement controller
kind: owner
plain_role: "측정 요청을 받고 필요한 자료를 모아 계산을 시작한다"
role: "Admits observations and owns the measurement run boundary"
owner: measurement
inputs: [observation_pair, pose, calibration]
outputs: [method_result, status, evidence_event]
failure_isolation: "A failed method does not erase diagnostics or other runs"
source: apps/Workstation/measurement_view_controller.py
modes: [live, saved-evidence, offline]
layout_group: runtime-owners
```

An edge record should identify the relation rather than merely drawing a line:

```yaml
from: BND-01
to: OWN-01
relation: command
view: primary-runtime
label: "validated command"
```

Roles, ownership, failure boundaries, coordinate frames, axis order, units, clocks, and
truth-versus-estimate meaning are semantic facts. Do not derive them solely from visual proximity,
Python import order, or a variable named `x`, `y`, or `z`.

## Non-expert HTML completion criterion

The first reader must allow a person who does not know the project to explain, without opening
source code, Markdown, or individual figures:

```text
person asks
  → screen receives the request
  → the system gathers the needed material
  → it checks and calculates
  → it shows success or the reason for failure
  → it saves the result and its supporting evidence
```

The generated reader must contain, in plain language before technical detail:

- a one-paragraph purpose statement;
- a numbered or clearly directed request-to-result flow;
- a sufficient-data/sufficiently-invalid-data branch;
- one concrete example of a normal operation;
- a short glossary for terms introduced later (`owner`, `worker`, `status`, age/freshness,
  snapshot, evidence, artifact, frame, method, provenance, and rebuild when used);
- an explicit statement that a button click or `VALID` label is not by itself proof of accuracy;
- a link to the technical maps and the per-change explanation.

Technical metadata may remain in the reader, but it must not be the first explanation a novice
encounters.

## Visual map contract

Use the smallest set of maps that explains the requested structure:

- system context: actors, application boundary, external inputs, and artifacts;
- primary runtime ownership: UI/boundary/owner/core handoffs with avoidable crossings removed;
- command/status: intent, handler, observed result, visible status, and evidence;
- lifecycle: start, busy, run, stop, error, and recovery transitions;
- data/evidence: source data, frozen input, result, journal, projections, and rebuild.

When a primary map drops duplicated or secondary edges to remain legible, the reader must point to
the map/table where those edges remain. Never silently remove a required dependency.

Run Archify's `finalize` workflow for its schema, delivery, and browser checks. When the request or project contract calls for perceptual review, inspect the delivered HTML at normal and narrow widths and check for clipped labels, missing edges, overflow, and avoidable crossings. A failed visual check remains a failed ledger entry until superseded by fresh evidence.

## Lightweight stale record

`modify-gui` and `verify-check` should record only this small status when an architecture-affecting
change is made and the user did not request a refresh:

```yaml
architecture_refresh:
  status: NOT_REQUESTED
  risk: LOW | MEDIUM | HIGH
  affected_nodes: [OWN-01, BND-01]
  reason: "owner/command/state/contract changed" 
  suggested_command: "Use $archify to refresh Workstation's architecture reader."
```

Use `NOT_APPLICABLE` for changes with no architecture-facing contract or ownership impact. Use
`REQUESTED`, `IN_PROGRESS`, `PASS`, `FAIL`, `BLOCKED`, or `NOT_RUN` only when the explicit refresh
workflow actually reaches that state. Do not turn `NOT_REQUESTED` into a hidden failure or run the
full browser review automatically.

## Audit entry minimum

Every explicit refresh adds an entry containing:

```text
refresh_id / scope
source of truth and affected node IDs
before revision or snapshot -> generated artifact identity
commands and visual observations
environment: automated / visual-manual / hardware-manual / unverified
status: PASS | FAIL | BLOCKED | NOT_RUN
changed files and separate explanation link
complexity: KEEP | REMOVE | DEFER
residual risk and next action
```

Write the packet state last. A full refresh does not authorize application behavior, schema,
device, or plugin changes that were not requested.
