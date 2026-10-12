# Minimum sufficient change

Apply this policy to the requested workflow or diff. Explicit user requirements and
project contracts determine what must work; simplicity chooses how to deliver it.

## Choose an implementation

The workflow owning a material implementation decision performs this comparison;
supporting workflows reuse its result. For a new system, substantial feature, or large
change, compare approaches after requirements are understood and before fixing the
implementation plan. Judge significance by effects on authoring, dependencies, shared
contracts, deployment, and future maintenance, not by file or line count.

Skip routine local fixes and mechanical changes. Respect explicit user choices and reuse
prior decisions while their requirements and assumptions remain valid. Reopen only the
choice affected by changed requirements or contrary evidence.

1. Trace the affected input, callers, state owner, output, and failure behavior.
   Identify the actual requirement before selecting an approach.
2. Inspect existing code, platform facilities, authoring tools, and suitable components
   or dependencies. Compare only viable alternatives, including retaining the current
   approach. Do not invent candidates to meet a quota. Reuse through allowed public
   boundaries; compare semantics, units/clocks, concurrency, limits, and errors.
3. Recommend the approach that meets the requirements with proportionate implementation,
   integration, and ongoing maintenance cost. Consider editability, compatibility,
   testability, portability, and dependency constraints where relevant. Handwritten code
   is one option; a mature tool or component can avoid unnecessary custom implementation.
4. Present the recommendation and material tradeoffs before committing to the approach.
   Record the decision question, viable alternatives, selected approach, reason, and
   assumptions needing verification in the existing plan or decision record. Keep this
   brief; a decision with no viable alternative needs a reason, not a comparison table.

Use available evidence first. Investigate uncertain claims that could change the choice;
web searches, prototypes, and subagents are not mandatory for every comparison. Stay within
existing authorization. Give a technical recommendation rather than making the user choose
routine implementation details. Reuse the existing approval process and decision record.

Use a qualitative complexity budget: name the structures needed now and the
evidence that would justify expanding them. Avoid arbitrary file, line, class, or
test quotas. A single-implementation adapter may be warranted by I/O isolation,
independent testing, ownership, or a simulation/replay boundary. Keep it narrow.
Several explicit small modules may be easier to maintain than one large panel.

## Preserve behavior when simplifying

Compare actual postconditions, including failure and recovery, rather than happy
path output alone. For example, a size-bounded memoization helper does not replace
a cache with required expiry; retaining a tested expiry policy may be the simplest
correct solution.

Preserve required validation, security, accessibility, cancellation, data-loss
handling, resource ownership, and evidence. Where relevant, preserve frame, axis,
unit, clock, epoch, and truth/estimate separation. These implementations can be
simplified when independent evidence still proves the same contract.

For a bug fix, inspect the affected callers and fix the cause at its responsible
owner. Avoid distributing duplicate guards across views, expanding unrelated
cleanup, or extracting a generic utility that creates cross-feature coupling.

## Review only meaningful candidates

At a slice checkpoint, classify actual complexity findings:

- **KEEP**: name the requirement or observed constraint that justifies the code.
- **REMOVE**: identify the replacement or prove the path is unused, including
  registrations, configuration, persisted formats, and public consumers. Apply
  removal only within authorized edit scope and verify affected behavior.
- **DEFER**: record the present limit, consequence, concrete revisit trigger, and
  next action in the existing decision/risk record. Defer optional expansion;
  reducing an agreed requirement needs the user's scope decision.

Review-only requests produce recommendations. These labels never authorize edits
and never replace verification status. A required failed or unrun check remains
unresolved even if a related enhancement is marked DEFER.

## Keep the process proportionate

Use one evidence ledger per change, shared by creation/modification and verification
work. Link decisions and tests instead of copying them. Record meaningful findings
and state changes; a no-findings check can be one sentence.

Reuse the project's test tools and focus on independent checks of observable
behavior. Extend regression coverage where a failure could recur; do not cap it at
one test, delete useful checks to reduce line counts, or create boilerplate tests
for trivial wording edits. A small task does not need every architecture document
or a replay subsystem. Decide persistence, rerun, and reproducibility from its
requirements; distinguish exact, tolerance-based, and statistical repeatability.

If reporting savings, measure the actual diff and separate handwritten code,
generated code, tests, and documents. File counts alone do not establish design
quality, and upstream benchmark percentages do not predict another project's gain.
