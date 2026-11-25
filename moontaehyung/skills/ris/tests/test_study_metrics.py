import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ris = load_module("ris_study_metrics_test_helper", SCRIPTS / "ris.py")
study = load_module("ris_study_metrics_test_module", SCRIPTS / "ris_study.py")


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    ris.initialize(root, "Metric study test", "Record and review calculated evidence")
    study.start_study(ris, root, "ST-METRIC", start_body())
    return root


def start_body():
    return {
        "goal": "Check whether the measured pass rate clears the criterion",
        "criteria": ["The pass rate is at least 75 percent"],
        "conditions": {"batch": "A"},
        "hypotheses": [{
            "id": "H1",
            "statement": "The process meets its pass-rate criterion",
            "prediction": "At least three quarters of samples pass",
            "basis": {"kind": "assumption", "note": "Baseline claim to check"},
        }],
        "test": {"description": "Count outcomes", "method": "Calculate the pass fraction", "limits": []},
        "recommendation": "Collect a baseline",
        "rationale": "No local outcome file is recorded yet",
        "next_action": "Run the baseline",
        "evaluations": {"H1": {"assessment": "untested", "rationale": "No measurement yet"}},
    }


def observation_body(observation_id="OBS-0001"):
    return {
        "id": observation_id,
        "finding": "The pass rate was calculated from the outcome file",
        "locator": "research/exploration/log.md#R-0001",
        "evidence_kind": "derived",
        "conditions": {"batch": "A"},
        "limitations": ["One batch"],
        "evaluations": {"H1": {"assessment": "inconclusive", "rationale": "The observation needs review"}},
        "recommendation": "Review the observed pass rate",
        "rationale": "The calculation records the selected rows",
        "next_action": "Repeat with another batch",
    }


def metric_definition(metric_id="pass_rate", unit="percent", threshold="75"):
    return {
        "id": metric_id,
        "format": "csv",
        "operation": "ratio",
        "where": {"batch": "A"},
        "numerator_where": {"result": "pass"},
        "unit": unit,
        "threshold": {"op": "ge", "value": threshold},
    }


def write_metrics_file(tmp_path, *, input_path="data/outcomes.csv", reported="75", hypotheses=None, definition=None):
    metrics_path = tmp_path / "metrics.json"
    entry = {"definition": definition or metric_definition(), "input": input_path}
    if reported is not ...:
        entry["reported"] = reported
    if hypotheses is not None:
        entry["hypotheses"] = hypotheses
    metrics_path.write_text(json.dumps([entry]), encoding="utf-8")
    return metrics_path


def write_outcomes(project, rows):
    path = project / "data" / "outcomes.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("batch,result\n" + "".join(f"A,{row}\n" for row in rows), encoding="utf-8")
    return path


def test_metrics_are_only_generated_from_explicit_file_and_report_threshold_correction(project, tmp_path):
    write_outcomes(project, ["pass", "pass", "fail", "fail"])
    metrics_file = write_metrics_file(tmp_path, reported=75, hypotheses=["H1"])

    captured = study.observe_study(ris, project, "ST-METRIC", 1, observation_body(), metrics_file=str(metrics_file))
    metric = captured["observations"][0]["metrics"][0]

    assert metric["definition"]["id"] == "pass_rate"
    assert metric["input"] == "data/outcomes.csv"
    assert metric["reported"] == "75"
    assert metric["result"]["value"] == "50"
    assert metric["result"]["input"]["sha256"]
    assert metric["reported_status"] == "mismatch"
    assert metric["decision_impact"]["reported_vs_computed"] == "threshold_crossed"
    assert metric["decision_impact"]["criterion"] == {
        "metric_id": "pass_rate", "threshold": {"op": "ge", "value": "75"}
    }
    assert metric["decision_impact"]["affected_hypotheses"] == ["H1"]
    assert metric["decision_impact"]["review_recommended"] is True
    assert captured["metric_review"][0]["metric_id"] == "pass_rate"
    assert captured["user_decision"] is None
    assert "Affected criterion" in study_path(project).read_text(encoding="utf-8")
    assert "threshold" in study_path(project).read_text(encoding="utf-8")
    assert "The user selected" not in study_path(project).read_text(encoding="utf-8")
    assert ris.check(project)["errors"] == []

    body_supplied = {**observation_body("OBS-0002"), "metrics": [metric]}
    with pytest.raises(ris.Error, match="unsupported fields"):
        study.observe_study(ris, project, "ST-METRIC", 2, body_supplied)


def test_metric_review_detects_threshold_crossing_across_revisions_and_keeps_history(project, tmp_path):
    write_outcomes(project, ["pass", "pass", "pass", "fail"])
    metrics_file = write_metrics_file(tmp_path, reported=...)
    first = study.observe_study(ris, project, "ST-METRIC", 1, observation_body(), metrics_file=str(metrics_file))
    first_digest = first["observations"][0]["metrics"][0]["result"]["input"]["sha256"]
    assert first["observations"][0]["metrics"][0]["result"]["threshold_met"] is True

    write_outcomes(project, ["pass", "pass", "fail", "fail"])
    second = study.observe_study(
        ris, project, "ST-METRIC", 2, observation_body("OBS-0002"), metrics_file=str(metrics_file)
    )
    metric = second["observations"][1]["metrics"][0]
    assert metric["result"]["threshold_met"] is False
    assert metric["decision_impact"]["across_revisions"]["from_revision"] == 2
    assert metric["decision_impact"]["across_revisions"]["decision_impact"] == "threshold_crossed"
    assert metric["decision_impact"]["review_recommended"] is True
    historical = study.read_study(ris, project, "ST-METRIC", revision=2)
    assert historical["observations"][0]["metrics"][0]["result"]["input"]["sha256"] == first_digest


def test_reported_fraction_and_subunit_decimal_use_shared_exact_codec(project, tmp_path):
    write_outcomes(project, ["pass", "fail", "fail"])
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps([
        {"definition": metric_definition("decimal_rate", "fraction", "0.75"),
         "input": "data/outcomes.csv", "reported": 0.75},
        {"definition": metric_definition("fraction_rate", "fraction", "0.3"),
         "input": "data/outcomes.csv", "reported": "2/6"},
    ]), encoding="utf-8")

    captured = study.observe_study(ris, project, "ST-METRIC", 1, observation_body(), metrics_file=str(metrics_path))
    by_id = {metric["definition"]["id"]: metric for metric in captured["observations"][0]["metrics"]}
    assert by_id["decimal_rate"]["reported"] == "0.75"
    assert by_id["decimal_rate"]["reported_status"] == "mismatch"
    assert by_id["fraction_rate"]["reported"] == "1/3"
    assert by_id["fraction_rate"]["reported_status"] == "match"


def test_observation_definition_file_matches_inline_definition(project, tmp_path):
    write_outcomes(project, ["pass", "pass", "fail"])
    rule_path = project / "rules" / "pass-rate.json"
    rule_path.parent.mkdir(parents=True)
    rule_path.write_text(json.dumps(metric_definition()), encoding="utf-8")
    file_metrics = tmp_path / "file-metrics.json"
    file_metrics.write_text(json.dumps([{
        "definition_file": "rules/pass-rate.json", "input": "data/outcomes.csv", "reported": "66.666666666666666666666666666666666666666666666667"
    }]), encoding="utf-8")
    captured_file = study.observe_study(
        ris, project, "ST-METRIC", 1, observation_body(), metrics_file=str(file_metrics)
    )["observations"][0]["metrics"][0]

    study.start_study(ris, project, "ST-INLINE", start_body())
    inline_metrics = write_metrics_file(
        tmp_path, reported="66.666666666666666666666666666666666666666666666667"
    )
    captured_inline = study.observe_study(
        ris, project, "ST-INLINE", 1, observation_body("OBS-INLINE"), metrics_file=str(inline_metrics)
    )["observations"][0]["metrics"][0]
    assert captured_file["definition"] == captured_inline["definition"]
    assert captured_file["result"] == captured_inline["result"]


def test_metric_retry_is_idempotent_with_original_digest_and_changed_input_conflicts(project, tmp_path):
    outcomes = write_outcomes(project, ["pass", "fail"])
    metrics_file = write_metrics_file(tmp_path, reported="50.0")
    first = study.observe_study(ris, project, "ST-METRIC", 1, observation_body(), metrics_file=str(metrics_file))
    original_digest = first["observations"][0]["metrics"][0]["result"]["input"]["sha256"]

    duplicate = study.observe_study(ris, project, "ST-METRIC", 1, observation_body(), metrics_file=str(metrics_file))
    assert duplicate["status"] == "already_recorded"
    assert duplicate["observations"][0]["metrics"][0]["result"]["input"]["sha256"] == original_digest

    outcomes.write_text("batch,result\nA,pass\nA,pass\n", encoding="utf-8")
    with pytest.raises(ris.Error, match="different content"):
        study.observe_study(ris, project, "ST-METRIC", 1, observation_body(), metrics_file=str(metrics_file))
    assert study.read_study(ris, project, "ST-METRIC")["observations"][0]["metrics"][0]["result"]["input"]["sha256"] == original_digest


def test_missing_input_is_indeterminate_repeatable_and_never_zero(project, tmp_path):
    metrics_file = write_metrics_file(tmp_path, reported=...)
    first = study.observe_study(ris, project, "ST-METRIC", 1, observation_body(), metrics_file=str(metrics_file))
    metric = first["observations"][0]["metrics"][0]
    assert metric["result"]["status"] == "indeterminate"
    assert metric["result"]["value"] is None
    assert metric["result"]["denominator"] is None
    assert metric["result"]["definition_sha256"]
    assert metric["result"]["input"]["sha256"] is None
    assert metric["reported_status"] == "not_reported"
    assert metric["decision_impact"]["review_recommended"] is True

    duplicate = study.observe_study(ris, project, "ST-METRIC", 1, observation_body(), metrics_file=str(metrics_file))
    assert duplicate["status"] == "already_recorded"
    assert duplicate["observations"][0]["metrics"][0]["result"] == metric["result"]
    assert "indeterminate" in study_path(project).read_text(encoding="utf-8")


def test_duplicate_metric_id_and_inconsistent_captured_digest_fail_before_write(project, tmp_path, monkeypatch):
    write_outcomes(project, ["pass", "fail"])
    metrics_path = tmp_path / "metrics.json"
    entry = {"definition": metric_definition(), "input": "data/outcomes.csv"}
    metrics_path.write_text(json.dumps([entry, entry]), encoding="utf-8")
    with pytest.raises(ris.Error, match="duplicate metric definition"):
        study.observe_study(ris, project, "ST-METRIC", 1, observation_body(), metrics_file=str(metrics_path))
    assert study.read_study(ris, project, "ST-METRIC")["revision"] == 1

    normalized = ris.companion("ris_metrics").normalize_definition(ris, metric_definition())
    fake_metrics = SimpleNamespace(
        normalize_definition=lambda _ris, definition: normalized,
        normalize_reported=lambda _ris, value: value,
        calculate=lambda _ris, _root, _definition, input_path: {
            "status": "ok", "metric_id": "pass_rate", "definition": normalized,
            "definition_sha256": "1" * 64, "value": "50", "numerator": 1,
            "denominator": 2, "unit": "percent", "threshold_met": False,
            "input": {"path": input_path, "sha256": "0" * 64},
        },
    )
    metrics_path.write_text(json.dumps([entry]), encoding="utf-8")
    monkeypatch.setattr(ris, "companion", lambda _name: fake_metrics)
    with pytest.raises(ris.Error, match="input changed while capturing evidence"):
        study.observe_study(
            ris, project, "ST-METRIC", 1, observation_body(),
            evidence_paths=["data/outcomes.csv"], metrics_file=str(metrics_path),
        )
    assert study.read_study(ris, project, "ST-METRIC")["revision"] == 1


def test_old_qualitative_snapshots_keep_shape_and_cli_observe_accepts_metrics_file(project, tmp_path, capsys):
    original = study.read_study(ris, project, "ST-METRIC")
    assert "metric_review" not in original
    write_outcomes(project, ["pass", "fail"])
    body_file = tmp_path / "observation.json"
    body_file.write_text(json.dumps(observation_body()), encoding="utf-8")
    metrics_file = write_metrics_file(tmp_path, reported=50)
    status = ris.main([
        "--project", str(project), "study", "observe", "ST-METRIC", "--expected-revision", "1",
        "--body-file", str(body_file), "--metrics-file", str(metrics_file),
    ])
    output = json.loads(capsys.readouterr().out)
    assert status == 0
    assert output["observations"][0]["metrics"][0]["definition"]["id"] == "pass_rate"
    with pytest.raises(ris.Error, match="unsupported fields"):
        study.observe_study(ris, project, "ST-METRIC", 1, {**observation_body(), "metrics": []})


def study_path(project):
    cfg = ris.config(project)
    return project / cfg["research_dir"] / "decisions" / "study-ST-METRIC.md"
