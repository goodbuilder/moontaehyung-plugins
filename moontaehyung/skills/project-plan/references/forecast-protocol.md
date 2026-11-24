# Forecast and observation protocol

Forecast alternatives under the same conditions and success criteria. For each option record:
expected outcome; prerequisites and resource/time requirements; benefits and tradeoffs; risk;
evidence IDs and actual review scope; uncertainty; a discriminating verification step; follow-up
choices and fallback/reconsideration trigger. Unknown is an acceptable value with a resolution route.
Numeric estimates need units, assumptions, observation/computation source and derivation. Use ranges
or scenarios only when justified, never invented probabilities. Recommendations are separate from
provisional assumptions and explicit confirmed selections. Hard constraints precede scoring.

Classify each material statement as one of: `VERIFIED FACT`, `CALCULATION`, `EVIDENCE-BASED
ESTIMATE`, `CONDITIONAL SCENARIO`, `ASSUMPTION`, or `UNKNOWN`. A fact names the source and the
portion actually reviewed. A calculation exposes its inputs, units, and method. An estimate states
the evidence and limitations supporting it. A scenario names its conditions and is not a prediction
that those conditions will occur. An assumption names its basis and a reconsideration trigger. An
unknown names what evidence or decision would resolve it, or why it is currently blocked.

Do not turn literature frequency, qualitative risk bands, or an uncalibrated forecast into a numeric
success probability. Compare candidates using the same assumptions and success criteria. Where
evidence cannot support a point estimate, retain the uncertainty or report comparable conditional
scenarios rather than adding false precision.

Record initial forecasts at their plan revision. Add dated observations with version/conditions,
method, evidence, differences from the original forecast and implicated assumptions. Preserve old
forecasts and decision events in append-only history rather than rewriting them to fit outcomes.
If the goal, assumption or selection changes, list affected downstream nodes as needing review;
keep unrelated nodes. Defer unstudied combinations and avoid automatic sum-of-benefits predictions.
For audit rework, identify the affected forecast, its canonical owner, and the exact correction or
new evidence required. Preserve earlier forecast and observation records when revising the current
assessment.
