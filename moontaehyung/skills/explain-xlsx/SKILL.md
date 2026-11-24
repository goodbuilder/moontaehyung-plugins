---
name: explain-xlsx
description: Create formula-traceable XLSX workbooks alongside code-derived numerical results. Use across simulation, research, engineering, analytics, operations, and other quantitative projects when producing a reportable result artifact, or when asked to explain calculations in a workbook. Not for routine data export or unrelated spreadsheet editing.
---

# Explain-xlsx

Use this skill when a task produces or packages code-derived numerical results for review or sharing. Treat an XLSX as a standard companion artifact unless the user or project format excludes it. Do not create one for a quick exploratory answer or routine status update. This workflow applies across domains; do not assume a particular project, model, sheet layout, or formula set. This skill owns code-to-cell traceability. For workbook authoring and formatting, follow the available Spreadsheets skill and its tool requirements.

## Trace the calculation

1. Identify the requested outputs and intended readers. Inspect the relevant source code, configuration, input files, and existing result artifacts. Trace the actual calculation path from each reported output to its inputs; do not infer equations from names or descriptions alone.
2. Preserve the code's conditions, units, signs, scaling, precision, rounding, missing-value handling, and domain meaning. Distinguish measured or model-produced values, assumptions, and values derived by formulas. Record the code revision or file hash and input provenance when available.
3. Design a report-first workbook for the task, with supporting calculation and source details behind the summary. Use the project and reader's language for labels and explanations. Choose sheets and charts only when they help the reader. Do not impose a reusable fixed template.
4. Keep full raw datasets in their existing files. Add only the rows, columns, and assumptions needed to recalculate workbook formulas. Record each source file and the used range or selection rule, plus a hash or version when available. Prefer embedded inputs with provenance over fragile external workbook links.

## Build the calculation trail

- Recreate the explicit, tractable calculations that lead to the requested outputs as spreadsheet formulas. Show meaningful intermediate values so readers can follow the sequence without hiding the calculation in one dense formula.
- Add a Formula Map sheet that connects each important workbook result or formula range to its meaning, unit, workbook cell, source file, function or symbol, code line, original expression, and spreadsheet formula. Include source revision information when available.
- For large loops, specialized numerical routines, or external-library algorithms that are impractical to reproduce faithfully in cells, keep the code-produced value as a clearly labeled fixed input. Map it to the source code, algorithm or library version, and its input/output context. Keep downstream spreadsheet formulas live and state which part does not recalculate in the workbook.
- If a required input or calculation rule is unclear, ask or mark the result unavailable. Never invent a formula, silently substitute a value, or imply that the workbook reruns code it only documents.
- Use formulas supported by both Excel and LibreOffice and do not use macros.

## Check and deliver

- Recalculate the workbook in an available spreadsheet engine and check for formula errors and broken references. Confirm that changing an embedded input updates dependent formulas.
- Compare representative spreadsheet outputs with the corresponding code results. Use exact comparison or a task-supported tolerance; do not invent a tolerance. Explain any expected differences from rounding or from fixed code-produced values.
- Check that important outputs and non-spreadsheet calculations are represented in the Formula Map, and that fixed values are clearly distinguished from live formulas.
- Deliver the XLSX as the primary artifact. State which calculations recalculate in the workbook and identify any material fixed-code exceptions.
