import json
from pathlib import Path
import subprocess
import sys


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ris.py"


def command(root, *args, body=None):
    result = subprocess.run([sys.executable, "-B", str(SCRIPT), "--project", str(root), *args],
                            input=body, text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def test_read_uses_traces_only_explicit_links_without_writing(tmp_path):
    command(tmp_path, "init")
    read = command(tmp_path, "explore", "--question", "first", "--kind", "read", "--via", "abstract",
                   "--text", "Sample paper §3 | correction notice")["id"]
    command(tmp_path, "explore", "--question", "second", "--reuse", read)
    command(tmp_path, "explore", "--question", "other", "--kind", "read", "--via", "full", "--text", "unrelated")
    log = tmp_path/".ris/research/exploration/log.md"
    before = log.read_bytes()
    result = command(tmp_path, "context", "--read", read)
    assert [(q["question_id"], q["reused"]) for q in result["questions"]] == [("first", False), ("second", True)]
    assert (result["locator"], result["scope"]) == ("Sample paper §3 | correction notice", "abstract")
    assert log.read_bytes() == before


def test_basis_is_evaluated_on_each_exclusion(tmp_path):
    command(tmp_path, "init")
    q = command(tmp_path, "explore", "--kind", "query", "--via", "code", "--text", "weight of recycled stock")["id"]
    r = command(tmp_path, "explore", "--kind", "read", "--via", "snippet", "--text", "standard stock catalogue")["id"]
    u = command(tmp_path, "explore", "--question", "paper", "--reuse", r)["reuse_events"][0]
    decision = command(tmp_path, "record", "--kind", "decision", "--title", "Confirmed selection", body="User chose B.")
    decision_file = Path(decision["path"]).name
    summary = f"""## 탐색한 접근 계열
- Catalogue ({r})

## 기각·보류한 후보와 이유
- [기각] Recycled paper is too light ({q})
- [보류] Data for recycled paper is missing ({q})
- [보류] Prior catalogue snippet only ({u})
- [사용자 결정] See [selection](../decisions/{decision_file})

## 미탐색 프런티어
없음

## 검수 요청
없음
"""
    saved = command(tmp_path, "summarize", body=summary)
    annotated = saved["exclusion_basis"]
    assert [i["basis"] for i in annotated] == ["query_only", "query_only", "read_linked", "reported_decision_link"]
    assert annotated[2]["read_scopes"] == {r:"snippet"}
    assert len(saved["warnings"]) == 1 and "too light" in saved["warnings"][0]
    checked = command(tmp_path, "check")
    assert checked["exploration_log"]["checklist"]["exclusion_basis"] == annotated
    assert saved["warnings"][0] in checked["warnings"]
