# GUI change regression supplement

Generic decomposition, evidence levels, failure tests, prerequisite status and completion evidence
are owned by [verify-check](../../verify-check/SKILL.md). Reuse its one ledger and the approved
requirements; do not repeat its procedure or add product capabilities just to test them.

## GUI-specific acceptance

- Map workflow IDs to operator action, visible feedback and observed backend postcondition.
- Drive primary commands with real or simulated clicks and keyboard actions. Check busy/disabled
  presentation separately from backend rejection, including duplicate actions and cancel where relevant.
- Inspect focus, shortcuts, dialogs, accessibility names, target scaling/resolution and localization.
- Exercise live updates with empty/stale/error/long values; verify geometry, click targets, selection,
  focus and scroll stability against the approved visual contract.
- Compare screens with the product-specific hierarchy and visual rationale. Screenshots support
  appearance checks but do not prove state transitions or external completion.
- Under applicable worker loads, verify the approved GUI responsiveness and visible overload/fallback
  behavior using existing resource-budget contracts. Do not invent fixed limits or extra infrastructure.
- Execute relevant recovery, restart and close flows through the application entry point, checking
  operator-visible next actions and the required persisted outcome.

Use mocks/fakes only for the boundaries they can substantiate. Runtime limits and field checks remain
explicit in the shared ledger; the GUI workflow owns the final approved acceptance decision.

Use workflow-impact.md or its mapped equivalent. Compare before/after behavior and preserve adjacent
critical flows sharing controls, commands or resources; document intentional differences separately.
