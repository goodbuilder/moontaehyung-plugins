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


ris = load_module("ris_study_test_helper", SCRIPTS / "ris.py")
study = load_module("ris_study_test_module", SCRIPTS / "ris_study.py")


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    ris.initialize(root, "Study test", "Study the repeated test")
    return root


def start_body():
    return {
        "goal": "Determine whether the mechanism is stable",
        "criteria": ["The measured effect exceeds the stated threshold"],
        "conditions": {"temperature": "20 C", "replicates": "3"},
        "hypotheses": [
            {
                "id": "H1",
                "statement": "The response is stable across repetitions",
                "prediction": "The response remains within tolerance",
                "basis": {"kind": "publication", "locator": "research/literature/prior.md#result-4", "note": "Reported prior finding"},
            },
            {
                "id": "H2",
                "statement": "The response depends on temperature",
                "prediction": "A higher temperature changes the response",
                "basis": {"kind": "assumption", "locator": "", "note": "Working assumption to test"},
            },
        ],
        "test": {"description": "Repeat the baseline measurement", "method": "Measure three replicates", "limits": ["Small sample"]},
        "recommendation": "Collect the baseline first",
        "rationale": "No local measurements are recorded yet",
        "next_action": "Run the baseline test",
        "evaluations": {
            "H1": {"assessment": "untested", "rationale": "No observation yet"},
            "H2": {"assessment": "untested", "rationale": "No observation yet"},
        },
    }


def observation_body(*, next_test=True):
    body = {
        "id": "OBS-0001",
        "finding": "All three replicates stayed within tolerance",
        "locator": "research/exploration/log.md#R-0001",
        "evidence_kind": "source",
        "conditions": {"temperature": "20 C", "replicates": "3"},
        "limitations": ["Only one temperature was tested"],
        "evaluations": {
            "H1": {"assessment": "supported", "rationale": "The replicates met the prediction"},
            "H2": {"assessment": "inconclusive", "rationale": "No temperature comparison was run"},
        },
        "recommendation": "Repeat the measurement at a second temperature",
        "rationale": "The current result supports H1 but does not evaluate H2",
        "next_action": "Run the same test at 25 C",
    }
    if next_test:
        body["next_test"] = {
            "description": "Compare the response at 25 C",
            "method": "Measure three replicates at 25 C",
            "limits": ["One additional temperature"],
            "predictions": {"H1": "Response remains within tolerance", "H2": "Response changes"},
        }
    return body


def decision_body(decision_id="DEC-0001", selection="H1"):
    return {
        "id": decision_id,
        "selection": selection,
        "rationale": "The user selected H1 for the next analysis",
        "locator": "user:turn-24#choice",
    }


def study_path(root, study_id="ST-001"):
    cfg = ris.config(root)
    return root / cfg["research_dir"] / "decisions" / f"study-{study_id}.md"


def test_start_creates_one_managed_readable_note_and_passes_project_check(project):
    result = study.start_study(ris, project, "ST-001", start_body())
    path = study_path(project)
    text = path.read_text(encoding="utf-8")
    metadata = ris.frontmatter(text)

    assert result["revision"] == 1 and result["status"] == "created"
    assert result["path"] == ".ris/research/decisions/study-ST-001.md"
    assert metadata["kind"] == "study" and metadata["project_id"] == ris.config(project)["project_id"]
    assert metadata["ris_id"] and metadata["study_schema_version"] == 1
    assert "Current recommendation (agent; not a user decision)" in text
    assert "No explicit user decision recorded." in text
    assert "Original hypotheses and predictions" in text and "Original test" in text
    assert "research/literature/prior" in text and "../literature/prior.md#result-4" in text
    assert study.read_study(ris, project, "ST-001")["observations"] == []
    assert ris.check(project)["errors"] == []
    assert list((project / ris.config(project)["research_dir"] / "decisions").glob("study-*.md")) == [path]


def test_saved_projection_digest_survives_renderer_changes_and_detects_edits(project, monkeypatch):
    study.start_study(ris, project, "ST-001", start_body())
    path = study_path(project)
    original = study.read_study(ris, project, "ST-001")
    monkeypatch.setattr(study, "_render_managed", lambda state: "a newer renderer projection")
    assert study.read_study(ris, project, "ST-001")["revision"] == original["revision"]
    monkeypatch.undo()

    data = path.read_text(encoding="utf-8")
    path.write_text(data.replace("## Original test", "## Altered test"), encoding="utf-8")
    with pytest.raises(ris.Error, match="digest mismatch"):
        study.read_study(ris, project, "ST-001")


def test_observations_are_append_only_cas_idempotent_and_keep_test_history(project):
    study.start_study(ris, project, "ST-001", start_body())
    path = study_path(project)
    path.write_text(path.read_text(encoding="utf-8") + "\nHuman note: repeat with the same sensor.\n", encoding="utf-8")

    first = study.observe_study(ris, project, "ST-001", 1, observation_body())
    assert first["revision"] == 2 and first["observations"][0]["recorded_at"]
    assert "evidence_files" not in first["observations"][0]
    assert first["observations"][0]["evidence_kind"] == "source"
    assert first["evaluations"]["H1"]["assessment"] == "supported"
    assert first["active_test"]["description"] == "Repeat the baseline measurement"
    assert first["next_test"]["predictions"]["H2"] == "Response changes"
    assert "Human note: repeat with the same sensor." in path.read_text(encoding="utf-8")

    historical = study.read_study(ris, project, "ST-001", revision=1)
    assert historical["revision"] == 1 and historical["observations"] == []
    assert historical["recommendation"] == "Collect the baseline first"
    duplicate = study.observe_study(ris, project, "ST-001", 1, observation_body())
    assert duplicate["status"] == "already_recorded" and duplicate["recorded_revision"] == 2
    assert len(duplicate["observations"]) == 1

    second = observation_body(next_test=False)
    second.update({
        "id": "OBS-0002",
        "finding": "At 25 C, the response changed",
        "locator": "research/exploration/log.md#R-0002",
        "conditions": {"temperature": "25 C", "replicates": "3"},
        "recommendation": "Treat temperature as a control condition",
        "rationale": "The second measurement changed as H2 predicted",
        "next_action": "Repeat with a larger sample",
        "evaluations": {
            "H1": {"assessment": "contradicted", "rationale": "The response was not stable across temperatures"},
            "H2": {"assessment": "supported", "rationale": "The response changed at 25 C"},
        },
    })
    latest = study.observe_study(ris, project, "ST-001", 2, second)
    assert latest["revision"] == 3
    assert latest["active_test"]["description"] == "Compare the response at 25 C"
    assert latest["next_test"] is None
    assert latest["observations"][1]["id"] == "OBS-0002"
    with pytest.raises(ris.Error, match="changed since revision"):
        study.observe_study(ris, project, "ST-001", 1, {**second, "id": "OBS-STALE"})
    with pytest.raises(ris.Error, match="different content"):
        study.observe_study(ris, project, "ST-001", 1, {**observation_body(), "finding": "Changed duplicate"})
    with pytest.raises(ris.Error, match="does not exist"):
        study.read_study(ris, project, "ST-001", revision=4)
    assert "Historical recommendation (agent)" in path.read_text(encoding="utf-8")


def test_explicit_evidence_files_capture_bytes_and_keep_idempotency(project):
    evidence = project / "data" / "raw.csv"
    evidence.parent.mkdir()
    evidence.write_bytes(b"temperature,result\n20,stable\n")
    study.start_study(ris, project, "ST-001", start_body())

    recorded = study.observe_study(ris, project, "ST-001", 1, observation_body(), ["data/raw.csv"])
    attached = recorded["observations"][0]["evidence_files"]
    assert attached == [{"path": "data/raw.csv", "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest()}]
    duplicate = study.observe_study(ris, project, "ST-001", 1, observation_body(), ["data/raw.csv"])
    assert duplicate["status"] == "already_recorded" and duplicate["revision"] == 2

    original_digest = attached[0]["sha256"]
    evidence.write_bytes(b"temperature,result\n20,changed\n")
    assert ris.study_evidence_hash(project, "data/raw.csv")["sha256"] != original_digest
    assert study.read_study(ris, project, "ST-001")["observations"][0]["evidence_files"] == attached
    with pytest.raises(ris.Error, match="different content"):
        study.observe_study(ris, project, "ST-001", 1, observation_body(), ["data/raw.csv"])


def test_missing_or_unsafe_explicit_evidence_files_fail_without_a_revision(project, tmp_path):
    study.start_study(ris, project, "ST-001", start_body())
    body = observation_body()
    forged = {**body, "evidence_files": [{"path": "data/guessed.csv", "sha256": "0" * 64}]}
    with pytest.raises(ris.Error, match="unsupported fields"):
        study.observe_study(ris, project, "ST-001", 1, forged)
    with pytest.raises(ris.Error, match="missing or not a regular file"):
        study.observe_study(ris, project, "ST-001", 1, body, ["data/missing.csv"])
    outside = tmp_path / "outside.csv"
    outside.write_text("private", encoding="utf-8")
    (project / "linked.csv").symlink_to(outside)
    with pytest.raises(ris.Error, match="Symlink"):
        study.observe_study(ris, project, "ST-001", 1, body, ["linked.csv"])
    with pytest.raises(ris.Error, match="Parent traversal"):
        study.observe_study(ris, project, "ST-001", 1, body, ["../outside.csv"])
    assert study.read_study(ris, project, "ST-001")["revision"] == 1


def test_decisions_are_distinct_from_observations_and_persist_until_explicitly_superseded(project):
    study.start_study(ris, project, "ST-001", start_body())
    decided = study.decide_study(ris, project, "ST-001", 1, decision_body())
    assert decided["revision"] == 2 and decided["observations"] == []
    assert decided["user_decision"]["selection"] == "H1"
    assert decided["user_decision"]["revision"] == 2
    duplicate = study.decide_study(ris, project, "ST-001", 1, decision_body())
    assert duplicate["status"] == "already_recorded" and duplicate["revision"] == 2

    observed = study.observe_study(ris, project, "ST-001", 2, observation_body())
    assert observed["revision"] == 3 and len(observed["observations"]) == 1
    assert observed["user_decision"]["id"] == "DEC-0001"
    assert study.read_study(ris, project, "ST-001", revision=2)["user_decision"]["selection"] == "H1"
    assert study.read_study(ris, project, "ST-001", revision=1)["user_decision"] is None

    superseding = study.decide_study(ris, project, "ST-001", 3, decision_body("DEC-0002", "H2"))
    assert superseding["revision"] == 4 and len(superseding["observations"]) == 1
    assert superseding["user_decision"]["id"] == "DEC-0002"
    assert superseding["user_decision"]["supersedes"] == "DEC-0001"
    assert [item["id"] for item in superseding["decisions"]] == ["DEC-0001", "DEC-0002"]
    assert study.read_study(ris, project, "ST-001", revision=3)["user_decision"]["id"] == "DEC-0001"
    with pytest.raises(ris.Error, match="different content"):
        study.decide_study(ris, project, "ST-001", 4, decision_body("DEC-0002", "H1"))
    with pytest.raises(ris.Error, match="changed since revision"):
        study.decide_study(ris, project, "ST-001", 2, decision_body("DEC-0003", "H1"))


def test_managed_history_is_immutable_via_note_edit_and_conflicted_observe_can_be_reopened(project, monkeypatch):
    study.start_study(ris, project, "ST-001", start_body())
    path = study_path(project)
    original_text = path.read_text(encoding="utf-8")
    annotation_text = original_text + "\nHuman annotation: keep this note.\n"
    assert study.validate_note_edit(ris, original_text, annotation_text)
    with pytest.raises(ris.Error, match="digest mismatch"):
        study.validate_note_edit(ris, original_text, original_text.replace("Determine whether the mechanism is stable", "Altered goal"))

    atomic_write = ris.atomic_note_write
    injected = {"done": False}

    def conflict_once(target, content, *, expected=None):
        if expected is not None and not injected["done"]:
            injected["done"] = True
            target.write_bytes(target.read_bytes() + b"\nEditor annotation during update.\n")
        return atomic_write(target, content, expected=expected)

    monkeypatch.setattr(ris, "atomic_note_write", conflict_once)
    with pytest.raises(ris.NoteConflict):
        study.observe_study(ris, project, "ST-001", 1, observation_body())
    reopened = study.read_study(ris, project, "ST-001")
    assert reopened["revision"] == 1 and reopened["observations"] == []
    assert "Editor annotation during update." in path.read_text(encoding="utf-8")
    monkeypatch.setattr(ris, "atomic_note_write", atomic_write)
    resumed = study.observe_study(ris, project, "ST-001", 1, observation_body())
    assert resumed["revision"] == 2
    assert "Editor annotation during update." in path.read_text(encoding="utf-8")


def test_payload_validation_rejects_missing_hypothesis_assessments_and_unclassified_basis(project):
    missing = start_body()
    missing["evaluations"].pop("H2")
    with pytest.raises(ris.Error, match="assess every hypothesis"):
        study.start_study(ris, project, "ST-001", missing)

    no_source_locator = start_body()
    no_source_locator["hypotheses"][0]["basis"] = {"kind": "publication", "locator": "", "note": "reported"}
    with pytest.raises(ris.Error, match="locator is required"):
        study.start_study(ris, project, "ST-001", no_source_locator)

    bad_observation = observation_body()
    bad_observation["evidence_kind"] = "guess"
    study.start_study(ris, project, "ST-001", start_body())
    with pytest.raises(ris.Error, match="evidence_kind"):
        study.observe_study(ris, project, "ST-001", 1, bad_observation)
    assert study.read_study(ris, project, "ST-001")["revision"] == 1


def test_study_parser_and_dispatch_accept_documented_commands(project, tmp_path):
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    study.add_parser(commands)
    body_file = tmp_path / "start.json"
    body_file.write_text(json.dumps(start_body()), encoding="utf-8")
    args = parser.parse_args(["study", "start", "ST-001", "--body-file", str(body_file)])
    created = study.dispatch(ris, project, args)
    assert created["revision"] == 1
    show_args = parser.parse_args(["study", "show", "ST-001", "--revision", "1"])
    assert study.dispatch(ris, project, show_args)["revision"] == 1
    assert study.dispatch(ris, project, parser.parse_args(["study", "list"]))["count"] == 1
    observe_args = parser.parse_args([
        "study", "observe", "ST-001", "--expected-revision", "1",
        "--body-file", str(body_file), "--evidence-file", "data/a.csv", "--evidence-file", "data/b.csv",
    ])
    assert observe_args.evidence_file == ["data/a.csv", "data/b.csv"]
    data_dir = project / "data"
    data_dir.mkdir()
    (data_dir / "a.csv").write_text("a", encoding="utf-8")
    (data_dir / "b.csv").write_text("b", encoding="utf-8")
    observation_file = tmp_path / "observation.json"
    observation_file.write_text(json.dumps(observation_body()), encoding="utf-8")
    observe_args = parser.parse_args([
        "study", "observe", "ST-001", "--expected-revision", "1",
        "--body-file", str(observation_file), "--evidence-file", "data/a.csv", "--evidence-file", "data/b.csv",
    ])
    observed = study.dispatch(ris, project, observe_args)
    assert [item["path"] for item in observed["observations"][0]["evidence_files"]] == ["data/a.csv", "data/b.csv"]
