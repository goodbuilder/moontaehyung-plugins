# Project-local retrieval and isolated local runtime

Cross-project knowledge and strategy reuse is prohibited. `knowledge assess/reuse` only use
studies in the selected project. The old `--source-project` option fails before inspecting the
provided path. Historical external knowledge notes are preserved as inert records; their
findings, provenance, paths and strategies must not enter search, context or resume.

`knowledge search "terms" --limit 20 --offset 0 --max-scan 1000` retrieves current local
study observations with pinned revision, observation ID, conditions and locator. Each term
must match. Results require scientific review and do not refresh attached evidence bytes.
The scan is capped, returns `scan_complete`, and retains at most offset+limit matches in
memory. Offset is capped at 10000. A partial scan is not a complete project search; increase
max-scan (maximum 10000 studies) or narrow the selected study collection. Search does not
follow symlinks or load a persisted cross-project index. Concurrent updates can yield a
mixed read snapshot; assess a pinned revision and recheck the current revision before reuse.

For a Linux local helper process with an enforced filesystem boundary:

```sh
python3 <skill>/scripts/ris_isolated.py --project <selected-project> -- context
python3 <skill>/scripts/ris_isolated.py --project <selected-project> -- knowledge search "terms"
```

This requires bubblewrap and usable user namespaces, and fails closed when unavailable.
It mounts only the selected project writable, bundled runtime scripts read-only, and system
runtime directories read-only. It starts a new PID/network namespace, clears inherited
environment variables and supplies an empty HOME. Host history, home configuration, sibling
projects and network are absent. Absolute symlinks to host files resolve inside this namespace
and cannot reopen the host paths. Synthetic tests exercise an inaccessible sibling file,
symlink escape, absent host home and stripped environment, plus actual isolated init/context.

Scope: this isolates the bundled **local RIS CLI process**, not an already-running Codex or
Claude session. It cannot erase another process's previously loaded context, fence arbitrary
host tools, establish a clean model-host conversation, or prevent a caller outside the namespace
from reading another project. A host must enter an independently enforced project sandbox
before reading project data and must use a fresh conversation without imported prior context.
No full model-host integration or model execution is claimed here. The selected project itself
and trusted installed runtime code remain readable; do not place unrelated secrets in either.

`ris_isolated.py --project <root> --check-model-eligibility` is a conservative preflight.
It reports known foreign project metadata, external provenance, nested projects and symlinks
as requiring a curated mount. Even without those markers it reports model execution ineligible
because no clean model host has been verified. Unmarked imported content and derived
publication prose cannot reliably be classified automatically. The local CLI mount includes
raw project history; it must not be reused as a model-host sandbox for an uncurated workspace.
Historical records are preserved, never deleted or rewritten by this check.
