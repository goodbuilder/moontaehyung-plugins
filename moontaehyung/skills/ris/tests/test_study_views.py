import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ris = load("ris_study_views_test_ris", SCRIPTS / "ris.py")
views = load("ris_study_views_test_module", SCRIPTS / "ris_study_views.py")
study_module = load("ris_study_views_test_study", SCRIPTS / "ris_study.py")


class FakeStudy:
    def read_study(self, ris_module, root, study_id, revision=None):
        cfg = ris_module.config(root)
        relative = f"{cfg['research_dir']}/decisions/study-{study_id}.md"
        path = ris_module.inside(root, relative)
        if not path.is_file():
            raise ris_module.Error(f"Study does not exist: {relative}")
        return {
            "id": study_id,
            "revision": revision or 1,
            "project_id": cfg["project_id"],
            "path": relative,
            "goal": "Choose a useful approach",
            "criteria": [],
            "conditions": [],
            "hypotheses": [],
            "test": {},
            "observations": [],
            "recommendation": "Option A",
            "rationale": "Best supported",
            "next_action": "Validate the assumption",
        }


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    ris.initialize(root, "Study views")
    return root


def reader():
    return FakeStudy()


def args(study_id="ST-0001", plan=None, allow_legacy=False):
    return SimpleNamespace(
        command="study-link",
        study_id=study_id,
        plan=plan,
        allow_legacy_handoff=allow_legacy,
    )


def call(root, command_args=None):
    command_args = command_args or args()
    if views.STUDY_ID.fullmatch(command_args.study_id):
        ensure_fake_study(root, command_args.study_id)
    return views.dispatch(ris, root, command_args, reader())


def ensure_fake_study(root, study_id):
    cfg = ris.config(root)
    relative = f"{cfg['research_dir']}/decisions/study-{study_id}.md"
    path = ris.inside(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            f"---\nproject_id: {cfg['project_id']}\nstudy_id: {study_id}\nrevision: 1\n---\n\n# {study_id}\n",
            encoding="utf-8",
        )


def to_v1(root):
    old = ris.config(root)
    (root / old["research_dir"]).rename(root / "research")
    legacy = {
        "schema_version": 1,
        "research_dir": "research",
        "template_version": old["template_version"],
        "project_id": old["project_id"],
        "name": old["name"],
        "recording_policy": old["recording_policy"],
        "created": old["created"],
    }
    (root / ".ris/project.yaml").write_text(ris.yaml_mapping(legacy), encoding="utf-8")


def add_plan(root, relative=".ris/research/plans/main.md"):
    cfg = ris.config(root)
    if relative.startswith(".ris/") and cfg["research_dir"] == "research":
        relative = relative.replace(".ris/research", "research", 1)
    path = ris.inside(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(ris.note(cfg["project_id"], "plan", "Plan", "## Decision\nStudy ST-0001 informs this choice."), encoding="utf-8")
    return relative


def set_active_plan(root, relative):
    cfg_path = root / ".ris/project.yaml"
    ris.configure(root, ris.sha(cfg_path.read_bytes()), active_plan=relative)


def test_add_parser_exposes_study_link_and_legacy_handoff_opt_in():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    views.add_parser(sub)
    parsed = parser.parse_args(["study-link", "ST-0001", "--allow-legacy-handoff"])
    assert parsed.command == "study-link"
    assert parsed.study_id == "ST-0001"
    assert parsed.plan is None
    assert parsed.allow_legacy_handoff is True


def test_fresh_v2_links_context_and_creates_private_handoff_without_plan(project):
    context = project / ".ris/research/CONTEXT.md"
    original = context.read_text(encoding="utf-8")
    context.write_text(original + "\nHuman annotation remains.\n", encoding="utf-8")
    unrelated_root_handoff = project / "HANDOFF.md"
    unrelated_root_handoff.write_text("Unrelated root handoff remains untouched.\n", encoding="utf-8")

    result = call(project)

    assert result["status"] == "linked"
    assert result["study"] == {
        "id": "ST-0001",
        "revision": 1,
        "path": ".ris/research/decisions/study-ST-0001.md",
    }
    assert (project / ".ris/HANDOFF.md").is_file()
    assert "[ST-0001 — canonical study record](decisions/study-ST-0001.md)" in context.read_text(encoding="utf-8")
    assert "Human annotation remains." in context.read_text(encoding="utf-8")
    handoff = ris.frontmatter((project / ".ris/HANDOFF.md").read_text(encoding="utf-8"))
    assert handoff["project_id"] == ris.config(project)["project_id"]
    assert handoff["kind"] == "handoff"
    assert "[ST-0001 — canonical study record](research/decisions/study-ST-0001.md)" in (project / ".ris/HANDOFF.md").read_text(encoding="utf-8")
    assert unrelated_root_handoff.read_text(encoding="utf-8") == "Unrelated root handoff remains untouched.\n"
    assert result["skipped"] == [{"target": "plan", "reason": "no supplied or active plan"}]
    assert not (project / ".ris/research/plans/main.md").exists()

    before = {path: (project / path).read_bytes() for path in (".ris/research/CONTEXT.md", ".ris/HANDOFF.md")}
    repeated = call(project)
    after = {path: (project / path).read_bytes() for path in before}
    assert repeated["status"] == "already_linked"
    assert before == after


def test_links_real_study_reader_canonical_note(project):
    payload = {
        "goal": "Choose a durable approach",
        "criteria": ["supported by observed evidence"],
        "conditions": {"environment": "controlled"},
        "hypotheses": [{
            "id": "H-1",
            "statement": "Option A is reliable",
            "prediction": "The check passes under the stated condition",
            "basis": {"kind": "assumption", "note": "Prior experience suggests reliability"},
        }],
        "test": {"description": "Run one controlled check", "method": "Compare output", "limits": ["Single trial"]},
        "recommendation": "Evaluate Option A",
        "rationale": "It meets the initial criteria",
        "next_action": "Run the controlled check",
        "evaluations": {"H-1": {"assessment": "untested", "rationale": "No observation yet"}},
    }
    created = study_module.start_study(ris, project, "ST-REAL1", payload)

    result = views.dispatch(ris, project, args("ST-REAL1"), study_module)

    assert result["study"]["path"] == created["path"] == ".ris/research/decisions/study-ST-REAL1.md"
    assert result["study"]["revision"] == 1
    assert "[ST-REAL1 — canonical study record](decisions/study-ST-REAL1.md)" in (project / ".ris/research/CONTEXT.md").read_text(encoding="utf-8")


def test_v1_context_and_plan_links_use_legacy_relative_paths(project):
    to_v1(project)
    plan = add_plan(project, "research/plans/main.md")
    set_active_plan(project, plan)
    context_before = (project / "research/CONTEXT.md").read_bytes()

    result = call(project)

    assert result["status"] == "linked"
    assert (project / "research/CONTEXT.md").read_bytes() != context_before
    assert "[ST-0001 — canonical study record](decisions/study-ST-0001.md)" in (project / "research/CONTEXT.md").read_text(encoding="utf-8")
    assert "[ST-0001 — canonical study record](research/decisions/study-ST-0001.md)" not in (project / "research/CONTEXT.md").read_text(encoding="utf-8")
    assert "[ST-0001 — canonical study record](../decisions/study-ST-0001.md)" in (project / plan).read_text(encoding="utf-8")
    assert not (project / "HANDOFF.md").exists()
    assert any(item["target"] == "HANDOFF.md" for item in result["skipped"])


def test_v1_unmanaged_handoff_is_preserved_until_explicit_opt_in(project):
    to_v1(project)
    handoff = project / "HANDOFF.md"
    handoff.write_text("# Human handoff\n\nHistorical status: waiting.\n", encoding="utf-8")

    skipped = call(project)
    assert handoff.read_text(encoding="utf-8") == "# Human handoff\n\nHistorical status: waiting.\n"
    assert any("unmanaged" in item["reason"] for item in skipped["skipped"])

    linked = call(project, args(allow_legacy=True))
    text = handoff.read_text(encoding="utf-8")
    assert linked["status"] == "linked"
    assert "Historical status: waiting." in text
    assert "[ST-0001 — canonical study record](research/decisions/study-ST-0001.md)" in text


def test_v1_owned_handoff_gets_relative_link_without_opt_in(project):
    to_v1(project)
    cfg = ris.config(project)
    handoff = project / "HANDOFF.md"
    handoff.write_text(ris.note(cfg["project_id"], "handoff", "Handoff", "Preserve this note."), encoding="utf-8")

    result = call(project)

    assert result["status"] == "linked"
    text = handoff.read_text(encoding="utf-8")
    assert "Preserve this note." in text
    assert "[ST-0001 — canonical study record](research/decisions/study-ST-0001.md)" in text


def test_supplied_plan_overrides_active_plan_and_does_not_copy_study_text(project):
    active = add_plan(project)
    supplied = add_plan(project, ".ris/research/plans/review.md")
    set_active_plan(project, active)

    result = call(project, args(plan=supplied))

    assert any(target["path"] == supplied for target in result["targets"])
    assert not any(target["path"] == active for target in result["targets"])
    plan_text = (project / supplied).read_text(encoding="utf-8")
    assert "[ST-0001 — canonical study record](../decisions/study-ST-0001.md)" in plan_text
    assert "Best supported" not in plan_text
    assert "Option A" not in plan_text


def test_state_active_plan_takes_precedence_over_configured_plan(project):
    configured = add_plan(project, ".ris/research/plans/configured.md")
    state_active = add_plan(project, ".ris/research/plans/state-active.md")
    set_active_plan(project, configured)
    ris.initialize_state(project, active_plan_ref=state_active)

    result = call(project)

    linked_paths = {target["path"] for target in result["targets"]}
    assert state_active in linked_paths
    assert configured not in linked_paths


def test_supplied_plan_must_be_a_current_project_plan_note(project):
    finding = ris.add_record(project, "finding", "Finding", "Not a plan")
    before = (project / ".ris/research/CONTEXT.md").read_bytes()

    with pytest.raises(ris.Error, match="under this project's research/plans"):
        call(project, args(plan=finding["path"]))

    assert (project / ".ris/research/CONTEXT.md").read_bytes() == before
    assert not (project / ".ris/HANDOFF.md").exists()


def test_conflict_in_any_target_is_found_before_writing_other_targets(project):
    context = project / ".ris/research/CONTEXT.md"
    context_before = context.read_bytes()
    plan = add_plan(project)
    plan_path = project / plan
    plan_path.write_text(plan_path.read_text(encoding="utf-8") + "\n<!-- RIS:STUDY-LINKS:BEGIN -->\n", encoding="utf-8")
    plan_before = plan_path.read_bytes()

    with pytest.raises(ris.Error, match="Malformed or duplicate study-links section"):
        call(project, args(plan=plan))

    assert context.read_bytes() == context_before
    assert not (project / ".ris/HANDOFF.md").exists()
    assert plan_path.read_bytes() == plan_before


def test_concurrent_calls_are_idempotent(project):
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: call(project), range(2)))

    context = (project / ".ris/research/CONTEXT.md").read_text(encoding="utf-8")
    handoff = (project / ".ris/HANDOFF.md").read_text(encoding="utf-8")
    assert context.count("<!-- RIS:STUDY-LINK:BEGIN ST-0001 -->") == 1
    assert handoff.count("<!-- RIS:STUDY-LINK:BEGIN ST-0001 -->") == 1
    assert sorted(result["status"] for result in results) == ["already_linked", "linked"]


def test_partial_write_is_reported_and_retry_finishes_idempotently(project, monkeypatch):
    handoff = project / ".ris/HANDOFF.md"
    handoff.write_text("# Existing managed-area handoff\n", encoding="utf-8")
    real_write = ris.atomic_note_write
    calls = {"count": 0}

    def fail_second(path, content, *, expected=None):
        calls["count"] += 1
        if calls["count"] == 2:
            raise ris.NoteConflict("simulated stale handoff")
        return real_write(path, content, expected=expected)

    monkeypatch.setattr(ris, "atomic_note_write", fail_second)
    partial = call(project)
    assert partial["status"] == "partial"
    assert partial["retryable"] is True
    assert partial["updated"] == [{"path": ".ris/research/CONTEXT.md", "status": "updated", "href": "decisions/study-ST-0001.md"}]
    assert partial["pending"] == [".ris/HANDOFF.md"]
    assert "simulated stale handoff" in partial["error"]

    monkeypatch.setattr(ris, "atomic_note_write", real_write)
    retried = call(project)
    assert retried["status"] == "linked"
    assert "[ST-0001 — canonical study record](research/decisions/study-ST-0001.md)" in handoff.read_text(encoding="utf-8")


def test_reader_revision_change_during_preparation_refuses_without_writes(project):
    class ChangingStudy(FakeStudy):
        reads = 0

        def read_study(self, ris_module, root, study_id, revision=None):
            self.reads += 1
            value = super().read_study(ris_module, root, study_id)
            if self.reads > 1:
                value["revision"] = 2
            return value

    context = project / ".ris/research/CONTEXT.md"
    before = context.read_bytes()
    ensure_fake_study(project, "ST-0001")
    with pytest.raises(ris.Error, match="changed from revision"):
        views.dispatch(ris, project, args(), ChangingStudy())
    assert context.read_bytes() == before
    assert not (project / ".ris/HANDOFF.md").exists()


@pytest.mark.parametrize("bad_id", ["../X", "a/b", "bad id", ".", ""])
def test_rejects_path_like_study_ids_before_creating_links(project, bad_id):
    context = project / ".ris/research/CONTEXT.md"
    before = context.read_bytes()
    with pytest.raises(ris.Error, match="Study ID"):
        call(project, args(study_id=bad_id))
    assert context.read_bytes() == before
    assert not (project / ".ris/HANDOFF.md").exists()
