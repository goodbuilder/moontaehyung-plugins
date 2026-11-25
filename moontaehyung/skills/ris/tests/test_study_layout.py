"""End-to-end migration checks for studies and reused evidence in a synthetic project."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ris.py"
RIS_SPEC = importlib.util.spec_from_file_location("ris_study_layout_test_ris", SCRIPT)
ris = importlib.util.module_from_spec(RIS_SPEC)
RIS_SPEC.loader.exec_module(ris)


def cli(project, *args, input_text=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--project", str(project), *map(str, args)],
        input=input_text, text=True, capture_output=True,
    )


def cli_json(project, *args, input_text=None):
    result = cli(project, *args, input_text=input_text)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def json_text(value):
    return json.dumps(value, ensure_ascii=False)


def start_body(conditions):
    return {
        "goal": "Compare a synthetic panel under controlled conditions.",
        "criteria": ["Record a traceable observation before recommending reuse."],
        "conditions": conditions,
        "hypotheses": [{
            "id": "H1", "statement": "The panel remains attached.",
            "prediction": "No delamination appears in the synthetic inspection.",
            "basis": {"kind": "assumption", "note": "Synthetic test fixture only."},
        }],
        "test": {"description": "Inspect a synthetic data row.", "method": "Read the fixture row.", "limits": ["Synthetic evidence only."]},
        "recommendation": "Hold pending the observation.",
        "rationale": "No result is recorded yet.",
        "next_action": "Inspect the synthetic row.",
        "evaluations": {"H1": {"assessment": "untested", "rationale": "No observation yet."}},
    }


def observation_body():
    return {
        "id": "OBS-1",
        "finding": "Synthetic panel remained attached in the inspected row.",
        "locator": "research/exploration/log.md#R-0001",
        "evidence_kind": "source",
        "conditions": {"panel": "A", "temperature": "20 C"},
        "limitations": ["One synthetic row; not real-world evidence."],
        "evaluations": {"H1": {"assessment": "supported", "rationale": "The fixture row matches the prediction."}},
        "recommendation": "Retain the panel for this synthetic case.",
        "rationale": "The recorded row matches the predicted outcome.",
        "next_action": "Review applicability before any real use.",
    }


def _to_schema_one(project):
    config = project / ".ris" / "project.yaml"
    text = config.read_text(encoding="utf-8")
    text, version_count = re.subn(r"(?m)^schema_version:\s*2\s*$", "schema_version: 1", text)
    text, directory_count = re.subn(
        r'(?m)^research_dir:\s*["\']?\.ris/research["\']?\s*$',
        'research_dir: "research"', text,
    )
    assert version_count == directory_count == 1
    (project / ".ris" / "research").rename(project / "research")
    config.write_text(text, encoding="utf-8")


def _file_snapshot(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*") if path.is_file() and not path.is_symlink()
    }


@pytest.fixture
def synthetic_v1(tmp_path):
    project = tmp_path / "synthetic-study"
    project.mkdir()
    assert project.resolve().is_relative_to(Path("/tmp").resolve()), "migration fixture must stay under /tmp"

    cli_json(project, "init", "--name", "Synthetic study migration")
    _to_schema_one(project)
    evidence = cli_json(
        project, "explore", "--kind", "read", "--via", "data",
        "--text", "synthetic.csv row 1", input_text=None,
    )
    assert evidence["id"] == "R-0001"
    plan = cli_json(
        project, "record", "--kind", "plan", "--title", "Synthetic migration plan",
        "--body-file", "-", input_text="Use only the synthetic fixture.\n",
    )
    conditions = {"panel": "A", "temperature": "20 C"}
    cli_json(project, "study", "start", "source", "--body-file", "-",
             input_text=json_text(start_body(conditions)))
    before = cli_json(project, "study", "show", "source", "--revision", "1")
    cli_json(project, "study", "observe", "source", "--expected-revision", "1",
             "--body-file", "-", input_text=json_text(observation_body()))
    cli_json(project, "study", "start", "target", "--body-file", "-",
             input_text=json_text(start_body(conditions)))
    linked = cli_json(project, "study-link", "target", "--plan", plan["path"],
                      "--allow-legacy-handoff")
    assert len(linked["targets"]) == 3

    target_path = project / "research" / "decisions" / "study-target.md"
    annotation = "\n\n## Human annotation\n\nKeep this note. [evidence](../exploration/log.md#R-0001)\n"
    target_path.write_text(target_path.read_text(encoding="utf-8") + annotation, encoding="utf-8")
    current = cli_json(project, "study", "show", "source")
    assert before["revision"] == 1 and before["observations"] == []
    assert current["revision"] == 2 and current["observations"][0]["id"] == "OBS-1"

    saved = cli_json(
        project, "knowledge", "reuse", "source", "--revision", "2", "--observation", "OBS-1",
        "--target", "target", "--target-revision", "1",
    )
    assert saved["status"] == "saved"
    note_path = project / saved["path"]
    note_text = note_path.read_text(encoding="utf-8")
    metadata = ris.frontmatter(note_text)
    assert metadata["source_revision"] == 2
    assert metadata["source_observation_id"] == "OBS-1"
    assert metadata["target_study_id"] == "target" and metadata["target_revision"] == 1
    assert metadata["source_observation_sha256"] == saved["source_observation_sha256"]
    assert metadata["source_study_path"] == "decisions/study-source.md"
    assert metadata["target_study_path"] == "decisions/study-target.md"

    return {
        "project": project,
        "project_id": ris.config(project)["project_id"],
        "plan": plan["path"],
        "old_source": before,
        "current_source": current,
        "annotation": annotation,
        "saved": saved,
        "finding_bytes": note_path.read_bytes(),
        "finding_path": saved["path"],
    }


def test_v1_to_v2_migration_preserves_study_navigation_and_reused_finding(synthetic_v1, tmp_path):
    project = synthetic_v1["project"]
    preview_preimage = _file_snapshot(project)
    preview = cli_json(project, "migrate-layout")
    assert preview["status"] == "preview"
    assert preview["from"] == {"schema_version": 1, "research_dir": "research"}
    assert preview["to"] == {"schema_version": 2, "research_dir": ".ris/research"}
    assert _file_snapshot(project) == preview_preimage

    migrated = cli_json(project, "migrate-layout", "--apply")
    assert migrated["status"] == "migrated"
    cfg = ris.config(project)
    assert cfg["project_id"] == synthetic_v1["project_id"]
    assert cfg["schema_version"] == 2 and cfg["research_dir"] == ".ris/research"
    assert not (project / "research").exists()

    source_note = project / ".ris/research/decisions/study-source.md"
    target_note = project / ".ris/research/decisions/study-target.md"
    assert source_note.is_file() and target_note.is_file()
    assert target_note.read_text(encoding="utf-8").endswith(synthetic_v1["annotation"])

    historical = cli_json(project, "study", "show", "source", "--revision", "1")
    current = cli_json(project, "study", "show", "source")
    assert historical["revision"] == synthetic_v1["old_source"]["revision"] == 1
    assert historical["observations"] == []
    assert current["revision"] == synthetic_v1["current_source"]["revision"] == 2
    assert current["observations"] == synthetic_v1["current_source"]["observations"]
    assert current["path"] == ".ris/research/decisions/study-source.md"

    finding = project / ".ris/research/findings" / Path(synthetic_v1["finding_path"]).name
    assert finding.read_bytes() == synthetic_v1["finding_bytes"]
    saved_metadata = ris.frontmatter(finding.read_text(encoding="utf-8"))
    assert saved_metadata["source_revision"] == 2
    assert saved_metadata["source_observation_id"] == "OBS-1"
    assert saved_metadata["source_observation_sha256"] == synthetic_v1["saved"]["source_observation_sha256"]
    assert saved_metadata["source_study_path"] == "decisions/study-source.md"
    assert saved_metadata["target_study_path"] == "decisions/study-target.md"
    finding_text = finding.read_text(encoding="utf-8")
    for study_link in ("../decisions/study-source.md", "../decisions/study-target.md"):
        assert f"[open](<{study_link}>)" in finding_text
        assert (finding.parent / study_link).is_file()

    context = project / ".ris/research/CONTEXT.md"
    handoff = project / ".ris/HANDOFF.md"
    plan = project / ".ris/research" / Path(synthetic_v1["plan"]).relative_to("research")
    for note, expected_link in (
        (context, "decisions/study-target.md"),
        (handoff, "research/decisions/study-target.md"),
        (plan, "../decisions/study-target.md"),
    ):
        text = note.read_text(encoding="utf-8")
        assert expected_link in text
        link_target = expected_link.split("#", 1)[0]
        assert (note.parent / link_target).resolve().is_file()

    context_result = cli_json(project, "context", "--study", "target")
    assert context_result["path"] == ".ris/research/decisions/study-target.md"
    assert len(context_result["reused_knowledge"]) == 1
    assert context_result["reused_knowledge"][0]["path"] == ".ris/research/findings/" + finding.name
    assert context_result["reused_knowledge"][0]["source_observation_sha256"] == saved_metadata["source_observation_sha256"]

    links_before_retry = {
        path: (project / path).read_bytes()
        for path in (".ris/research/CONTEXT.md", ".ris/HANDOFF.md", str(plan.relative_to(project)))
    }
    relinked = cli_json(project, "study-link", "target", "--plan", str(plan.relative_to(project)))
    assert relinked["status"] == "already_linked"
    assert all(item["status"] == "already_linked" for item in relinked["targets"])
    assert all((project / path).read_bytes() == data for path, data in links_before_retry.items())

    retry = cli_json(
        project, "knowledge", "reuse", "source", "--revision", "2", "--observation", "OBS-1",
        "--target", "target", "--target-revision", "1",
    )
    assert retry["status"] == "already_saved"
    assert retry["path"] == ".ris/research/findings/" + finding.name
    assert retry["sha256"] == hashlib.sha256(finding.read_bytes()).hexdigest()
    assert len(list((project / ".ris/research/findings").glob("knowledge-*.md"))) == 1

    checked = cli_json(project, "check")
    assert checked["ok"] is True, checked["errors"]
    assert not any("missing link" in warning for warning in checked["warnings"])

    # An exact retry is idempotent; a conflicting edit to the immutable finding is never overwritten.
    edited_finding = finding.read_text(encoding="utf-8").replace(
        "Synthetic panel remained attached", "Edited provenance", 1)
    assert edited_finding != finding.read_text(encoding="utf-8")
    finding.write_text(edited_finding, encoding="utf-8")
    conflicting_retry = cli(
        project, "knowledge", "reuse", "source", "--revision", "2", "--observation", "OBS-1",
        "--target", "target", "--target-revision", "1",
    )
    assert conflicting_retry.returncode != 0
    assert finding.read_text(encoding="utf-8") == edited_finding

    # Human annotations remain editable; managed study identity and revision history do not.
    current_text = target_note.read_text(encoding="utf-8")
    managed_start = current_text.index("<!-- RIS:STUDY:BEGIN -->")
    managed_end = current_text.index("<!-- RIS:STUDY:END -->") + len("<!-- RIS:STUDY:END -->")
    managed = current_text[managed_start:managed_end]
    annotated = current_text + "\n\nAdditional human annotation.\n"
    updated_body = tmp_path / "study-update.md"
    updated_body.write_text(annotated, encoding="utf-8")
    update = cli(
        project, "update", str(target_note.relative_to(project)),
        "--expected-hash", hashlib.sha256(current_text.encode("utf-8")).hexdigest(),
        "--body-file", updated_body,
    )
    assert update.returncode == 0, update.stderr
    after_annotation = target_note.read_text(encoding="utf-8")
    assert managed in after_annotation
    assert after_annotation.endswith("Additional human annotation.\n")

    tampered = after_annotation.replace("# Study target", "# Study edited", 1)
    assert tampered != after_annotation
    tampered_body = tmp_path / "tampered-study.md"
    tampered_body.write_text(tampered, encoding="utf-8")
    rejected = cli(
        project, "update", str(target_note.relative_to(project)),
        "--expected-hash", hashlib.sha256(after_annotation.encode("utf-8")).hexdigest(),
        "--body-file", tampered_body,
    )
    assert rejected.returncode != 0
    assert target_note.read_text(encoding="utf-8") == after_annotation
