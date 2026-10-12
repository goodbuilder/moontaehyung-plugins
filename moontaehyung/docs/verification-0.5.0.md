# 0.5.0 auto-subagents extraction — 2026-10-10

## Scope and design

Extract the approved selective delegation procedure from verify-check into a focused
auto-subagents skill. Initially route verification, boundary-maintenance investigations,
and task-outcome RCA evidence collection to it. Keep caller acceptance and domain decisions
with their existing owners. Normal implicit discovery remains enabled.

The package source is authoritative for shared delegation; the new skill and focused edits
are also synchronized into the existing personal installation. Personal/plugin-specific
reference layouts, complexity policy, and explicit-only architecture refresh remain intact.
The system skills are not changed. No hooks, MCP servers, new runtime scripts, model changes,
or personal harness are introduced.

## Documentation basis

- [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents): applicable
  skill instructions can request delegation; independent contexts, scoped assignments,
  and concise results are useful; extra agents can consume more tokens.
- [Build skills](https://learn.chatgpt.com/docs/build-skills): focused descriptions,
  implicit discovery, instruction-first packaging, and testing trigger behavior.
- [Skill evaluation](https://developers.openai.com/blog/eval-skills): evaluate actual
  outcomes and execution traces, not just text or successful frontmatter validation.

The usual one-or-two-agent size, caller routing, and no-further-delegation rule are local
design choices, not OpenAI platform limits. Delegation is not tied to Luna or Fast.

## Verification ledger

### Structure and preservation — PASS

- Official `skill-creator/scripts/quick_validate.py`: all 8 packaged and 11 personal
  candidate skills passed. All 54 package-local Markdown links resolve.
- Manifest version is 0.5.0; eight skill entrypoints exist. New personal/package
  `auto-subagents` files match, and implicit invocation is enabled.
- Inverse comparisons confirm that all six existing consumer copies differ only in
  the intended delegation section/insertion. Their domain criteria, coordinate contracts,
  oracle requirements, GUI authorization, and other instructions remain byte-for-byte intact.
- Existing `update-architecture` metadata, including explicit-only policy, is unchanged.
  Unrelated files are preserved; synchronization applies only the enumerated changed/new files.

### Independent forward tests — observed results

Tests used isolated fixture-r17 under a temporary directory, with no Workstation runtime,
network, hardware, production data, or source fixes. Evaluators received the request,
skills, and raw artifacts, without seeded diagnoses or expected delegation counts.

| Request | Observed behavior | Result |
|---|---|---|
| Read one configured value | Returned `max_workers=2` with local file reads and no subagents or mutations. | PASS |
| Review a tab-generation and export-failure incident through maintain-boundaries and RCA | Coordinator automatically spawned one native export investigator while investigating tab provenance itself; reused the completed assignment across verification and RCA. | PASS for scoped delegation and handoff |
| Same fixture with an explicit user prohibition on subagents | Used direct offline checks; reproduced the export failure; no child agents or source changes. | PASS |
| Continue the completed review using its existing record | Reused the completed assignment and results; verified six source hashes; no new delegation, test reruns, source changes, or extra report. | PASS |

The incident review correctly preserved both failed acceptance criteria: a stale job was
relabeled with the current tab generation; an export returned success/count two despite
only one of three supplied rows being acknowledged. It distinguished contrary evidence,
unknown pre-refactor history, and proposed fixes from executed fixes. Three passing baseline
tests were correctly treated as insufficient. Child completion was not treated as product PASS.
Only the pre-existing `task-notes.md` record changed; all fixture source/test hashes remained
unchanged, no second report was created, and the worker did not delegate further.

One inefficiency was observed: both coordinator and worker ran the same small baseline suite.
The final brief guidance now explicitly includes work already covered or assigned elsewhere.
The full incident evaluation was not repeated after this wording change, so improved duplicate
check avoidance is not claimed as a measured result.

### Limits

- Native delegation was executed after loading the caller/companion skill. Fresh-session
  implicit discovery and an environment with physically unavailable delegation tools were
  not executed; metadata and local fallback instructions were inspected.
- Competing writes/devices, cancellation, model-specific behavior, and all runtime permission
  combinations were not exhaustively exercised. Tests were read-only source investigations.
- No old/new performance benchmark or aggregate token accounting was collected. This release
  does not claim lower tokens, time, or superior quality; delegation still has overhead.
- Plugin installation, activation, publishing, and production/hardware use were not performed.
  This updates the packaged source and personal skill files only.

Coordinate contract checked: instruction-only delegation extraction; caller coordinate,
axis, unit, schema, and verification contracts remain authoritative. No application change.
