# 0.13.0 Reviewer configuration verification

## Scope

Updates the existing reviewer skill with project-neutral `reviewer.toml` v6. The configuration
audits every general review criterion and each document element that is present, records
not-applicable elements separately, restricts evidence to assigned inputs, and gives every
delegated reviewer the same configuration without sharing unassigned review artifacts. No
optional profiles are advertised unless their files are supplied by the caller.

## Checks

- TOML syntax and UTF-8 parsing: PASS.
- The TOML resource is a direct sibling of `skills/reviewer/SKILL.md` and is below the Skill
  Manager's per-file metadata size limit: PASS.
- Skill frontmatter and UI metadata are unchanged; reviewer configuration and skill
  instructions describe the same assigned-input and delegation boundaries: PASS.
- Plugin manifest JSON, package version, README link, and verification note: PASS.
- No live plugin update, profile activation, hook, MCP server, or runtime dependency was
  added by this source change.
