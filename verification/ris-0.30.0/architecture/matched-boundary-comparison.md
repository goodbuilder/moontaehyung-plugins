# Matched publication-boundary development comparison

The original offline_handoff results are retained as an omission diagnostic, not a ranking. This second probe applies the same clean/defect pattern to the same publication boundary in all ten open candidate families. Actual `ris_findings.validate_finding`, `ris_delivery.paragraphs` and `ris_delivery.contains` helpers execute against the same fixture. No evaluation custodian data, model calls or external services are used.

Common mandatory quality: all four fact/limit/scope passages survive final publication. Common resource boundary: no providers or physical work, at most 100000 serialized payload bytes per case, identical exact repair rule. Every arm receives complete identical facts before publication; the defect removes the same negative-control sentence only at publication. Independent stewardship checks every arm; conditional routing changes optional specialty handoffs only.

**Observed:** 40/40 cases met the common quality/resource conditions. All 20 defect controls detected the one omitted sentence and needed one scripted repair; all 20 clean controls needed zero repairs. No architecture had a quality advantage on this deterministic contract.

| Family | Covered development role allocation | Fixed stewardship clean/defect bytes | Conditional clean/defect bytes | Why represented / what remains unknown |
|---|---|---:|---:|---|
| A0 | existing roles + Skill + Helper | 1300/1865 | 1300/1865 | Included as an open family; proxy route tests transport only, not this family’s semantic capability. |
| A1 | add knowledge-only agent | 2075/2640 | 1300/2640 | Included as an open family; proxy route tests transport only, not this family’s semantic capability. |
| A2 | add user-understanding agent | 2079/2644 | 1300/2644 | Included as an open family; proxy route tests transport only, not this family’s semantic capability. |
| A3 | combine knowledge and human | 2081/2646 | 1300/2646 | Included as an open family; proxy route tests transport only, not this family’s semantic capability. |
| A4 | separate Knowledge Steward and Mentor | 2845/3410 | 1300/3410 | Included as an open family; proxy route tests transport only, not this family’s semantic capability. |
| A5 | specialists including Strategist | 3621/4186 | 1300/4186 | Included as an open family; proxy route tests transport only, not this family’s semantic capability. |
| A6 | specialists including Librarian | 3620/4185 | 1300/4185 | Included as an open family; proxy route tests transport only, not this family’s semantic capability. |
| A7 | reallocate across existing agents | 2842/3402 | 1295/3402 | Included as an open family; proxy route tests transport only, not this family’s semantic capability. |
| A8 | general worker with dynamic specialization | 1299/1863 | 1299/1863 | Included as an open family; proxy route tests transport only, not this family’s semantic capability. |
| A9 | hybrid agents/skills/helpers | 2084/2649 | 1300/2649 | Included as an open family; proxy route tests transport only, not this family’s semantic capability. |

CPU and wall nanoseconds for 100 local iterations per case are in the adjacent JSON. Synthetic human interventions are mechanically zero; actual human minutes, model latency, provider cost and model/scientific quality are null/unknown. Timing includes helper validation and JSON serialization, excludes model generation, filesystem acquisition and runtime startup. Do not treat local microseconds as a provider cost or performance estimate.

All A0–A9 families are included rather than screened out. A0/A8 have one producer route; A1–A3 add their named specialty; A4 separates steward and mentor; A5/A6 add the named strategist/librarian; A7 proxies redistribution across three existing agents; A9 proxies conditional helper delegation. These allocations are minimal development representatives, not exhaustive definitions of the families. Family-level architecture claims require real implementations, matched budgets and semantic evaluations; none are selected or rejected here.

Independent stewardship here is a distinct scripted role label at a mandatory common boundary. It does not prove separate model principals, independent security authority or independent scientific judgment. Conditional clean routing uses a fixture control flag known by the harness; a real coordinator must learn a reliable trigger and account for its cost. Complete split handoffs detect the same omission as integrated work; the original lossy split diagnostic therefore provides no basis to prefer integrated work.

Reproduce: `python3 matched_boundary_probe.py`. Raw results: `matched_boundary_results.json`. The first script and original results are preserved unchanged.
