import copy
import hashlib
import importlib.util
from pathlib import Path

import pytest


TESTS = Path(__file__).resolve().parent
SUPPORT_SPEC = importlib.util.spec_from_file_location(
    "ris_knowledge_metrics_test_support", TESTS / "test_knowledge.py")
support = importlib.util.module_from_spec(SUPPORT_SPEC)
SUPPORT_SPEC.loader.exec_module(support)

ris = support.ris
knowledge = support.knowledge
StudyStore = support.StudyStore
observation = support.observation


DEFINITION = {
    "id": "completion_rate",
    "format": "csv",
    "operation": "ratio",
    "where": {"cohort": "A"},
    "numerator_where": {"status": "done"},
    "unit": "percent",
    "threshold": {"op": "ge", "value": "80"},
}


def _metric_capture(root: Path, reported="75") -> dict:
    metric_api = ris.companion("ris_metrics")
    definition = metric_api.normalize_definition(ris, DEFINITION)
    result = metric_api.calculate(ris, root, definition, "metrics.csv")
    comparison = metric_api.compare_reported(definition, result, reported)
    criterion = {"metric_id": definition["id"], "threshold": definition["threshold"]}
    return {
        "definition": definition,
        "input": "metrics.csv",
        "reported": comparison["reported"],
        "result": result,
        "reported_status": comparison["reported_status"],
        "decision_impact": {
            "reported_vs_computed": comparison["decision_impact"],
            "across_revisions": None,
            "criterion": criterion,
            "affected_hypotheses": [],
            "review_recommended": comparison["reported_status"] == "mismatch",
            "reason": comparison["reason"],
        },
        "hypotheses": [],
    }


@pytest.fixture
def metric_env(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    ris.initialize(root, "Numeric replay fixture")
    input_path = root / "metrics.csv"
    input_path.write_text(
        "cohort,status\nA,done\nA,done\nA,pending\nA,done\n", encoding="utf-8")
    studies = StudyStore()
    source_observation = observation(
        conditions={"material": "Birch", "panel": "B", "temperature": "20 C"},
        evidence_files=None,
    )
    source_observation["metrics"] = [_metric_capture(root)]
    source_observation["evaluations"] = {"H-1": "contradicts"}
    studies.add(root, "SRC", conditions={"material": "Birch"},
                observations=[source_observation])
    studies.add(root, "TGT", conditions={
        "material": "Birch", "panel": "B", "temperature": "20 C",
    })
    return root, studies, source_observation, input_path


def _assess(metric_env, *, verify_evidence=True):
    root, studies, *_ = metric_env
    return knowledge.assess_knowledge(
        ris, root, studies, "SRC", 1, "O-1", "TGT",
        verify_evidence=verify_evidence)


def test_verify_evidence_replays_metric_and_uses_its_input_as_byte_evidence(metric_env):
    root, studies, source_observation, input_path = metric_env
    before = copy.deepcopy(studies.read_study(ris, root, "SRC", 1))

    result = _assess(metric_env)

    metric = result["assessment"]["metric_replays"][0]
    assert result["assessment"]["status"] == "scope_match"
    assert result["assessment"]["review_required"] is True
    assert result["assessment"]["evidence_status"] == "bytes_match"
    assert result["assessment"]["evidence_verification_variant"] == "verify_attached_files"
    assert metric["metric_id"] == "completion_rate"
    assert metric["input"] == "metrics.csv"
    assert metric["reported"] == "75"
    assert metric["reported_status"] == "match"
    assert metric["calculation_status"] == "match"
    assert metric["input_status"] == "bytes_match"
    assert metric["result"]["value"] == "75"
    assert metric["decision_impact"]["affected_threshold"] == {"op": "ge", "value": "80"}
    assert metric["replay_comparison"]["decision_impact"] == "threshold_unchanged"
    check = next(item for item in result["assessment"]["evidence_checks"]
                 if item.get("kind") == "metric_input")
    assert check["path"] == "metrics.csv"
    assert check["status"] == "bytes_match"
    assert check["actual_sha256"] == hashlib.sha256(input_path.read_bytes()).hexdigest()
    assert studies.read_study(ris, root, "SRC", 1) == before
    assert studies.read_study(ris, root, "SRC", 1)["observations"][0] == source_observation


def test_replay_separates_same_bytes_claim_mismatch_from_input_change(metric_env):
    root, studies, source_observation, input_path = metric_env
    metric = _metric_capture(root, reported="80")
    source_observation["metrics"] = [metric]
    studies.add(root, "SRC", revision=1, conditions={"material": "Birch"},
                observations=[source_observation])

    mismatch = _assess(metric_env)["assessment"]
    mismatch_metric = mismatch["metric_replays"][0]
    assert mismatch["status"] == "recheck"
    assert mismatch["evidence_status"] == "bytes_match"
    assert mismatch_metric["input_status"] == "bytes_match"
    assert mismatch_metric["reported_status"] == "mismatch"
    assert mismatch_metric["calculation_status"] == "match"
    assert mismatch_metric["decision_impact"]["reported_vs_replay"] == "threshold_crossed"
    assert any("affected threshold" in reason for reason in mismatch["rationale"])

    # Reorder identical rows: the arithmetic and claim still match, but the source bytes changed.
    input_path.write_text(
        "cohort,status\nA,done\nA,pending\nA,done\nA,done\n", encoding="utf-8")
    changed = _assess(metric_env)["assessment"]
    changed_metric = changed["metric_replays"][0]
    assert changed["status"] == "recheck"
    assert changed["evidence_status"] == "changed"
    assert changed_metric["reported_status"] == "mismatch"
    assert changed_metric["input_status"] == "changed"


def test_same_numeric_value_with_changed_bytes_is_reported_independently(metric_env):
    root, _studies, _source_observation, input_path = metric_env
    # Preserve the same 3/4 result while changing row order and therefore the input digest.
    input_path.write_text(
        "cohort,status\nA,done\nA,pending\nA,done\nA,done\n", encoding="utf-8")

    assessment = _assess(metric_env)["assessment"]
    metric = assessment["metric_replays"][0]
    assert assessment["evidence_status"] == "changed"
    assert assessment["status"] == "recheck"
    assert metric["result"]["value"] == "75"
    assert metric["reported_status"] == "match"
    assert metric["calculation_status"] == "match"
    assert metric["input_status"] == "changed"


def test_same_ratio_with_different_population_counts_keeps_numeric_value_status(metric_env):
    root, studies, source_observation, input_path = metric_env
    input_path.write_text(
        "cohort,status\nA,done\nA,pending\nA,done\nA,pending\n", encoding="utf-8")
    source_observation["metrics"] = [_metric_capture(root, reported="50")]
    studies.add(root, "SRC", revision=1, conditions={"material": "Birch"},
                observations=[source_observation])

    # Double every row: 2/4 becomes 4/8 with the same exact ratio and threshold result.
    input_path.write_text(
        "cohort,status\nA,done\nA,pending\nA,done\nA,pending\n"
        "A,done\nA,pending\nA,done\nA,pending\n", encoding="utf-8")
    assessment = _assess(metric_env)["assessment"]
    metric = assessment["metric_replays"][0]

    assert assessment["status"] == "recheck"
    assert assessment["evidence_status"] == "changed"
    assert metric["result"]["numerator"] == 4
    assert metric["result"]["denominator"] == 8
    assert metric["result"]["value"] == "50"
    assert metric["calculation_status"] == "mismatch"
    assert metric["value_status"] == "match"
    assert metric["reported_status"] == "match"
    assert metric["replay_comparison"]["decision_impact"] == "threshold_unchanged"


def test_omitted_reported_number_does_not_create_a_claim_mismatch(metric_env):
    root, studies, source_observation, _input_path = metric_env
    source_observation["metrics"] = [_metric_capture(root, reported=None)]
    studies.add(root, "SRC", revision=1, conditions={"material": "Birch"},
                observations=[source_observation])

    assessment = _assess(metric_env)["assessment"]
    metric = assessment["metric_replays"][0]
    assert assessment["status"] == "scope_match"
    assert assessment["evidence_status"] == "bytes_match"
    assert metric["reported"] is None
    assert metric["reported_status"] == "not_reported"
    assert metric["calculation_status"] == "match"
    assert metric["input_status"] == "bytes_match"
    assert metric["decision_impact"]["reported_vs_replay"] == "not_reported"


def test_ordinary_assessment_does_not_replay_registered_metrics(metric_env, monkeypatch):
    monkeypatch.setattr(
        ris, "companion",
        lambda *_: (_ for _ in ()).throw(AssertionError("ordinary assessment must not load metrics")),
    )

    assessment = _assess(metric_env, verify_evidence=False)["assessment"]
    assert "metric_replays" not in assessment
    assert assessment["evidence_status"] == "not_checked"


def test_indeterminate_replay_is_inconclusive_without_extra_input_read(metric_env, monkeypatch):
    root, studies, source_observation, input_path = metric_env
    input_path.write_text("cohort,status\nA,done,extra\n", encoding="utf-8")
    source_observation["metrics"] = [_metric_capture(root)]
    studies.add(root, "SRC", revision=1, conditions={"material": "Birch"},
                observations=[source_observation])
    monkeypatch.setattr(
        ris, "study_evidence_hash",
        lambda *_: (_ for _ in ()).throw(AssertionError("replay must not reread or rehash input")),
    )

    assessment = _assess(metric_env)["assessment"]
    metric = assessment["metric_replays"][0]
    assert assessment["status"] == "recheck"
    assert assessment["evidence_status"] == "bytes_match"
    assert metric["reported_status"] == "indeterminate"
    assert metric["calculation_status"] == "indeterminate"
    assert metric["input_status"] == "bytes_match"


def test_input_without_calculator_digest_is_not_rehashed(metric_env, monkeypatch):
    _root, _studies, source_observation, _input_path = metric_env
    metric_api = ris.companion("ris_metrics")
    captured = source_observation["metrics"][0]["result"]
    monkeypatch.setattr(metric_api, "calculate", lambda _ris, _root, definition, path: {
        "status": "indeterminate",
        "reason": "input exceeds the bounded processing limit",
        "metric_id": definition["id"],
        "definition": definition,
        "definition_sha256": captured["definition_sha256"],
        "value": None,
        "numerator": None,
        "denominator": None,
        "unit": definition["unit"],
        "threshold_met": None,
        "input": {"path": path, "sha256": None},
    })
    monkeypatch.setattr(
        ris, "study_evidence_hash",
        lambda *_: (_ for _ in ()).throw(AssertionError("must not make an unbounded second read")),
    )

    assessment = _assess(metric_env)["assessment"]
    metric = assessment["metric_replays"][0]
    assert assessment["status"] == "recheck"
    assert assessment["evidence_status"] == "unverified"
    assert metric["input_status"] == "unverified"
    assert metric["reported_status"] == "indeterminate"


def test_reuse_persists_replay_idempotently_and_history_does_not_reopen_inputs(metric_env, monkeypatch):
    root, studies, _source_observation, _input_path = metric_env
    saved = knowledge.reuse_knowledge(
        ris, root, studies, "SRC", 1, "O-1", "TGT", verify_evidence=True)
    repeated = knowledge.reuse_knowledge(
        ris, root, studies, "SRC", 1, "O-1", "TGT", verify_evidence=True)

    assert saved["status"] == "saved"
    assert repeated["status"] == "already_saved"
    assert repeated["path"] == saved["path"]
    assert repeated["metric_replays"] == saved["metric_replays"]
    note_path = ris.inside(root, saved["path"])
    text = note_path.read_text(encoding="utf-8")
    metadata = ris.frontmatter(text)
    assert metadata["knowledge_metric_replays"] == saved["metric_replays"]
    assert metadata["knowledge_metadata_sha256"] == knowledge._metadata_digest(metadata)
    assert "## Numeric reproduction" in text
    assert "metrics.csv" in text

    monkeypatch.setattr(
        ris, "study_evidence_hash",
        lambda *_: (_ for _ in ()).throw(AssertionError("historical listing must not rehash metrics")),
    )
    links = knowledge.list_saved_knowledge_links(ris, root, "TGT", studies)
    assert links["links"][0]["metric_replays"] == saved["metric_replays"]
    assert links["links"][0]["metric_replay_freshness"] == "not_refreshed"


def test_unregistered_legacy_observation_stays_compatible_and_is_not_replayed(metric_env, monkeypatch):
    root, studies, source_observation, _input_path = metric_env
    source_observation.pop("metrics")
    studies.add(root, "SRC", revision=1, conditions={"material": "Birch"},
                observations=[source_observation])
    monkeypatch.setattr(
        ris, "companion",
        lambda *_: (_ for _ in ()).throw(AssertionError("legacy observations must not load metrics")),
    )

    assessment = _assess(metric_env)["assessment"]
    assert "metric_replays" not in assessment
    assert assessment["evidence_status"] == "unverified"

    saved = knowledge.reuse_knowledge(
        ris, root, studies, "SRC", 1, "O-1", "TGT", verify_evidence=True)
    metadata = ris.frontmatter(ris.inside(root, saved["path"]).read_text(encoding="utf-8"))
    assert "knowledge_metric_replays" not in metadata
    assert metadata["knowledge_metadata_sha256"] == knowledge._metadata_digest(metadata)
    links = knowledge.list_saved_knowledge_links(ris, root, "TGT", studies)
    assert links["links"][0]["current_status"] in {"scope_match", "recheck"}
    assert "metric_replays" not in links["links"][0]

