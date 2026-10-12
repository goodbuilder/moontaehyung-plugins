# Worker CPU/GPU Resource Budgeting

Use this guidance when workers perform compute, inference, decoding, image/video processing, large plotting, simulation, or other sustained work that can compete with the GUI.

## Discover before deciding

For each workload, document:

- trigger, arrival rate, burst size, deadline, acceptable staleness, and whether work may be dropped, coalesced, paused, or cancelled;
- CPU libraries and their internal threads, process/thread model, GPU APIs and devices, expected memory, transfer volume, and initialization cost;
- latency/throughput priority relative to UI responsiveness and other workers;
- target hardware, OS, power mode, display load, drivers, and deployment environment;
- idle, representative, peak, degraded, startup, shutdown, and recovery behavior.

Do not translate “use 50% CPU/GPU” directly into an implementation. Utilization is device-, driver-, sampling-, and workload-dependent. Convert the intent into worker concurrency, queue limits, deadlines, memory ceilings, and measurable end-to-end outcomes on named hardware profiles.

## Allocation contract

Define one explicit policy owner for shared capacity and record:

- worker classes and priorities;
- maximum active jobs and pending work per class;
- bounded queue size, admission, backpressure, drop/coalesce, and cancellation rules;
- CPU thread/process counts, including nested OpenMP/BLAS/OpenCV/runtime threads to prevent hidden oversubscription;
- whether process affinity, priority, cgroups, or OS scheduling controls are justified by measurements and portable to supported platforms;
- GPU device selection, context/process ownership, maximum concurrent jobs, memory budget/reserve, streams/batching, and transfer policy;
- accelerator unavailable/out-of-memory/thermal-throttle behavior and whether CPU fallback, reduced quality/rate, pause, or fail-closed is approved;
- dynamic reconfiguration boundaries, persistence, safe defaults, and operator visibility;
- startup warm-up and orderly drain/cancel/release on shutdown.

Protect the GUI event thread from compute and blocking I/O. Avoid unbounded executors, queues, worker creation, library thread pools, and GPU allocations. A scheduler must not hide dropped work, stale results, silent CPU fallback, or missed deadlines.

## Observability

Expose enough structured telemetry to explain performance without turning the operator screen into a profiler:

- per-worker active/pending counts, throughput, latency/deadline misses, queue depth/age, drops/coalescing, and last failure;
- process and, when available, worker CPU time/utilization and memory;
- GPU device, utilization, memory used/reserved, active jobs, allocation failures, and fallback state;
- GUI input/event/render latency or a defensible responsiveness proxy;
- throttling, thermal/power condition, and configured policy/profile where supported.

Use diagnostics/logs for detail and concise health/degraded status for operators. Sampling must itself be bounded and must not become a performance problem.

## Verification and acceptance

Create named hardware/workload profiles and test idle, normal, peak, burst, overload, accelerator failure, memory pressure, recovery, and shutdown. Record exact workload, duration, sampling method, versions, and power/thermal conditions.

Acceptance should primarily use observable service outcomes: maximum GUI responsiveness latency, worker latency/throughput/deadline limits, maximum queue age, drop policy compliance, memory ceiling, and recovery behavior. CPU/GPU utilization may be a diagnostic or secondary guardrail, not the sole proof of correct allocation.
