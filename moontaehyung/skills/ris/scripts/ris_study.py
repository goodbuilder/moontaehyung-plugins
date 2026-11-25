#!/usr/bin/env python3
"""Append-only, project-local records for multi-session studies.

This module is loaded by ``ris.py`` and intentionally uses only the standard
library. Each study is one readable Markdown file. Its generated section is
validated against an embedded state payload before every read or write; text
outside that section remains human-owned and is preserved byte-for-byte.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
from decimal import Decimal
from pathlib import Path
import re
import sys
from datetime import datetime, timezone
from uuid import UUID, uuid4


SCHEMA_VERSION = 1
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
EVIDENCE_KINDS = {"source", "publication", "assumption", "derived", "unresolved"}
ASSESSMENTS = {"supported", "contradicted", "inconclusive", "untested"}
METRIC_STATUSES = {"match", "mismatch", "not_reported", "indeterminate"}

MANAGED_BEGIN = "<!-- RIS:STUDY:BEGIN -->"
MANAGED_END = "<!-- RIS:STUDY:END -->"
STATE_BEGIN = "<!-- RIS:STUDY:DATA:BEGIN"
STATE_END = "RIS:STUDY:DATA:END -->"
DIGEST_RE = re.compile(r"(?m)^<!-- RIS:STUDY:DIGEST:v(\d+) sha256=([0-9a-f]{64}) -->\n?")
DIGEST_VERSION = 1


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _nonempty_text(ris, value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ris.Error(f"{label} must be a non-empty string")
    return value.strip()


def _text_list(ris, value, label: str, *, allow_empty: bool) -> list[str]:
    if not isinstance(value, list):
        raise ris.Error(f"{label} must be an array of strings")
    if not allow_empty and not value:
        raise ris.Error(f"{label} must contain at least one item")
    result = []
    for i, item in enumerate(value, 1):
        result.append(_nonempty_text(ris, item, f"{label}[{i}]"))
    return result


def _conditions(ris, value, label: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ris.Error(f"{label} must be an object mapping condition names to strings")
    result = {}
    for key, item in value.items():
        name = _nonempty_text(ris, key, f"{label} key")
        result[name] = _nonempty_text(ris, item, f"{label}.{name}")
    return result


def _safe_id(ris, value, label: str) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise ris.Error(f"{label} must match [A-Za-z0-9][A-Za-z0-9_-]{{0,63}}")
    return value


def _exact_keys(ris, value: dict, required: set[str], label: str, *, allow: set[str] | None = None) -> None:
    missing = required - set(value)
    extra = set(value) - required - (allow or set())
    if missing:
        raise ris.Error(f"{label} is missing fields: " + ", ".join(sorted(missing)))
    if extra:
        raise ris.Error(f"{label} has unsupported fields: " + ", ".join(sorted(extra)))


def _basis(ris, value, label: str) -> dict:
    if not isinstance(value, dict):
        raise ris.Error(f"{label} must be an object with kind, locator, and note")
    allowed = {"kind", "locator", "note"}
    extra = set(value) - allowed
    if extra or "kind" not in value:
        if extra:
            raise ris.Error(f"{label} has unsupported fields: " + ", ".join(sorted(extra)))
        raise ris.Error(f"{label} is missing field: kind")
    kind = _nonempty_text(ris, value["kind"], f"{label}.kind")
    if kind not in EVIDENCE_KINDS:
        raise ris.Error(f"{label}.kind must be one of: " + ", ".join(sorted(EVIDENCE_KINDS)))
    locator = value.get("locator", "")
    note = value.get("note", "")
    if not isinstance(locator, str) or not isinstance(note, str):
        raise ris.Error(f"{label}.locator and {label}.note must be strings")
    locator = locator.strip()
    note = note.strip()
    if kind in {"source", "publication"} and not locator:
        raise ris.Error(f"{label}.locator is required for {kind} evidence")
    if kind in {"assumption", "derived", "unresolved"} and not note:
        raise ris.Error(f"{label}.note is required for {kind} evidence")
    return {"kind": kind, "locator": locator, "note": note}


def _evaluation(ris, value, label: str) -> dict:
    if not isinstance(value, dict):
        raise ris.Error(f"{label} must contain assessment and rationale")
    _exact_keys(ris, value, {"assessment", "rationale"}, label)
    assessment = _nonempty_text(ris, value["assessment"], f"{label}.assessment")
    if assessment not in ASSESSMENTS:
        raise ris.Error(f"{label}.assessment must be one of: " + ", ".join(sorted(ASSESSMENTS)))
    return {
        "assessment": assessment,
        "rationale": _nonempty_text(ris, value["rationale"], f"{label}.rationale"),
    }


def _evaluation_map(ris, value, hypothesis_ids: set[str], label: str) -> dict:
    if not isinstance(value, dict):
        raise ris.Error(f"{label} must map every hypothesis ID to an assessment")
    absent = hypothesis_ids - set(value)
    extra = set(value) - hypothesis_ids
    if absent or extra:
        parts = []
        if absent:
            parts.append("missing " + ", ".join(sorted(absent)))
        if extra:
            parts.append("unknown " + ", ".join(sorted(extra)))
        raise ris.Error(f"{label} must assess every hypothesis exactly once (" + "; ".join(parts) + ")")
    return {hid: _evaluation(ris, value[hid], f"{label}.{hid}") for hid in sorted(hypothesis_ids)}


def _test_plan(ris, value, label: str) -> dict:
    if not isinstance(value, dict):
        raise ris.Error(f"{label} must contain description, method, and limits")
    _exact_keys(ris, value, {"description", "method", "limits"}, label)
    return {
        "description": _nonempty_text(ris, value["description"], f"{label}.description"),
        "method": _nonempty_text(ris, value["method"], f"{label}.method"),
        "limits": _text_list(ris, value["limits"], f"{label}.limits", allow_empty=True),
    }


def _next_test(ris, value, hypothesis_ids: set[str], label: str) -> dict | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ris.Error(f"{label} must contain description, method, limits, and predictions")
    _exact_keys(ris, value, {"description", "method", "limits", "predictions"}, label)
    predictions = value["predictions"]
    if not isinstance(predictions, dict):
        raise ris.Error(f"{label}.predictions must map every hypothesis ID to a prediction")
    absent = hypothesis_ids - set(predictions)
    extra = set(predictions) - hypothesis_ids
    if absent or extra:
        parts = []
        if absent:
            parts.append("missing " + ", ".join(sorted(absent)))
        if extra:
            parts.append("unknown " + ", ".join(sorted(extra)))
        raise ris.Error(f"{label}.predictions must cover every hypothesis exactly once (" + "; ".join(parts) + ")")
    return {
        "description": _nonempty_text(ris, value["description"], f"{label}.description"),
        "method": _nonempty_text(ris, value["method"], f"{label}.method"),
        "limits": _text_list(ris, value["limits"], f"{label}.limits", allow_empty=True),
        "predictions": {hid: _nonempty_text(ris, predictions[hid], f"{label}.predictions.{hid}") for hid in sorted(hypothesis_ids)},
    }


def _active_test(ris, value, hypothesis_ids: set[str], label: str) -> dict:
    if not isinstance(value, dict):
        raise ris.Error(f"{label} must be a test plan")
    if "predictions" not in value:
        return _test_plan(ris, value, label)
    return _next_test(ris, value, hypothesis_ids, label)


def _decision_payload(ris, value: dict) -> dict:
    if not isinstance(value, dict):
        raise ris.Error("Study decision body must be a JSON object")
    _exact_keys(ris, value, {"id", "selection", "rationale", "locator"}, "Study decision body")
    return {
        "id": _safe_id(ris, value["id"], "decision.id"),
        "selection": _nonempty_text(ris, value["selection"], "selection"),
        "rationale": _nonempty_text(ris, value["rationale"], "rationale"),
        "locator": _nonempty_text(ris, value["locator"], "locator"),
    }


def _result_rule(ris, value, label: str) -> dict:
    """Normalize an explicit study result rule through the shared result contract."""
    if not isinstance(value, dict):
        raise ris.Error(f"{label} must be an object with mode and metric_ids")
    results = ris.companion("ris_results")
    normalize = getattr(results, "normalize_rule", None)
    if not callable(normalize):
        raise ris.Error("Study result-rule validator is unavailable")
    normalized = normalize(ris, value)
    if not isinstance(normalized, dict):
        raise ris.Error("Study result-rule validator returned an invalid result")
    return normalized


def _amendment_basis(ris, value, triggering_ids: list[str], label: str) -> dict:
    """Validate provenance for an amendment or an added hypothesis.

    Observation lineage must point only to earlier observations explicitly named by
    the amendment. Independent lineage needs a locator so the origin is reviewable.
    """
    if not isinstance(value, dict):
        raise ris.Error(f"{label} must identify observation or independent provenance")
    kind = value.get("kind")
    if kind == "observation":
        _exact_keys(ris, value, {"kind", "observation_ids"}, label)
        observation_ids = _text_list(ris, value["observation_ids"], f"{label}.observation_ids", allow_empty=False)
        if len(set(observation_ids)) != len(observation_ids):
            raise ris.Error(f"{label}.observation_ids contains duplicates")
        outside = set(observation_ids) - set(triggering_ids)
        if outside:
            raise ris.Error(f"{label}.observation_ids must be included in triggering_observation_ids: " + ", ".join(sorted(outside)))
        return {"kind": "observation", "observation_ids": observation_ids}
    if kind == "independent":
        _exact_keys(ris, value, {"kind", "locator"}, label)
        return {"kind": "independent", "locator": _nonempty_text(ris, value["locator"], f"{label}.locator")}
    raise ris.Error(f"{label}.kind must be observation or independent")


def _amendment_payload(ris, value: dict, active_ids: set[str], all_ids: set[str],
                       triggering_observations: dict[str, dict]) -> dict:
    if not isinstance(value, dict):
        raise ris.Error("Study amendment body must be a JSON object")
    required = {"id", "rationale", "triggering_observation_ids", "added_hypotheses"}
    optional = {"basis", "active_test", "next_test", "recommendation", "next_action", "result_rule"}
    missing, extra = required - set(value), set(value) - required - optional
    if missing:
        raise ris.Error("Study amendment body is missing fields: " + ", ".join(sorted(missing)))
    if extra:
        raise ris.Error("Study amendment body has unsupported fields: " + ", ".join(sorted(extra)))

    amendment_id = _safe_id(ris, value["id"], "amendment.id")
    rationale = _nonempty_text(ris, value["rationale"], "amendment.rationale")
    triggering_ids = _text_list(ris, value["triggering_observation_ids"], "triggering_observation_ids", allow_empty=True)
    if len(set(triggering_ids)) != len(triggering_ids):
        raise ris.Error("triggering_observation_ids contains duplicates")
    unknown_triggers = set(triggering_ids) - set(triggering_observations)
    if unknown_triggers:
        raise ris.Error("triggering_observation_ids must reference earlier observations: " + ", ".join(sorted(unknown_triggers)))

    if "basis" in value:
        basis = _amendment_basis(ris, value["basis"], triggering_ids, "basis")
    elif triggering_ids:
        basis = {"kind": "observation", "observation_ids": list(triggering_ids)}
    else:
        raise ris.Error("An amendment without triggering observations requires an explicit independent basis locator")

    if not isinstance(value["added_hypotheses"], list):
        raise ris.Error("added_hypotheses must be an array")
    added = []
    seen = set()
    split_groups = {}
    for index, item in enumerate(value["added_hypotheses"], 1):
        label = f"added_hypotheses[{index}]"
        if not isinstance(item, dict):
            raise ris.Error(f"{label} must be an object")
        fields = {"id", "statement", "prediction"}
        allowed = fields | {"parent_id", "basis"}
        missing_item, extra_item = fields - set(item), set(item) - allowed
        if missing_item:
            raise ris.Error(f"{label} is missing fields: " + ", ".join(sorted(missing_item)))
        if extra_item:
            raise ris.Error(f"{label} has unsupported fields: " + ", ".join(sorted(extra_item)))
        hypothesis_id = _safe_id(ris, item["id"], f"{label}.id")
        if hypothesis_id in all_ids or hypothesis_id in seen:
            raise ris.Error("Hypothesis IDs are immutable and may not be reused: " + hypothesis_id)
        seen.add(hypothesis_id)
        hypothesis = {
            "id": hypothesis_id,
            "statement": _nonempty_text(ris, item["statement"], f"{label}.statement"),
            "prediction": _nonempty_text(ris, item["prediction"], f"{label}.prediction"),
        }
        if "parent_id" in item:
            parent_id = _safe_id(ris, item["parent_id"], f"{label}.parent_id")
            if parent_id not in active_ids:
                raise ris.Error(f"{label}.parent_id must name an active hypothesis: {parent_id}")
            if parent_id == hypothesis_id:
                raise ris.Error(f"{label}.parent_id cannot equal its new hypothesis ID")
            hypothesis["parent_id"] = parent_id
            split_groups.setdefault(parent_id, []).append(hypothesis_id)
        hypothesis_basis = _amendment_basis(
            ris, item["basis"], triggering_ids, f"{label}.basis"
        ) if "basis" in item else basis
        hypothesis["basis"] = hypothesis_basis
        added.append(hypothesis)

    for parent_id, children in split_groups.items():
        if len(children) < 2:
            raise ris.Error(f"A split of {parent_id} requires at least two new child hypotheses")

    retired = sorted(split_groups)
    resulting_active = (set(active_ids) - set(retired)) | seen
    result = {
        "id": amendment_id,
        "rationale": rationale,
        "triggering_observation_ids": triggering_ids,
        "basis": basis,
        "added_hypotheses": added,
        "added_hypothesis_ids": [item["id"] for item in added],
        "retired_hypothesis_ids": retired,
    }

    if "active_test" in value:
        result["active_test"] = _test_plan(ris, value["active_test"], "active_test")
    if "next_test" in value:
        result["next_test"] = _next_test(ris, value["next_test"], resulting_active, "next_test")
    elif resulting_active != set(active_ids):
        raise ris.Error("An amendment that changes the active hypotheses must provide next_test predictions for every active hypothesis")
    if "recommendation" in value:
        result["recommendation"] = _nonempty_text(ris, value["recommendation"], "recommendation")
    if "next_action" in value:
        result["next_action"] = _nonempty_text(ris, value["next_action"], "next_action")
    if "result_rule" in value:
        result["result_rule"] = _result_rule(ris, value["result_rule"], "result_rule")
    return result


def _capture_evidence_files(ris, root: Path, paths: list[str] | None) -> list[dict] | None:
    if paths is None or paths == []:
        return None
    if not isinstance(paths, list):
        raise ris.Error("evidence_paths must be an array of explicit project-relative paths")
    capture = getattr(ris, "study_evidence_hash", None)
    if not callable(capture):
        raise ris.Error("Project evidence fingerprint helper is unavailable")
    result = []
    seen = set()
    for index, relative in enumerate(paths, 1):
        if not isinstance(relative, str) or not relative or relative != relative.strip():
            raise ris.Error(f"evidence file {index} must be an exact project-relative path")
        evidence = capture(root, relative)
        if not isinstance(evidence, dict) or set(evidence) != {"path", "sha256"}:
            raise ris.Error("Project evidence fingerprint helper returned an invalid result")
        path = _nonempty_text(ris, evidence["path"], f"evidence file {index}.path")
        digest = evidence["sha256"]
        if not re.fullmatch(r"[0-9a-f]{64}", digest if isinstance(digest, str) else ""):
            raise ris.Error(f"evidence file {index}.sha256 must be a lowercase SHA-256 digest")
        parts = path.split("/")
        if path.startswith("/") or "\\" in path or any(part in {"", ".", ".."} for part in parts):
            raise ris.Error(f"Evidence helper returned a non-canonical project path: {path}")
        if path in seen:
            raise ris.Error("Duplicate evidence file path: " + path)
        seen.add(path)
        result.append({"path": path, "sha256": digest})
    return sorted(result, key=lambda item: item["path"])


def _metrics_file_entries(ris, metrics_file: str) -> list[dict]:
    try:
        text = Path(metrics_file).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ris.Error(f"Could not read metrics file: {metrics_file}") from exc
    def reject_constant(value):
        raise ValueError("non-standard JSON numeric constant: " + value)
    def unique_object(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate JSON object key: " + key)
            value[key] = item
        return value
    try:
        entries = json.loads(text, parse_float=Decimal, parse_constant=reject_constant, object_pairs_hook=unique_object)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ris.Error(f"Metrics file must contain valid JSON: {metrics_file}") from exc
    if not isinstance(entries, list):
        raise ris.Error("Metrics file must contain a JSON array")
    return entries


def _metric_input_path(ris, value, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ris.Error(f"{label} must be an exact project-relative path")
    parts = value.split("/")
    if value.startswith("/") or "\\" in value or any(part in {"", ".", ".."} for part in parts):
        raise ris.Error(f"{label} must be a canonical project-relative path")
    return value


def _validate_metrics(ris, value, hypothesis_ids: set[str], label: str) -> list[dict]:
    if not isinstance(value, list):
        raise ris.Error(f"{label} must be an array")
    result = []
    seen = set()
    for index, item in enumerate(value, 1):
        item_label = f"{label}[{index}]"
        if not isinstance(item, dict):
            raise ris.Error(f"{item_label} must be an object")
        required = {"definition", "input", "reported", "result", "reported_status", "decision_impact", "hypotheses"}
        _exact_keys(ris, item, required, item_label)
        definition = item["definition"]
        if not isinstance(definition, dict) or not definition:
            raise ris.Error(f"{item_label}.definition must be a non-empty object")
        metric_input = _metric_input_path(ris, item["input"], f"{item_label}.input")
        reported = item["reported"]
        metric_api = ris.companion("ris_metrics")
        if reported is not None and (
            not isinstance(reported, str) or metric_api.normalize_reported(ris, reported) != reported
        ):
            raise ris.Error(f"{item_label}.reported must be a canonical exact decimal or rational string, or null")
        status = item["reported_status"]
        if not isinstance(status, str) or status not in METRIC_STATUSES:
            raise ris.Error(f"{item_label}.reported_status is unsupported")
        if (reported is None) != (status == "not_reported"):
            raise ris.Error(f"{item_label}.reported and reported_status disagree")
        metric_result = item["result"]
        result_status = metric_result.get("status") if isinstance(metric_result, dict) else None
        if not isinstance(metric_result, dict) or not isinstance(result_status, str) or result_status not in {"ok", "indeterminate"}:
            raise ris.Error(f"{item_label}.result must be a metric calculation result")
        metric_id = definition.get("id")
        digest = metric_result.get("definition_sha256")
        input_result = metric_result.get("input")
        input_digest = input_result.get("sha256") if isinstance(input_result, dict) else None
        if (not isinstance(metric_id, str) or not metric_id.strip()
                or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
                or not isinstance(input_result, dict)
                or input_result.get("path") != metric_input
                or not ((isinstance(input_digest, str) and re.fullmatch(r"[0-9a-f]{64}", input_digest))
                        or (input_digest is None and metric_result.get("status") == "indeterminate"))):
            raise ris.Error(f"{item_label}.result is missing its metric identity or captured input digest")
        if metric_result.get("definition") != definition:
            raise ris.Error(f"{item_label}.result definition does not match the normalized definition")
        if metric_result.get("metric_id") != metric_id or metric_result.get("unit") != definition.get("unit"):
            raise ris.Error(f"{item_label}.result metric identity or unit does not match its definition")
        if result_status == "ok":
            value = metric_result.get("value")
            if not isinstance(value, str) or ris.companion("ris_metrics").normalize_reported(ris, value) != value:
                raise ris.Error(f"{item_label}.result.value must be a canonical decimal string")
            threshold_met = metric_result.get("threshold_met")
            if threshold_met is not None and type(threshold_met) is not bool:
                raise ris.Error(f"{item_label}.result.threshold_met must be boolean or null")
        elif metric_result.get("value") is not None or metric_result.get("threshold_met") is not None:
            raise ris.Error(f"{item_label}.result must not infer a value or threshold result when indeterminate")
        identity = metric_id
        if identity in seen:
            raise ris.Error(f"{label} contains a duplicate metric definition: {metric_id}")
        seen.add(identity)
        impact = item["decision_impact"]
        expected_criterion = {"metric_id": metric_id, "threshold": definition["threshold"]} if "threshold" in definition else None
        if (not isinstance(impact, dict)
                or not isinstance(impact.get("reported_vs_computed"), str)
                or impact.get("reported_vs_computed") not in {"threshold_crossed", "threshold_unchanged", "no_threshold", "indeterminate"}
                or not isinstance(impact.get("across_revisions"), (dict, type(None)))
                or not isinstance(impact.get("criterion"), (dict, type(None)))
                or impact.get("criterion") != expected_criterion
                or impact.get("affected_hypotheses") != item["hypotheses"]
                or type(impact.get("review_recommended")) is not bool):
            raise ris.Error(f"{item_label}.decision_impact is invalid")
        if not isinstance(item["hypotheses"], list):
            raise ris.Error(f"{item_label}.hypotheses must be an array of known hypothesis IDs")
        hypotheses = []
        for hypothesis_id in item["hypotheses"]:
            hypothesis_id = _safe_id(ris, hypothesis_id, f"{item_label}.hypotheses item")
            if hypothesis_id not in hypothesis_ids:
                raise ris.Error(f"{item_label}.hypotheses references unknown hypothesis: {hypothesis_id}")
            if hypothesis_id in hypotheses:
                raise ris.Error(f"{item_label}.hypotheses contains duplicate ID: {hypothesis_id}")
            hypotheses.append(hypothesis_id)
        result.append({
            "definition": definition,
            "input": metric_input,
            "reported": reported,
            "result": metric_result,
            "reported_status": status,
            "decision_impact": impact,
            "hypotheses": hypotheses,
        })
    return result


def _metric_requests(ris, root: Path, metrics_file: str, hypothesis_ids: set[str]) -> list[dict]:
    entries = _metrics_file_entries(ris, metrics_file)
    metric_api = ris.companion("ris_metrics")
    requests = []
    seen = set()
    for index, entry in enumerate(entries, 1):
        label = f"metrics[{index}]"
        if not isinstance(entry, dict):
            raise ris.Error(f"{label} must be an object")
        definition_fields = {"definition", "definition_file"} & set(entry)
        required = {"input"}
        allowed = required | {"definition", "definition_file", "reported", "hypotheses"}
        missing, extra = required - set(entry), set(entry) - allowed
        if missing:
            raise ris.Error(f"{label} is missing fields: " + ", ".join(sorted(missing)))
        if extra:
            raise ris.Error(f"{label} has unsupported fields: " + ", ".join(sorted(extra)))
        if len(definition_fields) != 1:
            raise ris.Error(f"{label} must contain exactly one of definition or definition_file")
        if "definition" in definition_fields:
            definition_input = entry["definition"]
        else:
            definition_file = _metric_input_path(ris, entry["definition_file"], f"{label}.definition_file")
            resolved_definition_file = ris.inside(root, definition_file)
            definition_input = metric_api.load_definition_file(ris, str(resolved_definition_file))
        if not isinstance(definition_input, dict):
            raise ris.Error(f"{label}.definition must be an object")
        definition = metric_api.normalize_definition(ris, definition_input)
        metric_input = _metric_input_path(ris, entry["input"], f"{label}.input")
        reported_input = metric_api.normalize_reported(ris, entry.get("reported"))
        hypotheses_value = entry.get("hypotheses", [])
        if not isinstance(hypotheses_value, list):
            raise ris.Error(f"{label}.hypotheses must be an array of known hypothesis IDs")
        hypotheses = []
        for hypothesis_id in hypotheses_value:
            hypothesis_id = _safe_id(ris, hypothesis_id, f"{label}.hypotheses item")
            if hypothesis_id not in hypothesis_ids:
                raise ris.Error(f"{label}.hypotheses references unknown hypothesis: {hypothesis_id}")
            if hypothesis_id in hypotheses:
                raise ris.Error(f"{label}.hypotheses contains duplicate ID: {hypothesis_id}")
            hypotheses.append(hypothesis_id)
        identity = definition["id"]
        if identity in seen:
            raise ris.Error(f"Metrics file contains a duplicate metric definition: {definition['id']}")
        seen.add(identity)
        requests.append({
            "definition": definition,
            "input": metric_input,
            "reported": reported_input,
            "hypotheses": hypotheses,
        })
    return sorted(requests, key=lambda item: (item["definition"]["id"], item["input"]))


def _calculate_observation_metrics(ris, root: Path, requests: list[dict],
                                   revisions: list[dict], evidence_files: list[dict] | None = None) -> list[dict]:
    metric_api = ris.companion("ris_metrics")
    calculations = []
    captured_inputs = {item["path"]: item["sha256"] for item in (evidence_files or [])}
    for request in requests:
        definition = request["definition"]
        metric_input = request["input"]
        reported_input = request["reported"]
        hypotheses = request["hypotheses"]
        label = f"metric {definition['id']}"
        calculated = metric_api.calculate(ris, root, definition, metric_input)
        if not isinstance(calculated, dict):
            raise ris.Error(f"{label} metric helper returned an invalid result")
        input_record = calculated.get("input")
        if not isinstance(input_record, dict) or input_record.get("path") != metric_input:
            raise ris.Error(f"{label} metric helper returned an invalid captured input")
        input_digest = input_record.get("sha256")
        if metric_input in captured_inputs and captured_inputs[metric_input] != input_digest:
            raise ris.Error(f"Metric input changed while capturing evidence; retry observation: {metric_input}")
        captured_inputs[metric_input] = input_digest
        report_comparison = metric_api.compare_reported(definition, calculated, reported_input)
        if not isinstance(report_comparison, dict):
            raise ris.Error(f"{label} metric helper returned an invalid reported comparison")
        reported = report_comparison.get("reported")
        reported_status = report_comparison.get("reported_status")
        if reported_status not in METRIC_STATUSES:
            raise ris.Error(f"{label} metric helper returned an unsupported reported status")
        metric_id = calculated.get("metric_id", definition.get("id"))
        criterion = None
        if isinstance(metric_id, str) and "threshold" in definition:
            criterion = {"metric_id": metric_id, "threshold": definition["threshold"]}
        previous = None
        for prior_revision in reversed(revisions[1:]):
            prior_observation = prior_revision.get("observation")
            if prior_observation is None:
                continue
            for prior_metric in prior_observation.get("metrics", []):
                if prior_metric.get("definition", {}).get("id") == metric_id:
                    previous = (prior_revision["revision"], prior_metric)
                    break
            if previous is not None:
                break
        across_revisions = None
        if previous is not None:
            prior_revision_number, prior_metric = previous
            comparison = metric_api.compare_results(prior_metric["result"], calculated)
            if not isinstance(comparison, dict):
                raise ris.Error(f"{label} metric helper returned an invalid revision comparison")
            across_revisions = {"from_revision": prior_revision_number, **comparison}
        report_impact = report_comparison.get("decision_impact", "indeterminate")
        review_recommended = (
            reported_status == "mismatch"
            or report_impact == "threshold_crossed"
            or calculated.get("status") == "indeterminate"
            or (isinstance(across_revisions, dict)
                and (across_revisions.get("decision_impact") == "threshold_crossed"
                     or across_revisions.get("status") == "indeterminate"))
        )
        impact = {
            "reported_vs_computed": report_impact,
            "across_revisions": across_revisions,
            "criterion": criterion,
            "affected_hypotheses": hypotheses,
            "review_recommended": review_recommended,
            "reason": report_comparison.get("reason"),
        }
        calculations.append({
            "definition": definition,
            "input": metric_input,
            "reported": reported,
            "result": calculated,
            "reported_status": reported_status,
            "decision_impact": impact,
            "hypotheses": hypotheses,
        })
    hypothesis_ids = {hypothesis_id for request in requests for hypothesis_id in request["hypotheses"]}
    calculations = _validate_metrics(ris, calculations, hypothesis_ids, "metrics")
    return sorted(calculations, key=lambda item: (item["definition"]["id"], item["input"]))


def _validate_evidence_files(ris, value, label: str) -> list[dict]:
    if not isinstance(value, list) or not value:
        raise ris.Error(f"{label} must be a non-empty array of path and sha256 entries")
    result = []
    seen = set()
    for index, item in enumerate(value, 1):
        item_label = f"{label}[{index}]"
        if not isinstance(item, dict):
            raise ris.Error(f"{item_label} must be an object")
        _exact_keys(ris, item, {"path", "sha256"}, item_label)
        path = _nonempty_text(ris, item["path"], f"{item_label}.path")
        parts = path.split("/")
        if path.startswith("/") or "\\" in path or any(part in {"", ".", ".."} for part in parts):
            raise ris.Error(f"{item_label}.path must be a canonical project-relative path")
        digest = item["sha256"]
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ris.Error(f"{item_label}.sha256 must be a lowercase SHA-256 digest")
        if path in seen:
            raise ris.Error(f"{label} contains duplicate paths: {path}")
        seen.add(path)
        result.append({"path": path, "sha256": digest})
    return sorted(result, key=lambda entry: entry["path"])


def _start_payload(ris, study_id: str, project_id: str, value: dict) -> dict:
    if not isinstance(value, dict):
        raise ris.Error("Study start body must be a JSON object")
    required = {
        "goal", "criteria", "conditions", "hypotheses", "test", "recommendation",
        "rationale", "next_action", "evaluations",
    }
    missing, extra = required - set(value), set(value) - required - {"result_rule"}
    if missing:
        raise ris.Error("Study start body is missing fields: " + ", ".join(sorted(missing)))
    if extra:
        raise ris.Error("Study start body has unsupported fields: " + ", ".join(sorted(extra)))
    goal = _nonempty_text(ris, value["goal"], "goal")
    criteria = _text_list(ris, value["criteria"], "criteria", allow_empty=False)
    conditions = _conditions(ris, value["conditions"], "conditions")
    if not isinstance(value["hypotheses"], list) or not value["hypotheses"]:
        raise ris.Error("hypotheses must be a non-empty array")
    hypotheses = []
    seen = set()
    for i, item in enumerate(value["hypotheses"], 1):
        label = f"hypotheses[{i}]"
        if not isinstance(item, dict):
            raise ris.Error(f"{label} must be an object")
        _exact_keys(ris, item, {"id", "statement", "prediction", "basis"}, label)
        hid = _safe_id(ris, item["id"], f"{label}.id")
        if hid in seen:
            raise ris.Error("Duplicate hypothesis ID: " + hid)
        seen.add(hid)
        hypotheses.append({
            "id": hid,
            "statement": _nonempty_text(ris, item["statement"], f"{label}.statement"),
            "prediction": _nonempty_text(ris, item["prediction"], f"{label}.prediction"),
            "basis": _basis(ris, item["basis"], f"{label}.basis"),
        })
    initial = _evaluation_map(ris, value["evaluations"], seen, "evaluations")
    for hypothesis in hypotheses:
        hypothesis["initial_assessment"] = initial[hypothesis["id"]]
    state = {
        "schema_version": SCHEMA_VERSION,
        "id": study_id,
        "project_id": project_id,
        "ris_id": str(uuid4()),
        "created_at": _timestamp(),
        "goal": goal,
        "criteria": criteria,
        "conditions": conditions,
        "hypotheses": hypotheses,
        "test": _test_plan(ris, value["test"], "test"),
        "revisions": [{
            "revision": 1,
            "recorded_at": _timestamp(),
            "observation": None,
            "decision": None,
            "active_test": _test_plan(ris, value["test"], "test"),
            "next_test": None,
            "recommendation": _nonempty_text(ris, value["recommendation"], "recommendation"),
            "rationale": _nonempty_text(ris, value["rationale"], "rationale"),
            "next_action": _nonempty_text(ris, value["next_action"], "next_action"),
        }],
    }
    if "result_rule" in value:
        state["result_rule"] = _result_rule(ris, value["result_rule"], "result_rule")
    return state


def _observation_payload(ris, value: dict, hypothesis_ids: set[str], evidence_files: list[dict] | None = None) -> dict:
    if not isinstance(value, dict):
        raise ris.Error("Study observation body must be a JSON object")
    fields = {
        "id", "finding", "locator", "evidence_kind", "conditions", "limitations",
        "evaluations", "recommendation", "rationale", "next_action",
    }
    missing = fields - set(value)
    extra = set(value) - fields - {"next_test"}
    if missing:
        raise ris.Error("Study observation body is missing fields: " + ", ".join(sorted(missing)))
    if extra:
        raise ris.Error("Study observation body has unsupported fields: " + ", ".join(sorted(extra)))
    observation_id = _safe_id(ris, value["id"], "observation.id")
    evidence_kind = _nonempty_text(ris, value["evidence_kind"], "evidence_kind")
    if evidence_kind not in EVIDENCE_KINDS:
        raise ris.Error("evidence_kind must be one of: " + ", ".join(sorted(EVIDENCE_KINDS)))
    observation = {
        "id": observation_id,
        "finding": _nonempty_text(ris, value["finding"], "finding"),
        "locator": _nonempty_text(ris, value["locator"], "locator"),
        "evidence_kind": evidence_kind,
        "conditions": _conditions(ris, value["conditions"], "observation.conditions"),
        "limitations": _text_list(ris, value["limitations"], "limitations", allow_empty=True),
        "evaluations": _evaluation_map(ris, value["evaluations"], hypothesis_ids, "evaluations"),
        "recommendation": _nonempty_text(ris, value["recommendation"], "recommendation"),
        "rationale": _nonempty_text(ris, value["rationale"], "rationale"),
        "next_action": _nonempty_text(ris, value["next_action"], "next_action"),
        "next_test": _next_test(ris, value.get("next_test"), hypothesis_ids, "next_test") if "next_test" in value else None,
    }
    if evidence_files is not None:
        observation["evidence_files"] = _validate_evidence_files(ris, evidence_files, "evidence_files")
    return observation


def _iso_timestamp(ris, value, label: str) -> None:
    if not isinstance(value, str):
        raise ris.Error(f"{label} must be an ISO date-time with timezone")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("timezone required")
    except ValueError as exc:
        raise ris.Error(f"{label} must be an ISO date-time with timezone") from exc


def _original_hypotheses(state: dict) -> list[dict]:
    return [item for item in state["hypotheses"] if "introduced_revision" not in item]


def _known_hypotheses_at(state: dict, revision: int) -> list[dict]:
    return [
        item for item in state["hypotheses"]
        if item.get("introduced_revision", 1) <= revision
    ]


def _active_hypothesis_ids_at(state: dict, revision: int) -> set[str]:
    active = {item["id"] for item in _original_hypotheses(state)}
    for item in state["revisions"][1:revision]:
        amendment = item.get("amendment")
        if amendment is None:
            continue
        active.difference_update(amendment["retired_hypothesis_ids"])
        active.update(amendment["added_hypothesis_ids"])
    return active


def _validate_state(ris, state: dict, study_id: str, project_id: str) -> dict:
    root_fields = {
        "schema_version", "id", "project_id", "ris_id", "created_at", "goal", "criteria", "conditions",
        "hypotheses", "test", "revisions",
    }
    if not isinstance(state, dict):
        raise ris.Error("Study state must be a JSON object")
    missing, extra = root_fields - set(state), set(state) - root_fields - {"result_rule"}
    if missing:
        raise ris.Error("Study state is missing fields: " + ", ".join(sorted(missing)))
    if extra:
        raise ris.Error("Study state has unsupported fields: " + ", ".join(sorted(extra)))
    if type(state["schema_version"]) is not int or state["schema_version"] != SCHEMA_VERSION:
        raise ris.Error("Unsupported study record schema version")
    if state["id"] != study_id or state["project_id"] != project_id:
        raise ris.Error("Study identity or project identity mismatch")
    if not isinstance(state["ris_id"], str):
        raise ris.Error("Study ris_id must be a UUID string")
    try:
        if str(UUID(state["ris_id"])) != state["ris_id"]:
            raise ValueError("non-canonical UUID")
    except ValueError as exc:
        raise ris.Error("Study ris_id must be a canonical UUID string") from exc
    _iso_timestamp(ris, state["created_at"], "created_at")
    _nonempty_text(ris, state["goal"], "goal")
    _text_list(ris, state["criteria"], "criteria", allow_empty=False)
    _conditions(ris, state["conditions"], "conditions")
    if "result_rule" in state and _result_rule(ris, state["result_rule"], "result_rule") != state["result_rule"]:
        raise ris.Error("Study result_rule is not in normalized form")
    if not isinstance(state["hypotheses"], list) or not state["hypotheses"]:
        raise ris.Error("Study hypotheses are missing or invalid")

    hypothesis_by_id = {}
    previous_introduction = 1
    saw_amended_hypothesis = False
    for i, hypothesis in enumerate(state["hypotheses"], 1):
        label = f"hypotheses[{i}]"
        if not isinstance(hypothesis, dict):
            raise ris.Error(f"{label} must be an object")
        if "introduced_revision" not in hypothesis:
            if saw_amended_hypothesis:
                raise ris.Error("Original hypotheses must precede hypotheses added by amendments")
            _exact_keys(ris, hypothesis, {"id", "statement", "prediction", "basis", "initial_assessment"}, label)
            _basis(ris, hypothesis["basis"], f"{label}.basis")
            introduction = 1
        else:
            saw_amended_hypothesis = True
            required_hypothesis = {"id", "statement", "prediction", "basis", "initial_assessment", "introduced_revision"}
            _exact_keys(ris, hypothesis, required_hypothesis, label, allow={"parent_id"})
            introduction = hypothesis["introduced_revision"]
            if type(introduction) is not int or introduction < 2 or introduction < previous_introduction:
                raise ris.Error(f"{label}.introduced_revision must be a nondecreasing revision number greater than 1")
            previous_introduction = introduction
            if not isinstance(hypothesis["basis"], dict):
                raise ris.Error(f"{label}.basis must identify its amendment provenance")
        hid = _safe_id(ris, hypothesis["id"], f"{label}.id")
        if hid in hypothesis_by_id:
            raise ris.Error("Duplicate hypothesis ID: " + hid)
        hypothesis_by_id[hid] = hypothesis
        _nonempty_text(ris, hypothesis["statement"], f"{label}.statement")
        _nonempty_text(ris, hypothesis["prediction"], f"{label}.prediction")
        evaluation = _evaluation(ris, hypothesis["initial_assessment"], f"{label}.initial_assessment")
        if introduction > 1 and evaluation["assessment"] != "untested":
            raise ris.Error(f"{label}.initial_assessment must remain untested when introduced")
        if "parent_id" in hypothesis:
            _safe_id(ris, hypothesis["parent_id"], f"{label}.parent_id")
    _test_plan(ris, state["test"], "test")
    if not isinstance(state["revisions"], list) or not state["revisions"]:
        raise ris.Error("Study revision history is missing")

    initial_ids = {item["id"] for item in _original_hypotheses(state)}
    if not initial_ids:
        raise ris.Error("Study must retain at least one original hypothesis")
    observation_ids = {}
    decision_ids = set()
    amendment_ids = set()
    previous_active_test = None
    previous_next_test = None
    previous_decision_id = None
    active_ids = set(initial_ids)
    known_ids = set(initial_ids)
    for i, revision in enumerate(state["revisions"], 1):
        label = f"revisions[{i}]"
        if not isinstance(revision, dict):
            raise ris.Error(f"{label} must be an object")
        required_revision = {"revision", "recorded_at", "observation", "decision", "active_test", "next_test", "recommendation", "rationale", "next_action"}
        _exact_keys(ris, revision, required_revision, label, allow={"amendment"})
        if type(revision["revision"]) is not int or revision["revision"] != i:
            raise ris.Error("Study revisions must be consecutive starting at 1")
        _iso_timestamp(ris, revision["recorded_at"], f"{label}.recorded_at")
        for key in ("recommendation", "rationale", "next_action"):
            _nonempty_text(ris, revision[key], f"{label}.{key}")
        observation = revision["observation"]
        decision = revision["decision"]
        amendment = revision.get("amendment")
        event_count = sum(event is not None for event in (observation, decision, amendment))
        if i == 1:
            if event_count != 0:
                raise ris.Error("Revision 1 is the original proposal and cannot contain an observation, decision, or amendment")
            active_test = _active_test(ris, revision["active_test"], active_ids, f"{label}.active_test")
            next_test = _next_test(ris, revision["next_test"], active_ids, f"{label}.next_test")
            if active_test != state["test"] or next_test is not None:
                raise ris.Error("Revision 1 active_test must preserve the original test and have no next_test")
        else:
            if event_count != 1:
                raise ris.Error(f"{label} must contain exactly one observation, explicit user decision, or study amendment")
            if observation is not None:
                if not isinstance(observation, dict):
                    raise ris.Error(f"{label}.observation must be an object")
                observation_fields = {"id", "finding", "locator", "evidence_kind", "conditions", "limitations", "evaluations"}
                missing_observation = observation_fields - set(observation)
                extra_observation = set(observation) - observation_fields - {"evidence_files", "metrics"}
                if missing_observation:
                    raise ris.Error(f"{label}.observation is missing fields: " + ", ".join(sorted(missing_observation)))
                if extra_observation:
                    raise ris.Error(f"{label}.observation has unsupported fields: " + ", ".join(sorted(extra_observation)))
                oid = _safe_id(ris, observation["id"], f"{label}.observation.id")
                if oid in observation_ids:
                    raise ris.Error("Duplicate observation ID in history: " + oid)
                _nonempty_text(ris, observation["finding"], f"{label}.observation.finding")
                _nonempty_text(ris, observation["locator"], f"{label}.observation.locator")
                kind = observation["evidence_kind"]
                if not isinstance(kind, str) or kind not in EVIDENCE_KINDS:
                    raise ris.Error(f"{label}.observation.evidence_kind is unsupported")
                _conditions(ris, observation["conditions"], f"{label}.observation.conditions")
                _text_list(ris, observation["limitations"], f"{label}.observation.limitations", allow_empty=True)
                _evaluation_map(ris, observation["evaluations"], active_ids, f"{label}.observation.evaluations")
                if "evidence_files" in observation:
                    _validate_evidence_files(ris, observation["evidence_files"], f"{label}.observation.evidence_files")
                if "metrics" in observation:
                    _validate_metrics(ris, observation["metrics"], active_ids, f"{label}.observation.metrics")
                active_test = _active_test(ris, revision["active_test"], active_ids, f"{label}.active_test")
                next_test = _next_test(ris, revision["next_test"], active_ids, f"{label}.next_test")
                expected_active = previous_next_test or previous_active_test
                if i >= 3:
                    preceding_revision = state["revisions"][i - 2]
                    preceding_amendment = preceding_revision.get("amendment")
                    if preceding_amendment is not None and "active_test" in preceding_amendment:
                        before_amendment = state["revisions"][i - 3]
                        observations_before_amendment = any(
                            item.get("observation") is not None for item in state["revisions"][:i - 2]
                        )
                        if not observations_before_amendment and preceding_revision["active_test"] != before_amendment["active_test"]:
                            expected_active = previous_active_test
                if active_test != expected_active:
                    raise ris.Error(f"{label}.active_test must use the previous next_test when one exists")
                observation_ids[oid] = observation
            elif decision is not None:
                if not isinstance(decision, dict):
                    raise ris.Error(f"{label}.decision must be an object")
                _exact_keys(ris, decision, {"id", "selection", "rationale", "locator", "supersedes"}, f"{label}.decision")
                did = _safe_id(ris, decision["id"], f"{label}.decision.id")
                if did in decision_ids:
                    raise ris.Error("Duplicate decision ID in history: " + did)
                decision_ids.add(did)
                _nonempty_text(ris, decision["selection"], f"{label}.decision.selection")
                _nonempty_text(ris, decision["rationale"], f"{label}.decision.rationale")
                _nonempty_text(ris, decision["locator"], f"{label}.decision.locator")
                if decision["supersedes"] != previous_decision_id:
                    raise ris.Error(f"{label}.decision must supersede the latest explicit user decision")
                previous_decision_id = did
                active_test = _active_test(ris, revision["active_test"], active_ids, f"{label}.active_test")
                next_test = _next_test(ris, revision["next_test"], active_ids, f"{label}.next_test")
                if active_test != previous_active_test or next_test != previous_next_test:
                    raise ris.Error(f"{label} decision revisions must preserve the active and next tests")
            else:
                amendment_required = {
                    "id", "rationale", "triggering_observation_ids", "basis", "added_hypotheses",
                    "added_hypothesis_ids", "retired_hypothesis_ids",
                }
                amendment_optional = {"active_test", "next_test", "recommendation", "next_action", "result_rule"}
                if not isinstance(amendment, dict):
                    raise ris.Error(f"{label}.amendment must be an object")
                _exact_keys(ris, amendment, amendment_required, f"{label}.amendment", allow=amendment_optional)
                aid = _safe_id(ris, amendment["id"], f"{label}.amendment.id")
                if aid in amendment_ids:
                    raise ris.Error("Duplicate amendment ID in history: " + aid)
                amendment_ids.add(aid)
                rationale = _nonempty_text(ris, amendment["rationale"], f"{label}.amendment.rationale")
                if revision["rationale"] != rationale:
                    raise ris.Error(f"{label}.rationale must preserve its amendment rationale")
                triggers = _text_list(ris, amendment["triggering_observation_ids"], f"{label}.amendment.triggering_observation_ids", allow_empty=True)
                if len(set(triggers)) != len(triggers) or not set(triggers) <= set(observation_ids):
                    raise ris.Error(f"{label}.amendment.triggering_observation_ids must be unique earlier observations")
                basis = _amendment_basis(ris, amendment["basis"], triggers, f"{label}.amendment.basis")
                if basis != amendment["basis"]:
                    raise ris.Error(f"{label}.amendment.basis is not normalized")
                if not isinstance(amendment["added_hypotheses"], list):
                    raise ris.Error(f"{label}.amendment.added_hypotheses must be an array")
                event_added_ids = []
                split_groups = {}
                for added_index, added in enumerate(amendment["added_hypotheses"], 1):
                    added_label = f"{label}.amendment.added_hypotheses[{added_index}]"
                    if not isinstance(added, dict):
                        raise ris.Error(f"{added_label} must be an object")
                    added_required = {"id", "statement", "prediction", "basis"}
                    _exact_keys(ris, added, added_required, added_label, allow={"parent_id"})
                    hid = _safe_id(ris, added["id"], f"{added_label}.id")
                    if hid in known_ids or hid in event_added_ids:
                        raise ris.Error("Hypothesis IDs are immutable and may not be reused: " + hid)
                    hypothesis = hypothesis_by_id.get(hid)
                    if hypothesis is None:
                        raise ris.Error(f"{added_label} is missing its immutable hypothesis record")
                    if hypothesis.get("introduced_revision") != i:
                        raise ris.Error(f"{added_label} has an incorrect introduced_revision")
                    if hypothesis["id"] != hid or hypothesis["statement"] != added["statement"] or hypothesis["prediction"] != added["prediction"] or hypothesis["basis"] != added["basis"]:
                        raise ris.Error(f"{added_label} does not match the immutable hypothesis record")
                    if "parent_id" in added:
                        parent_id = _safe_id(ris, added["parent_id"], f"{added_label}.parent_id")
                        if parent_id not in active_ids or hypothesis.get("parent_id") != parent_id:
                            raise ris.Error(f"{added_label}.parent_id must name an active hypothesis and match its record")
                        split_groups.setdefault(parent_id, []).append(hid)
                    elif "parent_id" in hypothesis:
                        raise ris.Error(f"{added_label} omits its immutable parent_id")
                    normalized_basis = _amendment_basis(ris, added["basis"], triggers, f"{added_label}.basis")
                    if normalized_basis != added["basis"]:
                        raise ris.Error(f"{added_label}.basis is not normalized")
                    if hypothesis["initial_assessment"].get("assessment") != "untested":
                        raise ris.Error(f"{added_label} must start untested")
                    event_added_ids.append(hid)
                for parent_id, children in split_groups.items():
                    if len(children) < 2:
                        raise ris.Error(f"A split of {parent_id} requires at least two new child hypotheses")
                retired = sorted(split_groups)
                if amendment["added_hypothesis_ids"] != event_added_ids:
                    raise ris.Error(f"{label}.amendment.added_hypothesis_ids must match its added hypotheses")
                if amendment["retired_hypothesis_ids"] != retired:
                    raise ris.Error(f"{label}.amendment.retired_hypothesis_ids must match split parents")
                new_active_ids = (set(active_ids) - set(retired)) | set(event_added_ids)
                if amendment.get("result_rule") is not None:
                    if _result_rule(ris, amendment["result_rule"], f"{label}.amendment.result_rule") != amendment["result_rule"]:
                        raise ris.Error(f"{label}.amendment.result_rule is not normalized")
                if "recommendation" in amendment:
                    if _nonempty_text(ris, amendment["recommendation"], f"{label}.amendment.recommendation") != revision["recommendation"]:
                        raise ris.Error(f"{label}.recommendation must match its amendment")
                elif revision["recommendation"] != state["revisions"][i - 2]["recommendation"]:
                    raise ris.Error(f"{label}.recommendation must be preserved when the amendment omits it")
                if "next_action" in amendment:
                    if _nonempty_text(ris, amendment["next_action"], f"{label}.amendment.next_action") != revision["next_action"]:
                        raise ris.Error(f"{label}.next_action must match its amendment")
                elif revision["next_action"] != state["revisions"][i - 2]["next_action"]:
                    raise ris.Error(f"{label}.next_action must be preserved when the amendment omits it")
                active_test_expected = amendment.get("active_test", previous_active_test)
                if "active_test" in amendment and any(item.get("observation") is not None for item in state["revisions"][:i - 1]):
                    if active_test_expected != previous_active_test:
                        raise ris.Error(f"{label}.amendment cannot rewrite an active_test already tied to an observation; amend next_test instead")
                active_test = _active_test(ris, revision["active_test"], active_ids, f"{label}.active_test")
                if active_test != active_test_expected:
                    raise ris.Error(f"{label}.active_test must preserve the active test or match the pre-observation amendment")
                next_test_expected = amendment.get("next_test", previous_next_test)
                if new_active_ids != active_ids and "next_test" not in amendment:
                    raise ris.Error(f"{label}.amendment must provide next_test predictions after changing active hypotheses")
                next_test = _next_test(ris, revision["next_test"], new_active_ids, f"{label}.next_test")
                if next_test != next_test_expected:
                    raise ris.Error(f"{label}.next_test must preserve the previous test or match the amendment")
                active_ids = new_active_ids
                known_ids.update(event_added_ids)
        previous_active_test = active_test
        previous_next_test = next_test
    if set(hypothesis_by_id) != known_ids:
        raise ris.Error("Every added hypothesis must be introduced by exactly one earlier amendment")
    return state


def _escape(value: str) -> str:
    return html.escape(value, quote=False)


def _escape_markdown(value: str) -> str:
    escaped = _escape(value)
    for char in r"\`*_{}[]()#+-.!|~":
        escaped = escaped.replace(char, "\\" + char)
    return escaped


def _inline(value: str) -> str:
    return _escape_markdown(value).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")


def _quote(value: str) -> str:
    return "\n".join("> " + _escape_markdown(line) if line else ">" for line in value.splitlines()) or ">"


def _conditions_markdown(conditions: dict[str, str]) -> list[str]:
    if not conditions:
        return ["- None recorded."]
    return [f"- **{_inline(key)}**: {_inline(conditions[key])}" for key in sorted(conditions)]


def _list_markdown(items: list[str]) -> list[str]:
    return [f"- {_inline(item)}" for item in items] if items else ["- None recorded."]


def _locator_markdown(locator: str) -> str:
    path, marker, anchor = locator.partition("#")
    target = None
    for prefix in ("research/", ".ris/research/"):
        if path.startswith(prefix):
            target = "../" + path[len(prefix):]
            break
    if path.startswith("exploration/"):
        target = "../" + path
    suffix = "#" + anchor if marker else ""
    if target and not re.search(r'[\s()<>\"\[\]{}|`\\]', target + suffix):
        return f"[{_inline(locator)}](<{_escape(target + suffix)}>)"
    return _inline(locator)


def _test_markdown(label: str, test: dict | None) -> list[str]:
    if test is None:
        return [f"**{label}:** None proposed."]
    lines = [f"**{label}:**", *_quote(test["description"]).splitlines(), "**Method:**", *_quote(test["method"]).splitlines(), "**Known limits:**"]
    lines.extend(_list_markdown(test["limits"]))
    if "predictions" in test:
        lines.append("**Predictions by hypothesis:**")
        lines.extend(f"- **{hid}**: {_inline(prediction)}" for hid, prediction in test["predictions"].items())
    return lines


def _latest_decision(revisions: list[dict]) -> tuple[int, dict] | tuple[None, None]:
    for revision in reversed(revisions):
        if revision.get("decision") is not None:
            return revision["revision"], revision["decision"]
    return None, None


def _latest_evaluations(state: dict, revisions: list[dict]) -> dict:
    evaluations = {
        hypothesis["id"]: dict(hypothesis["initial_assessment"])
        for hypothesis in _original_hypotheses(state)
    }
    for revision in revisions[1:]:
        amendment = revision.get("amendment")
        if amendment is not None:
            for hypothesis_id in amendment["retired_hypothesis_ids"]:
                evaluations.pop(hypothesis_id, None)
            for hypothesis_id in amendment["added_hypothesis_ids"]:
                hypothesis = next(item for item in state["hypotheses"] if item["id"] == hypothesis_id)
                evaluations[hypothesis_id] = dict(hypothesis["initial_assessment"])
            continue
        observation = revision.get("observation")
        if observation is not None:
            evaluations = {key: dict(value) for key, value in observation["evaluations"].items()}
    return evaluations


def _effective_result_rule_record(state: dict, revisions: list[dict]) -> tuple[dict | None, int | None]:
    rule = state.get("result_rule")
    rule_revision = 1 if rule is not None else None
    for index, revision in enumerate(revisions[1:], start=2):
        amendment = revision.get("amendment")
        if amendment is not None and "result_rule" in amendment:
            rule = amendment["result_rule"]
            rule_revision = index
    return (dict(rule), rule_revision) if rule is not None else (None, None)


def _amendments_view(revisions: list[dict]) -> list[dict]:
    result = []
    for revision in revisions:
        amendment = revision.get("amendment")
        if amendment is None:
            continue
        result.append({**amendment, "revision": revision["revision"], "recorded_at": revision["recorded_at"]})
    return result


def _state_token(state: dict) -> str:
    raw = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def _seal_managed(ris, state: dict, relative: str) -> str:
    """Attach a digest over the original visible projection and payload, excluding itself."""
    report = ris.verified_study_results(_snapshot(state, relative))
    result_section = ris.companion("ris_results").render_results(report, embedded=True) if report else ""
    rendered = _render_managed(state, result_section=result_section)
    marker_at = rendered.rfind(MANAGED_END)
    if marker_at < 0:
        raise ValueError("Managed study renderer omitted its end marker")
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    return rendered[:marker_at] + f"<!-- RIS:STUDY:DIGEST:v{DIGEST_VERSION} sha256={digest} -->\n" + rendered[marker_at:]


def _render_managed(state: dict, *, result_section: str = "") -> str:
    current = state["revisions"][-1]
    current_decision_revision, current_decision = _latest_decision(state["revisions"])
    current_evaluations = _latest_evaluations(state, state["revisions"])
    lines = [MANAGED_BEGIN, f"# Study {state['id']}", ""]
    if result_section:
        lines.extend([result_section.rstrip(), ""])
    lines.extend(["## Current status", "**Goal**", _quote(state["goal"]), "", "**Current recommendation (agent; not a user decision)**", _quote(current["recommendation"]), "", "**Reason**", _quote(current["rationale"]), "", "**Next action**", _quote(current["next_action"]), "", "**Current hypothesis assessments**"])
    current_active_ids = _active_hypothesis_ids_at(state, current["revision"])
    for hypothesis in state["hypotheses"]:
        if hypothesis["id"] not in current_active_ids:
            continue
        evaluation = current_evaluations[hypothesis["id"]]
        lines.append(f"- **{hypothesis['id']}** — `{evaluation['assessment']}`: {_inline(evaluation['rationale'])}")
    lines.extend(["", "**Active test**"])
    lines.extend(_test_markdown("Active test", current["active_test"]))
    lines.extend(["", "**Next test proposed**"])
    lines.extend(_test_markdown("Next test", current["next_test"]))
    lines.extend(["", "**Explicit user decision**"])
    if current_decision is None:
        lines.append("No explicit user decision recorded.")
    else:
        lines.extend([
            f"- Decision `{_escape(current_decision['id'])}` at revision {current_decision_revision}: **{_inline(current_decision['selection'])}**",
            f"- Rationale: {_inline(current_decision['rationale'])}",
            f"- Confirmation locator: {_locator_markdown(current_decision['locator'])}",
            f"- Supersedes: {_escape(current_decision['supersedes']) if current_decision['supersedes'] else 'none'}",
        ])
    lines.extend(["", "## Success criteria"])
    lines.extend(_list_markdown(state["criteria"]))
    lines.extend(["", "## Original conditions"])
    lines.extend(_conditions_markdown(state["conditions"]))
    lines.extend(["", "## Original hypotheses and predictions"])
    for hypothesis in _original_hypotheses(state):
        basis = hypothesis["basis"]
        lines.extend([
            "", f"### {hypothesis['id']}", "**Statement**", _quote(hypothesis["statement"]),
            "", "**Prediction**", _quote(hypothesis["prediction"]),
            "", f"**Basis kind:** `{_escape(basis['kind'])}`",
        ])
        if basis["locator"]:
            lines.extend([f"**Basis locator:** {_locator_markdown(basis['locator'])}"])
        if basis["note"]:
            lines.extend(["**Basis note**", _quote(basis["note"])])
        initial = hypothesis["initial_assessment"]
        lines.extend([f"**Initial assessment:** `{initial['assessment']}` — {_inline(initial['rationale'])}"])
    added_hypotheses = [item for item in state["hypotheses"] if "introduced_revision" in item]
    if added_hypotheses:
        lines.extend(["", "## Hypotheses added by amendment"])
        for hypothesis in added_hypotheses:
            basis = hypothesis["basis"]
            lines.extend([
                "", f"### {hypothesis['id']} · introduced at revision {hypothesis['introduced_revision']}",
                "**Statement**", _quote(hypothesis["statement"]), "", "**Prediction**", _quote(hypothesis["prediction"]),
                f"**Basis:** `{_escape(basis['kind'])}`",
            ])
            if basis["kind"] == "observation":
                lines.append("**Trigger observations:** " + ", ".join(f"`{_escape(oid)}`" for oid in basis["observation_ids"]))
            else:
                lines.append(f"**Independent basis locator:** {_locator_markdown(basis['locator'])}")
            if "parent_id" in hypothesis:
                lines.append(f"**Split from:** `{_escape(hypothesis['parent_id'])}`")
            initial = hypothesis["initial_assessment"]
            lines.append(f"**Initial assessment:** `{initial['assessment']}` — {_inline(initial['rationale'])}")
    lines.extend(["", "## Original test"])
    lines.extend(_test_markdown("Original test", state["test"]))
    lines.extend(["", "## Revision history"])
    revisions = state["revisions"]
    for index in range(len(revisions) - 1, -1, -1):
        revision = revisions[index]
        label = "Current recommendation (agent)" if index == len(revisions) - 1 else "Historical recommendation (agent)"
        lines.extend([
            "", f"### Revision {revision['revision']} · {_escape(revision['recorded_at'])}",
            f"**{label}; not a user decision**", _quote(revision["recommendation"]),
            "", "**Reason**", _quote(revision["rationale"]),
            "", "**Next action**", _quote(revision["next_action"]),
            "", "**Active test**",
        ])
        lines.extend(_test_markdown("Active test", revision["active_test"]))
        lines.extend(["", "**Next test proposed**"])
        lines.extend(_test_markdown("Next test", revision["next_test"]))
        if revision["observation"] is None:
            if revision.get("amendment") is not None:
                amendment = revision["amendment"]
                assessments = _latest_evaluations(state, revisions[:index + 1])
                lines.extend(["", "**Study amendment**", f"- Event ID: `{_escape(amendment['id'])}`"])
                if amendment["triggering_observation_ids"]:
                    lines.append("- Trigger observations: " + ", ".join(f"`{_escape(oid)}`" for oid in amendment["triggering_observation_ids"]))
                if amendment["added_hypothesis_ids"]:
                    lines.append("- Added hypotheses: " + ", ".join(f"`{_escape(hid)}`" for hid in amendment["added_hypothesis_ids"]))
                if amendment["retired_hypothesis_ids"]:
                    lines.append("- Retired from future assessments: " + ", ".join(f"`{_escape(hid)}`" for hid in amendment["retired_hypothesis_ids"]))
                lines.extend(["- Basis: " + _escape(amendment["basis"]["kind"])])
            elif revision["decision"] is None:
                assessments = _latest_evaluations(state, revisions[:index + 1])
                lines.extend(["", "Original proposal; no observation or user decision is recorded."])
            else:
                assessments = _latest_evaluations(state, revisions[:index + 1])
        else:
            observation = revision["observation"]
            assessments = observation["evaluations"]
            lines.extend([
                "", "**Observation**", _quote(observation["finding"]),
                f"**Evidence kind:** `{_escape(observation['evidence_kind'])}`",
                f"**Evidence locator:** {_locator_markdown(observation['locator'])}",
                "", "**Observed conditions**",
            ])
            lines.extend(_conditions_markdown(observation["conditions"]))
            lines.extend(["", "**Limitations**"])
            lines.extend(_list_markdown(observation["limitations"]))
            if observation.get("evidence_files"):
                lines.extend(["", "**Explicit file evidence (SHA-256 at observation time)**"])
                lines.extend(
                    f"- `{_inline(item['path'])}` · `{item['sha256']}`"
                    for item in observation["evidence_files"]
                )
            if observation.get("metrics"):
                lines.extend(["", "**Calculated metrics (explicit metrics file)**"])
                for metric in observation["metrics"]:
                    definition = metric["definition"]
                    calculated = metric["result"]
                    impact = metric["decision_impact"]
                    metric_id = definition["id"]
                    value = calculated.get("value")
                    unit = calculated.get("unit") or definition.get("unit") or ""
                    reported = metric["reported"] if metric["reported"] is not None else "not reported"
                    value_text = "indeterminate" if value is None else str(value)
                    if unit:
                        value_text += " " + str(unit)
                    lines.append(
                        f"- **{_inline(metric_id)}**: calculated `{_inline(value_text)}`; "
                        f"reported `{_inline(reported)}` (`{_escape(metric['reported_status'])}`)"
                    )
                    criterion = impact.get("criterion")
                    if criterion is not None:
                        threshold_text = json.dumps(criterion["threshold"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                        lines.append(
                            f"  - Affected criterion: `{_inline(criterion['metric_id'])}` threshold "
                            f"`{_inline(threshold_text)}`; reported comparison: `{_escape(impact['reported_vs_computed'])}`"
                        )
                    if impact.get("across_revisions") is not None:
                        prior = impact["across_revisions"]
                        lines.append(
                            f"  - Revision comparison from {prior['from_revision']}: "
                            f"`{_escape(prior['decision_impact'])}`"
                        )
                    if metric["hypotheses"]:
                        lines.append("  - Affected hypotheses: " + ", ".join(f"`{_escape(hid)}`" for hid in metric["hypotheses"]))
                    if calculated.get("status") == "indeterminate" and calculated.get("reason"):
                        lines.append(f"  - Calculation status: indeterminate — {_inline(calculated['reason'])}")
                    if impact.get("review_recommended"):
                        lines.append("  - Review this observation and its recommendation against the recorded metric evidence.")
                    lines.append(f"  - Input: `{_inline(metric['input'])}` · SHA-256 `{calculated['input']['sha256']}`")
        if revision["decision"] is not None:
            decision = revision["decision"]
            lines.extend([
                "", "**Explicit user decision**",
                f"- `{_escape(decision['id'])}` selected **{_inline(decision['selection'])}**.",
                f"- Rationale: {_inline(decision['rationale'])}",
                f"- Confirmation locator: {_locator_markdown(decision['locator'])}",
                f"- Supersedes: {_escape(decision['supersedes']) if decision['supersedes'] else 'none'}",
            ])
        lines.extend(["", "**Hypothesis assessments**"])
        for hypothesis in state["hypotheses"]:
            if hypothesis["id"] not in assessments:
                continue
            evaluation = assessments[hypothesis["id"]]
            lines.append(f"- **{hypothesis['id']}** — `{evaluation['assessment']}`: {_inline(evaluation['rationale'])}")
    token = _state_token(state)
    lines.extend(["", STATE_BEGIN, token, STATE_END, MANAGED_END])
    return "\n".join(lines)


def _relative_path(ris, cfg: dict, study_id: str) -> str:
    return ris.research_path(cfg, "research/decisions/study-" + study_id + ".md")


def _path(ris, root: Path, cfg: dict, study_id: str) -> tuple[str, Path]:
    relative = _relative_path(ris, cfg, study_id)
    return relative, ris.inside(root, relative)


def _validate_frontmatter(ris, text: str, state: dict | None = None) -> dict:
    metadata = ris.frontmatter(text)
    required = {"ris_id", "project_id", "kind", "status", "created", "study_schema_version"}
    missing = required - set(metadata)
    if missing:
        raise ris.Error("Study frontmatter is missing fields: " + ", ".join(sorted(missing)))
    if (metadata["kind"] != "study" or metadata["status"] != "draft"
            or type(metadata["study_schema_version"]) is not int
            or metadata["study_schema_version"] != SCHEMA_VERSION):
        raise ris.Error("Expected this managed study's kind, status, and schema version")
    if not isinstance(metadata["ris_id"], str):
        raise ris.Error("Study frontmatter ris_id must be a UUID string")
    try:
        if str(UUID(metadata["ris_id"])) != metadata["ris_id"]:
            raise ValueError("non-canonical UUID")
    except ValueError as exc:
        raise ris.Error("Study frontmatter ris_id must be a canonical UUID string") from exc
    if not isinstance(metadata["project_id"], str) or not metadata["project_id"].strip():
        raise ris.Error("Study frontmatter project_id must be a non-empty string")
    _iso_timestamp(ris, metadata["created"], "study frontmatter created")
    if state is not None:
        if any(metadata[key] != state[state_key] for key, state_key in (
            ("ris_id", "ris_id"), ("project_id", "project_id"), ("created", "created_at")
        )):
            raise ris.Error("Study frontmatter identity does not match its state payload")
    return metadata


def _frontmatter(ris, state: dict) -> str:
    metadata = {
        "ris_id": state["ris_id"],
        "project_id": state["project_id"],
        "kind": "study",
        "status": "draft",
        "created": state["created_at"],
        "study_schema_version": SCHEMA_VERSION,
    }
    return "---\n" + ris.yaml_mapping(metadata) + "---\n\n"


def _extract_managed(ris, text: str) -> tuple[dict, str, str, str]:
    if text.count(MANAGED_BEGIN) != 1 or text.count(MANAGED_END) != 1:
        raise ris.Error("Study managed section is missing or duplicated; no changes were made")
    begin = text.index(MANAGED_BEGIN)
    end_marker = text.index(MANAGED_END)
    if end_marker < begin:
        raise ris.Error("Study managed section markers are out of order; no changes were made")
    end = end_marker + len(MANAGED_END)
    managed = text[begin:end]
    if managed.count(STATE_BEGIN) != 1 or managed.count(STATE_END) != 1:
        raise ris.Error("Study state payload is missing or duplicated; no changes were made")
    token_start = managed.index(STATE_BEGIN) + len(STATE_BEGIN)
    token_end = managed.index(STATE_END)
    if token_end < token_start:
        raise ris.Error("Study state payload markers are out of order; no changes were made")
    token = managed[token_start:token_end].strip()
    try:
        raw_state = base64.b64decode(token.encode("ascii"), altchars=b"-_", validate=True)
        state = json.loads(raw_state.decode("utf-8"))
    except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
        raise ris.Error("Study state payload is unreadable; no changes were made") from exc
    if not isinstance(state, dict) or not isinstance(state.get("id"), str) or not isinstance(state.get("project_id"), str):
        raise ris.Error("Study state payload is missing its identity")
    _validate_state(ris, state, state["id"], state["project_id"])
    _validate_frontmatter(ris, text, state)
    digest_matches = list(DIGEST_RE.finditer(managed))
    if len(digest_matches) != 1:
        raise ris.Error("Study managed digest is missing, malformed, or duplicated; no changes were made")
    digest_match = digest_matches[0]
    if int(digest_match.group(1)) != DIGEST_VERSION:
        raise ris.Error("Unsupported study managed digest version")
    digest_material = managed[:digest_match.start()] + managed[digest_match.end():]
    actual_digest = hashlib.sha256(digest_material.encode("utf-8")).hexdigest()
    if actual_digest != digest_match.group(2):
        raise ris.Error("Study generated content digest mismatch; preserve the original file and review the edit")
    return state, managed, text[:begin], text[end:]


def _decode_managed(ris, root: Path, cfg: dict, study_id: str, path: Path) -> tuple[dict, bytes, str, str]:
    try:
        original = path.read_bytes()
        text = original.decode("utf-8")
    except UnicodeError as exc:
        raise ris.Error("Study file is not valid UTF-8: " + str(path.relative_to(root))) from exc
    state, _, prefix, suffix = _extract_managed(ris, text)
    if state["id"] != study_id or state["project_id"] != cfg["project_id"]:
        raise ris.Error("Study identity or project identity mismatch")
    return state, original, prefix, suffix


def _metric_review_view(observations: list[dict]) -> list[dict]:
    latest = {}
    for observation in observations:
        for metric in observation.get("metrics", []):
            latest[metric["result"]["definition_sha256"]] = (observation, metric)
    review = []
    for observation, metric in latest.values():
        impact = metric["decision_impact"]
        if not impact["review_recommended"]:
            continue
        review.append({
            "metric_id": metric["definition"]["id"],
            "observation_id": observation["id"],
            "revision": observation["revision"],
            "reported": metric["reported"],
            "calculated": metric["result"]["value"],
            "reported_status": metric["reported_status"],
            "criterion": impact["criterion"],
            "affected_hypotheses": metric["hypotheses"],
            "decision_impact": impact,
        })
    return sorted(review, key=lambda item: (item["metric_id"], item["revision"]))


def _snapshot(state: dict, relative: str, revision: int | None = None) -> dict:
    selected_revision = state["revisions"][-1]["revision"] if revision is None else revision
    history = state["revisions"][:selected_revision]
    current = history[-1]
    known_hypotheses = _known_hypotheses_at(state, selected_revision)
    observations = []
    decisions = []
    for rev in history:
        if rev.get("decision") is not None:
            decision = dict(rev["decision"])
            decision.update({"revision": rev["revision"], "recorded_at": rev["recorded_at"]})
            decisions.append(decision)
        if rev.get("observation") is None:
            continue
        observation = dict(rev["observation"])
        observation.update({
            "revision": rev["revision"],
            "recorded_at": rev["recorded_at"],
            "recommendation": rev["recommendation"],
            "rationale": rev["rationale"],
            "next_action": rev["next_action"],
        })
        observations.append(observation)
    decision_revision, decision = _latest_decision(history)
    user_decision = None
    if decision is not None:
        user_decision = dict(decision)
        user_decision.update({"revision": decision_revision, "recorded_at": history[decision_revision - 1]["recorded_at"]})
    evaluations = _latest_evaluations(state, history)
    snapshot = {
        "id": state["id"],
        "revision": selected_revision,
        "project_id": state["project_id"],
        "path": relative,
        "goal": state["goal"],
        "criteria": list(state["criteria"]),
        "conditions": dict(state["conditions"]),
        "hypotheses": [dict(item) for item in known_hypotheses],
        "test": dict(state["test"]),
        "active_test": dict(current["active_test"]),
        "next_test": dict(current["next_test"]) if current["next_test"] is not None else None,
        "evaluations": {key: dict(value) for key, value in evaluations.items()},
        "observations": observations,
        "decisions": decisions,
        "user_decision": user_decision,
        "recommendation": current["recommendation"],
        "rationale": current["rationale"],
        "next_action": current["next_action"],
    }
    result_rule, result_rule_revision = _effective_result_rule_record(state, history)
    if result_rule is not None:
        snapshot["result_rule"] = result_rule
        snapshot["result_rule_revision"] = result_rule_revision
    amendments = _amendments_view(history)
    if amendments:
        active_ids = _active_hypothesis_ids_at(state, selected_revision)
        snapshot["active_hypothesis_ids"] = [item["id"] for item in known_hypotheses if item["id"] in active_ids]
        snapshot["retired_hypothesis_ids"] = [item["id"] for item in known_hypotheses if item["id"] not in active_ids]
        snapshot["amendments"] = amendments
        indistinguishable, prediction_warnings = _prediction_distinctions(
            current["next_test"], active_ids, known_hypotheses
        )
        snapshot["indistinguishable_groups"] = indistinguishable
        snapshot["prediction_warnings"] = prediction_warnings
    if any(observation.get("metrics") for observation in observations):
        snapshot["metric_review"] = _metric_review_view(observations)
    return snapshot


def read_study(ris, root: Path, study_id: str, revision: int | None = None) -> dict:
    """Read one current or historical study snapshot without writing files."""
    study_id = _safe_id(ris, study_id, "study ID")
    if revision is not None and (type(revision) is not int or revision < 1):
        raise ris.Error("revision must be a positive integer")
    cfg = ris.config(root)
    relative, path = _path(ris, root, cfg, study_id)
    if not path.is_file():
        raise ris.Error("Study does not exist: " + relative)
    state, _, _, _ = _decode_managed(ris, root, cfg, study_id, path)
    current_revision = state["revisions"][-1]["revision"]
    if revision is not None and revision > current_revision:
        raise ris.Error(f"Study revision {revision} does not exist; current revision is {current_revision}")
    ris.confirm_layout_current(root, cfg)
    return _snapshot(state, relative, revision)


def validate_note_edit(ris, before_text: str, after_text: str) -> bool:
    """Allow edits to the human-owned suffix, but keep managed study history immutable here.

    ``ris.py update`` should call this for a file identified as a managed study by its
    canonical ``decisions/study-<ID>.md`` path or its managed marker.
    """
    before, before_managed, before_prefix, _ = _extract_managed(ris, before_text)
    after, after_managed, after_prefix, _ = _extract_managed(ris, after_text)
    if before["id"] != after["id"] or before["project_id"] != after["project_id"] or before["ris_id"] != after["ris_id"]:
        raise ris.Error("A note edit must preserve study identity")
    if before_prefix != after_prefix:
        raise ris.Error("A note edit must preserve study frontmatter and identity; edit only human annotations")
    if before_managed != after_managed:
        raise ris.Error("Study generated content and revision history can be changed only through study observe, study decide, or study amend")
    return True


def start_study(ris, root: Path, study_id: str, payload: dict) -> dict:
    study_id = _safe_id(ris, study_id, "study ID")
    cfg = ris.config(root)
    with ris.project_lock(root):
        cfg = ris.config(root)
        relative, path = _path(ris, root, cfg, study_id)
        if path.exists():
            raise ris.Error("Study already exists; read it before continuing: " + relative)
        state = _start_payload(ris, study_id, cfg["project_id"], payload)
        _validate_state(ris, state, study_id, cfg["project_id"])
        path.parent.mkdir(parents=True, exist_ok=True)
        # Re-resolve after mkdir so a symlinked managed directory is rejected.
        relative, path = _path(ris, root, cfg, study_id)
        managed = _seal_managed(ris, state, relative)
        annotations = (
            "\n\n<!-- RIS:STUDY:ANNOTATIONS:BEGIN -->\n"
            "## Human annotations\n\n"
            "<!-- Add human-authored notes below. -->\n"
            "<!-- RIS:STUDY:ANNOTATIONS:END -->\n"
        )
        try:
            content = (_frontmatter(ris, state) + managed + annotations).encode("utf-8")
            ris.atomic_note_write(path, content)
        except FileExistsError as exc:
            raise ris.Error("Study was created concurrently; read it before continuing: " + relative) from exc
        ris.confirm_layout_current(root, cfg)
    result = _snapshot(state, relative)
    result["status"] = "created"
    return result


def _observation_record_by_id(state: dict, observation_id: str) -> tuple[int, dict] | tuple[None, None]:
    for revision in state["revisions"]:
        observation = revision.get("observation")
        if observation is not None and observation["id"] == observation_id:
            return revision["revision"], observation
    return None, None


def _validate_new_hypothesis_confirmation(ris, state: dict, observation: dict) -> None:
    assessment_matches = {"supported", "contradicted"}
    metrics = observation.get("metrics", [])
    for hypothesis in state["hypotheses"]:
        introduced_revision = hypothesis.get("introduced_revision")
        if introduced_revision is None:
            continue
        evaluation = observation["evaluations"].get(hypothesis["id"])
        if evaluation is None or evaluation["assessment"] not in assessment_matches:
            continue
        linked_metrics = [
            item for item in metrics if hypothesis["id"] in item.get("hypotheses", [])
        ]
        if linked_metrics:
            # When a metric explicitly claims to assess this hypothesis, only that
            # metric's pinned input can establish a fresh test for it. An unrelated
            # metric or an unassigned attachment cannot mask a reused linked input.
            inputs = [item["result"]["input"] for item in linked_metrics]
        else:
            # Preserve observation-level evidence semantics when no metric is assigned
            # to this hypothesis; exclude metrics explicitly assigned to other hypotheses.
            inputs = list(observation.get("evidence_files", []))
            inputs.extend(
                item["result"]["input"] for item in metrics if not item.get("hypotheses")
            )
        current_digests = {item["sha256"] for item in inputs if item.get("sha256")}
        current_paths = {item["path"] for item in inputs}
        basis = hypothesis["basis"]
        origin_locators = set()
        origin_digests = set()
        origin_paths = set()
        if basis["kind"] == "observation":
            origins = basis["observation_ids"]
            for origin_id in origins:
                _, origin = _observation_record_by_id(state, origin_id)
                if origin is None:
                    continue
                origin_locators.add(origin["locator"])
                for item in origin.get("evidence_files", []):
                    origin_paths.add(item["path"])
                    if item.get("sha256") is not None:
                        origin_digests.add(item["sha256"])
                for item in origin.get("metrics", []):
                    origin_paths.add(item["input"])
                    digest = (item.get("result", {}).get("input") or {}).get("sha256")
                    if digest is not None:
                        origin_digests.add(digest)
        elif basis["kind"] == "independent":
            origin_locators.add(basis["locator"])
        reused_digests = current_digests & origin_digests
        has_fresh_digest = bool(current_digests - origin_digests)
        reused_material_only = bool(reused_digests) and not has_fresh_digest
        if not current_digests and current_paths & origin_paths:
            reused_material_only = True
        # Fingerprinting an old locator for the first time, or editing its file in place, does
        # not establish a second test. A contextual citation can accompany a separately pinned input.
        distinct_followup = bool(origin_digests) and any(
            item.get("sha256") and item["sha256"] not in origin_digests and item["path"] not in origin_paths
            for item in inputs
        )
        reused_locator_only = observation["locator"] in origin_locators and not distinct_followup
        reused = reused_material_only or reused_locator_only
        if reused:
            raise ris.Error(
                f"Observation {observation['id']} reuses the motivating locator or evidence for new hypothesis "
                f"{hypothesis['id']}; record it as inconclusive/untested or provide later independent evidence"
            )


def _active_test_for_observation(state: dict) -> dict:
    previous = state["revisions"][-1]
    amendment = previous.get("amendment")
    if amendment is not None and "active_test" in amendment and len(state["revisions"]) >= 2:
        prior_plan = state["revisions"][-2]["active_test"]
        observations_before = any(item.get("observation") is not None for item in state["revisions"][:-1])
        if not observations_before and previous["active_test"] != prior_plan:
            return previous["active_test"]
    return previous["next_test"] or previous["active_test"]


def observe_study(ris, root: Path, study_id: str, expected_revision: int, payload: dict,
                  evidence_paths: list[str] | None = None,
                  metrics_file: str | None = None) -> dict:
    study_id = _safe_id(ris, study_id, "study ID")
    if type(expected_revision) is not int or expected_revision < 1:
        raise ris.Error("expected_revision must be a positive integer")
    cfg = ris.config(root)
    with ris.project_lock(root):
        cfg = ris.config(root)
        relative, path = _path(ris, root, cfg, study_id)
        if not path.is_file():
            raise ris.Error("Study does not exist: " + relative)
        state, before, prefix, suffix = _decode_managed(ris, root, cfg, study_id, path)
        evidence_files = _capture_evidence_files(ris, root, evidence_paths)
        if not isinstance(payload, dict):
            raise ris.Error("Study observation body must be a JSON object")
        observation_id = _safe_id(ris, payload.get("id"), "observation.id")
        found_revision_number, existing_observation = _observation_record_by_id(state, observation_id)
        current_revision = state["revisions"][-1]["revision"]
        if found_revision_number is None and expected_revision != current_revision:
            raise ris.Error(f"Study changed since revision {expected_revision}; current revision is {current_revision}. Reload before observing.")
        in_scope_ids = _active_hypothesis_ids_at(state, found_revision_number or current_revision)
        metric_requests = _metric_requests(ris, root, metrics_file, in_scope_ids) if metrics_file is not None else None
        if metric_requests and "finding" not in payload:
            # Keep a stable reference. The figures and verdicts have one source in the metric records.
            payload = {**payload, "finding": "이 관측의 수치와 기준별 판정은 등록된 지표 결과를 참조하세요."}
        observation = _observation_payload(ris, payload, in_scope_ids, evidence_files)
        if found_revision_number is not None:
            observation_record = {key: observation[key] for key in (
                "id", "finding", "locator", "evidence_kind", "conditions", "limitations", "evaluations"
            )}
            if "evidence_files" in observation:
                observation_record["evidence_files"] = observation["evidence_files"]
            if metric_requests is not None:
                observation_record["metrics"] = _calculate_observation_metrics(
                    ris, root, metric_requests, state["revisions"][:found_revision_number - 1], evidence_files
                )
            found_revision = state["revisions"][found_revision_number - 1]
            if existing_observation != observation_record or any(found_revision[key] != observation[key] for key in ("recommendation", "rationale", "next_action")) or found_revision["next_test"] != observation["next_test"]:
                raise ris.Error("Observation ID already exists with different content: " + observation_id)
            result = _snapshot(state, relative)
            result.update({"status": "already_recorded", "observation_id": observation_id, "recorded_revision": found_revision_number})
            return result
        if metric_requests is not None:
            observation["metrics"] = _calculate_observation_metrics(
                ris, root, metric_requests, state["revisions"], evidence_files
            )
        _validate_new_hypothesis_confirmation(ris, state, observation)
        observation_record = {key: observation[key] for key in (
            "id", "finding", "locator", "evidence_kind", "conditions", "limitations", "evaluations"
        )}
        if "evidence_files" in observation:
            observation_record["evidence_files"] = observation["evidence_files"]
        if "metrics" in observation:
            observation_record["metrics"] = observation["metrics"]
        new_revision = {
            "revision": current_revision + 1,
            "recorded_at": _timestamp(),
            "decision": None,
            "active_test": _active_test_for_observation(state),
            "next_test": observation["next_test"],
            "observation": observation_record,
            "recommendation": observation["recommendation"],
            "rationale": observation["rationale"],
            "next_action": observation["next_action"],
        }
        state["revisions"].append(new_revision)
        _validate_state(ris, state, study_id, cfg["project_id"])
        new_text = prefix + _seal_managed(ris, state, relative) + suffix
        ris.atomic_note_write(path, new_text.encode("utf-8"), expected=before)
        ris.confirm_layout_current(root, cfg)
    result = _snapshot(state, relative)
    result.update({"status": "recorded", "observation_id": observation["id"], "recorded_revision": new_revision["revision"]})
    return result


def _prediction_distinctions(next_test: dict | None, active_ids: set[str], hypotheses: list[dict]) -> tuple[list[list[str]], list[str]]:
    if next_test is None or "predictions" not in next_test:
        return [], []
    order = [item["id"] for item in hypotheses if item["id"] in active_ids]
    grouped = {}
    for hypothesis_id in order:
        prediction = next_test["predictions"].get(hypothesis_id)
        if prediction is None:
            continue
        normalized = " ".join(prediction.split()).casefold()
        grouped.setdefault(normalized, []).append(hypothesis_id)
    indistinguishable = [ids for ids in grouped.values() if len(ids) > 1]
    warnings = [
        "The proposed test gives matching predictions for " + ", ".join(ids) + "; it does not distinguish this group."
        for ids in indistinguishable
    ]
    return indistinguishable, warnings


def amend_study(ris, root: Path, study_id: str, expected_revision: int, payload: dict) -> dict:
    """Append a history-safe hypothesis, test, or result-rule amendment."""
    study_id = _safe_id(ris, study_id, "study ID")
    if type(expected_revision) is not int or expected_revision < 1:
        raise ris.Error("expected_revision must be a positive integer")
    cfg = ris.config(root)
    with ris.project_lock(root):
        cfg = ris.config(root)
        relative, path = _path(ris, root, cfg, study_id)
        if not path.is_file():
            raise ris.Error("Study does not exist: " + relative)
        state, before, prefix, suffix = _decode_managed(ris, root, cfg, study_id, path)
        if not isinstance(payload, dict):
            raise ris.Error("Study amendment body must be a JSON object")
        amendment_id = _safe_id(ris, payload.get("id"), "amendment.id")
        prior_revision = None
        prior_amendment = None
        for revision in state["revisions"]:
            event = revision.get("amendment")
            if event is not None and event["id"] == amendment_id:
                prior_revision = revision["revision"]
                prior_amendment = event
                break
        if prior_revision is not None:
            prior_active_ids = _active_hypothesis_ids_at(state, prior_revision - 1)
            prior_known_ids = {item["id"] for item in _known_hypotheses_at(state, prior_revision - 1)}
            prior_triggers = {
                item["observation"]["id"]: item["observation"]
                for item in state["revisions"][:prior_revision - 1]
                if item.get("observation") is not None
            }
            normalized = _amendment_payload(ris, payload, prior_active_ids, prior_known_ids, prior_triggers)
            if normalized != prior_amendment:
                raise ris.Error("Amendment ID already exists with different content: " + amendment_id)
            result = _snapshot(state, relative)
            result.update({"status": "already_recorded", "amendment_id": amendment_id, "recorded_revision": prior_revision})
            return result

        current_revision = state["revisions"][-1]["revision"]
        if expected_revision != current_revision:
            raise ris.Error(f"Study changed since revision {expected_revision}; current revision is {current_revision}. Reload before amending.")
        active_ids = _active_hypothesis_ids_at(state, current_revision)
        known_ids = {item["id"] for item in _known_hypotheses_at(state, current_revision)}
        triggering_observations = {
            item["observation"]["id"]: item["observation"]
            for item in state["revisions"]
            if item.get("observation") is not None
        }
        amendment = _amendment_payload(ris, payload, active_ids, known_ids, triggering_observations)
        new_revision_number = current_revision + 1
        for added in amendment["added_hypotheses"]:
            hypothesis = {
                "id": added["id"],
                "statement": added["statement"],
                "prediction": added["prediction"],
                "basis": added["basis"],
                "initial_assessment": {
                    "assessment": "untested",
                    "rationale": f"Introduced by amendment {amendment_id}; no later observation has evaluated it.",
                },
                "introduced_revision": new_revision_number,
            }
            if "parent_id" in added:
                hypothesis["parent_id"] = added["parent_id"]
            state["hypotheses"].append(hypothesis)

        previous = state["revisions"][-1]
        new_active_ids = (set(active_ids) - set(amendment["retired_hypothesis_ids"])) | set(amendment["added_hypothesis_ids"])
        active_test = amendment.get("active_test", previous["active_test"])
        if "active_test" in amendment and any(item.get("observation") is not None for item in state["revisions"]):
            if active_test != previous["active_test"]:
                raise ris.Error("Cannot rewrite an active test already tied to an observation; amend next_test instead")
        next_test = amendment.get("next_test", previous["next_test"])
        new_revision = {
            "revision": new_revision_number,
            "recorded_at": _timestamp(),
            "observation": None,
            "decision": None,
            "amendment": amendment,
            "active_test": active_test,
            "next_test": next_test,
            "recommendation": amendment.get("recommendation", previous["recommendation"]),
            "rationale": amendment["rationale"],
            "next_action": amendment.get("next_action", previous["next_action"]),
        }
        state["revisions"].append(new_revision)
        _validate_state(ris, state, study_id, cfg["project_id"])
        new_text = prefix + _seal_managed(ris, state, relative) + suffix
        ris.atomic_note_write(path, new_text.encode("utf-8"), expected=before)
        ris.confirm_layout_current(root, cfg)
    result = _snapshot(state, relative)
    event_view = {**amendment, "revision": new_revision_number, "recorded_at": new_revision["recorded_at"]}
    active_ids_after = _active_hypothesis_ids_at(state, new_revision_number)
    indistinguishable, warnings = _prediction_distinctions(
        new_revision["next_test"], active_ids_after, _known_hypotheses_at(state, new_revision_number)
    )
    result.update({
        "status": "recorded",
        "amendment_id": amendment_id,
        "recorded_revision": new_revision_number,
        "amendment": event_view,
        "indistinguishable_groups": indistinguishable,
        "warnings": warnings,
    })
    return result


def decide_study(ris, root: Path, study_id: str, expected_revision: int, payload: dict) -> dict:
    """Append an explicit user-reported selection as a decision event, never an observation."""
    study_id = _safe_id(ris, study_id, "study ID")
    if type(expected_revision) is not int or expected_revision < 1:
        raise ris.Error("expected_revision must be a positive integer")
    cfg = ris.config(root)
    with ris.project_lock(root):
        cfg = ris.config(root)
        relative, path = _path(ris, root, cfg, study_id)
        if not path.is_file():
            raise ris.Error("Study does not exist: " + relative)
        state, before, prefix, suffix = _decode_managed(ris, root, cfg, study_id, path)
        decision = _decision_payload(ris, payload)
        for revision in state["revisions"]:
            existing = revision.get("decision")
            if existing is None or existing["id"] != decision["id"]:
                continue
            if any(existing[key] != decision[key] for key in ("id", "selection", "rationale", "locator")):
                raise ris.Error("Decision ID already exists with different content: " + decision["id"])
            result = _snapshot(state, relative)
            result.update({"status": "already_recorded", "decision_id": decision["id"], "recorded_revision": revision["revision"]})
            return result
        current_revision = state["revisions"][-1]["revision"]
        if expected_revision != current_revision:
            raise ris.Error(f"Study changed since revision {expected_revision}; current revision is {current_revision}. Reload before deciding.")
        _, prior_decision = _latest_decision(state["revisions"])
        decision["supersedes"] = prior_decision["id"] if prior_decision else None
        previous = state["revisions"][-1]
        new_revision = {
            "revision": current_revision + 1,
            "recorded_at": _timestamp(),
            "observation": None,
            "decision": decision,
            "active_test": previous["active_test"],
            "next_test": previous["next_test"],
            "recommendation": previous["recommendation"],
            "rationale": previous["rationale"],
            "next_action": previous["next_action"],
        }
        state["revisions"].append(new_revision)
        _validate_state(ris, state, study_id, cfg["project_id"])
        new_text = prefix + _seal_managed(ris, state, relative) + suffix
        ris.atomic_note_write(path, new_text.encode("utf-8"), expected=before)
        ris.confirm_layout_current(root, cfg)
    result = _snapshot(state, relative)
    result.update({"status": "recorded", "decision_id": decision["id"], "recorded_revision": new_revision["revision"]})
    return result


def list_studies(ris, root: Path) -> dict:
    cfg = ris.config(root)
    directory_relative = ris.research_path(cfg, "research/decisions")
    directory = ris.inside(root, directory_relative)
    items = []
    if directory.exists():
        if not directory.is_dir():
            raise ris.Error("Study decisions path is not a directory: " + directory_relative)
        for path in sorted(directory.glob("study-*.md"), key=lambda item: item.name.casefold()):
            relative = str(path.relative_to(root))
            if path.is_symlink():
                raise ris.Error("Symlink is not a managed study path: " + relative)
            match = re.fullmatch(r"study-(.+)\.md", path.name)
            if not match or not SAFE_ID.fullmatch(match.group(1)):
                continue
            # Historical decision notes may share this filename convention. The managed
            # kind and schema marker, not the basename alone, identify this record type.
            try:
                metadata = ris.frontmatter(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError) as exc:
                raise ris.Error("Could not inspect study candidate: " + relative) from exc
            if metadata.get("kind") != "study" or metadata.get("study_schema_version") != SCHEMA_VERSION:
                continue
            snapshot = read_study(ris, root, match.group(1))
            items.append({key: snapshot[key] for key in (
                "id", "revision", "project_id", "path", "goal", "recommendation", "next_action"
            )})
    ris.confirm_layout_current(root, cfg)
    return {"project_id": cfg["project_id"], "count": len(items), "studies": items}


def _body_from_file(body_file: str) -> dict:
    text = sys.stdin.read() if body_file == "-" else Path(body_file).read_text(encoding="utf-8")
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Body file must contain valid JSON (line {exc.lineno}, column {exc.colno})") from exc
    if not isinstance(value, dict):
        raise ValueError("Body file must contain a JSON object")
    return value


def add_parser(sub):
    study = sub.add_parser("study", help="Create and resume append-only multi-session study records")
    actions = study.add_subparsers(dest="study_action", required=True)
    start = actions.add_parser("start", help="Create a study at revision 1")
    start.add_argument("id", help="Stable study ID (letters/digits followed by letters, digits, _ or -)")
    start.add_argument("--body-file", required=True, help="JSON input file, or - for stdin")
    show = actions.add_parser("show", help="Read the current or a historical study snapshot")
    show.add_argument("id")
    show.add_argument("--revision", type=int)
    observe = actions.add_parser("observe", help="Append an observation with revision compare-and-swap")
    observe.add_argument("id")
    observe.add_argument("--expected-revision", type=int, required=True)
    observe.add_argument("--body-file", required=True, help="JSON input file, or - for stdin")
    observe.add_argument(
        "--evidence-file", action="append", default=[], metavar="PROJECT_RELATIVE_PATH",
        help="Explicitly hash a regular project file; repeat for multiple files",
    )
    observe.add_argument("--metrics-file", help="JSON array of explicit metric definitions and project-relative data inputs")
    decide = actions.add_parser("decide", help="Record an explicit user-reported selection")
    decide.add_argument("id")
    decide.add_argument("--expected-revision", type=int, required=True)
    decide.add_argument("--body-file", required=True, help="JSON input file, or - for stdin")
    actions.add_parser("list", help="List studies in this project")
    amend = actions.add_parser("amend", help="Append a provenance-backed hypothesis or test revision")
    amend.add_argument("id")
    amend.add_argument("--expected-revision", type=int, required=True)
    amend.add_argument("--body-file", required=True, help="JSON input file, or - for stdin")
    return actions


def dispatch(ris, root: Path, args):
    if args.study_action == "start":
        return start_study(ris, root, args.id, _body_from_file(args.body_file))
    if args.study_action == "show":
        return read_study(ris, root, args.id, args.revision)
    if args.study_action == "observe":
        return observe_study(
            ris, root, args.id, args.expected_revision, _body_from_file(args.body_file),
            args.evidence_file, args.metrics_file,
        )
    if args.study_action == "decide":
        return decide_study(ris, root, args.id, args.expected_revision, _body_from_file(args.body_file))
    if args.study_action == "amend":
        return amend_study(ris, root, args.id, args.expected_revision, _body_from_file(args.body_file))
    if args.study_action == "list":
        return list_studies(ris, root)
    raise ris.Error("Unknown study command")

