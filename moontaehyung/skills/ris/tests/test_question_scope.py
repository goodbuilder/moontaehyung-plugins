import json
from pathlib import Path
import subprocess
import sys

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ris.py"


def cli(project, *args, input=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--project", str(project), *map(str, args)],
        input=input,
        text=True,
        capture_output=True,
    )


def ok(project, *args):
    result = cli(project, *args)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def explore(project, kind=None, via=None, text=None, question=None, reuse=()):
    args = ["explore"]
    if kind is not None:
        args += ["--kind", kind]
    if via is not None:
        args += ["--via", via]
    if text is not None:
        args += ["--text", text]
    if question is not None:
        args += ["--question", question]
    for entry_id in reuse:
        args += ["--reuse", entry_id]
    return ok(project, *args)


def scope(report):
    return report["exploration_log"]["question_scope"]


def test_unrelated_history_is_excluded_and_reuse_does_not_inflate_project_totals(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    ok(project, "init", "--name", "Question scope")

    scanner_queries = [
        explore(project, "query", "code", text, question="scanner")
        for text in ("scanner hopper", "scanner capacity", "scanner offline")
    ]
    full_read = explore(project, "read", "full", "scanner-test.log §2", question="scanner")
    snippet_read = explore(project, "read", "snippet", "scanner-result snippet", question="scanner")
    battery_query = explore(project, "query", "code", "battery runtime", question="battery")

    scanner_refs = ", ".join(entry["id"] for entry in [*scanner_queries, full_read, snippet_read])
    summary = f'''## 탐색한 접근 계열
- Scanner conditions were searched and the source was opened ({scanner_refs}).
- Battery runtime was searched ({battery_query["id"]}).

## 기각·보류한 후보와 이유
없음

## 미탐색 프런티어
- Battery primary evidence remains to be opened ({battery_query["id"]}).

## 검수 요청
- Battery result is not ready for ranking ({battery_query["id"]}).
'''
    summary_result = cli(project, "summarize", input=summary)
    assert summary_result.returncode == 0, summary_result.stderr

    project_check = ok(project, "check")
    before = project_check["exploration_log"]
    before_report = ok(project, "check", "--question", "battery")
    before_scope = scope(before_report)
    assert project_check["warnings"] == []
    assert before_scope["new"] == {"queries": 1, "reads": 0, "reads_beyond_snippet": 0}
    assert before_scope["reused"] == {"read_ids": [], "reads": 0, "reads_beyond_snippet": 0}
    assert before_scope["checklist"] == {
        "distinct_queries": 1,
        "queries_meet_minimum": False,
        "sources_opened_beyond_snippet": 0,
    }
    assert before_scope["warnings"]
    assert set(before_scope["warnings"]).issubset(set(before_report["warnings"]))
    assert any("at least 3" in warning for warning in before_scope["warnings"])
    assert any("snippet" in warning for warning in before_scope["warnings"])
    assert before["queries"] == 4
    assert before["reads"] == 2
    assert before["reads_beyond_snippet"] == 1

    explore(
        project,
        question="battery",
        reuse=(full_read["id"], snippet_read["id"]),
    )
    # Repeating an existing question/source link is idempotent.
    explore(project, question="battery", reuse=(full_read["id"],))

    after_report = ok(project, "check")
    after = after_report["exploration_log"]
    after_scope = scope(ok(project, "check", "--question", "battery"))
    assert after_scope["new"] == {"queries": 1, "reads": 0, "reads_beyond_snippet": 0}
    assert set(after_scope["reused"]["read_ids"]) == {full_read["id"], snippet_read["id"]}
    assert after_scope["reused"]["reads"] == 2
    assert after_scope["reused"]["reads_beyond_snippet"] == 1
    assert any("at least 3" in warning for warning in after_scope["warnings"])
    assert not any("snippet" in warning for warning in after_scope["warnings"])
    assert (after["queries"], after["reads"], after["reads_beyond_snippet"]) == (
        before["queries"], before["reads"], before["reads_beyond_snippet"]
    )
    assert "question_scope" not in after


def test_legacy_five_column_rows_remain_unassigned_until_explicitly_reused(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    initialized = ok(project, "init", "--name", "Legacy question scope")
    project_id = initialized["project_id"]
    log = project / initialized["research_dir"] / "exploration" / "log.md"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(
        f'''---
ris_id: "legacy-exploration-log"
project_id: "{project_id}"
kind: "exploration"
status: "draft"
created: "2026-11-24T10:00:00Z"
---

# 탐색 작업 기록

| ID | 시각(UTC) | 종류 | 채널/범위 | 내용 |
|---|---|---|---|---|
| Q-0001 | 2026-11-24T10:00:01Z | query | code | legacy scanner query |
| R-0001 | 2026-11-24T10:00:02Z | read | full | legacy scanner source §1 |
| R-0002 | 2026-11-24T10:00:03Z | read | snippet | legacy scanner result snippet |
''',
        encoding="utf-8",
    )

    new_query = explore(project, "query", "code", "battery runtime", question="battery")
    assert new_query["id"] == "Q-0002"
    before = ok(project, "check", "--question", "battery")["exploration_log"]
    assert before["unassigned"] == {"queries": 1, "reads": 2, "reads_beyond_snippet": 1}
    assert before["question_scope"]["new"] == {
        "queries": 1,
        "reads": 0,
        "reads_beyond_snippet": 0,
    }
    assert before["question_scope"]["reused"] == {
        "read_ids": [],
        "reads": 0,
        "reads_beyond_snippet": 0,
    }

    explore(project, question="battery", reuse=("R-0001", "R-0002"))
    after = ok(project, "check", "--question", "battery")["exploration_log"]
    assert after["unassigned"] == {"queries": 1, "reads": 2, "reads_beyond_snippet": 1}
    assert set(after["question_scope"]["reused"]["read_ids"]) == {"R-0001", "R-0002"}
    assert after["question_scope"]["reused"]["reads"] == 2
    assert after["question_scope"]["reused"]["reads_beyond_snippet"] == 1
    assert (after["queries"], after["reads"], after["reads_beyond_snippet"]) == (2, 2, 1)


def test_invalid_reuse_is_rejected_without_appending_log_events(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    ok(project, "init", "--name", "Invalid reuse")
    explore(project, "query", "code", "source question", question="source")
    own_read = explore(project, "read", "full", "source.log §1", question="source")

    log = project / ".ris" / "research" / "exploration" / "log.md"
    before = log.read_bytes()
    invalid_targets = ("R-9999", "Q-0001", own_read["id"])
    for entry_id in invalid_targets:
        result = cli(project, "explore", "--question", "source", "--reuse", entry_id)
        assert result.returncode != 0
        assert result.stderr
        assert log.read_bytes() == before

    report = ok(project, "check", "--question", "source")["exploration_log"]
    assert report["question_scope"]["reused"] == {
        "read_ids": [],
        "reads": 0,
        "reads_beyond_snippet": 0,
    }


def project_files(project):
    return {
        path.relative_to(project).as_posix(): path.read_bytes()
        for path in project.rglob("*")
        if path.is_file() and not path.is_symlink()
    }


def log_path(project):
    return project / ".ris" / "research" / "exploration" / "log.md"


def test_question_context_is_scoped_ordered_read_only_and_legacy_context_stays_compatible(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    initialized = ok(project, "init", "--name", "Question context")
    context_note = project / initialized["research_dir"] / "CONTEXT.md"
    context_note.write_text(
        context_note.read_text(encoding="utf-8") + "\nProject-only context sentinel.\n",
        encoding="utf-8",
    )

    target_query_1 = explore(project, "query", "web", "term A | term B", question="target")
    explore(project, "query", "web", "unrelated query sentinel", question="unrelated")
    target_read = explore(project, "read", "full", "target-paper.pdf §3", question="target")
    shared_read = explore(project, "read", "code", "shared|source.py line 12", question="unrelated")
    explore(project, "read", "data", "unlinked source sentinel", question="unrelated")
    target_query_2 = explore(project, "query", "code", "target query two", question="target")
    reuse = explore(project, question="target", reuse=(shared_read["id"],))
    explore(project, "query", "zotero", "later unrelated query sentinel", question="unrelated")

    before = project_files(project)
    view = ok(project, "context", "--question", "target")
    after = project_files(project)

    assert before == after
    assert view["question_id"] == "target"
    assert view["total_entries"] == 4
    assert view["omitted_entries"] == 0
    entries = view["entries"]
    assert [entry["id"] for entry in entries] == [
        target_query_1["id"], target_read["id"], target_query_2["id"], shared_read["id"]
    ]
    assert [entry["kind"] for entry in entries] == ["query", "read", "query", "read"]
    assert entries[0]["query"] == "term A | term B" and entries[0]["channel"] == "web"
    assert entries[1]["locator"] == "target-paper.pdf §3"
    assert entries[1]["scope"] == "full" and entries[1]["reused"] is False
    assert entries[2]["query"] == "target query two"
    assert entries[3]["locator"] == "shared|source.py line 12"
    assert entries[3]["scope"] == "code" and entries[3]["reused"] is True
    assert entries[3]["reuse_id"] == reuse["reuse_events"][0]
    assert entries[3]["source_question"] == "unrelated"

    serialized = json.dumps(view, ensure_ascii=False)
    assert "unrelated query sentinel" not in serialized
    assert "later unrelated query sentinel" not in serialized
    assert "unlinked source sentinel" not in serialized
    assert "Project-only context sentinel" not in serialized

    unknown = ok(project, "context", "--question", "not-a-question")
    assert unknown["question_id"] == "not-a-question"
    assert unknown["entries"] == []
    assert unknown["total_entries"] == 0
    assert unknown["omitted_entries"] == 0

    default_context = ok(project, "context")
    assert default_context["mode"] == "prepared_snapshot"
    assert "project" in default_context and "records" in default_context
    assert any(record["path"].endswith("CONTEXT.md") for record in default_context["records"])


def test_question_context_reads_legacy_five_column_entry_when_explicitly_reused(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    initialized = ok(project, "init", "--name", "Legacy reuse context")
    legacy_read_id = "R-0001"
    legacy_locator = "old-study.pdf §1"
    log_path(project).parent.mkdir(parents=True, exist_ok=True)
    log_path(project).write_text(
        f'''---
ris_id: "legacy-exploration-log"
project_id: "{initialized["project_id"]}"
kind: "exploration"
status: "draft"
created: "2026-11-24T10:00:00Z"
---

# 탐색 작업 기록

| ID | 시각(UTC) | 종류 | 채널/범위 | 내용 |
|---|---|---|---|---|
| R-0001 | 2026-11-24T10:00:01Z | read | snippet | {legacy_locator} |
''',
        encoding="utf-8",
    )

    query = explore(project, "query", "code", "current question query", question="current")
    reuse = explore(project, question="current", reuse=(legacy_read_id,))
    view = ok(project, "context", "--question", "current")

    assert view["total_entries"] == 2
    assert [entry["kind"] for entry in view["entries"]] == ["query", "read"]
    assert view["entries"][0]["id"] == query["id"]
    assert view["entries"][0]["query"] == "current question query"
    reused = view["entries"][1]
    assert reused["id"] == legacy_read_id
    assert reused["kind"] == "read"
    assert reused["locator"] == legacy_locator
    assert reused["scope"] == "snippet"
    assert reused["reused"] is True
    assert reused["reuse_id"] == reuse["reuse_events"][0]
    assert reused["source_question"] is None


def test_question_context_budget_omits_whole_entries_and_recovers_with_required_size(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    ok(project, "init", "--name", "Bounded question context")
    queries = ["A" * 600, "B" * 600, "C" * 600]
    recorded = [explore(project, "query", "code", query, question="bounded") for query in queries]

    limited = ok(project, "context", "--question", "bounded", "--max-chars", "1000")
    repeated = ok(project, "context", "--question", "bounded", "--max-chars", "1000")
    assert limited["total_entries"] == 3
    assert limited["characters_required"] > 1000
    assert 0 < limited["omitted_entries"] < limited["total_entries"]
    assert len(limited["entries"]) + limited["omitted_entries"] == limited["total_entries"]
    assert limited["entries"] == repeated["entries"]

    complete = ok(
        project,
        "context",
        "--question",
        "bounded",
        "--max-chars",
        str(limited["characters_required"]),
    )
    assert complete["total_entries"] == 3
    assert complete["omitted_entries"] == 0
    assert [entry["id"] for entry in complete["entries"]] == [entry["id"] for entry in recorded]
    assert [entry["query"] for entry in complete["entries"]] == queries
    assert limited["entries"] == complete["entries"][:len(limited["entries"])]


def test_question_context_rejects_wrong_log_identity_and_broken_or_ambiguous_reuse(tmp_path):
    wrong_project = tmp_path / "wrong-project"
    wrong_project.mkdir()
    initialized = ok(wrong_project, "init", "--name", "Wrong identity")
    explore(wrong_project, "query", "code", "target query", question="target")
    path = log_path(wrong_project)
    original = path.read_text(encoding="utf-8")
    path.write_text(
        original.replace(f'project_id: "{initialized["project_id"]}"', 'project_id: "foreign-project"', 1),
        encoding="utf-8",
    )
    wrong_identity = cli(wrong_project, "context", "--question", "target")
    assert wrong_identity.returncode != 0
    assert wrong_identity.stderr

    for mode in ("broken", "ambiguous"):
        project = tmp_path / mode
        project.mkdir()
        ok(project, "init", "--name", mode)
        source = explore(project, "read", "full", "source-paper.pdf §2", question="source")
        explore(project, "query", "code", "target query", question="target")
        explore(project, question="target", reuse=(source["id"],))
        path = log_path(project)
        text = path.read_text(encoding="utf-8")
        source_line = next(line for line in text.splitlines() if line.startswith(f'| {source["id"]} |'))
        if mode == "broken":
            text = text.replace(source_line + "\n", "", 1)
        else:
            text = text.replace(source_line + "\n", source_line + "\n" + source_line.replace("source-paper.pdf", "conflicting.pdf") + "\n", 1)
        path.write_text(text, encoding="utf-8")
        result = cli(project, "context", "--question", "target")
        assert result.returncode != 0
        assert result.stderr


def test_question_context_rejects_invalid_question_id(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    ok(project, "init", "--name", "Invalid question context")
    result = cli(project, "context", "--question", "bad question id")
    assert result.returncode != 0
    assert result.stderr
