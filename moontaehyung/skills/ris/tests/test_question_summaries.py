import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ris.py"
spec = importlib.util.spec_from_file_location("ris_question_summary_helper", SCRIPT)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)

SUMMARY_BODY = '''## 탐색한 접근 계열
- Reviewed the available research log.

## 기각·보류한 후보와 이유
없음

## 미탐색 프런티어
- 후보 Z의 변형 조건

## 검수 요청
- Continue reviewing primary evidence.
'''


def new_project(path):
    path.mkdir()
    helper.initialize(path)
    return path


def summary_path(project):
    return project / helper.config(project)["research_dir"] / "exploration" / "summary.md"


def test_generated_question_tally_labels_legacy_rows_as_unassigned_and_keeps_project_totals(tmp_path):
    project = new_project(tmp_path / "legacy")
    cfg = helper.config(project)
    log = project / cfg["research_dir"] / "exploration" / "log.md"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(
        helper.note(
            cfg["project_id"],
            "exploration",
            "Legacy exploration log",
            '''| ID | 시각(UTC) | 종류 | 채널/범위 | 내용 |
|---|---|---|---|---|
| Q-0001 | 2026-11-24T10:00:01Z | query | web | legacy question one |
| Q-0002 | 2026-11-24T10:00:02Z | query | web | legacy question two |
| R-0001 | 2026-11-24T10:00:03Z | read | full | legacy source one |
| R-0002 | 2026-11-24T10:00:04Z | read | snippet | legacy source two |
''',
        ),
        encoding="utf-8",
    )

    saved = helper.add_summary(project, SUMMARY_BODY)
    text = summary_path(project).read_text(encoding="utf-8")

    assert saved["status"] == "created"
    assert "질의 2건 · 열람 2건 (snippet 초과 1건)" in text
    assert "| 미지정 | 2 | 2 | 0 |" in text
    assert "| 질문 ID | 질의 | 신규 열람 | 재사용 열람 |" in text
    assert text.endswith(SUMMARY_BODY)


def test_generated_question_tally_counts_shared_reads_and_idempotent_reuse_without_inflating_totals(tmp_path):
    project = new_project(tmp_path / "shared")
    helper.add_exploration(project, "query", "alpha search", "web", question="alpha")
    shared = helper.add_exploration(project, "read", "alpha source §1", "full", question="alpha")
    helper.add_exploration(project, "query", "beta search", "web", question="beta")
    helper.add_exploration(project, "read", "beta source §2", "abstract", question="beta")
    helper.add_exploration(project, "query", "gamma search", "web", question="gamma")

    first = helper.add_exploration(project, None, None, None, question="beta", reuse=[shared["id"], shared["id"]])
    repeated = helper.add_exploration(project, None, None, None, question="beta", reuse=[shared["id"]])
    third_topic = helper.add_exploration(project, None, None, None, question="gamma", reuse=[shared["id"]])
    assert len(first["reuse_events"]) == 1
    assert repeated["reuse_events"] == []
    assert len(third_topic["reuse_events"]) == 1

    helper.add_summary(project, SUMMARY_BODY)
    text = summary_path(project).read_text(encoding="utf-8")

    assert "질의 3건 · 열람 2건 (snippet 초과 2건)" in text
    assert "| alpha | 1 | 1 | 0 |" in text
    assert "| beta | 1 | 1 | 1 |" in text
    assert "| gamma | 1 | 0 | 1 |" in text
    assert "| beta |" not in SUMMARY_BODY  # the user supplies no manually copied tally


def test_refresh_regenerates_question_tally_and_keeps_human_edits_behind_hash_guard(tmp_path):
    project = new_project(tmp_path / "refresh")
    helper.add_exploration(project, "query", "alpha search", "web", question="alpha")
    shared = helper.add_exploration(project, "read", "alpha source §1", "full", question="alpha")
    helper.add_summary(project, SUMMARY_BODY)
    path = summary_path(project)
    original = path.read_bytes()

    human_body = SUMMARY_BODY.replace(
        "- 후보 Z의 변형 조건",
        "- 후보 Z의 변형 조건\n- 사람이 직접 추가한 확인 항목",
    )
    human_edit = path.read_text(encoding="utf-8").replace(
        "- 후보 Z의 변형 조건",
        "- 후보 Z의 변형 조건\n- 사람이 직접 추가한 확인 항목",
    )
    path.write_text(human_edit, encoding="utf-8")
    edited_hash = helper.sha(path.read_bytes())

    helper.add_exploration(project, "query", "beta search", "web", question="beta")
    helper.add_exploration(project, None, None, None, question="beta", reuse=[shared["id"]])
    with pytest.raises(helper.Error, match="Summary changed"):
        helper.add_summary(project, human_body, helper.sha(original))

    updated = helper.add_summary(project, human_body, edited_hash)
    refreshed = path.read_text(encoding="utf-8")

    assert updated["status"] == "updated"
    assert "| beta | 1 | 0 | 1 |" in refreshed
    assert "사람이 직접 추가한 확인 항목" in refreshed
    assert refreshed.endswith(human_body)


def test_generated_tally_keeps_the_full_inventory_when_it_exceeds_the_human_body_limit(tmp_path):
    project = new_project(tmp_path / "many-topics")
    cfg = helper.config(project)
    log = project / cfg["research_dir"] / "exploration" / "log.md"
    log.parent.mkdir(parents=True, exist_ok=True)
    questions = [f"topic-{number:03d}" for number in range(1, 301)]
    rows = [
        f"| Q-{number:04d} | 2026-11-24T10:00:00Z | query | web | search {number} | {question} |"
        for number, question in enumerate(questions, start=1)
    ]
    log.write_text(
        helper.note(
            cfg["project_id"],
            "exploration",
            "Many questions",
            helper.EXPLORE_SCOPED_HEADER
            + "\n"
            + helper.EXPLORE_SCOPED_SEPARATOR
            + "\n"
            + "\n".join(rows)
            + "\n",
        ),
        encoding="utf-8",
    )

    helper.add_summary(project, SUMMARY_BODY)
    text = summary_path(project).read_text(encoding="utf-8")
    stats = text.split(helper.STATS_BEGIN, 1)[1].split(helper.STATS_END, 1)[0]
    inventory = [line for line in stats.splitlines() if line.startswith("| topic-")]
    found = {line.split("|", 2)[1].strip() for line in inventory}

    assert len(stats) > helper.SUMMARY_LIMIT
    assert len(inventory) == len(questions)
    assert found == set(questions)
    assert text.endswith(SUMMARY_BODY)
    report = helper.check(project)
    assert report["exploration_log"]["checklist"]["summary_structure"] == "ok"
    assert not any("Summary body is" in warning for warning in report["warnings"])
