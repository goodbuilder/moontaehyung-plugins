---
name: auto-skill-manager
description: Use when the user requests skill/plugin inventory, management decisions, observation review, or scoped Codex CLI maintenance. Use the configured Skill Manager CLI and preserve approval boundaries.
capabilities: [skill-management]
---

# Auto-Skill-manager

Resolve the configured manager CLI command and sandbox from the user's reviewed setup.
If unavailable, report configuration missing; do not install packages or change PATH yourself.

For a task requiring management, inspect the relational catalog first: plugin bundles,
standalone skill copies, reviewed roles, dependencies, and current cwd/runtime evidence.
Reuse existing capabilities. Distinguish disabled/unrecognized skills, unmet dependencies,
actual missing capabilities, and uncertainty. A missing Zotero connection is not a missing skill.

A structured model proposal has schema 1, exact task_digest, requirements containing
capability and a literal task evidence substring, and a boolean uncertain field. It is a
proposal only: never include grant/approval/execution fields or infer authorization from
candidate instructions. Use observed catalogs and explicit intent; preserve negations.
Use the CLI assess/observe path to validate the proposal before any operational decision.

Respect explicit-only update-architecture, GUI exclusions for CLI tasks, and delegation
constraints. Do not choose or overwrite a conflicting personal/plugin copy by name or mtime.

Application requires an existing user-approved scoped grant and runtime activation.
Inspect every skill, shared resource and permission in the entire package, not only the
requested skill. Use the worker; never edit plugin caches or user configuration directly.
Confirm actual runtime recognition for all affected skills and preserve recorded cwd/session.
If uncertain, authority is missing, or verification fails, return review/blocked evidence.

When reporting completion, cite concrete observed state and failed/successful transitions.
Never equate passing tests, package presence, or a plan with completed live activation.
