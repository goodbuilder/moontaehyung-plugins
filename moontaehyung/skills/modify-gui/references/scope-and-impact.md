# Scope and Product-Document Routing

## Classification

Choose the narrowest mode that covers the observable user outcome.

### Frontend-only

No backend request, response, state, persistence, protocol, worker, or resource-owner contract changes. Verify that this remains true by following the control's real signal/callback path.

### Backend-coupled

The operator action or displayed result depends on a changed controller, service, worker, device/API adapter, state model, persistence path, or error mapping. Treat frontend and directly coupled backend as one approved vertical slice.

### Backend-only GUI contract

No widget code may change, but the backend changes data, state, timing, error, or persistence semantics consumed by the GUI. Preserve the existing frontend contract or document and approve its change.

### Out of scope

The request has no user-visible GUI contract. Do not expand `modify-gui` to cover general infrastructure or backend maintenance.

## Shared product documents

When the project uses the CreateGUI numbered documentation, route by impact:

| Change | Read first |
|---|---|
| operator workflow or navigation flow | `00`, `01`, `02`, `03`, `04`, `06`, `07`, `10` |
| layout, styling, interaction | `00`, `01`, `03`, `04`, `08`, `10` |
| dynamic text/data or layout stability | `01`, `04`, `06`, `08`, `10` |
| commands or state | `01`, `05`, `06`, `07`, `10` |
| device, protocol, stream | `01`, `05`, `06`, `07`, `09`, `10`, `11` |
| worker CPU/GPU allocation or performance | `01`, `05`, `06`, `07`, `09`, `10`, `11` |
| settings, persistence, migration | `02`, `05`, `06`, `07`, `09`, `10`, `11` |
| packaging or deployment | `02`, `09`, `10`, `11` |
| full redesign | all relevant `00`–`11` documents |

This table is a starting route. Add or remove documents based on actual dependencies and list the chosen paths in packet state `read_next` and `affected_product_docs`.

If numbered documents do not exist, map the same concerns to existing project documentation. Create a missing product document only when the accepted change needs an authoritative long-lived home; do not scaffold an unused documentation suite during an ordinary modification.

## Impact map

For every affected layer, record current owner, proposed change, preserved invariant, dependencies, test oracle, migration need, and rollback/recovery path:

- operator workflow and permissions;
- widgets, models, navigation, dialogs, keyboard and accessibility;
- controller/facade payloads and callbacks;
- domain state, commands, validation, timing, and concurrency;
- devices, services, protocols, native SDKs, workers, and queues;
- CPU/GPU topology, library thread pools, accelerator memory, scheduling/backpressure, telemetry, and overload/fallback;
- files, settings, schemas, evidence, and restart recovery;
- packaging, configuration, deployment, and field operations;
- tests, fakes, fixtures, screenshots, and hardware procedures.

Omit unaffected layers explicitly rather than leaving them ambiguous.
