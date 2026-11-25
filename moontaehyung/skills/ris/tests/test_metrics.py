import argparse
import hashlib
import importlib.util
import json
import os
from decimal import Decimal
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ris = load_module("ris_metrics_test_ris", SCRIPTS / "ris.py")
metrics = load_module("ris_metrics_test_module", SCRIPTS / "ris_metrics.py")


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    return root


def write_input(root, relative, data):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
    return path


def parser():
    top = argparse.ArgumentParser()
    sub = top.add_subparsers(dest="command", required=True)
    metrics.add_parser(sub)
    return top


def test_csv_count_handles_bom_quoting_unicode_and_preserves_string_values(project):
    raw = "\ufeffgroup,flag,note\nα,01,\"hello, \"\"세계\"\"\"\nα,1,other\n".encode("utf-8")
    write_input(project, "data/events.csv", raw)
    definition = {
        "id": "count_alpha",
        "format": "csv",
        "operation": "count",
        "where": {"group": "α", "flag": "01"},
        "unit": "rows",
    }

    result = metrics.calculate(ris, project, definition, "data/events.csv")

    assert result["status"] == "ok"
    assert result["value"] == "1"
    assert result["numerator"] is None and result["denominator"] == 1
    assert result["input"]["sha256"] == hashlib.sha256(raw).hexdigest()


def test_jsonl_ratio_uses_typed_equality_and_matches_exact_empty_array(project):
    raw = (
        '{"cohort":"A","done":true,"tags":[]}\n'
        '{"cohort":"A","done":1,"tags":[]}\n'
        '{"cohort":"A","done":false,"tags":[]}\n'
        '{"cohort":"B","done":true,"tags":[]}\n'
    ).encode("utf-8")
    write_input(project, "data/events.jsonl", raw)
    definition = {
        "id": "completion_rate",
        "format": "jsonl",
        "operation": "ratio",
        "where": {"cohort": "A", "tags": []},
        "numerator_where": {"done": True},
        "unit": "fraction",
        "threshold": {"op": "gt", "value": "0.3333333333333333333333333333"},
    }

    result = metrics.calculate(ris, project, definition, "data/events.jsonl")

    assert result["status"] == "ok"
    assert (result["numerator"], result["denominator"]) == (1, 3)
    assert result["exact_value"] == "1/3"
    assert result["value_representation"] == "decimal_rounded"
    assert result["value_rounding"] == "50 significant decimal digits, ROUND_HALF_EVEN"
    assert result["threshold_met"] is True


def test_exact_threshold_boundary_and_comparison_reported_rational(project):
    write_input(project, "data/events.jsonl", '{"group":"A","hit":true}\n{"group":"A","hit":false}\n')
    definition = {
        "id": "half",
        "format": "jsonl",
        "operation": "ratio",
        "where": {"group": "A"},
        "numerator_where": {"hit": True},
        "unit": "fraction",
        "threshold": {"op": "eq", "value": Decimal("0.5")},
    }

    result = metrics.calculate(ris, project, definition, "data/events.jsonl")

    assert result["threshold_met"] is True
    assert result["definition"]["threshold"] == {"op": "eq", "value": "0.5"}
    assert metrics.compare_reported(definition, result, "1/2") == {
        "reported": "1/2", "reported_status": "match", "decision_impact": "threshold_unchanged", "reason": None,
    }
    crossed = metrics.compare_reported(definition, result, "0.499")
    assert crossed["reported_status"] == "mismatch"
    assert crossed["decision_impact"] == "threshold_crossed"
    assert metrics.compare_reported(definition, result, Decimal("0.5"))["reported_status"] == "match"


def test_ratio_without_denominator_is_indeterminate_not_zero(project):
    write_input(project, "data/events.jsonl", '{"group":"B","hit":true}\n')
    definition = {
        "id": "empty_rate", "format": "jsonl", "operation": "ratio",
        "where": {"group": "A"}, "numerator_where": {"hit": True}, "unit": "percent",
    }

    result = metrics.calculate(ris, project, definition, "data/events.jsonl")

    assert result["status"] == "indeterminate"
    assert "denominator is zero" in result["reason"]
    assert result["value"] is None
    assert (result["numerator"], result["denominator"]) == (0, 0)
    assert result["input"]["sha256"]
    assert result["definition_sha256"]


def test_ratio_requires_explicit_numerator_filter():
    definition = {
        "id": "rate", "format": "jsonl", "operation": "ratio", "where": {}, "unit": "fraction",
    }

    with pytest.raises(ris.Error, match="must declare numerator_where"):
        metrics.normalize_definition(ris, definition)


def test_ratio_allows_explicit_empty_numerator_filter(project):
    write_input(project, "data/events.jsonl", '{"group":"A"}\n{"group":"A"}\n')
    definition = {
        "id": "population_share", "format": "jsonl", "operation": "ratio",
        "where": {"group": "A"}, "numerator_where": {}, "unit": "fraction",
    }

    result = metrics.calculate(ris, project, definition, "data/events.jsonl")

    assert result["status"] == "ok"
    assert result["value"] == "1"
    assert (result["numerator"], result["denominator"]) == (2, 2)


@pytest.mark.parametrize(
    ("contents", "reason"),
    [
        ('{"a":1,"a":2}\n', "duplicate JSON object key"),
        ('[]\n', "must contain a JSON object"),
        ('{"a":1}\nnot-json\n', "is malformed"),
    ],
)
def test_malformed_jsonl_is_indeterminate_with_snapshot_hash(project, contents, reason):
    raw = contents.encode("utf-8")
    write_input(project, "data/events.jsonl", raw)
    definition = {"id": "count_a", "format": "jsonl", "operation": "count", "where": {}, "unit": "rows"}

    result = metrics.calculate(ris, project, definition, "data/events.jsonl")

    assert result["status"] == "indeterminate"
    assert reason in result["reason"]
    assert result["value"] is None
    assert result["input"]["sha256"] == hashlib.sha256(raw).hexdigest()


def test_duplicate_or_missing_csv_columns_are_indeterminate(project):
    write_input(project, "data/duplicate.csv", "group,group\nA,A\n")
    definition = {"id": "count_a", "format": "csv", "operation": "count", "where": {"group": "A"}, "unit": "rows"}

    duplicate = metrics.calculate(ris, project, definition, "data/duplicate.csv")
    write_input(project, "data/missing.csv", "other\nA\n")
    missing = metrics.calculate(ris, project, definition, "data/missing.csv")

    assert duplicate["status"] == "indeterminate" and "duplicate column" in duplicate["reason"]
    assert missing["status"] == "indeterminate" and "missing required columns" in missing["reason"]


def test_missing_input_retains_normalized_definition_without_fake_value(project):
    definition = {"id": "missing", "format": "csv", "operation": "count", "where": {}, "unit": "rows"}

    result = metrics.calculate(ris, project, definition, "data/not-there.csv")

    assert result["status"] == "indeterminate"
    assert result["value"] is None
    assert result["definition"]["id"] == "missing"
    assert result["definition_sha256"]
    assert result["input"] == {"path": "data/not-there.csv", "sha256": None}


def test_unsafe_paths_and_internal_or_broken_symlinks_are_refused(project, tmp_path):
    definition = {"id": "count_all", "format": "csv", "operation": "count", "where": {}, "unit": "rows"}
    write_input(project, "data.csv", "x\n1\n")
    (project / "link.csv").symlink_to(project / "data.csv")
    (project / "broken.csv").symlink_to(project / "missing.csv")

    for unsafe in ("../outside.csv", str(project / "data.csv"), "link.csv", "broken.csv"):
        with pytest.raises(ris.Error):
            metrics.calculate(ris, project, definition, unsafe)

    outside = tmp_path / "outside.csv"
    outside.write_text("x\n1\n", encoding="utf-8")
    (project / "external.csv").symlink_to(outside)
    with pytest.raises(ris.Error):
        metrics.calculate(ris, project, definition, "external.csv")


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO files are unavailable on this platform")
def test_nonregular_fifo_input_is_refused_without_blocking(project):
    definition = {"id": "count_all", "format": "csv", "operation": "count", "where": {}, "unit": "rows"}
    os.mkfifo(project / "events.csv")

    with pytest.raises(ris.Error, match="regular file"):
        metrics.calculate(ris, project, definition, "events.csv")


def test_compare_results_reports_exact_value_change_even_without_threshold(project):
    definition = {"id": "count_a", "format": "jsonl", "operation": "count", "where": {"group": "A"}, "unit": "rows"}
    write_input(project, "data/one.jsonl", '{"group":"A"}\n{"group":"B"}\n')
    write_input(project, "data/two.jsonl", '{"group":"A"}\n{"group":"A"}\n')
    one = metrics.calculate(ris, project, definition, "data/one.jsonl")
    two = metrics.calculate(ris, project, definition, "data/two.jsonl")

    comparison = metrics.compare_results(one, two)

    assert comparison["status"] == "ok"
    assert comparison["decision_impact"] == "no_threshold"
    assert comparison["value_difference"] == "1"
    assert comparison["exact_value_difference"] == "1"
    assert comparison["unit"] == "rows"
    assert metrics.compare_results(one, {**two, "definition_sha256": "0" * 64})["status"] == "indeterminate"


def test_normalize_rejects_ambiguous_schema_and_high_precision_filter_numbers():
    base = {"id": "count_a", "format": "jsonl", "operation": "count", "where": {}, "unit": "rows"}
    with pytest.raises(ris.Error, match="unsupported fields"):
        metrics.normalize_definition(ris, {**base, "extra": True})
    with pytest.raises(ris.Error, match="represented exactly"):
        metrics.normalize_definition(ris, {**base, "where": {"x": Decimal("1.234567890123456789")}})


def test_cli_run_and_compare_input_use_baseline_then_variant_orientation(project, tmp_path):
    write_input(project, "data/base.jsonl", '{"group":"A"}\n')
    write_input(project, "data/variant.jsonl", '{"group":"A"}\n{"group":"A"}\n')
    definition_path = tmp_path / "metric.json"
    definition_path.write_text(json.dumps({
        "id": "count_a", "format": "jsonl", "operation": "count", "where": {"group": "A"}, "unit": "rows",
    }), encoding="utf-8")
    args = parser().parse_args([
        "metric", "run", "--definition", str(definition_path), "--input", "data/base.jsonl",
        "--compare-input", "data/variant.jsonl",
    ])

    output = metrics.dispatch(ris, project, args)

    assert output["status"] == "ok"
    assert output["input_comparison"]["value_difference"] == "1"
    assert output["input_comparison"]["unit"] == "rows"
    assert output["compare_input_result"]["input"]["path"] == "data/variant.jsonl"


def test_cli_malformed_definition_returns_indeterminate_with_input_digest(project, tmp_path):
    raw = b"not json"
    definition_path = tmp_path / "bad.json"
    definition_path.write_bytes(raw)
    input_bytes = b'{"group":"A"}\n'
    write_input(project, "data/events.jsonl", input_bytes)
    args = parser().parse_args(["metric", "run", "--definition", str(definition_path), "--input", "data/events.jsonl"])

    output = metrics.dispatch(ris, project, args)

    assert output["status"] == "indeterminate"
    assert "invalid metric definition" in output["reason"]
    assert output["input"]["sha256"] == hashlib.sha256(input_bytes).hexdigest()


def test_cli_replays_study_metric_and_compares_to_pinned_result(project, monkeypatch):
    definition = {
        "id": "count_a", "format": "jsonl", "operation": "count", "where": {"group": "A"}, "unit": "rows",
    }
    write_input(project, "data/previous.jsonl", '{"group":"B"}\n')
    write_input(project, "data/current.jsonl", '{"group":"A"}\n')
    previous = metrics.calculate(ris, project, definition, "data/previous.jsonl")
    snapshot = {
        "observations": [{
            "id": "OBS-1",
            "metrics": [{"definition": metrics.normalize_definition(ris, definition), "result": previous}],
        }],
    }

    class Study:
        @staticmethod
        def read_study(_ris, _root, study_id, revision):
            assert study_id == "ST-1" and revision == 1
            return snapshot

    monkeypatch.setattr(ris, "companion", lambda name: Study if name == "ris_study" else None)
    args = parser().parse_args([
        "metric", "run", "--study", "ST-1", "--revision", "1", "--observation", "OBS-1",
        "--metric", "count_a", "--input", "data/current.jsonl",
    ])

    output = metrics.dispatch(ris, project, args)

    assert output["status"] == "ok"
    assert output["previous_comparison"]["decision_impact"] == "no_threshold"
    assert output["previous_comparison"]["value_difference"] == "1"
