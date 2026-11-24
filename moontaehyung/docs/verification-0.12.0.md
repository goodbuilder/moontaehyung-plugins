# 0.12.0 Explain-xlsx verification

## Scope

Adds Explain-xlsx as a domain-independent skill that creates reviewable XLSX companions when code-derived numerical results are packaged for review or sharing. It distinguishes live spreadsheet formulas from fixed code-produced values, keeps full raw datasets external, maps important workbook calculations to source code, and delegates workbook authoring to the existing Spreadsheets skill. No hooks, MCP servers, templates, or runtime dependencies are added.

## Checks

- Skill structure and frontmatter validator: PASS.
- Skill UI metadata parse and implicit invocation policy: PASS.
- Plugin manifest JSON parse, skill inventory, README, routing entry, and local links: PASS; the inventory is 13 existing skills plus Explain-xlsx.
- Project-neutrality review: PASS; the instructions cover both a trajectory calculation with a numerical loop and a non-Simulation cost/tax calculation without requiring domain-specific fields or sheet names. This is a scenario review, not an end-to-end workbook generation test.

