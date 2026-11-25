"""User-facing projections on the normal RIS CLI, including a qualitative-only control."""
import json
import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ris.py"


def run(project, *args, body=None, expect=0, raw=False):
    process = subprocess.run([sys.executable, "-B", str(SCRIPT), "--project", str(project), *map(str, args)],
                             input=json.dumps(body) if body is not None else None, capture_output=True, text=True)
    assert process.returncode == expect, process.stderr or process.stdout
    if expect:
        return process.stderr
    return process.stdout if raw else json.loads(process.stdout)


def test_first_projection_is_verified_and_original_interpretation_remains_attributable(tmp_path, monkeypatch):
    run(tmp_path, "init", "--name", "공개 자료 확인")
    hypothesis = {"id": "H1", "statement": "두 기준을 충족한다.", "prediction": "두 지표 모두 통과한다.",
                  "basis": {"kind": "assumption", "note": "검증 전 가정"}}
    evaluations = {"H1": {"assessment": "untested", "rationale": "초기 상태"}}
    start = {"goal": "처리 기준 확인", "criteria": ["전체 4건 이상", "실패율 70% 이하"], "conditions": {"run": "a"},
             "hypotheses": [hypothesis], "test": {"description": "사건 집계", "method": "원본을 센다", "limits": []},
             "recommendation": "보류", "rationale": "자료 확인 전", "next_action": "집계", "evaluations": evaluations,
             "result_rule": {"mode": "all", "metric_ids": ["total", "rate"]}}
    run(tmp_path, "study", "start", "case", "--body-file", "-", body=start)
    (tmp_path/"rows.csv").write_text("outcome\nmiss\nmiss\nmiss\nhit\n", encoding="utf-8")
    metrics = [
        {"input": "rows.csv", "definition": {"id": "total", "format": "csv", "operation": "count", "where": {},
         "unit": "rows", "threshold": {"op": "ge", "value": 4}}, "reported": 3},
        {"input": "rows.csv", "definition": {"id": "rate", "format": "csv", "operation": "ratio",
         "where": {}, "numerator_where": {"outcome": "miss"}, "unit": "percent",
         "threshold": {"op": "le", "value": 70}}, "reported": 75}]
    packet = tmp_path/"metrics.json"
    packet.write_text(json.dumps(metrics))
    observation = {"id": "O1", "locator": "rows.csv", "conditions": {"run": "a"}, "evidence_kind": "source",
                   "limitations": [], "evaluations": evaluations, "recommendation": "표본 확대 검토",
                   "rationale": "한 회차만 관측했다", "next_action": "다른 회차와 비교"}
    run(tmp_path, "study", "observe", "case", "--expected-revision", 1, "--body-file", "-",
        body=observation, expect=2)
    recorded = run(tmp_path, "study", "observe", "case", "--expected-revision", 1, "--body-file", "-",
                   "--metrics-file", packet, body=observation)
    report = run(tmp_path, "study", "results", "case")
    assert recorded["verified_results"] == report
    assert report["overall"]["computed"]["verdict"] == "fail"
    rows = {row["metric_id"]:row for row in report["criterion_results"]}
    assert rows["total"]["reported_value"] == "3" and rows["total"]["computed_value"] == "4"
    assert rows["total"]["reported_threshold"] == "fail" and rows["total"]["computed_threshold"] == "pass"
    assert rows["rate"]["computed_value"] == "75" and rows["rate"]["computed_threshold"] == "fail"
    preview = run(tmp_path, "study", "results", "case", "--any", "total", "rate")
    assert preview["overall"]["computed"]["verdict"] == "pass" and preview["rule"] != report["rule"]
    assert run(tmp_path, "study", "results", "case") == report
    context = run(tmp_path, "context", "--study", "case")
    assert context["verified_summary"] == report["summary"] and context["user_decision"] is None
    rendered = run(tmp_path, "study", "results", "case", "--format", "markdown", raw=True).strip()
    note = (tmp_path/recorded["path"]).read_text()
    table_rows = [line for line in rendered.splitlines() if line.startswith("| ")]
    assert any("total" in line for line in table_rows) and any("rate" in line for line in table_rows)
    assert all(line in note and note.index(line) < note.index("표본 확대 검토") for line in table_rows)
    assert run(tmp_path, "study", "observe", "case", "--expected-revision", 1, "--body-file", "-",
               "--metrics-file", packet, body=observation)["status"] == "already_recorded"

    # A projection that cannot be generated must fail before publishing the observation.
    spec = importlib.util.spec_from_file_location("ris_presentation_check", SCRIPT)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    def unavailable(*_args, **_kwargs):
        raise ValueError("projection unavailable")
    monkeypatch.setattr(helper.companion("ris_results"), "render_results", unavailable)
    before = (tmp_path / recorded["path"]).read_bytes()
    with pytest.raises(ValueError, match="projection unavailable"):
        helper.companion("ris_study").observe_study(
            helper, tmp_path, "case", 2, {**observation, "id": "O2"}, metrics_file=str(packet))
    assert (tmp_path / recorded["path"]).read_bytes() == before
