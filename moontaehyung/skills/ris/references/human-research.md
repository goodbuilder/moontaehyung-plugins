# Human research integration

A user may switch `delegated`, `assist` and `collaborate` at any turn. These are
responsibility preferences, never permission to change goals, constraints, spend,
send, or run experiments. Preserve the user's intent and attributed contributions
in the selected project context; compare them with evidence and constraints before
synthesis. Conflicts with consequential implications require a user decision.
`ris learning session --mode … --intent … --contribution … --view …` returns this
turn's contract without reading a profile or writing a project. Its output contains
project-local text and must stay in that project, never in a general profile.

`researcher` shows evidence, uncertainty and the next decision. `designer` shows
alternatives, dependencies, tradeoffs and verification criteria. `teach-me` explains
a general concept and invites a concrete demonstration. A plausible response or
agent inference is not proof of ability. Actual demonstration may be recorded as
confirmed only when the user explicitly confirms the ability assessment; a CLI
flag records that attestation, not independently verified cognitive competence.

## Optional general profile host interface

There is no default profile, home-directory discovery or automatic extraction.
A trusted host must provision an existing user-owned mode-0700 directory outside
all projects via `RIS_LEARNING_PROFILE_ROOT`. Only its fixed
`learning-profile.json` is accepted through `--profile`. This environment channel
must be inaccessible to untrusted workers; do not forward worker-selected values.
The host obtains
separate informed consent with `create --consent general-concepts-only-v1`.
Explain before consent that only six general concept labels, five dimensions (definition, explanation,
calculation, application, limits), four levels, four evidence categories and a
general confirmation time are stored. Consent does not cover project histories or content.
The file must be outside project knowledge/history ingestion roots, selected and
protected by the host. Never pass its path to a project KB reader.

`inspect` exposes every stored field and its hash. `set --expected-hash HASH`
changes a single bounded concept dimension via `--dimension`. Unknown requires
none; learning allows self-report/inferred; practiced requires self-report;
confirmed requires user-confirmed demonstration. Teaching is never compulsory. `confirmed` requires
`--evidence demonstration-confirmed-by-user --user-confirmed`. `delete
--expected-hash HASH` removes the entire selected file and revokes recorded consent.
No content, identifiers, project timestamps, URLs, source references, arbitrary concept
names or free-text fields are accepted. A general UTC confirmation time is
generated only for explicitly user-confirmed demonstrations; no lesson/event log
is stored. The host may pass only the validated
bounded payload for adapting explanation depth. The profile access path has no project
reader or KB callback; the project KB must never use it to discover history.

This is a bounded local file interface, not a process security sandbox. A host
with unrestricted filesystem privileges could bypass it; enforce actual access
isolation separately when making a security claim. Cooperative calls serialize
using an advisory parent-directory lock; this does not defend against an attacker
replacing paths outside the protocol. No automatic ability update, consent inference,
project import, background profile lookup or profile-derived execution authority
is provided. General concept preferences cannot establish domain expertise.

## Project-local contribution integration

`learning contribute --input contribution.json --expected-hash CONTEXT_SHA256`
updates only the existing canonical `.ris/research/CONTEXT.md`, using the normal
project note CAS/history primitives under one project lock from policy read through
commit. The payload must bind the exact selected `project_id`; a policy reduction
before commit blocks an unauthorized write. It creates no new goal authority or global memory.
For manual/restricted policies, include explicit `--authorize-record`. Read the
current CONTEXT hash from `context` before writing; stale input fails without a
partial append. The input is project-relative JSON with exactly these fields:

```json
{
  "project_id": "Exact ID from the selected project configuration",
  "attributed_to": "User-selected attribution",
  "contributor": "user",
  "intent": "Compare options under the present research question",
  "purpose": {"status": "USER_STATED", "text": "Understand the measurement limits"},
  "constraints": ["No real experiment"],
  "hypotheses": ["Timing may be irregular"],
  "observations": ["The selected rows have no timestamps"],
  "decision": {"kind": "USER_DEFERS", "reason": "Need more evidence"},
  "goal_change": null
}
```

`contributor` is user or agent. Purpose is `USER_STATED`, `INFERRED` or `PROPOSED`;
an agent cannot claim `USER_STATED` or assert a user decision. Decisions are
`NO_DECISION`, `USER_ACCEPTS`, `USER_REJECTS`, `USER_DEFERS`. These are attributed
records, not authenticated identity or independent scientific observation.
Hypotheses and observations retain attribution with an explicit unverified stamp.
Constraints are input to the existing goal/HARD-constraint decision process, never
silently adopted constraint changes. A timestamp and exact CONTEXT preimage hash
identify the contribution; safe-update preserves the prior canonical note.

To change the current research goal, provide its exact text in `goal_change`,
`contributor: user`, `decision.kind: USER_ACCEPTS`, and
`--user-approved-goal-change`. This replaces only the existing canonical question
section, retaining the prior version in normal history. Inferred/proposed purpose
never changes that section. If its canonical heading has changed, integration
fails and the host must review that actual note. Other contributions need no goal
approval. No project contribution can create, read or update a general profile.

## Adaptive optional worked learning

`learning lesson --mode assist --requested --concept uncertainty --dimension-view
'JSON'` accepts only the validated general profile-shaped allowlist payload already
supplied by the trusted host. It does not open a profile or inspect project history.
Choose `collaborate` when sharing the exercise; delegated mode and absent explicit
lesson request return `teaching: false`. Designer/researcher views remain available
without any lesson or persistent ability assessment.

The least established supplied dimension is the lesson focus (unsupplied means
unknown). The output includes a labeled synthetic numerical application, arithmetic,
a boundary/limitation, a short exercise and answer. For uncertainty, the worked
case computes 10 ± 2 as [8,12] and explicitly says an assumed interval is not a
confidence guarantee. This is a scaffold, not measured cognitive competence or
project validation. The output says `NOT_ASSESSED`; only an actual demonstration
explicitly confirmed by the user may later become a separate host-approved general
profile update. There is no project-to-profile extraction or automatic write.

## Fine-grained erasure and lesson differentiation

`learning erase --profile FILE --expected-hash HASH --concept uncertainty
--dimension definition` removes just that dimension. Omit `--dimension` to erase
only that concept. Other concepts and dimensions remain unchanged; the same
trusted host path and hash precondition apply.

Lesson content changes with the focus: a missing definition introduces a
prerequisite definition, explanation asks for reasoning, calculation works the
arithmetic, application handles a missing-input decision, and limits examines
a counterexample and verification boundary. If every dimension is confirmed,
basics are skipped and only a requested transfer task is offered. Delegated or
unrequested teaching stays disabled. Profile confirmations are attested historical
observations; these deterministic scaffolds have not demonstrated actual cognitive
improvement, retained understanding or transfer in a real user study.
