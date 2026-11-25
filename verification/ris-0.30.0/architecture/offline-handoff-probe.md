# Offline architecture transport prototype

Executed `python3 offline_handoff_probe.py` against a common development-only fixture. No
custodian preregistered candidate or evaluation results were read. No model, network research,
physical experiment or cost-bearing call was made. The script and raw JSON are adjacent.

The fixture contains a pinned observation at revision 2 with current revision 3, source 20 C
versus target 25 C, matching evidence bytes, an explicit temperature-dependent failure case,
a missing negative control and the same-project/no-external-run hard limits. Every path ends
with the same deterministic decision: evidence reuse needs recheck; strategy transfer is
unverified. This tests transport and required-key validation, not researcher reasoning quality.

| Path | Injected missing top-level facts detected | Rework rounds | Inter-role messages / bytes | Coordinator JSON bytes | Local Python total for 1000 iterations |
|---|---:|---:|---:|---:|---:|
| Integrated | 0 | 0 | 0 / 0 | 592 | 10.17 ms |
| Split producer using lossy summary | 3 / 3 | 1 | 3 / 645 | 810 | 25.24 ms |
| Typed conditional handoff | 0 | 0 | 1 / 525 | 807 | 20.09 ms |

The lossy producer projection deliberately omits current source revision, strategy restrictions
and hard limits. The consumer validator requests exactly those three facts and receives a repair.
All paths have zero missing required facts after repair. The conditional path sends complete
boundary-critical information once and its coordinator passes a reference plus required schema,
instead of resending the handoff body. Integrated work has no producer/consumer boundary here.

These are mechanically counted serialized UTF-8 JSON envelope bytes. They are not model tokens,
actual context occupancy, provider usage, cost, model latency or semantic error rates. Timings are
single-run local Python microbenchmarks (1000 iterations, including serialization); scheduler and
machine differences make them unsuitable for model performance estimates. Missing facts are
injected by a deliberately deficient summary contract, so differences cannot establish that split
roles inherently lose facts. The topology and contract differ together. A complete split contract
could also avoid these repairs. The defensible result is narrower: contract-required boundary
facts prevent this fixture's omission, while references avoid coordinator body duplication.

This is implementation preparation and does not choose or certify a model architecture. A
subsequent comparable provider evaluation must keep source facts, authority, acceptance rule,
retrieval scope, model budget and timing boundaries constant, and independently inspect semantic
omissions, scientific quality, actual tool work, cost and user intervention.
