#!/usr/bin/env python3
"""Initialize durable CreateGUI interview documentation without overwriting files."""

from __future__ import annotations

import argparse
from pathlib import Path


FILES = {
    "README.md": """# GUI Project Documentation

This directory is the authoritative specification and durable interview record.

## Status

- Interview status: interviewing
- Implementation approval: not granted

## Documents

See the numbered documents for product, workflow, architecture, and verification decisions. Resume an interview from `interview/state.md`.

The plain-language approval request is maintained in `approval-summary.md`.
""",
    "00-product-vision.md": """# Product Vision

## Facts

## Decisions

## Proposals and assumptions

## Glossary
""",
    "01-operator-workflows.md": """# Operator Workflows

## Primary operators

## Current real-world workflows

## Target workflows

## Startup and shutdown

## Normal and repeated operation

## Decisions, handoffs, and artifacts

## Interruption, cancellation, retry, and resume

## Degraded, error, and recovery workflows

## Workflow completion and next actions

## Workflow-to-screen, command, state, and verification traceability
""",
    "02-requirements-and-scope.md": """# Requirements and Scope

## Functional requirements

## Non-functional requirements

## Version 1 scope

## Non-goals

## Acceptance boundaries
""",
    "03-information-architecture.md": """# Information Architecture

## Entities and terminology

## Navigation

## Workspace ownership

## Feature catalog and ownership
""",
    "04-workspace-layout.md": """# Workspace Layout

## Application shell

## Workspaces

## Displays and scaling

## Dynamic-content geometry, focus, and scroll stability
""",
    "05-device-and-data-contracts.md": """# Device and Data Contracts

## External boundaries

## Data, rates, units, and clocks

## Ownership and provenance

## Feature and shared-resource ownership
""",
    "06-state-and-command-model.md": """# State and Command Model

## State vocabulary

## Command contracts

## Transition tables

## Cross-feature public contracts
""",
    "07-error-recovery-and-safety.md": """# Error, Recovery, and Safety

## Failure scenarios

## Degraded operation

## Retry, cancellation, and shutdown

## Feature failure isolation
""",
    "08-design-system.md": """# Design System

## Visual principles

## Product-specific visual rationale

## AI/template-like UI rejection criteria

## Semantic tokens and status

## Density, typography, and components

## Accessibility and interaction

## Dynamic values, text formatting, overflow, and update stability
""",
    "09-architecture-and-implementation.md": """# Architecture and Implementation

## Technology decision

## Runtime boundaries and threading

## Feature boundaries and dependency direction

## Worker CPU/GPU budgets, scheduling, and backpressure

## Persistence and resource ownership

## Phased implementation plan
""",
    "10-testing-and-validation.md": """# Testing and Validation

## Acceptance matrix

## Automated and simulated evidence

## Performance, load, and target-hardware evidence

## Feature isolation and contract evidence

## Visual authenticity and dynamic-layout stability evidence

## Visual and hardware/manual evidence

## Open field conditions
""",
    "11-deployment-and-operations.md": """# Deployment and Operations

## Supported platforms

## Hardware and accelerator profiles

## Packaging, installation, and updates

## Configuration, logging, backup, and recovery
""",
    "approval-summary.md": """# Approval Summary

This document explains the proposed application in plain language. Technical detail remains in the numbered documents.

## What will be built

## How the operator will use it

## What success looks like

## Delay, failure, overload, and recovery

## Preserved capabilities and excluded scope

## Performance priorities and allowed degradation

## Visual character and how dynamic information stays stable

## How acceptance will be demonstrated

## Cost, risks, assumptions, and field limits

## Exact scope awaiting approval

Not yet approved.
""",
    "open-questions.md": """# Open Questions

Track each unresolved item with priority, blocking impact, owner, and next action.
""",
    "interview/state.md": """---
schema: create-gui-interview-state-v1
status: interviewing
phase: context-and-intent
updated: null
last_completed: "Documentation initialized"
next_question: "Who will operate this application, in what environment, and what outcome must it achieve?"
read_next:
  - docs/00-product-vision.md
blocking_questions: 0
implementation_allowed: false
approval:
  state: not-requested
  scope: null
  recorded_at: null
---

# Interview Resume Notes

The specification is not approved. Resume with the `next_question` above after checking repository context.
""",
    "interview/decision-log.md": """# Decision Log

Append accepted decisions chronologically. Supersede old entries instead of deleting history.
""",
}


def resolve_root(raw_root: str) -> Path:
    root = Path(raw_root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"Project root does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"Project root is not a directory: {root}")
    return root


def initialize(root: Path) -> tuple[list[Path], list[Path]]:
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    preserved: list[Path] = []
    for relative, content in FILES.items():
        destination = docs / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            preserved.append(destination)
            continue
        destination.write_text(content, encoding="utf-8")
        created.append(destination)
    return created, preserved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=".",
        help="Existing GUI project root; defaults to the current directory.",
    )
    args = parser.parse_args()
    root = resolve_root(args.root)
    created, preserved = initialize(root)
    print(f"Documentation root: {root / 'docs'}")
    print(f"Created: {len(created)}")
    for path in created:
        print(f"  + {path.relative_to(root)}")
    print(f"Preserved: {len(preserved)}")
    for path in preserved:
        print(f"  = {path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
