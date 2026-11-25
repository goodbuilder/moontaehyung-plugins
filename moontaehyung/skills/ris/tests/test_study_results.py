import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ris = load_module("ris_study_results_test_ris", SCRIPTS / "ris.py")
metrics = load_module("ris_study_results_test_metrics", SCRIPTS / "ris_metrics.py")
results = load_module("ris_study_results_test_module", SCRIPTS / "ris_results.py")


def definition(metric_id, threshold="75"):
    return {
        "id": metric_id,
        "format": "csv",
        "operation": "ratio",
        "where": {},
        "numerator_where": {"result": "pass"},
        "unit": "percent",
        "threshold": {"op": "ge", "value": threshold},
    }


def record(tmp_path, metric_id, revision, observation_id, *, passing, reported="80", threshold="75",
           input_name=None, conditions=None):
    input_name = input_name or f"data/{metric_id}.csv"
    path = tmp_path / input_name
    path.parent.mkdir(parents=True, exist_ok=True)
    row_count = 4
    pass_count = round(row_count * passing / 100)
    path.write_text("result\n" + "pass\n" * pass_count + "fail\n" * (row_count - pass_count), encoding="utf-8")
    metric_definition = definition(metric_id, threshold)
    calculated = metrics.calculate(ris, tmp_path, metric_definition, input_name)
    compared = metrics.compare_reported(metric_definition, calculated, reported)
    return {
        "definition": calculated["definition"],
        "input": input_name,
        "reported": compared["reported"],
        "result": calculated,
        "reported_status": compared["reported_status"],
        "decision_impact": {
            "reported_vs_computed": compared["decision_impact"],
            "across_revisions": None,
            "criterion": {"metric_id": metric_id, "threshold": calculated["definition"]["threshold"]},
            "affected_hypotheses": [],
            "review_recommended": compared["reported_status"] == "mismatch",
        },
        "hypotheses": [],
        "_revision": revision,
        "_observation_id": observation_id,
        "_conditions": conditions or {"batch": "A"},
    }


def observation(revision, observation_id, metric_records=(), *, conditions=None):
    records = [value for _, value in metric_records]
    return {
        "id": observation_id,
        "revision": revision,
        "conditions": conditions or (records[0]["_conditions"] if records else {"batch": "A"}),
        "metrics": [{key: value for key, value in item.items() if not key.startswith("_")} for item in records],
        "recommendation": "A prose recommendation must not enter the deterministic summary.",
    }


def snapshot(revision, observations, *, result_rule=None, conditions=None):
    value = {
        "id": "ST-RESULTS",
        "project_id": "P-RESULTS",
        "revision": revision,
        "conditions": conditions or {"batch": "A"},
        "observations": observations,
        "recommendation": "Do not copy this prose into the verified summary.",
        "user_decision": {"selection": "Keep candidate A", "revision": revision},
    }
    if result_rule is not None:
        value["result_rule"] = result_rule
    return value


def test_rule_validation_is_explicit_and_rejects_incomplete_or_duplicate_sets():
    error_api = SimpleNamespace(Error=RuntimeError)
    assert results.normalize_rule(error_api, {"mode": "all", "metric_ids": ["alpha", "beta"]}) == {
        "mode": "all", "metric_ids": ["alpha", "beta"]
    }
    for invalid in (
        {"mode": "all", "metric_ids": []},
        {"mode": "xor", "metric_ids": ["alpha"]},
        {"mode": "all", "metric_ids": ["alpha", "alpha"]},
        {"mode": "all", "metric_ids": ["alpha"], "extra": True},
    ):
        with pytest.raises(RuntimeError):
            results.normalize_rule(error_api, invalid)


def test_report_separates_original_reported_verdict_and_exact_recomputed_result(tmp_path):
    measured = record(tmp_path, "pass_rate", 2, "OBS-1", passing=50, reported="80")
    data = snapshot(2, [observation(2, "OBS-1", [("pass_rate", measured)])],
                    result_rule={"mode": "all", "metric_ids": ["pass_rate"]})

    report = results.build_results(data)

    row = report["criterion_results"][0]
    assert report["project_id"] == "P-RESULTS"
    assert row["reported_value"] == "80"
    assert row["computed_value"] == "50"
    assert row["unit"] == "percent"
    assert row["reported_verdict"] == "mismatch"
    assert row["reported_threshold"] == "pass"
    assert row["computed_threshold"] == "fail"
    assert row["correction_effect"] == "pass_to_fail"
    assert row["threshold_changed"] is True
    assert row["formula_identity"]["definition_sha256"] == measured["result"]["definition_sha256"]
    assert row["input"]["sha256"] == measured["result"]["input"]["sha256"]
    assert report["overall"]["reported"]["verdict"] == "pass"
    assert report["overall"]["computed"]["verdict"] == "fail"
    assert report["rule"]["source"] == "persisted"
    assert report["rule"]["effective_revision"] == 1
    assert "80%" in report["summary"]
    assert "50%" in report["summary"]
    assert "75% 이상" in report["summary"]
    assert "Do not copy this prose" not in report["summary"]
    assert "Keep candidate A" not in report["summary"]
    assert report["agent_recommendation"] == data["recommendation"]
    assert report["user_decision"] == data["user_decision"]


def test_any_rule_can_keep_overall_pass_when_one_criterion_flips(tmp_path):
    prior_a = record(tmp_path, "alpha", 2, "OBS-1", passing=100, reported="100")
    prior_b = record(tmp_path, "beta", 2, "OBS-1", passing=100, reported="100")
    current_a = record(tmp_path, "alpha", 3, "OBS-2", passing=50, reported="100")
    current_b = record(tmp_path, "beta", 3, "OBS-2", passing=100, reported="100")
    data = snapshot(3, [
        observation(2, "OBS-1", [("alpha", prior_a), ("beta", prior_b)]),
        observation(3, "OBS-2", [("alpha", current_a), ("beta", current_b)]),
    ])

    report = results.build_results(data, {"mode": "any", "metric_ids": ["alpha", "beta"]})

    rows = {row["metric_id"]: row for row in report["criterion_results"]}
    assert rows["alpha"]["prior_to_current"] == "pass_to_fail"
    assert rows["beta"]["prior_to_current"] == "pass_to_pass"
    assert report["overall"]["prior"]["computed"]["verdict"] == "pass"
    assert report["overall"]["computed"]["verdict"] == "pass"
    assert report["overall"]["prior_to_current_computed"] == "pass_to_pass"
    assert report["overall"]["prior_to_current_reported"] == "pass_to_pass"
    assert report["rule"]["source"] == "runtime_scenario"
    assert report["rule"]["effective_revision"] is None
    assert "가정" in report["summary"] and "이번 조회에만 적용" in report["summary"]
    markdown = results.render_results(report)
    assert "가정 규칙(이번 조회에만 적용)" in markdown


def test_all_rule_reports_changed_overall_and_pass_to_fail_correction(tmp_path):
    prior_a = record(tmp_path, "alpha", 2, "OBS-1", passing=100, reported="100")
    prior_b = record(tmp_path, "beta", 2, "OBS-1", passing=100, reported="100")
    current_a = record(tmp_path, "alpha", 3, "OBS-2", passing=100, reported="100")
    current_b = record(tmp_path, "beta", 3, "OBS-2", passing=0, reported="100")
    data = snapshot(3, [
        observation(2, "OBS-1", [("alpha", prior_a), ("beta", prior_b)]),
        observation(3, "OBS-2", [("alpha", current_a), ("beta", current_b)]),
    ])

    report = results.build_results(data, {"mode": "all", "metric_ids": ["alpha", "beta"]})

    assert report["overall"]["prior"]["computed"]["verdict"] == "pass"
    assert report["overall"]["reported"]["verdict"] == "pass"
    assert report["overall"]["computed"]["verdict"] == "fail"
    assert report["overall"]["reported_correction_effect"] == "pass_to_fail"
    assert report["overall"]["prior_to_current_computed"] == "pass_to_fail"


def test_fail_to_fail_is_reported_as_an_unchanged_overall_determination(tmp_path):
    prior = record(tmp_path, "alpha", 2, "OBS-1", passing=0, reported="0")
    current = record(tmp_path, "alpha", 3, "OBS-2", passing=0, reported="0")
    data = snapshot(3, [
        observation(2, "OBS-1", [("alpha", prior)]),
        observation(3, "OBS-2", [("alpha", current)]),
    ])

    report = results.build_results(data, {"mode": "all", "metric_ids": ["alpha"]})

    assert report["criterion_results"][0]["prior_to_current"] == "fail_to_fail"
    assert report["overall"]["prior"]["computed"]["verdict"] == "fail"
    assert report["overall"]["computed"]["verdict"] == "fail"
    assert report["overall"]["prior_to_current_computed"] == "fail_to_fail"
    assert report["overall"]["reported"]["verdict"] == "fail"
    assert report["overall"]["prior_to_current_reported"] == "fail_to_fail"


def test_missing_indeterminate_and_unregistered_conditions_remain_unknown(tmp_path):
    empty = snapshot(2, [], result_rule={"mode": "all", "metric_ids": ["missing"]})
    no_observation = results.build_results(empty)
    assert no_observation["overall"]["computed"]["verdict"] == "unknown"
    assert no_observation["overall"]["computed"]["missing_metric_ids"] == ["missing"]
    assert no_observation["criterion_results"] == []
    assert no_observation["missing_criteria"] == [{
        "metric_id": "missing", "record_status": "missing", "computed_threshold": "unknown",
        "reason": "no_measurement",
    }]
    assert "missing는 자료가 없어 미확정입니다" in no_observation["summary"]
    missing_markdown = results.render_results(no_observation, embedded=True)
    assert "| missing | — | — | 자료 없음 | 자료 없음 | — | — | — | — | 미확정 | — | — |" in missing_markdown
    assert "개정 None" not in missing_markdown
    assert "과거 관측이 없어 이전 전체 판정은 없습니다" in missing_markdown

    indeterminate = record(tmp_path, "empty_rate", 2, "OBS-1", passing=0, reported=None)
    path = tmp_path / indeterminate["input"]
    path.write_text("result\n", encoding="utf-8")
    indeterminate["result"] = metrics.calculate(
        ris, tmp_path, indeterminate["definition"], indeterminate["input"]
    )
    indeterminate["reported_status"] = "not_reported"
    obs = observation(2, "OBS-1", [("empty_rate", indeterminate)], conditions={"batch": "A", "device": "D1"})
    data = snapshot(2, [obs], result_rule={"mode": "all", "metric_ids": ["empty_rate"]})
    report = results.build_results(data)
    row = report["criterion_results"][0]
    assert row["computed_value"] is None
    assert row["computed_threshold"] == "unknown"
    assert report["overall"]["computed"]["verdict"] == "unknown"
    assert report["unregistered_conditions"] == [{
        "name": "device", "value": "D1", "observation_id": "OBS-1", "revision": 2
    }]
    assert "device" not in report["summary"]
    assert "device" in results.render_results(report, embedded=True)


def test_qualitative_study_has_no_inferred_metrics_or_overall():
    data = snapshot(1, [], conditions={"cohort": "A"})

    report = results.build_results(data)

    assert report["criterion_results"] == []
    assert report["overall"] is None
    assert "수치 지표 관측이 없습니다" in report["summary"]
    rendered = results.render_results(report)
    assert "명시된 전체 판정 규칙이 없어" in rendered
    assert "| 기록 없음 |" in rendered
    embedded = results.render_results(report, embedded=True)
    assert not embedded.startswith("# 연구 결과")
    assert "에이전트 권고" not in embedded
    assert "명시된 사용자 결정" not in embedded
    assert "| 지표 |" in embedded


def test_changed_definition_under_same_id_does_not_reinterpret_persisted_rule(tmp_path):
    prior = record(tmp_path, "alpha", 2, "OBS-1", passing=100, reported="100", threshold="75")
    current = record(tmp_path, "alpha", 3, "OBS-2", passing=100, reported="100", threshold="80")
    data = snapshot(3, [
        observation(2, "OBS-1", [("alpha", prior)]),
        observation(3, "OBS-2", [("alpha", current)]),
    ], result_rule={"mode": "all", "metric_ids": ["alpha"]})

    report = results.build_results(data)

    row = report["criterion_results"][0]
    assert row["computed_threshold"] == "pass"
    assert row["definition_changed"] is True
    assert row["prior_determination"]["comparable"] is False
    assert row["prior_to_current"] == "definition_changed"
    assert report["overall"]["computed"]["verdict"] == "unknown"
    assert report["overall"]["computed"]["definition_changed_metric_ids"] == ["alpha"]


def test_incompatible_observation_conditions_make_combined_criterion_unknown(tmp_path):
    alpha = record(tmp_path, "alpha", 2, "OBS-1", passing=100, reported="100", conditions={"run": "A"})
    beta = record(tmp_path, "beta", 3, "OBS-2", passing=100, reported="100", conditions={"run": "B"})
    data = snapshot(3, [
        observation(2, "OBS-1", [("alpha", alpha)], conditions={"run": "A"}),
        observation(3, "OBS-2", [("beta", beta)], conditions={"run": "B"}),
    ])

    report = results.build_results(data, {"mode": "all", "metric_ids": ["alpha", "beta"]})

    current = report["overall"]["computed"]
    assert current["verdict"] == "unknown"
    assert current["condition_scope_conflict"] is True
    assert current["incompatible_scope_metric_ids"] == ["alpha", "beta"]


def test_conflicting_hash_for_shared_input_path_blocks_combined_evaluation(tmp_path):
    alpha = record(tmp_path, "alpha", 2, "OBS-1", passing=100, reported="100", input_name="data/shared.csv")
    alpha_hash = alpha["result"]["input"]["sha256"]
    beta = record(tmp_path, "beta", 3, "OBS-2", passing=0, reported="100", input_name="data/shared.csv")
    assert beta["result"]["input"]["sha256"] != alpha_hash
    data = snapshot(3, [
        observation(2, "OBS-1", [("alpha", alpha)]),
        observation(3, "OBS-2", [("beta", beta)]),
    ])

    report = results.build_results(data, {"mode": "all", "metric_ids": ["alpha", "beta"]})

    current = report["overall"]["computed"]
    assert current["verdict"] == "unknown"
    assert current["conflicting_input_paths"] == ["data/shared.csv"]
    assert current["incompatible_scope_metric_ids"] == ["alpha", "beta"]


def test_same_conditions_and_matching_shared_input_hash_remain_combinable(tmp_path):
    alpha = record(tmp_path, "alpha", 2, "OBS-1", passing=100, reported="100", input_name="data/shared.csv")
    beta = record(tmp_path, "beta", 3, "OBS-2", passing=100, reported="100", input_name="data/shared.csv")
    assert beta["result"]["input"]["sha256"] == alpha["result"]["input"]["sha256"]
    data = snapshot(3, [
        observation(2, "OBS-1", [("alpha", alpha)]),
        observation(3, "OBS-2", [("beta", beta)]),
    ])

    report = results.build_results(data, {"mode": "all", "metric_ids": ["alpha", "beta"]})

    current = report["overall"]["computed"]
    assert current["verdict"] == "pass"
    assert current["condition_scope_conflict"] is False
    assert current["conflicting_input_paths"] == []


@pytest.mark.parametrize(
    "mode,measured,expected",
    [("any", "pass", "pass"), ("all", "fail", "fail")],
)
def test_logically_decisive_aggregation_survives_an_unmeasured_member(tmp_path, mode, measured, expected):
    value = record(tmp_path, "known", 2, "OBS-1", passing=100 if measured == "pass" else 0,
                   reported="100" if measured == "pass" else "0")
    data = snapshot(2, [observation(2, "OBS-1", [("known", value)])])

    report = results.build_results(data, {"mode": mode, "metric_ids": ["known", "not_yet_measured"]})

    aggregate = report["overall"]["computed"]
    assert aggregate["verdict"] == expected
    assert aggregate["missing_metric_ids"] == ["not_yet_measured"]


def test_rule_binding_revision_is_explicit_but_current_rule_can_use_prior_evidence(tmp_path):
    value = record(tmp_path, "alpha", 2, "OBS-1", passing=100, reported="100")
    data = snapshot(2, [observation(2, "OBS-1", [("alpha", value)])],
                    result_rule={"mode": "all", "metric_ids": ["alpha"]})
    data["result_rule_revision"] = 3

    report = results.build_results(data)

    assert report["rule"]["effective_revision"] == 3
    assert report["overall"]["status"] == "not_yet_effective"
    assert report["overall"]["computed"] is None

    data["revision"] = 3
    current = results.build_results(data)
    assert current["overall"]["computed"]["verdict"] == "pass"
    assert current["overall"]["prior"]["kind"] == "scenario_reconstruction"
    assert "당시 규칙을 뜻하지 않습니다" in current["summary"]


@pytest.mark.parametrize(
    "mode,known_value,expected",
    [("all", "fail", "fail"), ("any", "pass", "pass")],
)
def test_definition_changed_member_is_unknown_but_other_criterion_can_decide(tmp_path, mode, known_value, expected):
    prior = record(tmp_path, "changed", 2, "OBS-1", passing=100, reported="100", threshold="75")
    changed = record(tmp_path, "changed", 3, "OBS-2", passing=100, reported="100", threshold="80")
    known = record(tmp_path, "known", 3, "OBS-2", passing=100 if known_value == "pass" else 0,
                   reported="100" if known_value == "pass" else "0")
    data = snapshot(3, [
        observation(2, "OBS-1", [("changed", prior)]),
        observation(3, "OBS-2", [("changed", changed), ("known", known)]),
    ], result_rule={"mode": mode, "metric_ids": ["changed", "known"]})

    report = results.build_results(data)

    assert report["overall"]["computed"]["definition_changed_metric_ids"] == ["changed"]
    assert report["overall"]["computed"]["verdict"] == expected


def test_binding_after_prior_definition_change_uses_new_formula_without_old_conflict(tmp_path):
    old = record(tmp_path, "alpha", 2, "OBS-1", passing=100, reported="100", threshold="75")
    rebound = record(tmp_path, "alpha", 3, "OBS-2", passing=100, reported="100", threshold="80")
    data = snapshot(3, [
        observation(2, "OBS-1", [("alpha", old)]),
        observation(3, "OBS-2", [("alpha", rebound)]),
    ], result_rule={"mode": "all", "metric_ids": ["alpha"]})
    data["result_rule_revision"] = 3

    report = results.build_results(data)

    assert report["criterion_results"][0]["definition_changed"] is True
    assert report["overall"]["computed"]["verdict"] == "pass"
    assert report["overall"]["computed"]["definition_changed_metric_ids"] == []

