import argparse
from contextlib import contextmanager
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ris = load("ris_knowledge_ris_helper", SCRIPTS / "ris.py")
knowledge = load("ris_knowledge_helper", SCRIPTS / "ris_knowledge.py")


class StudyStore:
    def __init__(self):
        self.snapshots = {}
        self.latest = {}
        self.paths = {}
        self.mutex = threading.Lock()

    def add(self, root, study_id, revision=1, *, conditions=None, observations=None,
            goal=None, criteria=None):
        project_id = ris.config(root)["project_id"]
        key = (project_id, study_id)
        if key not in self.paths:
            relative = ris.research_path(
                ris.config(root), f"research/decisions/study-{study_id}.md")
            path = ris.inside(root, relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            ris.write_new(path, ris.note(project_id, "decision", f"Study {study_id}",
                                         "Synthetic study fixture"))
            self.paths[key] = relative
        snapshot = {
            "id": study_id,
            "revision": revision,
            "project_id": project_id,
            "path": self.paths[key],
            "goal": goal or f"Goal for {study_id}",
            "criteria": criteria or ["criterion A"],
            "conditions": copy.deepcopy(conditions or {}),
            "hypotheses": [{"id": "H-1", "statement": "Synthetic hypothesis"}],
            "test": {"method": "Synthetic test"},
            "observations": copy.deepcopy(observations or []),
            "recommendation": "hold",
            "rationale": "Fixture rationale",
            "next_action": "Review evidence",
        }
        with self.mutex:
            self.snapshots[(project_id, study_id, revision)] = snapshot
            self.latest[key] = max(revision, self.latest.get(key, 0))
        return snapshot

    def read_study(self, _ris, root, study_id, revision=None):
        project_id = ris.config(root)["project_id"]
        key = (project_id, study_id)
        with self.mutex:
            selected = self.latest.get(key) if revision is None else revision
            value = self.snapshots.get((project_id, study_id, selected))
            if value is None:
                raise ris.Error(f"Study {study_id} revision {selected} was not found")
            return copy.deepcopy(value)


def observation(*, conditions=None, finding="Synthetic successful finding",
                evidence_kind="source", observation_id="O-1", limitations=None,
                evidence_files=None):
    value = {
        "id": observation_id,
        "finding": finding,
        "locator": "study-data.csv rows 2-4",
        "conditions": copy.deepcopy(conditions or {}),
        "limitations": list(limitations or ["Small synthetic sample"]),
        "evidence_kind": evidence_kind,
        "evaluations": {"H-1": "contradicts"},
        "recommendation": "reject candidate",
        "rationale": "The observed test failed.",
        "next_action": "Inspect the failure mechanism.",
    }
    if evidence_files is not None:
        value["evidence_files"] = copy.deepcopy(evidence_files)
    return value


@pytest.fixture
def env(tmp_path):
    root = tmp_path / "target-project"
    root.mkdir()
    ris.initialize(root, "Target project")
    studies = StudyStore()
    source_obs = observation(
        conditions={"material": "Birch", "panel": "B", "temperature": "20 C"},
        finding="Failed: panel B delaminated at 20 C.",
        limitations=["One replicate", "Surface preparation not measured"],
    )
    source = studies.add(root, "SRC-1", conditions={"material": "Birch"},
                         observations=[source_obs])
    target = studies.add(root, "TGT-1", conditions={
        "material": "Birch", "panel": "B", "temperature": "20 C",
    })
    return root, studies, source, target, source_obs


def assess(env, **kwargs):
    root, studies, *_ = env
    return knowledge.assess_knowledge(
        ris, root, studies, "SRC-1", 1, "O-1", "TGT-1", **kwargs)


def test_assess_is_read_only_and_keeps_failed_observation_and_provenance(env):
    root, studies, source, target, source_obs = env
    before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}

    result = assess(env)

    after = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert after == before
    assert result["assessment"]["status"] == "scope_match"
    assert result["assessment"]["assessment_scope"] == "recorded_conditions"
    assert result["assessment"]["evidence_status"] == "not_checked"
    assert result["assessment"]["review_required"] is True
    assert result["assessment"]["transfer_claimed"] is False
    assert result["assessment"]["recommendations_promoted"] is False
    assert result["source"]["project_id"] == source["project_id"]
    assert result["source"]["study_id"] == "SRC-1"
    assert result["source"]["revision"] == 1
    assert result["source"]["observation"] == source_obs
    assert result["source"]["observation_digest"] == hashlib.sha256(
        json.dumps(source_obs, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert result["target"]["study_id"] == "TGT-1"
    assert result["target"]["revision"] == 1
    assert result["assessment"]["condition_comparison"]["exact_match"] is True
    assert "scientific transfer" in " ".join(result["assessment"]["limitations"])


def test_fabricated_locator_is_never_treated_as_verified_and_no_implicit_hash_read(env, monkeypatch):
    root, studies, *_ = env
    studies.add(root, "SRC-1", conditions={"material": "Birch"}, observations=[
        observation(conditions={"material": "Birch", "panel": "B", "temperature": "20 C"},
                    evidence_files=[{"path": "missing/fabricated.csv", "sha256": "0" * 64}])
    ])
    monkeypatch.setattr(ris, "study_evidence_hash", lambda *_: (_ for _ in ()).throw(AssertionError("implicit hash read")))

    result = assess(env)

    assert result["status"] == "scope_match"
    assert result["assessment_scope"] == "recorded_conditions"
    assert result["evidence_status"] == "not_checked"
    assert result["review_required"] is True
    assert result["assessment"]["review_required"] is True


@pytest.mark.parametrize(
    "source_conditions,target_conditions,expected_reason",
    [
        ({"panel": "B"}, {"panel": "A"}, "changed from"),
        ({"panel": "B", "humidity": "40%"}, {"panel": "B"}, "missing source scope"),
        ({"panel": "B"}, {"panel": "B", "humidity": "40%"}, "outside the source evidence scope"),
        ({"panel": "미확인"}, {"panel": "미확인"}, "explicitly unknown"),
        ({}, {}, "No known source scope conditions"),
    ],
)
def test_condition_gaps_changes_unknown_and_empty_maps_require_recheck(
        tmp_path, source_conditions, target_conditions, expected_reason):
    root = tmp_path / "project"
    root.mkdir()
    ris.initialize(root)
    studies = StudyStore()
    studies.add(root, "SRC", conditions={}, observations=[observation(conditions=source_conditions)])
    studies.add(root, "TGT", conditions=target_conditions)

    result = knowledge.assess_knowledge(ris, root, studies, "SRC", 1, "O-1", "TGT")

    assert result["assessment"]["status"] == "recheck"
    assert expected_reason.casefold() in " ".join(result["assessment"]["rationale"]).casefold()


def test_older_managed_study_snapshots_without_condition_maps_are_unknown_not_transferable(env):
    root, studies, *_ = env
    source = studies.snapshots[(ris.config(root)["project_id"], "SRC-1", 1)]
    target = studies.snapshots[(ris.config(root)["project_id"], "TGT-1", 1)]
    source.pop("conditions")
    source["observations"][0].pop("conditions")
    target.pop("conditions")

    result = assess(env)

    assert result["assessment"]["status"] == "recheck"
    assert result["assessment"]["condition_comparison"]["source_study_gaps"]
    assert result["assessment"]["condition_comparison"]["source_observation_gaps"]
    assert result["assessment"]["condition_comparison"]["target_gaps"]


def test_source_study_and_observation_condition_conflict_requires_recheck(env):
    root, studies, *_ = env
    studies.add(root, "SRC-1", conditions={"panel": "A"}, observations=[
        observation(conditions={"material": "Birch", "panel": "B", "temperature": "20 C"})
    ])

    result = assess(env)

    assert result["assessment"]["status"] == "recheck"
    assert result["assessment"]["condition_comparison"]["conflicts"] == [
        {"condition": "panel", "study_value": "A", "observation_value": "B"}
    ]


@pytest.mark.parametrize(
    "observed_conditions,expected_unobserved",
    [({}, ["material", "panel", "temperature"]),
     ({"material": "Birch", "panel": "B"}, ["temperature"])],
)
def test_planned_conditions_are_not_inferred_when_observation_map_is_empty_or_partial(
        tmp_path, observed_conditions, expected_unobserved):
    root = tmp_path / "project"
    root.mkdir()
    ris.initialize(root)
    studies = StudyStore()
    planned = {"material": "Birch", "panel": "B", "temperature": "20 C"}
    studies.add(root, "SRC", conditions=planned,
                observations=[observation(conditions=observed_conditions)])
    studies.add(root, "TGT", conditions=planned)

    result = knowledge.assess_knowledge(ris, root, studies, "SRC", 1, "O-1", "TGT")

    assert result["assessment"]["status"] == "recheck"
    assert result["assessment"]["condition_comparison"]["planned_not_observed"] == expected_unobserved
    assert any("does not record planned" in item for item in result["assessment"]["rationale"])


@pytest.mark.parametrize("evidence_kind", ["assumption", "unresolved"])
def test_assumption_and_unresolved_observations_are_never_verified_support(env, evidence_kind):
    root, studies, *_ = env
    studies.add(root, "SRC-1", conditions={"material": "Birch"}, observations=[
        observation(conditions={"material": "Birch", "panel": "B", "temperature": "20 C"}, evidence_kind=evidence_kind)
    ])

    result = assess(env)

    assert result["assessment"]["status"] == "recheck"
    assert any("not verified support" in reason for reason in result["assessment"]["rationale"])
    assert "not verified support" in " ".join(result["assessment"]["limitations"])


@pytest.mark.parametrize("evidence_kind", ["publication", "derived"])
def test_publication_and_derived_findings_keep_limits_even_when_scope_matches(env, evidence_kind):
    root, studies, *_ = env
    studies.add(root, "SRC-1", conditions={"material": "Birch"}, observations=[
        observation(conditions={"material": "Birch", "panel": "B", "temperature": "20 C"}, evidence_kind=evidence_kind)
    ])

    result = assess(env)

    assert result["assessment"]["status"] == "scope_match"
    assert result["assessment"]["review_required"] is True
    assert any(evidence_kind in item.casefold() for item in result["assessment"]["limitations"])


def test_explicit_external_source_path_reads_only_selected_source_project(env, tmp_path):
    root, studies, *_ = env
    external = tmp_path / "external-source"
    external.mkdir()
    ris.initialize(external, "Explicit source")
    source = studies.add(external, "EXT-1", conditions={"material": "Birch"}, observations=[
        observation(conditions={"material": "Birch", "panel": "B", "temperature": "20 C"})
    ])

    result = knowledge.assess_knowledge(
        ris, root, studies, "EXT-1", 1, "O-1", "TGT-1", source_project=external)

    assert result["assessment"]["status"] == "scope_match"
    assert result["assessment"]["review_required"] is True
    assert result["source"]["project_id"] == source["project_id"]
    assert result["source"]["project_id"] != ris.config(root)["project_id"]
    with pytest.raises(ris.Error, match="not found"):
        knowledge.assess_knowledge(ris, root, studies, "SRC-1", 1, "O-1", "TGT-1",
                                   source_project=external)


def test_explicit_evidence_file_hash_matches_then_changed_or_missing_requires_recheck(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    ris.initialize(root)
    evidence_path = root / "data" / "source.csv"
    evidence_path.parent.mkdir()
    evidence_path.write_text("sample,result\n1,fail\n", encoding="utf-8")
    captured = ris.study_evidence_hash(root, "data/source.csv")
    studies = StudyStore()
    studies.add(root, "SRC", conditions={"material": "Birch"}, observations=[
        observation(conditions={"material": "Birch", "panel": "B", "temperature": "20 C"},
                    evidence_files=[captured])
    ])
    studies.add(root, "TGT", conditions={"material": "Birch", "panel": "B", "temperature": "20 C"})

    matched = knowledge.assess_knowledge(
        ris, root, studies, "SRC", 1, "O-1", "TGT", verify_evidence=True)
    assert matched["status"] == "scope_match"
    assert matched["evidence_status"] == "bytes_match"
    assert matched["review_required"] is True
    assert matched["assessment"]["evidence_checks"] == [{
        "path": "data/source.csv", "expected_sha256": captured["sha256"],
        "actual_sha256": captured["sha256"], "status": "bytes_match",
    }]

    evidence_path.write_text("sample,result\n1,changed\n", encoding="utf-8")
    changed = knowledge.assess_knowledge(
        ris, root, studies, "SRC", 1, "O-1", "TGT", verify_evidence=True)
    assert changed["status"] == "recheck"
    assert changed["evidence_status"] == "changed"
    assert any("changed since observation" in item for item in changed["assessment"]["rationale"])

    evidence_path.unlink()
    missing = knowledge.assess_knowledge(
        ris, root, studies, "SRC", 1, "O-1", "TGT", verify_evidence=True)
    assert missing["status"] == "recheck"
    assert missing["evidence_status"] == "missing"


def test_assessment_variant_is_part_of_saved_identity(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    ris.initialize(root)
    evidence_path = root / "evidence.csv"
    evidence_path.write_text("value\n1\n", encoding="utf-8")
    captured = ris.study_evidence_hash(root, "evidence.csv")
    studies = StudyStore()
    studies.add(root, "SRC", conditions={"panel": "B"}, observations=[
        observation(conditions={"panel": "B"}, evidence_files=[captured])
    ])
    studies.add(root, "TGT", conditions={"panel": "B"})

    unchecked = knowledge.reuse_knowledge(ris, root, studies, "SRC", 1, "O-1", "TGT")
    checked = knowledge.reuse_knowledge(
        ris, root, studies, "SRC", 1, "O-1", "TGT", verify_evidence=True)

    assert unchecked["path"] != checked["path"]
    assert unchecked["evidence_status"] == "not_checked"
    assert checked["evidence_status"] == "bytes_match"
    assert len(list((root / ris.config(root)["research_dir"] / "findings").glob("knowledge-*.md"))) == 2


def test_required_source_revision_rejects_missing_or_unknown_revision(env):
    root, studies, *_ = env
    with pytest.raises(ris.Error, match="required"):
        knowledge.assess_knowledge(ris, root, studies, "SRC-1", None, "O-1", "TGT-1")
    with pytest.raises(ris.Error, match="not found"):
        knowledge.assess_knowledge(ris, root, studies, "SRC-1", 2, "O-1", "TGT-1")


def test_historical_source_revision_is_pinned_but_marked_for_recheck(env):
    root, studies, source, *_ = env
    studies.add(root, "SRC-1", revision=2, conditions={"material": "Birch"}, observations=[
        observation(conditions={"material": "Birch", "panel": "B", "temperature": "20 C"})
    ])

    result = assess(env, target_revision=1)

    assert result["source"]["revision"] == 1
    assert result["source"]["current_revision"] == 2
    assert result["assessment"]["status"] == "recheck"
    assert result["assessment"]["source_is_current"] is False
    assert any("Pinned source revision 1 is historical" in item for item in result["assessment"]["rationale"])


def test_explicit_stale_target_revision_is_marked_for_recheck_and_never_saved(env):
    root, studies, *_ = env
    current = studies.add(root, "TGT-1", revision=2, conditions={
        "material": "Birch", "panel": "B", "temperature": "20 C",
    })

    assessed = assess(env, target_revision=1)
    assert assessed["assessment"]["status"] == "recheck"
    assert assessed["assessment"]["target_is_current"] is False
    assert any("stale" in reason for reason in assessed["assessment"]["rationale"])
    with pytest.raises(ris.Error, match="stale target"):
        knowledge.reuse_knowledge(ris, root, studies, "SRC-1", 1, "O-1", "TGT-1",
                                  target_revision=1)
    assert not list((root / ris.config(root)["research_dir"] / "findings").glob("knowledge-*.md"))


def test_reuse_creates_canonical_finding_and_duplicate_retry_does_not_overwrite(env):
    root, studies, *_ = env

    first = knowledge.reuse_knowledge(ris, root, studies, "SRC-1", 1, "O-1", "TGT-1")
    path = root / first["path"]
    original = path.read_bytes()
    second = knowledge.reuse_knowledge(ris, root, studies, "SRC-1", 1, "O-1", "TGT-1")

    assert first["status"] == "saved"
    assert second["status"] == "already_saved"
    assert second["path"] == first["path"]
    assert path.read_bytes() == original
    metadata = ris.frontmatter(path.read_text(encoding="utf-8"))
    assert metadata["kind"] == "finding"
    assert metadata["source_project_id"] == ris.config(root)["project_id"]
    assert metadata["source_study_id"] == "SRC-1"
    assert metadata["source_revision"] == 1
    assert metadata["source_observation_id"] == "O-1"
    assert metadata["source_observation_sha256"] == first["source_observation_sha256"]
    assert metadata["knowledge_assessment_status"] == "scope_match"
    assert metadata["review_required"] is True
    assert metadata["evidence_status"] == "not_checked"
    assert metadata["source_observation"]["finding"] == "Failed: panel B delaminated at 20 C."
    assert metadata["source_observation"]["evaluations"] == {"H-1": "contradicts"}
    assert metadata["transfer_claimed"] is False
    assert metadata["recommendations_promoted"] is False
    assert "Target study note: [open]" in path.read_text(encoding="utf-8")
    assert ris.check(root)["ok"]

    links = knowledge.list_saved_knowledge_links(ris, root, "TGT-1", studies)
    assert links["current_revision"] == 1
    assert len(links["links"]) == 1
    assert links["links"][0]["path"] == first["path"]
    assert links["links"][0]["current_status"] == "scope_match"
    assert links["links"][0]["evidence_status"] == "not_checked"
    assert links["links"][0]["review_required"] is True
    assert links["links"][0]["permanent_invalidity"] is False


def test_concurrent_duplicate_reuse_has_one_canonical_note(env):
    root, studies, *_ = env
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(
            knowledge.reuse_knowledge, ris, root, studies, "SRC-1", 1, "O-1", "TGT-1")
            for _ in range(2)]
        results = [future.result(timeout=10) for future in futures]

    assert sorted(result["status"] for result in results) == ["already_saved", "saved"]
    findings = list((root / ris.config(root)["research_dir"] / "findings").glob("knowledge-*.md"))
    assert len(findings) == 1


def test_conflict_safe_retry_refuses_manual_body_edits_without_overwriting(env):
    root, studies, *_ = env
    saved = knowledge.reuse_knowledge(ris, root, studies, "SRC-1", 1, "O-1", "TGT-1")
    path = root / saved["path"]
    tampered = path.read_bytes() + b"\nHuman edit\n"
    path.write_bytes(tampered)

    with pytest.raises(ris.Error, match="body integrity conflict"):
        knowledge.reuse_knowledge(ris, root, studies, "SRC-1", 1, "O-1", "TGT-1")
    assert path.read_bytes() == tampered


def test_retry_accepts_new_display_renderer_when_stored_body_checksum_is_intact(env, monkeypatch):
    root, studies, *_ = env
    saved = knowledge.reuse_knowledge(ris, root, studies, "SRC-1", 1, "O-1", "TGT-1")
    path = root / saved["path"]
    original = path.read_bytes()
    original_renderer = knowledge._knowledge_note

    def new_renderer(*args, **kwargs):
        text = original_renderer(*args, **kwargs)
        match = knowledge.re.match(r"\A---\r?\n.*?\r?\n---(?:\r?\n|$)", text, knowledge.re.S)
        metadata = ris.frontmatter(text)
        body = text[match.end():].replace("## Scope assessment", "## Assessment summary", 1)
        if body.startswith("\n"):
            body = body[1:]
        metadata["knowledge_body_sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
        metadata["knowledge_metadata_sha256"] = knowledge._metadata_digest(metadata)
        return "---\n" + ris.yaml_mapping(metadata) + "---\n\n" + body

    monkeypatch.setattr(knowledge, "_knowledge_note", new_renderer)
    retried = knowledge.reuse_knowledge(ris, root, studies, "SRC-1", 1, "O-1", "TGT-1")

    assert retried["status"] == "already_saved"
    assert path.read_bytes() == original


def test_target_revision_change_during_locked_save_is_rechecked(env, monkeypatch):
    root, studies, *_ = env
    original_lock = ris.project_lock

    @contextmanager
    def change_target_while_locked(project_root):
        with original_lock(project_root):
            studies.add(project_root, "TGT-1", revision=2, conditions={
                "material": "Birch", "panel": "B", "temperature": "20 C",
            })
            yield

    monkeypatch.setattr(ris, "project_lock", change_target_while_locked)
    with pytest.raises(ris.Error, match="changed from revision 1 to 2"):
        knowledge.reuse_knowledge(ris, root, studies, "SRC-1", 1, "O-1", "TGT-1")
    assert not list((root / ris.config(root)["research_dir"] / "findings").glob("knowledge-*.md"))


def test_target_advance_marks_saved_link_for_review_not_permanent_invalidity(env):
    root, studies, *_ = env
    saved = knowledge.reuse_knowledge(ris, root, studies, "SRC-1", 1, "O-1", "TGT-1")
    studies.add(root, "TGT-1", revision=2, conditions={
        "material": "Birch", "panel": "B", "temperature": "21 C",
    })

    links = knowledge.list_saved_knowledge_links(ris, root, "TGT-1", studies)

    assert links["current_revision"] == 2
    assert links["links"][0]["path"] == saved["path"]
    assert links["links"][0]["saved_status"] == "scope_match"
    assert links["links"][0]["current_status"] == "recheck"
    assert links["links"][0]["stale_target"] is True
    assert links["links"][0]["review_required"] is True
    assert links["links"][0]["permanent_invalidity"] is False
    assert "review_against_current_target" in links["links"][0]["next_actions"]


def test_same_project_source_advance_marks_link_for_review(env):
    root, studies, *_ = env
    saved = knowledge.reuse_knowledge(ris, root, studies, "SRC-1", 1, "O-1", "TGT-1")
    studies.add(root, "SRC-1", revision=2, conditions={"material": "Birch"}, observations=[
        observation(conditions={"material": "Birch", "panel": "B", "temperature": "20 C"})
    ])

    links = knowledge.list_saved_knowledge_links(ris, root, "TGT-1", studies)

    assert links["links"][0]["path"] == saved["path"]
    assert links["links"][0]["source_freshness"] == "advanced"
    assert links["links"][0]["current_status"] == "recheck"
    assert links["links"][0]["permanent_invalidity"] is False


def test_external_source_freshness_is_not_refreshed_during_target_context_list(env, tmp_path):
    root, studies, *_ = env
    external = tmp_path / "external"
    external.mkdir()
    ris.initialize(external)
    studies.add(external, "EXT", conditions={"material": "Birch"}, observations=[
        observation(conditions={"material": "Birch", "panel": "B", "temperature": "20 C"})
    ])
    knowledge.reuse_knowledge(ris, root, studies, "EXT", 1, "O-1", "TGT-1",
                              source_project=external)
    studies.add(external, "EXT", revision=2, conditions={"material": "Birch"}, observations=[
        observation(conditions={"material": "Birch", "panel": "B", "temperature": "20 C"})
    ])

    links = knowledge.list_saved_knowledge_links(ris, root, "TGT-1", studies)

    assert links["links"][0]["source_freshness"] == "not_refreshed"
    assert links["links"][0]["source_current_revision"] is None
    assert links["links"][0]["source_current_revision_at_save"] == 1
    assert links["links"][0]["source_freshness_checked_at"]
    assert links["links"][0]["external_source_not_refreshed"] is True
    assert links["links"][0]["current_status"] == "scope_match"


def test_link_listing_reads_only_deterministic_knowledge_files(env):
    root, studies, *_ = env
    knowledge.reuse_knowledge(ris, root, studies, "SRC-1", 1, "O-1", "TGT-1")
    findings = root / ris.config(root)["research_dir"] / "findings"
    (findings / "unrelated.md").write_text("---\nmalformed metadata\n", encoding="utf-8")
    outside = root.parent / "outside.md"
    outside.write_text("must not be read", encoding="utf-8")
    (findings / "unrelated-link.md").symlink_to(outside)

    result = knowledge.list_saved_knowledge_links(ris, root, "TGT-1", studies)

    assert len(result["links"]) == 1


def test_resume_rejects_edited_assessment_status_or_body_checksum(env):
    root, studies, *_ = env
    saved = knowledge.reuse_knowledge(ris, root, studies, "SRC-1", 1, "O-1", "TGT-1")
    path = root / saved["path"]
    original = path.read_text(encoding="utf-8")
    edited = original.replace('knowledge_assessment_status: "scope_match"',
                              'knowledge_assessment_status: "recheck"', 1)
    path.write_text(edited, encoding="utf-8")

    with pytest.raises(ris.Error, match="metadata integrity conflict"):
        knowledge.list_saved_knowledge_links(ris, root, "TGT-1", studies)

    path.write_text(original + "\nExternally edited body\n", encoding="utf-8")
    with pytest.raises(ris.Error, match="body integrity conflict"):
        knowledge.list_saved_knowledge_links(ris, root, "TGT-1", studies)


def test_parser_and_dispatch_contract_for_assess_and_reuse(env):
    root, studies, *_ = env
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    knowledge.add_parser(sub)
    for action, expected in (("assess", "scope_match"), ("reuse", "saved")):
        args = parser.parse_args([
            "knowledge", action, "SRC-1", "--revision", "1", "--observation", "O-1",
            "--target", "TGT-1",
        ])
        result = knowledge.dispatch(ris, root, args, studies)
        assert result["review_required"] is True
        assert result["evidence_status"] == "not_checked"
        if action == "assess":
            assert result["assessment"]["status"] == expected
        else:
            assert result["status"] == expected


def _cli(project, *args, input_text=None):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "ris.py"), "--project", str(project), *map(str, args)],
        text=True, input=input_text, capture_output=True)


def _cli_json(project, *args, input_text=None):
    result = _cli(project, *args, input_text=input_text)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_real_cli_study_assess_reuse_and_target_context_flow(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    _cli_json(root, "init")

    def start_body():
        return {
            "goal": "Compare the panel material under defined conditions",
            "criteria": ["Keep the observed panel and temperature explicit"],
            "conditions": {"material": "Birch", "panel": "B", "temperature": "20 C"},
            "hypotheses": [{
                "id": "H-1", "statement": "The material affects delamination",
                "prediction": "Birch delaminates less",
                "basis": {"kind": "source", "locator": "paper.pdf §2", "note": ""},
            }],
            "test": {"description": "Panel test", "method": "Compare samples", "limits": []},
            "recommendation": "Hold", "rationale": "Need observed evidence",
            "next_action": "Record the test result",
            "evaluations": {"H-1": {"assessment": "untested", "rationale": "No test yet"}},
        }

    _cli_json(root, "study", "start", "SRC", "--body-file", "-",
              input_text=json.dumps(start_body()))
    _cli_json(root, "study", "start", "TGT", "--body-file", "-",
              input_text=json.dumps(start_body()))
    observed = {
        "id": "O-1", "finding": "Failed: Birch delaminated in panel B at 20 C.",
        "locator": "test.csv rows 2-5", "evidence_kind": "source",
        "conditions": {"material": "Birch", "panel": "B", "temperature": "20 C"},
        "limitations": ["Only two samples"],
        "evaluations": {"H-1": {"assessment": "contradicted", "rationale": "Failure occurred"}},
        "recommendation": "Reject current candidate",
        "rationale": "The observed result did not match the prediction",
        "next_action": "Inspect surface preparation",
    }
    evidence_file = root / "data" / "test.csv"
    evidence_file.parent.mkdir()
    evidence_file.write_text("sample,result\n1,failed\n", encoding="utf-8")
    _cli_json(root, "study", "observe", "SRC", "--expected-revision", "1", "--body-file", "-",
              "--evidence-file", "data/test.csv",
              input_text=json.dumps(observed))

    assessed = _cli_json(root, "knowledge", "assess", "SRC", "--revision", "2",
                         "--observation", "O-1", "--target", "TGT", "--verify-evidence")
    assert assessed["status"] == "scope_match"
    assert assessed["assessment"]["status"] == "scope_match"
    assert assessed["evidence_status"] == "bytes_match"
    assert assessed["review_required"] is True
    assert assessed["source"]["current_revision"] == 2
    assert assessed["source"]["observation"]["finding"].startswith("Failed:")
    assert assessed["source"]["observation"]["evidence_files"][0]["path"] == "data/test.csv"

    saved = _cli_json(root, "knowledge", "reuse", "SRC", "--revision", "2",
                      "--observation", "O-1", "--target", "TGT", "--verify-evidence")
    assert saved["status"] == "saved"
    assert saved["assessment_status"] == "scope_match"
    assert saved["review_required"] is True
    assert saved["evidence_status"] == "bytes_match"
    evidence_file.write_text("sample,result\n1,changed after save\n", encoding="utf-8")
    resumed = _cli_json(root, "context", "--study", "TGT")
    assert resumed["study_id"] == "TGT"
    assert resumed["reused_knowledge"][0]["path"] == saved["path"]
    assert resumed["reused_knowledge"][0]["current_status"] == "scope_match"
    assert resumed["reused_knowledge"][0]["review_required"] is True
    assert resumed["reused_knowledge"][0]["evidence_status"] == "bytes_match"
    assert resumed["reused_knowledge"][0]["evidence_freshness"] == "not_refreshed"
