---
name: Zotero
description: Use Zotero Desktop from Codex to search a local library, verify reference metadata and recommendation evidence, read indexed full text when requested, export BibTeX, insert citation keys, and import verified records. Never invent references or fill bibliographic gaps from memory.
---

# Zotero

Use this skill to operate a user's local Zotero Desktop library from Codex.

Core helper:

```bash
python3 <plugin-root>/skills/zotero/scripts/zotero.py <command>
```

Resolve `<plugin-root>` by going two directories up from this `SKILL.md` file.

The helper is stdlib-only and follows the repo convention of running plugin Python helpers with `python3` / `#!/usr/bin/env python3`; it does not require Codex-specific runtime discovery.

## Fast starts

Check readiness in one command:

```bash
python3 <plugin-root>/skills/zotero/scripts/zotero.py status --json
```

Enable the local API and restart Zotero if needed:

```bash
python3 <plugin-root>/skills/zotero/scripts/zotero.py enable --restart
```

Search and export citation data:

```bash
python3 <plugin-root>/skills/zotero/scripts/zotero.py search "transformer" --json
python3 <plugin-root>/skills/zotero/scripts/zotero.py export-bibtex --out references.bib
```

Insert a citation from Zotero into a draft and keep `references.bib` in sync:

```bash
python3 <plugin-root>/skills/zotero/scripts/zotero.py cite --query "Attention Is All You Need" --tex paper.tex --bib references.bib --marker '<cite>'
```

## Workflow

1. Start with `status --json`. Do not rediscover prefs, ports, or profile paths manually unless the helper fails.
2. If `local_api_enabled_pref` is false, run `enable --restart` when the user asked you to operate Zotero. This updates Zotero's local preference and restarts Zotero so port `23119` comes up.
3. Use read-only local API commands for normal work:
   - `inventory` for item/collection/tag summaries.
   - `search <query>` for papers/items.
   - `export-bibtex` or `sync-bib` for `.bib` files.
   - `cite` for inserting a citation into a draft.
4. Only retrieve attachment file URLs or full text when the user asks for PDFs, attachment paths, or full-text content.
5. Treat Zotero library writes as explicit write actions. Before `import-bibtex`, `import-ris`, or connector save commands, confirm the exact record/source and destination unless the user's prompt already explicitly asked to add/import it.


## Reference integrity

Preventing fabricated or misattributed references is a hard constraint. Search results and model memory are discovery hints, never evidence that a reference exists or supports a claim.

### Keep evidence states separate

- **Zotero record found** means the exact item key and metadata came from the local Zotero API. This proves that a record exists in the user's library; it does not prove the metadata is correct or that the paper supports a claim.
- **Metadata verified** means the title, author identity/list, year, venue or publication type, and DOI or canonical URL were checked against an authoritative source. Prefer publisher/journal pages, official proceedings, or the official repository for preprints. Use DOI registration metadata as a cross-check. Search snippets, citation counts, secondary summaries, and Zotero presence alone do not verify metadata.
- **Content checked** means the abstract or relevant full text was read. Recommendations must state what was checked and give a section, page, or figure locator when available. Abstract-only evidence supports only an abstract-level relevance claim.

Never collapse these states or call a reference verified without the corresponding evidence.

### Rules for citations and recommendations

- Never invent or complete a title, author, year, venue, DOI, URL, page number, result, or citation key from model memory. Keep unavailable fields marked as unknown.
- Treat external search results as candidates. Do not cite, recommend, or import an external candidate as verified until its metadata is checked against an authoritative source. If identity is ambiguous, fields conflict, or no authoritative source is available, mark it unverified and abstain.
- Recommend a paper only after its metadata is verified and its abstract or relevant full text is checked for relevance. If only the abstract was checked, say so. Do not claim a paper supports a specific result without checking the relevant full-text passage.
- For citations, use the exact Zotero item key and returned BibTeX/citation key. If multiple records match or Zotero metadata conflicts with the source, do not choose or silently repair the record; report the ambiguity. When a Zotero record has not been independently checked, identify it as a library record only and do not call it verified. Withhold insertion if its identity is uncertain or fields conflict.
- Before importing, identify the verified record and its source. Import only when the user requested the write, following the existing write-confirmation rules.
- If a required field or claim cannot be verified, say what could not be checked. Do not fill the gap with a plausible-looking reference.

For each external recommendation or import candidate, report its title, authors, year, venue/type, DOI or official URL, metadata verification source, and whether the abstract or full text was checked. For a Zotero match, include its item key and BibTeX key when available. If the user asked only to discover candidates, label unchecked items as candidates, not recommendations.

## Common commands

```bash
# Readiness and route map
python3 <plugin-root>/skills/zotero/scripts/zotero.py status --json
python3 <plugin-root>/skills/zotero/scripts/zotero.py probe --json

# Library inventory
python3 <plugin-root>/skills/zotero/scripts/zotero.py inventory
python3 <plugin-root>/skills/zotero/scripts/zotero.py collections
python3 <plugin-root>/skills/zotero/scripts/zotero.py tags

# Search and export
python3 <plugin-root>/skills/zotero/scripts/zotero.py search "BERT"
python3 <plugin-root>/skills/zotero/scripts/zotero.py export-bibtex --out references.bib
python3 <plugin-root>/skills/zotero/scripts/zotero.py export-bibtex --item-key PXW99EKT
python3 <plugin-root>/skills/zotero/scripts/zotero.py citations --style apa --json

# Draft editing
python3 <plugin-root>/skills/zotero/scripts/zotero.py cite --item-key PXW99EKT --tex paper.tex --bib references.bib --marker '<cite>'
python3 <plugin-root>/skills/zotero/scripts/zotero.py cite --query "BERT" --markdown notes.md --bib references.bib --marker '<cite>'

# Attachments and full text; use only on request
python3 <plugin-root>/skills/zotero/scripts/zotero.py children PXW99EKT --json
python3 <plugin-root>/skills/zotero/scripts/zotero.py fulltext 2JAZS9U8 --out attention-fulltext.txt
python3 <plugin-root>/skills/zotero/scripts/zotero.py file-url 2JAZS9U8

# Writes to Zotero; confirm first unless explicitly requested
python3 <plugin-root>/skills/zotero/scripts/zotero.py selected-target --json
python3 <plugin-root>/skills/zotero/scripts/zotero.py import-bibtex --file new-reference.bib --yes
python3 <plugin-root>/skills/zotero/scripts/zotero.py import-ris --file new-reference.ris --yes
```

## Output standards

- For inventory/search, return title, creators, year, Zotero item key, and BibTeX key when available.
- Explain the two-key distinction when relevant: Zotero item keys like `PXW99EKT` are not the same as exported BibTeX keys like `vaswani_attention_2023`.
- For `.bib` export, return the absolute output path and entry count.
- For draft citation insertion, report the edited file, inserted citation key, and updated `.bib` path.
- For blockers, name the exact gate: Zotero app missing, local API disabled, port closed, connector unavailable, no matching item, or write not confirmed.

## Route details

Read `references/local-api-routes.md` only when you need endpoint details beyond the helper commands.
