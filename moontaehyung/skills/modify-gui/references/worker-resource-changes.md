# Worker CPU/GPU Resource Changes

Use this when an existing application's worker counts, CPU/GPU placement, scheduling, queues, inference/media load, accelerator memory, priority, or load-time responsiveness may change.

## Freeze the baseline first

On each supported or representative hardware profile, record:

- worker/process/thread topology and ownership;
- internal thread pools from OpenMP, BLAS, OpenCV, inference runtimes, codecs, and similar libraries;
- idle, normal, peak, and burst CPU; GPU device/utilization/memory; host memory; queue depth/age; throughput; latency/deadline misses; drops; and GUI responsiveness;
- workload, sample duration/method, software/driver versions, power mode, display load, and thermal/throttling conditions;
- current overload, fallback, recovery, and shutdown behavior.

Use repeatable workloads and time-series or distribution evidence, not one instantaneous percentage. If the existing system lacks telemetry, approve the smallest instrumentation needed before claiming a tuning result.

## Define the proposed contract

Record one explicit resource-policy owner and the before/after values for:

- worker classes, priority, active and pending limits;
- bounded queue admission, backpressure, drop/coalesce, cancellation, and staleness rules;
- CPU thread/process counts and nested runtime/library threads;
- any affinity, process priority, cgroup, or OS scheduling control, including platform support and rollback;
- GPU device/context/process ownership, concurrency, streams/batching, transfer policy, and memory budget/reserve;
- accelerator unavailable, out-of-memory, thermal-throttle, or driver-reset behavior;
- whether CPU fallback, reduced quality/rate, pause, or fail-closed is approved and how the GUI exposes it;
- configuration, safe defaults, persistence/migration, live reconfiguration, warm-up, drain, and release.

Do not silently trade correctness or evidence fidelity for utilization. Preserve ordering, pairing, timestamps, provenance, and state semantics when dropping, coalescing, batching, or deferring work.

## Approval and verification

Allocation changes may affect the whole host even if few files change. Include dependent workers and critical GUI workflows in the impact map. Require explicit approval before introducing affinity/priority controls, new GPU fallback, quality/rate degradation, or hardware-specific configuration.

Compare baseline and candidate under the same named workloads. Acceptance should use service outcomes—GUI latency, worker deadlines/throughput, maximum queue age, drop-policy compliance, memory ceiling, recovery, and shutdown—plus CPU/GPU metrics as diagnostics or secondary guardrails. Test peak, burst, overload, accelerator failure, memory pressure, recovery, and sustained/thermal behavior. State clearly which evidence is measured on real target hardware versus simulated or unavailable.
