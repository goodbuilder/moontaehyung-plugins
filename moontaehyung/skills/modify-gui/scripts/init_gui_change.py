#!/usr/bin/env python3
"""Create a durable ModifyGUI change packet without overwriting existing work."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re


SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def resolve_root(raw_root: str) -> Path:
    root = Path(raw_root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"Repository root does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"Repository root is not a directory: {root}")
    return root


def validate_slug(slug: str) -> str:
    value = slug.strip()
    if not SLUG_PATTERN.fullmatch(value):
        raise SystemExit(
            "Slug must use lowercase letters, digits, and single hyphens "
            "without leading or trailing hyphens."
        )
    if len(value) > 63:
        raise SystemExit("Slug must be 63 characters or fewer.")
    return value


def choose_change_id(changes_root: Path, slug: str, date_prefix: str) -> str:
    base = f"{date_prefix}-{slug}"
    candidate = base
    suffix = 2
    while (changes_root / candidate).exists():
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def packet_files(change_id: str, created_on: str) -> dict[str, str]:
    packet = f"docs/changes/{change_id}"
    return {
        "state.md": f"""---
schema: modify-gui-change-state-v1
change_id: {change_id}
status: interviewing
mode: unclassified
updated: {created_on}
baseline_ref: null
last_completed: "Change packet initialized"
next_question: "What operator-visible outcome should change, and how will the operator know it succeeded?"
read_next:
  - {packet}/change-brief.md
  - {packet}/current-behavior.md
affected_product_docs: []
blocking_questions: 0
source_changed: false
implementation_allowed: false
approval:
  state: not-requested
  scope: null
  conditions: []
  recorded_at: null
---

# Resume Notes

No source modification is approved. Inspect the repository baseline before asking the next question.
""",
        "change-brief.md": """# Change Brief

## Operator outcome

## Motivation

## Included scope

## Excluded scope and non-goals

## Acceptance summary
""",
        "current-behavior.md": """# Current Behavior

## Version and worktree context

## Reproduction

## Observed frontend behavior

## Observed backend and persistence behavior

## Documentation, code, test, and runtime conflicts
""",
        "workflow-impact.md": """# Workflow Impact

## Affected operators and workflow IDs

## Current workflow

## Proposed workflow

## Preserved, added, removed, and reordered steps

## Decisions, confirmations, handoffs, waits, and artifacts

## Interruption, cancellation, retry, restart, and resume

## Degraded, error, and recovery behavior

## Completion and next actions

## Training, operating-procedure, and compatibility impact

## Workflow-to-screen, command, state, and regression traceability
""",
        "ui-quality-and-stability.md": """# UI Quality and Stability

## Existing product-specific visual language and component tokens

## Affected screens, components, text, tables, plots, and conditional controls

## AI/template-like pattern rejection audit

## Dynamic value formats, precision, units, longest extents, and update rates

## Reserved geometry, overflow, wrapping, elision, and detail access

## Focus, selection, scroll, table-column, dock/splitter, and window stability

## Accessibility, font scaling, DPI, locale, theme, and target-size checks

## Before/after screenshots and dynamic-state sequence evidence
""",
        "impact-analysis.md": """# Impact Analysis

## Preserved invariants

## Affected layers and components

## Feature dependency, ownership, and coupling changes

## Worker CPU/GPU resource impact

## Compatibility and migration

## Rollback and recovery

## Risks and assumptions
""",
        "frontend-contract.md": """# Frontend Contract

## Controls and inputs

## Payloads and commands

## Visible states and transitions

## Errors and recovery actions

## Keyboard, focus, accessibility, and layout

## Cross-feature visible behavior and isolation
""",
        "backend-contract.md": """# Backend Contract

## Commands and validation

## State, ownership, and concurrency

## Worker resource budgets, scheduling, and backpressure

## External boundaries and workers

## Results, errors, timeout, retry, and cancellation

## Persistence, restart, and shutdown
""",
        "integration-flow.md": """# Integration Flow

## Action-to-postcondition traces

## Transition tables

## Failure and recovery flows

## Cross-feature contracts and dependency direction
""",
        "decisions.md": """# Decisions

Append accepted decisions chronologically. Supersede entries rather than deleting history.
""",
        "implementation-plan.md": """# Implementation Plan

## Approval status

Not approved.

## Slices and dependencies

## File and component map

## Migration and rollback steps

## Stopping conditions
""",
        "approval-summary.md": """# Approval Summary

This document explains the proposed modification in plain language. Technical detail remains in the other packet documents.

## What changes and what stays the same

## Operator workflow before and after

## Success, delay, rejection, failure, overload, and recovery

## Data and compatibility effects

## Performance priorities and allowed degradation

## Visual and interaction changes, including dynamic-layout stability

## How acceptance will be demonstrated

## Cost, risks, assumptions, rollback, and field limits

## Exact scope awaiting approval

Not yet approved.
""",
        "verification.md": """# Verification

## Requirement-to-evidence matrix

## Focused test evidence

## Regression and application evidence

## Performance, load, and target-hardware evidence

## Feature isolation and contract evidence

## Visual authenticity and dynamic-layout stability evidence

## Visual and hardware/manual evidence

## Residual conditions
""",
    }


def initialize(root: Path, slug: str, date_prefix: str | None = None) -> Path:
    valid_slug = validate_slug(slug)
    day = date_prefix or date.today().strftime("%Y%m%d")
    if not re.fullmatch(r"\d{8}", day):
        raise SystemExit("Date prefix must use YYYYMMDD.")

    changes_root = root / "docs" / "changes"
    changes_root.mkdir(parents=True, exist_ok=True)
    change_id = choose_change_id(changes_root, valid_slug, day)
    packet_root = changes_root / change_id
    packet_root.mkdir(exist_ok=False)

    created_on = f"{day[:4]}-{day[4:6]}-{day[6:]}"
    for relative, content in packet_files(change_id, created_on).items():
        (packet_root / relative).write_text(content, encoding="utf-8")
    return packet_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Existing repository root.")
    parser.add_argument("--slug", required=True, help="Short lowercase hyphenated change slug.")
    args = parser.parse_args()

    root = resolve_root(args.root)
    packet = initialize(root, args.slug)
    print(f"Created change packet: {packet.relative_to(root)}")
    print(f"Resume state: {(packet / 'state.md').relative_to(root)}")
    print("Source modification approved: no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
