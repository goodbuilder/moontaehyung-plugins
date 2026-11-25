# Optional Designer navigation views

`ris.py view research|knowledge|decision|evidence|plan|learning|strategy` is a
read-only CLI projection over existing canonical owners. It creates no page, map,
dashboard, profile, duplicated claim store or new source of authority. Use ordinary
owner commands to inspect or change the referenced content.

- `research` starts at the existing INDEX and CONTEXT.
- `knowledge` selects the question's governed findings (`--question`), using its
  owner reader and revision. Dirty/unreviewed findings are omitted.
- `decision` can select a canonical `--study ID --revision N` or an explicitly
  included decision note. Existing study validation remains authoritative.
- `evidence` accepts explicitly selected source/literature/finding/study notes.
  Follow their canonical receipts/locators for evidence; the view does not certify it.
- `plan` selects the existing active plan from state/config or `--include PATH`.
  Existing note IDs and map/anchor links are preserved exactly; maps are never opened.
- `learning` points at canonical CONTEXT and explicitly included concept notes,
  identifies attributed contribution sections, and never reads a global profile.
- `strategy` references the existing recovery ledger revision and explicitly
  included originating finding/plan/study notes. Strategy IDs point to owner records;
  no strategy applicability or causal benefit is inferred by this projection.

`--include` can repeat up to twenty project-relative managed Markdown paths.
Unrelated note kinds, unmanaged/foreign/legacy-external notes, missing files,
oversized inputs, dirty governed records and transient revisions are omitted with
explicit reasons. Referenced links are displayed as original hrefs and never followed.
External links are omitted from this navigation surface. No sibling scan or project-wide
history scan is performed. A normal prose edit has no invented dirty-state model:
its exact current file hash is the pin; governed owners additionally enforce their
own direct-edit rules.

Every included record exposes its canonical path, stable `ris_id`, exact SHA256,
kind/status and bounded navigation links. Governed/study records add owner revisions.
`receipt` binds the project, view, explicit selection and included revisions;
`--expected-receipt HASH` rejects changed input rather than presenting stale pins.
A final reread omits records changed during projection. This is an observed snapshot,
not a filesystem lock or authenticated scientific approval. `--limit` defaults to
20 (maximum 50); `--max-chars` defaults to 16000 (2000–64000). Omission lists are
also bounded and report truncation. Each selected file is capped at 256 KiB.

Examples:

```sh
python3 scripts/ris.py --project /selected/project view research
python3 scripts/ris.py --project /selected/project view plan --include .ris/research/plans/current.md
python3 scripts/ris.py --project /selected/project view decision --study experiment-a --revision 2
python3 scripts/ris.py --project /selected/project view knowledge --question timing --limit 10
```

These views supply Designer navigation through existing official records. They do
not establish independent reviewer identity, cognitive improvement, scientific
completeness, strategy applicability or model-host isolation.
