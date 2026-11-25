#!/usr/bin/env python3
"""Deterministic, read-only results for canonical RIS study snapshots."""
from __future__ import annotations

from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys


SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REPORTED_STATUSES = {"match", "mismatch", "not_reported", "indeterminate"}


class _ValidationRis:
    class Error(ValueError):
        pass


@lru_cache(maxsize=1)
def _metric_api():
    """Load the bundled metric contract without reading study or project state."""
    path = Path(__file__).with_name("ris_metrics.py")
    name = f"{__name__}.ris_metrics_contract"
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("Bundled RIS metric contract is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def normalize_rule(ris, rule) -> dict:
    """Validate an explicit all/any rule over a complete, ordered set of IDs."""
    error = getattr(ris, "Error", ValueError)
    if not isinstance(rule, dict):
        raise error("result_rule must be an object with mode and metric_ids")
    extra = set(rule) - {"mode", "metric_ids"}
    missing = {"mode", "metric_ids"} - set(rule)
    if missing:
        raise error("result_rule is missing fields: " + ", ".join(sorted(missing)))
    if extra:
        raise error("result_rule has unsupported fields: " + ", ".join(sorted(extra)))
    mode = rule["mode"]
    if not isinstance(mode, str) or mode not in {"all", "any"}:
        raise error("result_rule.mode must be all or any")
    metric_ids = rule["metric_ids"]
    if not isinstance(metric_ids, list) or not metric_ids:
        raise error("result_rule.metric_ids must be a non-empty array")
    normalized_ids = []
    for index, metric_id in enumerate(metric_ids, 1):
        if not isinstance(metric_id, str) or not SAFE_ID.fullmatch(metric_id):
            raise error(f"result_rule.metric_ids[{index}] is not a valid metric ID")
        if metric_id in normalized_ids:
            raise error("result_rule.metric_ids contains duplicate ID: " + metric_id)
        normalized_ids.append(metric_id)
    return {"mode": mode, "metric_ids": normalized_ids}


def _snapshot_fields(snapshot):
    if not isinstance(snapshot, dict):
        raise ValueError("study snapshot must be an object")
    study_id = snapshot.get("id")
    if not isinstance(study_id, str) or not SAFE_ID.fullmatch(study_id):
        raise ValueError("study snapshot has an invalid ID")
    revision = snapshot.get("revision")
    if type(revision) is not int or revision < 1:
        raise ValueError("study snapshot has an invalid revision")
    observations = snapshot.get("observations", [])
    if not isinstance(observations, list):
        raise ValueError("study snapshot observations must be an array")
    return study_id, revision, observations


def _threshold_verdict(metrics, definition, result) -> str:
    """Return a checked criterion verdict using ris_metrics' exact validator."""
    if not isinstance(result, dict):
        return "unknown"
    if result.get("status") == "indeterminate":
        return "unthresholded" if "threshold" not in definition else "unknown"
    if result.get("status") != "ok":
        return "unknown"
    normalized, _exact_value = metrics._validated_result(result)
    if normalized is None or normalized != definition:
        return "unknown"
    if "threshold" not in definition:
        return "unthresholded"
    flag = result.get("threshold_met")
    if type(flag) is not bool:
        return "unknown"
    return "pass" if flag else "fail"


def _reported_threshold_verdict(metrics, definition, reported) -> str:
    if "threshold" not in definition:
        return "unthresholded"
    if reported is None:
        return "unknown"
    try:
        exact, _canonical = metrics._parse_reported(_ValidationRis, reported)
        passed = metrics._threshold_test(exact, definition)
    except (TypeError, ValueError, ArithmeticError):
        return "unknown"
    return "pass" if passed else "fail"


def _validated_metric(metrics, observation, metric) -> dict:
    if not isinstance(metric, dict):
        raise ValueError("observation metric must be an object")
    definition = metric.get("definition")
    if not isinstance(definition, dict):
        raise ValueError("observation metric has no definition")
    try:
        normalized = metrics.normalize_definition(_ValidationRis, definition)
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("observation metric has an invalid definition") from exc
    fingerprint = metrics._definition_fingerprint(normalized)
    metric_id = normalized["id"]
    result = metric.get("result")
    if not isinstance(result, dict):
        raise ValueError(f"metric {metric_id} has no calculation result")
    if (result.get("definition") != normalized
            or result.get("definition_sha256") != fingerprint
            or result.get("metric_id") != metric_id
            or result.get("unit") != normalized["unit"]):
        raise ValueError(f"metric {metric_id} result does not match its captured definition")
    input_record = result.get("input")
    if (not isinstance(input_record, dict)
            or not isinstance(input_record.get("path"), str)
            or not input_record["path"]
            or not (input_record.get("sha256") is None
                    or (isinstance(input_record.get("sha256"), str)
                        and HEX_SHA256.fullmatch(input_record["sha256"])))):
        raise ValueError(f"metric {metric_id} has an invalid input fingerprint")
    if metric.get("input") != input_record["path"]:
        raise ValueError(f"metric {metric_id} input does not match its calculation result")
    if result.get("status") not in {"ok", "indeterminate"}:
        raise ValueError(f"metric {metric_id} has an unsupported calculation status")
    if result.get("status") == "indeterminate" and (
            result.get("value") is not None or result.get("threshold_met") is not None):
        raise ValueError(f"metric {metric_id} has values despite an indeterminate result")
    conditions = observation.get("conditions", {})
    if (not isinstance(conditions, dict)
            or any(not isinstance(key, str) or not isinstance(value, str)
                   for key, value in conditions.items())):
        raise ValueError(f"metric {metric_id} observation has invalid recorded conditions")
    computed_verdict = _threshold_verdict(metrics, normalized, result)
    reported = metric.get("reported")
    reported_status = metric.get("reported_status")
    if reported_status not in _REPORTED_STATUSES:
        raise ValueError(f"metric {metric_id} has an unsupported original reported verdict")
    if (reported is None) != (reported_status == "not_reported"):
        raise ValueError(f"metric {metric_id} reported value and verdict disagree")
    if reported is not None:
        if (not isinstance(reported, str)
                or metrics.normalize_reported(_ValidationRis, reported) != reported):
            raise ValueError(f"metric {metric_id} has a non-canonical original reported value")
    reported_verdict = _reported_threshold_verdict(metrics, normalized, reported)
    impact = (
        "unthresholded" if computed_verdict == "unthresholded"
        else f"{reported_verdict}_to_{computed_verdict}"
    )
    threshold_changed = (
        None if "unknown" in {reported_verdict, computed_verdict}
        else reported_verdict != computed_verdict
    )
    result_is_verified = (
        result.get("status") == "ok"
        and metrics._validated_result(result)[0] == normalized
    )
    result_value = result.get("value") if result_is_verified else None
    input_digest = input_record.get("sha256")
    return {
        "metric_id": metric_id,
        "observation_id": observation.get("id"),
        "revision": observation.get("revision"),
        "definition": normalized,
        "threshold": normalized.get("threshold"),
        "formula_identity": {
            "metric_id": metric_id,
            "definition_sha256": fingerprint,
        },
        "input": {"path": input_record["path"], "sha256": input_digest},
        "conditions": dict(conditions),
        "reported_value": reported,
        "computed_value": result_value,
        "exact_computed_value": result.get("exact_value") if result_is_verified else None,
        "unit": normalized["unit"],
        "reported_verdict": reported_status,
        "reported_threshold": reported_verdict,
        "computed_threshold": computed_verdict,
        "correction_effect": impact,
        "threshold_changed": threshold_changed,
        "result_status": result.get("status"),
        "result_validation": "verified" if result_is_verified else (
            "indeterminate" if result.get("status") == "indeterminate" else "invalid"
        ),
    }


def _all_metric_records(metrics, observations, snapshot_revision):
    records = {}
    revisions_seen = set()
    for observation in observations:
        if not isinstance(observation, dict):
            raise ValueError("study observation must be an object")
        revision = observation.get("revision")
        if type(revision) is not int or revision < 2:
            raise ValueError("study observation has an invalid revision")
        if revision > snapshot_revision:
            raise ValueError("study snapshot contains an observation from a later revision")
        if revision in revisions_seen:
            raise ValueError("study snapshot has duplicate observation revisions")
        revisions_seen.add(revision)
        observation_id = observation.get("id")
        if not isinstance(observation_id, str) or not SAFE_ID.fullmatch(observation_id):
            raise ValueError("study observation has an invalid ID")
        values = observation.get("metrics", [])
        if not isinstance(values, list):
            raise ValueError("observation metrics must be an array")
        seen_here = set()
        for metric in values:
            record = _validated_metric(metrics, observation, metric)
            metric_id = record["metric_id"]
            if metric_id in seen_here:
                raise ValueError(f"observation contains duplicate metric ID: {metric_id}")
            seen_here.add(metric_id)
            records.setdefault(metric_id, []).append(record)
    for items in records.values():
        items.sort(key=lambda item: item["revision"])
        fingerprints = []
        for item in items:
            fingerprint = item["formula_identity"]["definition_sha256"]
            if fingerprint not in fingerprints:
                fingerprints.append(fingerprint)
            item["definition_changed"] = len(fingerprints) > 1
            item["definition_history"] = list(fingerprints)
    return records


def _transition(previous, current) -> str:
    if previous is None:
        return "first_observation"
    if previous["formula_identity"]["definition_sha256"] != current["formula_identity"]["definition_sha256"]:
        return "definition_changed"
    before = previous["computed_threshold"]
    after = current["computed_threshold"]
    return f"{before}_to_{after}"


def _criterion_rows(records):
    rows = []
    for metric_id in sorted(records):
        history = records[metric_id]
        current = dict(history[-1])
        prior = history[-2] if len(history) > 1 else None
        current["definition_changed"] = history[-1]["definition_changed"]
        current["definition_history"] = list(history[-1]["definition_history"])
        current["prior_determination"] = None if prior is None else {
            "observation_id": prior["observation_id"],
            "revision": prior["revision"],
            "definition": prior["definition"],
            "formula_identity": prior["formula_identity"],
            "input": prior["input"],
            "unit": prior["unit"],
            "reported_value": prior["reported_value"],
            "computed_value": prior["computed_value"],
            "reported_verdict": prior["reported_verdict"],
            "reported_threshold": prior["reported_threshold"],
            "computed_threshold": prior["computed_threshold"],
            "comparable": prior["formula_identity"]["definition_sha256"] == current["formula_identity"]["definition_sha256"],
        }
        current["prior_to_current"] = _transition(prior, current)
        current["reported_prior_to_current"] = (
            "first_observation" if prior is None else
            "definition_changed" if prior["formula_identity"]["definition_sha256"] != current["formula_identity"]["definition_sha256"] else
            f"{prior['reported_threshold']}_to_{current['reported_threshold']}"
        )
        rows.append(current)
    return rows


def _aggregate(mode, verdicts):
    values = list(verdicts)
    if not values:
        return "unknown"
    known = [value for value in values if value in {"pass", "fail"}]
    if mode == "all":
        if "fail" in known:
            return "fail"
        return "pass" if len(known) == len(values) else "unknown"
    if "pass" in known:
        return "pass"
    return "fail" if len(known) == len(values) else "unknown"


def _records_at(records, metric_ids, revision, binding_revision=1):
    selected = {}
    for metric_id in metric_ids:
        history = records.get(metric_id, [])
        eligible = [candidate for candidate in history if candidate["revision"] <= revision]
        record = None
        if eligible:
            record = dict(eligible[-1])
            before_or_at_binding = [candidate for candidate in history
                                    if candidate["revision"] <= binding_revision]
            binding_record = before_or_at_binding[-1] if before_or_at_binding else next(
                (candidate for candidate in history if candidate["revision"] > binding_revision), None
            )
            bound_fingerprint = (
                None if binding_record is None
                else binding_record["formula_identity"]["definition_sha256"]
            )
            binding_anchor_revision = None if binding_record is None else binding_record["revision"]
            record["definition_changed"] = bound_fingerprint is not None and any(
                candidate["revision"] > binding_anchor_revision
                and candidate["revision"] <= revision
                and candidate["formula_identity"]["definition_sha256"] != bound_fingerprint
                for candidate in history
            )
            record["definition_changed"] = record["definition_changed"] or (
                bound_fingerprint is not None
                and record["formula_identity"]["definition_sha256"] != bound_fingerprint
            )
        selected[metric_id] = record
    return selected


def _scope_conflicts(selected, metric_ids):
    present = [(metric_id, selected.get(metric_id)) for metric_id in metric_ids
               if selected.get(metric_id) is not None]
    condition_scopes = {json.dumps(record["conditions"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                        for _, record in present}
    condition_conflict = len(condition_scopes) > 1
    condition_conflict_ids = [metric_id for metric_id, _ in present] if condition_conflict else []
    path_digests = {}
    for metric_id, record in present:
        input_record = record["input"]
        path_digests.setdefault(input_record["path"], []).append((metric_id, input_record["sha256"]))
    conflicting_paths = []
    conflicting_ids = set(condition_conflict_ids)
    for path in sorted(path_digests):
        entries = path_digests[path]
        if len({digest for _, digest in entries}) > 1:
            conflicting_paths.append(path)
            conflicting_ids.update(metric_id for metric_id, _ in entries)
    return condition_conflict, sorted(conflicting_ids), conflicting_paths


def _aggregate_at(rule, selected, basis):
    mode = rule["mode"]
    ids = rule["metric_ids"]
    condition_conflict, scope_conflict_ids, input_path_conflicts = _scope_conflicts(selected, ids)
    changed = [metric_id for metric_id in ids
               if selected.get(metric_id) is not None and selected[metric_id]["definition_changed"]]
    missing = [metric_id for metric_id in ids if selected.get(metric_id) is None]
    verdicts = []
    for metric_id in ids:
        record = selected.get(metric_id)
        verdicts.append(
            "unknown" if record is None or metric_id in changed or metric_id in scope_conflict_ids
            else record[basis]
        )
    verdict = _aggregate(mode, verdicts)
    return {
        "verdict": verdict,
        "missing_metric_ids": missing,
        "definition_changed_metric_ids": changed,
        "condition_scope_conflict": condition_conflict,
        "incompatible_scope_metric_ids": scope_conflict_ids,
        "conflicting_input_paths": input_path_conflicts,
    }


def _overall(rule, records, snapshot_revision, effective_revision, rule_source):
    if rule is None:
        return None
    ids = rule["metric_ids"]
    binding_revision = effective_revision if effective_revision is not None else 1
    selected = _records_at(records, ids, snapshot_revision, binding_revision)
    reported = _aggregate_at(rule, selected, "reported_threshold")
    computed = _aggregate_at(rule, selected, "computed_threshold")
    observed_revisions = [
        item["revision"] for metric_id in ids for item in records.get(metric_id, [])
        if item["revision"] <= snapshot_revision
    ]
    comparison_revision = max(observed_revisions, default=None)
    previous_as_of = (comparison_revision - 1) if comparison_revision else 0
    previous_selected = _records_at(records, ids, previous_as_of, binding_revision)
    prior_reported = _aggregate_at(rule, previous_selected, "reported_threshold")
    prior_computed = _aggregate_at(rule, previous_selected, "computed_threshold")
    def overall_change(previous, current):
        return f"{previous}_to_{current}"
    return {
        "rule": {"mode": rule["mode"], "metric_ids": ids},
        "effective_revision": effective_revision,
        "reported": reported,
        "computed": computed,
        "prior": {
            "as_of_revision": previous_as_of if comparison_revision else None,
            "reported": prior_reported,
            "computed": prior_computed,
            "kind": (
                "scenario_reconstruction"
                if rule_source == "runtime_scenario" or (effective_revision is not None and previous_as_of < effective_revision)
                else "recorded_rule_evaluation"
            ),
        },
        "reported_correction_effect": overall_change(
            reported["verdict"], computed["verdict"]
        ),
        "prior_to_current_computed": overall_change(
            prior_computed["verdict"], computed["verdict"]
        ),
        "prior_to_current_reported": overall_change(
            prior_reported["verdict"], reported["verdict"]
        ),
        "comparison_revision": comparison_revision,
    }


def _unregistered_conditions(snapshot, observations):
    registered = snapshot.get("conditions", {})
    if not isinstance(registered, dict):
        registered = {}
    latest = max(observations, key=lambda item: item["revision"], default=None)
    if latest is None:
        return []
    conditions = latest.get("conditions", {})
    if not isinstance(conditions, dict):
        return []
    return [
        {"name": key, "value": conditions[key], "observation_id": latest["id"], "revision": latest["revision"]}
        for key in sorted(conditions)
        if key not in registered
    ]


def _summary(study_id, revision, rows, missing, rule, overall, rule_source, effective_revision):
    parts = []
    if not rows and not missing:
        parts.append(f"연구 {study_id}, {revision}차 개정에는 수치 지표 관측이 없습니다.")
    elif rows:
        parts.append(f"연구 {study_id}, {revision}차 개정의 지표 결과입니다.")
    for row in rows:
        reported = "미보고" if row["reported_value"] is None else _display_value(row["reported_value"], row["unit"])
        computed = "미산출" if row["computed_value"] is None else _display_value(row["computed_value"], row["unit"])
        threshold = row.get("threshold")
        criterion = "임계값 없음" if threshold is None else _display_threshold(threshold, row["unit"])
        parts.append(
            f"{row['metric_id']} 계산값은 {computed}이며 기준 {criterion}에 대해 "
            f"{_KOREAN_VERDICTS[row['computed_threshold']]}입니다. 원 보고값은 {reported}, "
            f"기록된 보고 검증은 {_KOREAN_VERDICTS[row['reported_verdict']]}, "
            f"보고값 기준 판정은 {_KOREAN_VERDICTS[row['reported_threshold']]}입니다."
        )
        if row.get("prior_determination") is None:
            parts.append(f"{row['metric_id']} 이전 관측은 없습니다.")
        else:
            parts.append(f"{row['metric_id']} 이전 판정에서 현재 판정으로의 변화는 {_transition_text(row['prior_to_current'], row['prior_determination'])}입니다.")
    for item in missing:
        parts.append(f"{item['metric_id']}는 자료가 없어 미확정입니다.")
    if rule is None:
        parts.append("명시된 전체 판정 규칙이 없어 전체 결과를 산출하지 않았습니다.")
    elif overall.get("status") == "not_yet_effective":
        parts.append(f"저장된 전체 판정 규칙은 {effective_revision}차 개정부터 적용되어 이 스냅샷에서는 유효하지 않습니다.")
    else:
        mode_text = "모든 지정 기준을 통과해야 합니다" if rule["mode"] == "all" else "지정 기준 중 하나 이상이 통과해야 합니다"
        if rule_source == "runtime_scenario":
            parts.append(f"가정 규칙(이번 조회에만 적용)은 {mode_text}. 대상 지표는 {', '.join(rule['metric_ids'])}입니다.")
        else:
            parts.append(f"저장된 규칙({effective_revision}차 개정부터 적용)은 {mode_text}. 대상 지표는 {', '.join(rule['metric_ids'])}입니다.")
        parts.append(
            f"원 보고값 기준 전체 판정은 {_KOREAN_VERDICTS[overall['reported']['verdict']]}, "
            f"재계산 전체 판정은 {_KOREAN_VERDICTS[overall['computed']['verdict']]}입니다."
        )
        if overall["prior"].get("as_of_revision") is None:
            parts.append("이전 전체 판정을 계산할 과거 관측은 없습니다.")
        else:
            prior_verdict = _KOREAN_VERDICTS[overall['prior']['computed']['verdict']]
            transition = _transition_text(overall['prior_to_current_computed'], overall['prior'])
            parts.append(f"이전 전체 판정은 {overall['prior']['as_of_revision']}차 개정 기준 {prior_verdict}입니다. 변화는 {transition}입니다.")
            if overall["prior"].get("kind") == "scenario_reconstruction":
                parts.append("이전 판정은 현재 규칙을 과거 자료에 적용한 재구성이며 당시 규칙을 뜻하지 않습니다.")
        blocked = overall["computed"].get("definition_changed_metric_ids", [])
        if blocked:
            parts.append("현재 규칙과 정의가 맞지 않아 미확정인 지표는 " + ", ".join(blocked) + "입니다.")
        incompatible = overall["computed"].get("incompatible_scope_metric_ids", [])
        if incompatible:
            parts.append("관측 조건이나 입력 파일 개정이 달라 함께 판정하기 어려운 지표는 " + ", ".join(incompatible) + "입니다.")
    return " ".join(parts)


_KOREAN_VERDICTS = {
    "pass": "통과", "fail": "실패", "unknown": "미확정", "unthresholded": "기준 없음",
    "match": "일치", "mismatch": "불일치", "not_reported": "미보고", "indeterminate": "판정 불가",
}


def _display_unit(unit):
    return {"percent": "%", "rows": "건", "fraction": "비율"}.get(unit, unit)


def _display_value(value, unit):
    if unit in {"percent", "rows"}:
        return f"{value}{_display_unit(unit)}"
    return f"{value} {_display_unit(unit)}"


def _display_threshold(threshold, unit):
    op, value = threshold["op"], threshold["value"]
    if op == "ge":
        return f"{_display_value(value, unit)} 이상"
    if op == "gt":
        return f"{_display_value(value, unit)} 초과"
    if op == "le":
        return f"{_display_value(value, unit)} 이하"
    if op == "lt":
        return f"{_display_value(value, unit)} 미만"
    return f"{_display_value(value, unit)}와 같음"


def _transition_text(transition, prior):
    if prior is None:
        return "이전 관측 없음"
    if transition == "definition_changed":
        return "정의 변경으로 이전 판정과 비교 불가"
    before, separator, after = (transition or "").partition("_to_")
    if not separator:
        return "전이 정보 없음"
    if before == after:
        return f"{_KOREAN_VERDICTS.get(after, after)} 유지"
    return f"이전 {_KOREAN_VERDICTS.get(before, before)} → 현재 {_KOREAN_VERDICTS.get(after, after)}"


def build_results(snapshot, rule=None) -> dict:
    """Apply deterministic result logic to an already-read study snapshot.

    Passing ``rule`` creates a read-only runtime scenario. When omitted, only an
    explicitly persisted ``snapshot['result_rule']`` is used. No study state is
    read or written here.
    """
    study_id, snapshot_revision, observations = _snapshot_fields(snapshot)
    project_id = snapshot.get("project_id")
    if not isinstance(project_id, str) or not project_id:
        raise ValueError("study snapshot has an invalid project ID")
    metrics = _metric_api()
    records = _all_metric_records(metrics, observations, snapshot_revision)
    rows = _criterion_rows(records)
    selected_rule = rule if rule is not None else snapshot.get("result_rule")
    normalized_rule = None if selected_rule is None else normalize_rule(_ValidationRis, selected_rule)
    measured_ids = set(records)
    missing = [] if normalized_rule is None else [
        {"metric_id": metric_id, "record_status": "missing", "computed_threshold": "unknown",
         "reason": "no_measurement"}
        for metric_id in normalized_rule["metric_ids"] if metric_id not in measured_ids
    ]
    rule_source = None
    effective_revision = None
    if normalized_rule is not None:
        rule_source = "runtime_scenario" if rule is not None else "persisted"
        effective_revision = None if rule is not None else snapshot.get("result_rule_revision", 1)
        if effective_revision is not None and (type(effective_revision) is not int or effective_revision < 1):
            raise ValueError("result rule has an invalid effective revision")
    if normalized_rule is None:
        overall = None
    elif rule is None and snapshot_revision < effective_revision:
        overall = {
            "rule": {"mode": normalized_rule["mode"], "metric_ids": normalized_rule["metric_ids"]},
            "rule_source": rule_source,
            "effective_revision": effective_revision,
            "status": "not_yet_effective",
            "reported": None,
            "computed": None,
            "prior": None,
            "prior_to_current_computed": None,
        }
    else:
        overall = _overall(normalized_rule, records, snapshot_revision, effective_revision, rule_source)
        overall["rule_source"] = rule_source
    if normalized_rule is not None:
        overall["effective_revision"] = effective_revision
    extra_conditions = _unregistered_conditions(snapshot, observations)
    report = {
        "study_id": study_id,
        "snapshot_revision": snapshot_revision,
        "criterion_results": rows,
        "missing_criteria": missing,
        "project_id": project_id,
        "rule": None if normalized_rule is None else {
            **normalized_rule, "source": rule_source, "effective_revision": effective_revision,
            **({"scenario_evaluation_from_revision": 1} if rule is not None else {}),
        },
        "overall": overall,
        "unregistered_conditions": extra_conditions,
        "agent_recommendation": snapshot.get("recommendation"),
        "user_decision": snapshot.get("user_decision"),
    }
    report["summary"] = _summary(
        study_id, snapshot_revision, rows, missing, normalized_rule, overall,
        rule_source, effective_revision,
    )
    return report


def _md(value) -> str:
    text = "" if value is None else str(value)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    for char in r"\`*_{}[]()#+-.!|~":
        text = text.replace(char, "\\" + char)
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")


def render_results(report, *, embedded=False) -> str:
    """Render a deterministic Markdown table and separately labeled judgments."""
    if not isinstance(report, dict):
        raise ValueError("results report must be an object")
    if type(embedded) is not bool:
        raise ValueError("embedded must be a boolean")
    rows = report.get("criterion_results", [])
    lines = []
    if not embedded:
        lines.extend([
            f"# 연구 결과: {_md(report.get('study_id'))}",
            "",
            f"프로젝트: {_md(report.get('project_id'))} · 개정: {_md(report.get('snapshot_revision'))}",
            "",
        ])
    lines.extend([
        "## 지표별 결과",
        "",
        "| 지표 | 관측 ID | 관측 개정 | 원 보고값 | 계산값 | 단위 | 기준 | 원 보고 판정 | 보고값 기준 | 계산 기준 | 이전 판정 | 정의 지문 |",
        "|---|---|---:|---:|---:|---|---|---|---|---|---|---|",
    ])
    for row in rows:
        prior = row.get("prior_determination")
        if prior is None:
            prior_text = "이전 관측 없음"
        elif row.get("prior_to_current") == "definition_changed":
            prior_text = (
                f"정의가 바뀌었습니다. 이전 계산값 "
                f"{_display_value(prior['computed_value'], prior['unit']) if prior['computed_value'] is not None else '미산출'} "
                f"({_KOREAN_VERDICTS[prior['computed_threshold']]}, 개정 {prior['revision']})"
            )
        else:
            prior_reported = "미보고" if prior["reported_value"] is None else _display_value(prior["reported_value"], prior["unit"])
            prior_computed = "미산출" if prior["computed_value"] is None else _display_value(prior["computed_value"], prior["unit"])
            prior_text = (
                f"원 보고 {prior_reported}, 계산 {prior_computed} "
                f"({_KOREAN_VERDICTS[prior['computed_threshold']]}, 개정 {prior['revision']}) → "
                f"{_KOREAN_VERDICTS[row['computed_threshold']]}"
            )
        lines.append("| " + " | ".join([
            _md(row.get("metric_id")),
            _md(row.get("observation_id")),
            _md(row.get("revision")),
            _md("미보고" if row.get("reported_value") is None else _display_value(row["reported_value"], row["unit"])),
            _md("미산출" if row.get("computed_value") is None else _display_value(row["computed_value"], row["unit"])),
            _md(_display_unit(row.get("unit"))),
            _md("기준 없음" if row.get("threshold") is None else _display_threshold(row["threshold"], row["unit"])),
            _md(f"{_KOREAN_VERDICTS[row['reported_verdict']]} ({row['reported_verdict']})"),
            _md(_KOREAN_VERDICTS[row["reported_threshold"]]),
            _md(_KOREAN_VERDICTS[row["computed_threshold"]]),
            _md(prior_text),
            _md(row.get("formula_identity", {}).get("definition_sha256")),
        ]) + " |")
    missing = report.get("missing_criteria", [])
    for item in missing:
        lines.append("| " + " | ".join([
            _md(item["metric_id"]), "—", "—", "자료 없음", "자료 없음", "—", "—", "—", "—",
            _md(_KOREAN_VERDICTS["unknown"]), "—", "—",
        ]) + " |")
    if not rows and not missing:
        lines.append("| 기록 없음 | — | — | — | — | — | — | — | — | — | — | — |")
    lines.extend(["", "## 전체 기준 결과", ""])
    overall = report.get("overall")
    if overall is None:
        lines.append("명시된 전체 판정 규칙이 없어 전체 결과를 산출하지 않았습니다.")
    elif overall.get("status") == "not_yet_effective":
        lines.append(f"저장된 규칙은 {_md(overall['effective_revision'])}차 개정부터 적용되므로 이 과거 스냅샷의 전체 판정은 산출하지 않았습니다.")
    else:
        rule = overall["rule"]
        if overall.get("rule_source") == "runtime_scenario":
            source = "가정 규칙(이번 조회에만 적용)"
        else:
            source = f"저장된 규칙(적용 개정 {_md(overall.get('effective_revision'))})"
        mode = "모두 통과" if rule["mode"] == "all" else "하나 이상 통과"
        lines.append(
            f"{source}은 지정 지표 {', '.join(_md(item) for item in rule['metric_ids'])} 중 {mode} 조건입니다."
        )
        lines.append(f"원 보고값 기준 전체 판정은 **{_md(_KOREAN_VERDICTS[overall['reported']['verdict']])}**입니다.")
        lines.append(f"재계산 전체 판정은 **{_md(_KOREAN_VERDICTS[overall['computed']['verdict']])}**입니다.")
        if overall["prior"].get("as_of_revision") is None:
            lines.append("과거 관측이 없어 이전 전체 판정은 없습니다.")
        else:
            prior_verdict = overall['prior']['computed']['verdict']
            current_verdict = overall['computed']['verdict']
            revision = _md(overall['prior']['as_of_revision'])
            if prior_verdict == current_verdict:
                lines.append(f"{revision}차 개정과 현재의 전체 판정은 모두 {_KOREAN_VERDICTS[current_verdict]}입니다.")
            else:
                lines.append(f"{revision}차 개정의 전체 판정은 {_KOREAN_VERDICTS[prior_verdict]}였고 "
                             f"현재 판정은 {_KOREAN_VERDICTS[current_verdict]}입니다.")
            if overall["prior"].get("kind") == "scenario_reconstruction":
                lines.append("이전 판정은 현재 규칙을 과거 자료에 적용한 재구성이며 당시 규칙을 뜻하지 않습니다.")
    conditions = report.get("unregistered_conditions", [])
    if conditions:
        lines.extend(["", "## 등록되지 않은 관측 조건", "", "| 이름 | 기록값 | 관측 ID | 개정 |", "|---|---|---|---:|"])
        for item in conditions:
            lines.append("| " + " | ".join(_md(item.get(key)) for key in ("name", "value", "observation_id", "revision")) + " |")
    lines.extend(["", "## 요약", "", _md(report.get("summary")), ""])
    if not embedded:
        recommendation = report.get("agent_recommendation")
        if recommendation is not None:
            lines.extend(["## 에이전트 권고 (기록값)", "", _md(recommendation), ""])
        decision = report.get("user_decision")
        if decision is not None:
            lines.extend(["## 명시된 사용자 결정 (기록값)", ""])
            lines.append(f"선택: {_md(decision.get('selection'))}.")
            lines.append(f"개정: {_md(decision.get('revision'))}.")
            lines.append("")
    return "\n".join(lines)

