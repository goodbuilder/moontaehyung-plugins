# Engineering analysis and simulation

An Engineer first defines the decision the model can change. Name each control,
measurement, exogenous value and derived output. Locate the inputs and check units,
signs, coordinate conventions, time basis and initial conditions where applicable.
Keep unresolved dimensions explicit. When model predictions do not distinguish
the alternatives, change the test or retain the competing explanations.

For an authorized standard-library Python analysis on Linux, place the reviewed
model and a JSON case in the selected project. Invoke the installed RIS helper.

```sh
python3 "$RIS" --project "$PROJECT" simulate --model model.py --case case.json --timeout 10
```

The model receives the frozen case path in `sys.argv[1]` and emits one JSON object.
The case contains text for `question`, `model` (equation), `method`, `assumptions`,
`boundary` and `limits`, an `inputs` object with a matching `units` object, and
an integer `seed` or JSON null for a deterministic method. The Engineer must
actually use the specified seed in stochastic code. Include the data revision,
measurement errors, reference point and timestamps where relevant. For large
observations, use the existing Study/Metric evidence workflow and link the reduced
case to the original input. Each model and case is limited to 8 MiB.

The launcher copies the reviewed bytes to a temporary read-only input mount,
uses the system Python with an empty user environment, and exposes a temporary
filesystem to the model. It caps wall time, CPU time, address space, process count
and output file size. Its result identifies the code and case digests and contains
the executed output. This service is for reviewed research code. Host capabilities
and external tools require their own resource and permission boundary.

Use an analytically checkable limiting case, a normal case, an invalid condition
and perturbations that could reverse the choice. Compare against a separate
calculation and explain residuals and numerical error. Link decision-bearing
outputs to the question's canonical Study or findings with the case, code and
receipt. A selected option and a measured physical outcome have different owners.
A model failure, unavailable namespace or exhausted limit reopens the analysis
with its evidence and the smallest valid recovery. Never infer an experimental
result from successful program exit.

For a decision-bearing numerical output, include its unit in the case's `output_units`
object. Pass `--record-result QUESTION_ID FINDING_ID FIELD --expected-revision N`.
The same execution proposes just that named scalar or short vector and its applicable
conditions, pins both source files and retains failure state if execution stopped. The
knowledge owner reviews the proposal and the Auditor checks the result as warranted.
Inspect the question to obtain N (zero for a new question). An explicitly authorized
manual-policy record also needs `--authorize-record`. With restricted saving, omit these
options to run the analysis without persistent recording. A conflict returns the observed
result and pending proposal for reconciliation.
