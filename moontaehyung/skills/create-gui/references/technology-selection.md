# Technology Selection for Operator GUIs

Choose after inspecting target platforms, existing code, device SDKs, deployment constraints, team skills, and interface demands. Record the comparison and accepted decision in the project documents.

## Default recommendation

For a new conventional desktop engineering/operator application, start the comparison with:

- Python 3.12 or the newest version supported by every required SDK;
- PySide6 as the official Qt for Python binding;
- Qt Widgets for dense tables, trees, forms, toolbars, menus, docks, diagnostics, and native desktop behavior;
- pytest plus pytest-qt for logic and interaction tests;
- model/view for substantial lists and tables;
- typed domain state and command services isolated from widgets;
- worker threads or processes around blocking device, network, compute, and media boundaries;
- a virtual environment and locked dependencies;
- the deployment mechanism selected only after supported OSes and driver/plugin needs are known.

This is a recommendation, not an invariant. Pin exact versions after checking current official compatibility and required vendor SDKs.

## Reconsider the default when

- a browser is the primary delivery surface or remote multi-user access is fundamental;
- mobile/touch-first operation is primary;
- highly animated, fluid, custom-rendered interaction dominates conventional controls;
- an existing C++/Qt, .NET, JVM, or web codebase and team makes another stack materially safer;
- safety certification, hard real-time requirements, vendor SDK restrictions, or deployment policy constrain Python;
- startup, memory, GPU/video, or very high-rate visualization budgets cannot be met by the proposed architecture.

Qt Quick/QML is a valid Qt alternative for custom fluid interfaces, but it adds a declarative boundary and is not automatically better for a traditional workstation. A web stack can simplify remote distribution but introduces browser/runtime, local-device, packaging, and operational complexity. Compare against actual requirements rather than trend or familiarity.

## GUI authoring choices

Once the framework is chosen, compare suitable form editors, existing widget/component
sets, and code-based composition for the actual screens. Consider who will edit layouts,
how often they change, custom/live views, generated-code boundaries, reproducible packaging,
and interaction testing. Use the Qt Designer guidance in SKILL.md only for Qt Widgets.
Carry accepted authoring constraints into architecture planning rather than reselecting them.

## Required decision evidence

Before approval, document:

- supported OS, CPU/GPU, displays, scaling, and offline requirements;
- required device SDK and native library compatibility;
- data rates, latency, startup, memory, and shutdown budgets;
- CPU/GPU worker topology, concurrency limits, accelerator memory budget, overload policy, and target-hardware performance evidence;
- packaging, installation, updates, rollback, and logs;
- licensing constraints;
- team maintenance skills and debugging path;
- automated testing and hardware simulation strategy;
- a small risk spike for any unproven video, GPU, protocol, or packaging boundary.
