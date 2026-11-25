import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ris = load_module("ris_study_amend_helper", SCRIPTS / "ris.py")
study = load_module("ris_study_amend_module", SCRIPTS / "ris_study.py")


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    ris.initialize(root, "Study amendment test", "Preserve hypothesis and test history")
    return root


def start_body(*, result_rule=True):
    body = {
        "goal": "Determine whether the response changes under a second condition",
        "criteria": ["Measure a response outside the baseline tolerance"],
        "conditions": {"temperature": "20 C", "replicates": "3"},
        "hypotheses": [
            {
                "id": "H1",
                "statement": "The response remains stable across repetitions",
                "prediction": "The response stays within tolerance",
                "basis": {"kind": "publication", "locator": "research/literature/prior.md#result", "note": "Prior result"},
            },
            {
                "id": "H2",
                "statement": "The response depends on temperature",
                "prediction": "A higher temperature changes the response",
                "basis": {"kind": "assumption", "locator": "", "note": "Working explanation"},
            },
        ],
        "test": {"description": "Repeat the baseline measurement", "method": "Measure three replicates", "limits": ["One temperature"]},
        "recommendation": "Collect the baseline first",
        "rationale": "No local measurement is recorded yet",
        "next_action": "Run the baseline measurement",
        "evaluations": {
            "H1": {"assessment": "untested", "rationale": "No observation yet"},
            "H2": {"assessment": "untested", "rationale": "No observation yet"},
        },
    }
    if result_rule:
        body["result_rule"] = {"mode": "all", "metric_ids": ["pass_rate"]}
    return body


def observation_body(observation_id="OBS-0001", *, locator="research/exploration/log.md#R-0001", next_test=True):
    body = {
        "id": observation_id,
        "finding": "All three baseline replicates stayed within tolerance",
        "locator": locator,
        "evidence_kind": "source",
        "conditions": {"temperature": "20 C", "replicates": "3"},
        "limitations": ["Only one temperature was tested"],
        "evaluations": {
            "H1": {"assessment": "supported", "rationale": "The replicates met the prediction"},
            "H2": {"assessment": "inconclusive", "rationale": "No temperature comparison was run"},
        },
        "recommendation": "Compare the response at a second temperature",
        "rationale": "The baseline supports H1 but does not test H2",
        "next_action": "Measure at 25 C",
    }
    if next_test:
        body["next_test"] = {
            "description": "Compare the response at 25 C",
            "method": "Measure three replicates at 25 C",
            "limits": ["One additional temperature"],
            "predictions": {"H1": "Response stays within tolerance", "H2": "Response changes"},
        }
    return body


def decision_body():
    return {
        "id": "DEC-0001",
        "selection": "H1",
        "rationale": "The user selected H1 for the next analysis",
        "locator": "user:turn-24#choice",
    }


def split_amendment():
    return {
        "id": "AMD-0001",
        "rationale": "The baseline left two distinct mechanisms inside H1; separate their predictions before the next comparison.",
        "triggering_observation_ids": ["OBS-0001"],
        "basis": {"kind": "observation", "observation_ids": ["OBS-0001"]},
        "added_hypotheses": [
            {
                "id": "H3",
                "statement": "The apparent stability is caused by a reversible response",
                "prediction": "The response returns within tolerance after a temperature change",
                "parent_id": "H1",
            },
            {
                "id": "H4",
                "statement": "The apparent stability is caused by a persistent response",
                "prediction": "The response returns within tolerance after a temperature change",
                "parent_id": "H1",
            },
        ],
        "next_test": {
            "description": "Compare the response at 25 C",
            "method": "Measure three replicates at 25 C",
            "limits": ["One additional temperature"],
            "predictions": {
                "H2": "The response changes at 25 C",
                "H3": "The response returns within tolerance after cooling",
                "H4": "The response returns within tolerance after cooling",
            },
        },
    }


def metric_definition():
    return {
        "id": "pass_rate",
        "format": "csv",
        "operation": "ratio",
        "where": {"batch": "A"},
        "numerator_where": {"result": "pass"},
        "unit": "percent",
        "threshold": {"op": "ge", "value": "75"},
    }


def write_metric_inputs(project, tmp_path):
    data = project / "data" / "outcomes.csv"
    data.parent.mkdir(parents=True)
    data.write_text("batch,result\nA,pass\nA,pass\nA,fail\nA,fail\n", encoding="utf-8")
    request = tmp_path / "metrics.json"
    request.write_text(json.dumps([{
        "definition": metric_definition(),
        "input": "data/outcomes.csv",
        "reported": "75",
        "hypotheses": ["H1"],
    }]), encoding="utf-8")
    return request


def test_split_keeps_old_views_decision_metrics_and_observation_retry(project, tmp_path):
    created = study.start_study(ris, project, "ST-AMEND", start_body())
    metrics_file = write_metric_inputs(project, tmp_path)
    measured = study.observe_study(
        ris, project, "ST-AMEND", 1, observation_body(), metrics_file=str(metrics_file)
    )
    decided = study.decide_study(ris, project, "ST-AMEND", 2, decision_body())
    old_views = {revision: study.read_study(ris, project, "ST-AMEND", revision) for revision in (1, 2, 3)}
    assert measured["observations"][0]["metrics"][0]["result"]["input"]["sha256"] == hashlib.sha256(
        (project / "data" / "outcomes.csv").read_bytes()
    ).hexdigest()
    assert old_views[3]["user_decision"]["selection"] == "H1"

    amended = study.amend_study(ris, project, "ST-AMEND", 3, split_amendment())
    assert amended["revision"] == 4 and amended["status"] == "recorded"
    assert amended["active_hypothesis_ids"] == ["H2", "H3", "H4"]
    assert amended["retired_hypothesis_ids"] == ["H1"]
    assert amended["evaluations"]["H2"]["assessment"] == "inconclusive"
    assert amended["evaluations"]["H3"]["assessment"] == "untested"
    assert amended["evaluations"]["H4"]["assessment"] == "untested"
    assert amended["user_decision"]["selection"] == "H1"
    assert amended["indistinguishable_groups"] == [["H3", "H4"]]
    assert len(amended["warnings"]) == 1
    assert study.read_study(ris, project, "ST-AMEND")["prediction_warnings"] == amended["warnings"]
    assert amended["result_rule"] == {"mode": "all", "metric_ids": ["pass_rate"]}
    assert amended["result_rule_revision"] == 1
    assert amended["hypotheses"][0]["id"] == "H1"  # Retired history remains visible.
    assert "H1" not in amended["evaluations"]
    for revision, before in old_views.items():
        assert study.read_study(ris, project, "ST-AMEND", revision) == before

    retry = study.amend_study(ris, project, "ST-AMEND", 3, split_amendment())
    assert retry["status"] == "already_recorded" and retry["recorded_revision"] == 4
    with pytest.raises(ris.Error, match="different content"):
        study.amend_study(ris, project, "ST-AMEND", 4, {**split_amendment(), "rationale": "Changed retry"})
    with pytest.raises(ris.Error, match="changed since revision"):
        study.amend_study(ris, project, "ST-AMEND", 3, {
            **split_amendment(), "id": "AMD-STALE", "rationale": "A new stale amendment",
        })

    observation_retry = study.observe_study(
        ris, project, "ST-AMEND", 1, observation_body(), metrics_file=str(metrics_file)
    )
    assert observation_retry["status"] == "already_recorded"
    assert observation_retry["recorded_revision"] == 2
    assert observation_retry["revision"] == 4
    assert observation_retry["observations"][0]["metrics"] == old_views[2]["observations"][0]["metrics"]

    reused = observation_body("OBS-0002", next_test=False)
    reused["evaluations"] = {
        "H2": {"assessment": "inconclusive", "rationale": "Not resolved"},
        "H3": {"assessment": "supported", "rationale": "The same source appears consistent"},
        "H4": {"assessment": "inconclusive", "rationale": "Not resolved"},
    }
    with pytest.raises(ris.Error, match="reuses the motivating locator or evidence"):
        study.observe_study(ris, project, "ST-AMEND", 4, reused)
    assert study.read_study(ris, project, "ST-AMEND")["revision"] == 4

    fresh = observation_body("OBS-0002", locator="research/exploration/log.md#R-0002", next_test=False)
    fresh["evaluations"] = {
        "H2": {"assessment": "inconclusive", "rationale": "The second condition remains insufficient"},
        "H3": {"assessment": "supported", "rationale": "The fresh cooling result matched H3"},
        "H4": {"assessment": "inconclusive", "rationale": "The result does not resolve H4"},
    }
    after_test = study.observe_study(ris, project, "ST-AMEND", 4, fresh)
    assert after_test["revision"] == 5
    assert set(after_test["evaluations"]) == {"H2", "H3", "H4"}
    assert after_test["evaluations"]["H3"]["assessment"] == "supported"
    assert after_test["user_decision"]["selection"] == "H1"
    assert after_test["active_test"]["description"] == "Compare the response at 25 C"

    rule_only = {
        "id": "AMD-0002",
        "rationale": "Bind the explicit acceptance rule from the reviewed criteria note.",
        "triggering_observation_ids": [],
        "basis": {"kind": "independent", "locator": "research/decisions/acceptance.md#pass-rate"},
        "added_hypotheses": [],
        "result_rule": {"mode": "any", "metric_ids": ["pass_rate"]},
    }
    rule_revision = study.amend_study(ris, project, "ST-AMEND", 5, rule_only)
    assert rule_revision["revision"] == 6
    assert rule_revision["result_rule"] == {"mode": "any", "metric_ids": ["pass_rate"]}
    assert rule_revision["result_rule_revision"] == 6
    assert study.read_study(ris, project, "ST-AMEND", revision=5)["result_rule"] == {
        "mode": "all", "metric_ids": ["pass_rate"]
    }
    assert study.read_study(ris, project, "ST-AMEND", revision=5)["result_rule_revision"] == 1
    assert decided["revision"] == 3 and created["revision"] == 1


def test_split_requires_two_children_and_trigger_ids_must_be_earlier(project):
    study.start_study(ris, project, "ST-AMEND", start_body(result_rule=False))
    one_child = {
        "id": "AMD-BAD",
        "rationale": "Try a one-child split",
        "triggering_observation_ids": [],
        "basis": {"kind": "independent", "locator": "research/literature/mechanism.md#claim"},
        "added_hypotheses": [{
            "id": "H3", "statement": "New explanation", "prediction": "A different response", "parent_id": "H1",
        }],
        "next_test": {
            "description": "Check the response", "method": "Measure once", "limits": [],
            "predictions": {"H2": "Change", "H3": "Different"},
        },
    }
    with pytest.raises(ris.Error, match="at least two new child hypotheses"):
        study.amend_study(ris, project, "ST-AMEND", 1, one_child)
    assert study.read_study(ris, project, "ST-AMEND")["revision"] == 1

    unknown_trigger = {
        "id": "AMD-UNKNOWN",
        "rationale": "A result that is not in history cannot trigger this amendment",
        "triggering_observation_ids": ["OBS-FUTURE"],
        "added_hypotheses": [],
    }
    with pytest.raises(ris.Error, match="earlier observations"):
        study.amend_study(ris, project, "ST-AMEND", 1, unknown_trigger)
    assert study.read_study(ris, project, "ST-AMEND")["revision"] == 1


def test_confirmation_guard_compares_content_digests_across_paths_and_evidence_types(project, tmp_path):
    study.start_study(ris, project, "ST-AMEND", start_body(result_rule=False))
    source = project / "data" / "origin.csv"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"batch,result\nA,pass\nA,fail\n")
    study.observe_study(
        ris, project, "ST-AMEND", 1, observation_body(), evidence_paths=["data/origin.csv"]
    )
    study.amend_study(ris, project, "ST-AMEND", 2, split_amendment())

    copied = project / "data" / "renamed.csv"
    copied.write_bytes(source.read_bytes())
    copied_metrics = tmp_path / "copied-metrics.json"
    copied_metrics.write_text(json.dumps([{
        "definition": metric_definition(), "input": "data/renamed.csv", "hypotheses": ["H3"],
    }]), encoding="utf-8")
    reused = observation_body("OBS-0002", locator="research/exploration/log.md#R-0002", next_test=False)
    reused["evaluations"] = {
        "H2": {"assessment": "inconclusive", "rationale": "Not resolved"},
        "H3": {"assessment": "supported", "rationale": "The copied data matches"},
        "H4": {"assessment": "inconclusive", "rationale": "Not resolved"},
    }
    with pytest.raises(ris.Error, match="reuses the motivating locator or evidence"):
        study.observe_study(ris, project, "ST-AMEND", 3, reused, metrics_file=str(copied_metrics))

    follow_up = project / "data" / "follow-up.csv"
    follow_up.write_bytes(b"batch,result\nA,pass\nA,pass\n")
    follow_up_metrics = tmp_path / "follow-up-metrics.json"
    follow_up_metrics.write_text(json.dumps([{
        "definition": metric_definition(), "input": "data/follow-up.csv", "hypotheses": ["H3"],
    }]), encoding="utf-8")
    contextual = {**reused, "locator": "research/exploration/log.md#R-0001"}
    accepted = study.observe_study(
        ris, project, "ST-AMEND", 3, contextual, metrics_file=str(follow_up_metrics)
    )
    assert accepted["revision"] == 4
    assert accepted["evaluations"]["H3"]["assessment"] == "supported"


def test_freshness_for_a_hypothesis_uses_only_metrics_linked_to_it(project, tmp_path):
    initial = start_body(result_rule=False)
    initial["hypotheses"] = initial["hypotheses"][:1]
    initial["evaluations"] = {"H1": initial["evaluations"]["H1"]}
    study.start_study(ris, project, "ST-LINKED", initial)

    original = project / "data" / "original.csv"
    original.parent.mkdir(parents=True)
    original.write_bytes(b"batch,result\nA,pass\nA,fail\n")
    origin_definition = metric_definition()
    origin_definition["id"] = "origin_metric"
    origin_metrics = tmp_path / "origin-metrics.json"
    origin_metrics.write_text(json.dumps([{
        "definition": origin_definition, "input": "data/original.csv",
    }]), encoding="utf-8")
    origin_observation = {
        "id": "OBS-0001",
        "finding": "The baseline metric was calculated",
        "locator": "research/exploration/log.md#R-0001",
        "evidence_kind": "derived",
        "conditions": {"temperature": "20 C"},
        "limitations": ["One baseline run"],
        "evaluations": {"H1": {"assessment": "inconclusive", "rationale": "The baseline does not distinguish the explanations"}},
        "recommendation": "Collect an independent follow-up",
        "rationale": "Only the baseline is recorded",
        "next_action": "Repeat under the second condition",
    }
    study.observe_study(ris, project, "ST-LINKED", 1, origin_observation, metrics_file=str(origin_metrics))

    amendment = {
        "id": "AMD-H2",
        "rationale": "The baseline motivates a separately testable explanation.",
        "triggering_observation_ids": ["OBS-0001"],
        "added_hypotheses": [{
            "id": "H2", "statement": "The response changes at 25 C", "prediction": "The response differs at 25 C",
        }],
        "next_test": {
            "description": "Measure at 25 C", "method": "Calculate the pass rate", "limits": [],
            "predictions": {"H1": "The rate stays within tolerance", "H2": "The rate changes"},
        },
    }
    study.amend_study(ris, project, "ST-LINKED", 2, amendment)

    renamed = project / "data" / "renamed.csv"
    renamed.write_bytes(original.read_bytes())
    unrelated = project / "data" / "unassigned.csv"
    unrelated.write_bytes(b"batch,result\nA,pass\nA,pass\n")
    linked_definition = metric_definition()
    linked_definition["id"] = "h2_metric"
    unassigned_definition = metric_definition()
    unassigned_definition["id"] = "unassigned_metric"
    second_metrics = tmp_path / "second-metrics.json"
    second_metrics.write_text(json.dumps([
        {"definition": linked_definition, "input": "data/renamed.csv", "hypotheses": ["H2"]},
        {"definition": unassigned_definition, "input": "data/unassigned.csv", "hypotheses": []},
    ]), encoding="utf-8")
    second_observation = {
        "id": "OBS-0002",
        "finding": "The H2-linked metric input is unchanged from the motivating baseline",
        "locator": "research/exploration/log.md#R-0002",
        "evidence_kind": "derived",
        "conditions": {"temperature": "25 C"},
        "limitations": [],
        "evaluations": {
            "H1": {"assessment": "inconclusive", "rationale": "The result does not resolve H1"},
            "H2": {"assessment": "supported", "rationale": "The linked result appears consistent"},
        },
        "recommendation": "Repeat with fresh linked data",
        "rationale": "The assigned H2 input must be checked independently",
        "next_action": "Use the follow-up run",
    }
    with pytest.raises(ris.Error, match="reuses the motivating locator or evidence"):
        study.observe_study(ris, project, "ST-LINKED", 3, second_observation, metrics_file=str(second_metrics))
    assert study.read_study(ris, project, "ST-LINKED")["revision"] == 3

    follow_up = project / "data" / "follow-up.csv"
    follow_up.write_bytes(b"batch,result\nA,pass\nA,pass\nA,pass\n")
    linked_definition["id"] = "h2_metric_followup"
    second_metrics.write_text(json.dumps([
        {"definition": linked_definition, "input": "data/follow-up.csv", "hypotheses": ["H2"]},
        {"definition": unassigned_definition, "input": "data/unassigned.csv", "hypotheses": []},
    ]), encoding="utf-8")
    contextual_observation = {
        **second_observation,
        "locator": "research/exploration/log.md#R-0001",
        "finding": "A new H2-linked follow-up metric was calculated",
    }
    accepted = study.observe_study(
        ris, project, "ST-LINKED", 3, contextual_observation, metrics_file=str(second_metrics)
    )
    assert accepted["revision"] == 4
    assert accepted["evaluations"]["H2"]["assessment"] == "supported"


@pytest.mark.parametrize("attach_original", [False, True])
def test_fingerprinting_or_editing_original_locator_does_not_make_a_new_test(project, attach_original):
    study.start_study(ris, project, "ST-AMEND", start_body(result_rule=False))
    source = project / "run.csv"
    source.write_text("value\n1\n", encoding="utf-8")
    study.observe_study(ris, project, "ST-AMEND", 1, observation_body(locator="run.csv:2"),
                        evidence_paths=["run.csv"] if attach_original else None)
    study.amend_study(ris, project, "ST-AMEND", 2, split_amendment())
    if attach_original:
        source.write_text("value\n2\n", encoding="utf-8")
    replay = observation_body("OBS-later", locator="run.csv:2", next_test=False)
    replay["evaluations"] = {
        "H2": {"assessment": "inconclusive", "rationale": "Open"},
        "H3": {"assessment": "supported", "rationale": "Refers back to the motivating record"},
        "H4": {"assessment": "untested", "rationale": "Open"},
    }
    with pytest.raises(ris.Error, match="reuses the motivating locator or evidence"):
        study.observe_study(ris, project, "ST-AMEND", 3, replay, evidence_paths=["run.csv"])
    assert study.read_study(ris, project, "ST-AMEND")["revision"] == 3


def test_test_only_amendment_can_change_initial_active_test_with_provenance(project):
    study.start_study(ris, project, "ST-AMEND", start_body(result_rule=False))
    body = {
        "id": "AMD-TEST",
        "rationale": "Replace the baseline check with the reviewed measurement method.",
        "triggering_observation_ids": [],
        "basis": {"kind": "independent", "locator": "research/methods/repeatability.md#procedure"},
        "added_hypotheses": [],
        "active_test": {"description": "Use a calibrated sensor", "method": "Measure three replicates", "limits": ["One temperature"]},
        "next_test": {
            "description": "Compare at 25 C",
            "method": "Measure three replicates at 25 C",
            "limits": [],
            "predictions": {"H1": "Stable", "H2": "Changes"},
        },
    }
    amended = study.amend_study(ris, project, "ST-AMEND", 1, body)
    assert amended["revision"] == 2
    assert amended["active_test"]["description"] == "Use a calibrated sensor"
    assert amended["next_test"]["predictions"] == {"H1": "Stable", "H2": "Changes"}
    observed_body = observation_body("OBS-0001", next_test=False)
    observed = study.observe_study(ris, project, "ST-AMEND", 2, observed_body)
    assert observed["revision"] == 3
    assert observed["active_test"]["description"] == "Use a calibrated sensor"


def test_study_amend_cli_uses_expected_revision_and_body_file(project, tmp_path):
    study.start_study(ris, project, "ST-AMEND", start_body(result_rule=False))
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    actions = study.add_parser(commands)
    assert actions is not None
    body = {
        "id": "AMD-CLI",
        "rationale": "The planned test method is updated from an independent protocol.",
        "triggering_observation_ids": [],
        "basis": {"kind": "independent", "locator": "research/methods/protocol.md#v2"},
        "added_hypotheses": [],
        "next_test": {
            "description": "Use the revised protocol",
            "method": "Measure three replicates",
            "limits": [],
            "predictions": {"H1": "Stable", "H2": "Changes"},
        },
    }
    body_file = tmp_path / "amendment.json"
    body_file.write_text(json.dumps(body), encoding="utf-8")
    args = parser.parse_args([
        "study", "amend", "ST-AMEND", "--expected-revision", "1", "--body-file", str(body_file),
    ])
    result = study.dispatch(ris, project, args)
    assert result["status"] == "recorded" and result["amendment_id"] == "AMD-CLI"
    assert study.dispatch(ris, project, parser.parse_args(["study", "show", "ST-AMEND"]))["revision"] == 2
    assert study.dispatch(ris, project, parser.parse_args(["study", "list"]))["count"] == 1
