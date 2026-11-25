# Execution feasibility and custody

## Confirmed

- Installed Codex 0.172.0 and Claude Code 2.1.331 start in network-disabled minimal filesystem namespaces; no real home is mounted.
- Claude native offline `plugin validate /product` discovers 25 product skills and 5 product agents, exits 0. This validates manifests/discovery, not model execution or role operation. Catalog publication warnings are separate.
- Codex native offline app-server `initialize` and `skills/list` discover RIS through a read-only local `.agents/skills` projection. RIS has scope=repo and pluginId=null. This is supported project-skill discovery, not installed marketplace-plugin proof. No thread/start or turn/start was sent. Extra system skills returned by the CLI are distinct from the 25 product skills.
- New credential-free worker prototype executes actual product `init` then `status` successfully in its temporary project. These are deterministic local CLI checks, not product research E2E. It blocks real-home, credential-path, sealed-packet and symlink escape reads, product-code writes, and external network connection. Custodian packet, hidden material, real credentials and unrelated projects have no mount.
- Read-only quota observation returns ordinaryUsageAllowed=true and weekly usedPercent=0. Paid-credit availability=true and positive-balance=true; no credit amount or account identity was preserved. Backend spendControlReached=false.

## Actual current boundary

User authorized a maximum four combined development regression/minimal E2E sessions, ten million cache-inclusive-token target and 94% weekly stop, CONDITIONAL on external-charge blocking and worker isolation. These do not authorize old balanced holdout, arbitrary retries, remote writes or settings changes. Admission currently fails charge-blocking evidence. No model requests have been made.

The installed Codex protocol documents ordinaryUsageAllowed as backend permission for ordinary included usage; null is unavailable and must not be inferred from percentages/reset times. This admission observation does not establish a transactional included-only cap for subsequent requests. Neither inspected TurnStartParams/ThreadStartParams nor local CLI exec help provides an observed per-request included-only charge-control field. This is a bounded absence finding, not a universal statement about all provider controls. Claude's help exposes max-budget-usd as an API-call budget, which is not evidence of a subscription-only or zero-external-charge contract. No account settings were read or changed.

A 94% local poll pre-stop reduces quota exhaustion risk; it cannot by itself prevent an in-flight request from consuming credits. A token target is not a provider-side billing limit. Existing positive credits make a fail-open assumption material. No model call is permitted until main confirms an independently evidenced included-only hard stop.

## Trusted host versus worker

`worker_controller.py` is a minimal controller/worker prototype with fail-closed admission and no model transport. A trusted host can retain its own session/authentication outside the worker; it must pass only normalized input/proposals to this worker and collect exit/stdout/stderr/events. Product project state is confined to /project; product source is read-only /product. Controller state and independent review packet are separate paths with no worker mounts. The current worker only runs explicit deterministic argv, with process timeout and OS network/filesystem isolation.

It is not yet a verified plugin-loaded model-host broker. Giving a normal plugin-loaded host its real home/auth and relying on product instructions to route every shell/read action through this worker would not enforce isolation. Built-in file/shell tools and model-native subagents must all share the same boundary or be disabled and replaced by an independently verified broker surface. Native API forwarding, tool substitution, persisted thread resumption and role execution have not been tested. No undocumented tool interception is assumed.

Historical subject_host.py actual mode binds / and hides only selected directories. It is unsuitable as a complete worker boundary, despite stronger restrictions in its fixture-only probe mode. Do not merge probe success into actual-host proof.

## Holdout and comparison

The old enrollment remains enrolled, untouched and unexecuted. No sealed questions, reference answers or private rubric were opened. The current four-session ceiling cannot be represented as the old 24-session/48-stage fixed matched design. Preserve it as NOT_RUN until independently authorized resources and compatible pinned identities exist. Development fixtures and architecture comparison cannot replace final scientific/holdout acceptance.

Before live development, freeze the exact candidate manifest and intended host adapter; this packet's discovery snapshot is time-local and may precede later candidate edits. Run known regression first, then smallest fresh product E2E with actual state/thread and native-role evidence. Preserve failures and all host interventions. Independent audits assess unchanged contracts and observed artifacts; authors must not self-approve their output. No early holdout case is used as a development regression.

## Reproduction

- `python3 replay_cli_compatibility.py`: deterministic isolated CLI versions.
- `python3 codex_skills_probe.py`: offline local project skill discovery only.
- `python3 worker_controller.py --probe`: deterministic product local CLI and boundary probes. Re-running against its existing project may report already initialized; use new project for a fresh execution.
- `quota-included-read.py`: read-only authenticated quota observer, no model; output must remain field-filtered. Its trusted observer namespace is NOT the credential-free worker namespace.

Raw evidence: host-compatibility.json, offline-discovery.json (first failed argument probe preserved), offline-discovery-corrected.json, candidate-discovery-manifest.json, codex-skills-probe.json, schema-generation.json, worker-controller-probe.json, quota-included.json. Every model/product research E2E, REAL validation and sealed final holdout remains NOT_RUN.
