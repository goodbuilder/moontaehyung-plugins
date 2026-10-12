# Slice Patterns

Use the smallest applicable pattern and combine them when a feature crosses layers.

## External protocol or device

- Contract: message schema, offsets, types, units, endian, ACK/readback semantics.
- Encoder: inspect exact bytes against a hand-built or specification-derived fixture.
- Decoder: parse an independently constructed receiver payload.
- Runtime: compare actual readback to an expected value that does not come from the same faulty
  encoder/parser path.
- Failure: NAK, checksum/length error, disconnect, timeout, stale response, and retry.

Typical examples include UBX, RTCM, MAVLink, camera command protocols, serial probing, and FTP.

## Asynchronous capture or worker

- Command sequence: enable/configure, capture, completion poll, result collection.
- Lifecycle: start, running, completed, failed, timed out, cancelled, and cleared.
- Concurrency: duplicate request, simultaneous channels, session start/stop during capture.
- Result: left/right pairing, IDs, timestamps, status, source, and failure reason.
- Evidence: append-only event record plus session aggregate and recovery behavior.

## UI-to-backend workflow

- Control: visible label, enabled/disabled state, default, tooltip, and user intent.
- Payload: event name and exact fields sent to the controller or facade.
- Routing: handler, backend method, worker, and result callback.
- Feedback: status/error text, overlay, approval gate, manual fallback, and edit provenance.
- Regression: existing manual path remains usable and unrelated controls remain unchanged.

## Persistence and session data

- Schema: required fields, defaults, version, JSON-safe values, and backward compatibility.
- Write path: success, partial failure, duplicate event, and append ordering.
- Read path: recovery, missing file, malformed row, and legacy data.
- Provenance: source, state, timestamps, hashes, and user/manual versus automatic origin.
- Operator view: confirm the persisted evidence explains what actually happened, not merely what
  the UI requested.

## Independent-oracle checklist

Prefer, in order:

1. Published specification or explicit user-provided contract.
2. Hand-built raw fixture with distinct sentinel values in adjacent fields.
3. Captured real-device response or approved simulation artifact.
4. Alternate implementation or independently calculated expected value.
5. Existing implementation only as a compatibility check, never as the sole oracle.
