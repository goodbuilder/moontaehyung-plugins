#!/usr/bin/env python3
"""Assess and explicitly save study-scoped evidence reuse."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import quote


UNKNOWN_VALUES = {
    "?", "unknown", "unresolved", "unspecified", "not specified", "not known",
    "not reported", "not recorded", "n/a", "na", "tbd", "미확인", "알 수 없음",
    "알수없음", "미상", "미기록", "미지정", "불명", "확인되지 않음",
}
SUPPORTED_EVIDENCE_KINDS = {"source", "publication", "derived"}
UNVERIFIED_EVIDENCE_KINDS = {"assumption", "unresolved"}
STUDY_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


def _error(ris, message: str):
    raise ris.Error(message)


def _validate_id(ris, value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value:
        _error(ris, f"{label} must be a non-empty single-line ID")
    return value.strip()


def _revision(ris, value: int | None, label: str, *, required: bool = False) -> int | None:
    if value is None:
        if required:
            _error(ris, f"{label} is required to pin a study snapshot")
        return None
    if type(value) is not int or value < 1:
        _error(ris, f"{label} must be a positive integer")
    return value


def _selected_source_root(ris, root: Path, source_project: str | Path | None) -> Path:
    if source_project is None:
        return root
    selected = Path(source_project).expanduser()
    if not selected.is_absolute():
        selected = root / selected
    selected = selected.resolve()
    if not selected.is_dir():
        _error(ris, "Selected source project must already exist as a directory")
    # Validate precisely the user-selected project. Never search sibling workspaces.
    ris.config(selected)
    return selected


def _load_study(ris, root: Path, study, study_id: str, revision: int | None, label: str) -> dict:
    value = study.read_study(ris, root, study_id, revision)
    if not isinstance(value, dict):
        _error(ris, f"{label} study reader returned an invalid snapshot")
    for field in ("id", "revision", "project_id", "path", "observations"):
        if field not in value:
            _error(ris, f"{label} study snapshot is missing {field}")
    if value["id"] != study_id:
        _error(ris, f"{label} study ID does not match the selected ID")
    if not isinstance(value["id"], str) or not STUDY_ID_RE.fullmatch(value["id"]):
        _error(ris, f"{label} study ID is invalid")
    if type(value["revision"]) is not int or value["revision"] < 1:
        _error(ris, f"{label} study revision is invalid")
    cfg = ris.config(root)
    if value["project_id"] != cfg["project_id"]:
        _error(ris, f"{label} study project identity mismatch")
    if not isinstance(value["observations"], list):
        _error(ris, f"{label} study observations are invalid")
    expected_path = ris.research_path(cfg, f"research/decisions/study-{study_id}.md")
    if value["path"] != expected_path:
        _error(ris, f"{label} study path is not its canonical managed location")
    _validate_managed_study_path(ris, root, cfg, value["path"], label)
    return value


def _validate_managed_study_path(ris, root: Path, cfg: dict, relative: str, label: str) -> Path:
    if not isinstance(relative, str) or not relative:
        _error(ris, f"{label} study has no canonical location")
    path = ris.inside(root, relative)
    research = ris.inside(root, cfg["research_dir"])
    if not path.is_relative_to(research) or path.suffix != ".md" or not path.is_file():
        _error(ris, f"{label} study location is not a managed research Markdown note")
    return path


def _research_relative_path(ris, cfg: dict, relative: str, label: str) -> str:
    try:
        return Path(relative).relative_to(cfg["research_dir"]).as_posix()
    except ValueError:
        _error(ris, f"{label} study location is outside its configured research root")


def _read_observation(ris, source: dict, observation_id: str) -> dict:
    matches = [item for item in source["observations"]
               if isinstance(item, dict) and item.get("id") == observation_id]
    if len(matches) != 1:
        if not matches:
            _error(ris, f"Observation {observation_id} is not present in source study revision {source['revision']}")
        _error(ris, f"Source study revision has duplicate observation ID {observation_id}")
    observation = matches[0]
    required = {"id", "finding", "locator", "limitations"}
    if not required.issubset(observation):
        _error(ris, "Selected source observation is missing required evidence fields")
    if not isinstance(observation["limitations"], list):
        _error(ris, "Selected source observation limitations are invalid")
    return observation


def _clean_conditions(value: dict, label: str) -> tuple[dict[str, str], list[str]]:
    """Keep known key/value pairs; surface malformed or missing maps as scope gaps."""
    clean: dict[str, str] = {}
    gaps = []
    if not isinstance(value, dict):
        return clean, [f"{label} condition map is missing or invalid"]
    for key, item in value.items():
        if not isinstance(key, str) or not key.strip() or not isinstance(item, str):
            gaps.append(f"{label} contains a condition without a known string key and value")
            continue
        clean[key] = item
    return clean, gaps


def _is_unknown(value: str) -> bool:
    return value.strip().casefold() in UNKNOWN_VALUES


def _compare_conditions(source: dict, observation: dict, target: dict) -> dict:
    source_study, source_study_gaps = _clean_conditions(source.get("conditions"), "Source study")
    source_observation, source_observation_gaps = _clean_conditions(observation.get("conditions"), "Source observation")
    target_conditions, target_gaps = _clean_conditions(target.get("conditions"), "Target study")

    conflicts = []
    for key in sorted(source_study.keys() & source_observation.keys()):
        if source_study[key] != source_observation[key]:
            conflicts.append({"condition": key, "study_value": source_study[key],
                              "observation_value": source_observation[key]})
    # Study-level conditions describe the planned study scope. They cannot stand in for
    # conditions explicitly recorded on an observation. Compare the actual observation map
    # to the target, and separately require every planned condition to be observed.
    source_scope = source_observation
    planned_not_observed = sorted(source_study.keys() - source_observation.keys())
    missing = sorted(source_scope.keys() - target_conditions.keys())
    extra = sorted(target_conditions.keys() - source_scope.keys())
    changed = [{"condition": key, "source": source_scope[key], "target": target_conditions[key]}
               for key in sorted(source_scope.keys() & target_conditions.keys())
               if source_scope[key] != target_conditions[key]]
    unknown_source = ([{"condition": key, "value": value, "level": "observation"}
                      for key, value in sorted(source_observation.items()) if _is_unknown(value)]
                      + [{"condition": key, "value": value, "level": "study"}
                         for key, value in sorted(source_study.items()) if _is_unknown(value)])
    unknown_target = [{"condition": key, "value": value}
                      for key, value in sorted(target_conditions.items()) if _is_unknown(value)]
    if not source_scope:
        source_study_gaps.append("No known source scope conditions are recorded")
    if not target_conditions:
        target_gaps.append("No known target scope conditions are recorded")
    exact_match = (bool(source_scope) and bool(target_conditions)
                   and not source_study_gaps and not source_observation_gaps and not target_gaps
                   and not conflicts and not planned_not_observed and not missing and not extra and not changed
                   and not unknown_source and not unknown_target)
    return {
        "source_study_conditions": source_study,
        "source_observation_conditions": source_observation,
        "source_scope_conditions": source_scope,
        "target_conditions": target_conditions,
        "source_study_gaps": source_study_gaps,
        "source_observation_gaps": source_observation_gaps,
        "target_gaps": target_gaps,
        "conflicts": conflicts,
        "planned_not_observed": planned_not_observed,
        "missing_in_target": missing,
        "extra_in_target": extra,
        "changed_values": changed,
        "unknown_source": unknown_source,
        "unknown_target": unknown_target,
        "exact_match": exact_match,
    }


def _target_read(ris, root: Path, study, target_id: str,
                 target_revision: int | None) -> tuple[dict, dict, bool]:
    current = _load_study(ris, root, study, target_id, None, "Target")
    selected = (current if target_revision is None or target_revision == current["revision"]
                else _load_study(ris, root, study, target_id, target_revision, "Target"))
    return selected, current, selected["revision"] == current["revision"]


def _canonical_digest(value: object) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _metadata_digest(metadata: dict) -> str:
    volatile = {"created", "source_freshness_checked_at", "knowledge_metadata_sha256"}
    stable = {key: value for key, value in metadata.items() if key not in volatile}
    return _canonical_digest(stable)


def _target_context(target: dict) -> dict:
    fields = (
        "goal", "criteria", "conditions", "hypotheses", "evaluations", "test",
        "active_test", "next_test", "observations", "recommendation", "user_decision",
        "rationale", "next_action", "decisions",
    )
    return {field: target[field] for field in fields if field in target}


def _verify_attached_evidence(ris, source_root: Path, observation: dict,
                             requested: bool) -> dict:
    """Hash only file paths explicitly attached to the pinned observation."""
    variant = "verify_attached_files" if requested else "scope_only"
    attached = observation.get("evidence_files", [])
    if attached is None:
        attached = []
    if not isinstance(attached, list):
        return {
            "verification_variant": variant,
            "evidence_status": "missing",
            "evidence_checks": [],
            "recheck_reasons": ["Attached evidence file list is malformed"],
            "review_rationale": ["Evidence file references need review."],
        }
    if not requested:
        return {
            "verification_variant": variant,
            "evidence_status": "not_checked",
            "evidence_checks": [],
            "recheck_reasons": [],
            "review_rationale": ["Evidence bytes were not checked; review required."],
        }
    if not attached:
        return {
            "verification_variant": variant,
            "evidence_status": "unverified",
            "evidence_checks": [],
            "recheck_reasons": [],
            "review_rationale": ["No attached evidence files were available to check; review required."],
        }

    checks = []
    recheck_reasons = []
    for item in attached:
        if not isinstance(item, dict):
            checks.append({"status": "missing", "reason": "Invalid attached evidence-file entry"})
            recheck_reasons.append("An attached evidence-file entry is invalid")
            continue
        relative = item.get("path")
        expected = item.get("sha256")
        if (not isinstance(relative, str) or not relative.strip()
                or Path(relative).is_absolute() or not isinstance(expected, str)
                or not re.fullmatch(r"[0-9a-f]{64}", expected)):
            checks.append({"path": relative, "expected_sha256": expected, "status": "missing",
                           "reason": "Attached evidence file needs a valid project-relative path and SHA-256"})
            recheck_reasons.append(f"Attached evidence file reference is invalid: {relative!r}")
            continue
        try:
            actual = ris.study_evidence_hash(source_root, relative)
        except (ris.Error, OSError, ValueError) as exc:
            checks.append({"path": relative, "expected_sha256": expected, "actual_sha256": None,
                           "status": "missing", "reason": str(exc)})
            recheck_reasons.append(f"Attached evidence file is missing or unreadable: {relative}")
            continue
        actual_digest = actual.get("sha256") if isinstance(actual, dict) else None
        checked_path = actual.get("path", relative) if isinstance(actual, dict) else relative
        if not isinstance(actual_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", actual_digest):
            checks.append({"path": relative, "expected_sha256": expected, "actual_sha256": actual_digest,
                           "status": "missing", "reason": "Evidence hash helper returned an invalid digest"})
            recheck_reasons.append(f"Could not verify attached evidence file: {relative}")
        elif actual_digest == expected:
            checks.append({"path": checked_path, "expected_sha256": expected,
                           "actual_sha256": actual_digest, "status": "bytes_match"})
        else:
            checks.append({"path": checked_path, "expected_sha256": expected,
                           "actual_sha256": actual_digest, "status": "changed"})
            recheck_reasons.append(f"Attached evidence file changed since observation: {relative}")

    if recheck_reasons:
        statuses = {item["status"] for item in checks}
        evidence_status = "recheck" if len(statuses & {"missing", "changed"}) > 1 else (
            "missing" if "missing" in statuses else "changed")
        review_rationale = ["Attached evidence files did not all match their recorded digests; review required."]
    else:
        evidence_status = "bytes_match"
        review_rationale = ["Attached evidence bytes match their recorded digests; scientific review is still required."]
    return {
        "verification_variant": variant,
        "evidence_status": evidence_status,
        "evidence_checks": checks,
        "recheck_reasons": recheck_reasons,
        "review_rationale": review_rationale,
    }


def _metric_helper(ris):
    """Load the bundled numeric metric helper without searching outside this skill."""
    companion = getattr(ris, "companion", None)
    if not callable(companion):
        raise ris.Error("Numeric metric replay helper is unavailable")
    return companion("ris_metrics")


def _metric_identifier(metric: dict, index: int) -> str:
    result = metric.get("result")
    definition = metric.get("definition")
    for value in (
            result.get("metric_id") if isinstance(result, dict) else None,
            definition.get("id") if isinstance(definition, dict) else None,
            definition.get("metric_id") if isinstance(definition, dict) else None):
        if isinstance(value, str) and value.strip():
            return value.strip()
    return f"metric-{index}"


def _metric_input_path(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value:
        return None
    normalized = path.as_posix()
    if normalized in {"", "."} or normalized != value:
        return None
    return normalized


def _indeterminate_metric(reason: str, *, definition: dict | None = None,
                          input_path: str | None = None) -> dict:
    result = {
        "status": "indeterminate",
        "reason": reason,
        "value": None,
        "numerator": None,
        "denominator": None,
        "unit": None,
        "threshold_met": None,
        "input": {"path": input_path, "sha256": None},
    }
    if isinstance(definition, dict):
        result["definition"] = definition
    return result


def _metric_input_digest(input_path: str | None, current_result: dict) -> str | None:
    current_input = current_result.get("input")
    if (not isinstance(current_input, dict)
            or current_input.get("path") != input_path):
        return None
    current_digest = (current_input.get("sha256")
                      if isinstance(current_input, dict) else None)
    if isinstance(current_digest, str) and re.fullmatch(r"[0-9a-f]{64}", current_digest):
        return current_digest
    return None


def _replay_registered_metrics(ris, source_root: Path, observation: dict) -> dict:
    """Recalculate explicitly captured observation metrics and fingerprint their inputs."""
    if "metrics" not in observation:
        return {"metric_replays": [], "evidence_checks": [], "recheck_reasons": []}
    metrics = observation.get("metrics")
    if not isinstance(metrics, list):
        result = {
            "metric_id": "metrics",
            "reported": None,
            "reported_status": "indeterminate",
            "result": _indeterminate_metric("Registered observation metrics are malformed"),
            "decision_impact": {"review_recommended": True},
            "input_status": "unverified",
            "calculation_status": "indeterminate",
            "replay_comparison": {"decision_impact": "indeterminate"},
        }
        return {
            "metric_replays": [result],
            "evidence_checks": [],
            "recheck_reasons": ["Registered observation metrics are malformed; review required."],
        }
    if not metrics:
        return {"metric_replays": [], "evidence_checks": [], "recheck_reasons": []}

    metric_helper = _metric_helper(ris)
    replays = []
    evidence_checks = []
    recheck_reasons = []
    for index, metric in enumerate(metrics, 1):
        if not isinstance(metric, dict):
            metric = {}
        metric_id = _metric_identifier(metric, index)
        raw_definition = metric.get("definition")
        definition = raw_definition if isinstance(raw_definition, dict) else None
        input_path = _metric_input_path(metric.get("input"))
        reported = metric.get("reported")
        invalid_reported = False
        if reported is not None and not isinstance(reported, str):
            reported = None
            invalid_reported = True
        previous_result = metric.get("result")
        if not isinstance(previous_result, dict):
            previous_result = None
        reason = None
        if definition is None or input_path is None:
            reason = "Registered metric definition or input path is invalid"
        try:
            if reason:
                raise ris.Error(reason)
            # calculate owns the bounded read and returns that exact snapshot's digest.
            # Do not pre-validate the definition or reread the input before/after it.
            current_result = metric_helper.calculate(ris, source_root, definition, input_path)
            if not isinstance(current_result, dict):
                current_result = _indeterminate_metric(
                    "Metric calculator returned an invalid result", definition=definition,
                    input_path=input_path)
        except (ris.Error, OSError, ValueError, TypeError, KeyError) as exc:
            reason = str(exc) or "Metric replay could not be completed"
            current_result = _indeterminate_metric(reason, definition=definition,
                                                   input_path=input_path)
        normalize = getattr(metric_helper, "normalize_definition", None)
        if callable(normalize) and isinstance(raw_definition, dict):
            try:
                definition = normalize(ris, raw_definition)
            except (ris.Error, OSError, ValueError, TypeError, KeyError):
                # Preserve malformed registered content as review context; calculate's
                # indeterminate result still carries any digest from its bounded snapshot.
                definition = raw_definition
        elif isinstance(current_result.get("definition"), dict):
            definition = current_result["definition"]

        # Keep the current byte check independent from the reported value and arithmetic.
        actual_digest = _metric_input_digest(input_path, current_result)
        previous_input = previous_result.get("input") if previous_result else None
        expected_digest = previous_input.get("sha256") if isinstance(previous_input, dict) else None
        if actual_digest is None:
            current_reason = current_result.get("reason")
            input_status = "missing" if current_reason == "input file does not exist" else "unverified"
        elif not isinstance(expected_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_digest):
            input_status = "unverified"
        elif actual_digest == expected_digest:
            input_status = "bytes_match"
        else:
            input_status = "changed"
        evidence_checks.append({
            "path": input_path or metric.get("input"),
            "expected_sha256": expected_digest,
            "actual_sha256": actual_digest,
            "status": input_status,
            "kind": "metric_input",
            "metric_id": metric_id,
            "reason": reason or current_result.get("reason"),
        })

        if input_status in {"changed", "missing", "unverified"}:
            label = {"changed": "changed since the observation was captured",
                     "missing": "is missing or unreadable",
                     "unverified": "has no captured input digest"}[input_status]
            detail = current_result.get("reason")
            suffix = f" ({detail})" if isinstance(detail, str) and detail else ""
            recheck_reasons.append(f"Metric input for {metric_id} {label}{suffix}; review required.")

        try:
            if invalid_reported:
                claim_comparison = {"reported_status": "indeterminate",
                                    "decision_impact": "indeterminate",
                                    "reason": "Registered reported value is invalid"}
            else:
                claim_comparison = metric_helper.compare_reported(definition, current_result, reported)
            if not isinstance(claim_comparison, dict):
                claim_comparison = {"reported_status": "indeterminate",
                                    "decision_impact": "indeterminate",
                                    "reason": "Reported-value comparison returned an invalid result"}
        except (ris.Error, OSError, ValueError, TypeError, KeyError) as exc:
            claim_comparison = {"reported_status": "indeterminate",
                                "decision_impact": "indeterminate", "reason": str(exc)}
        reported_status = claim_comparison.get("reported_status", "indeterminate")

        if previous_result is None or previous_result.get("status") != "ok" or current_result.get("status") != "ok":
            calculation_status = "indeterminate"
            value_status = "indeterminate"
        else:
            calculation_fields = ("definition_sha256", "value", "numerator", "denominator",
                                  "unit", "threshold_met")
            calculation_status = ("match" if all(previous_result.get(field) == current_result.get(field)
                                                  for field in calculation_fields) else "mismatch")
            if (previous_result.get("definition_sha256") != current_result.get("definition_sha256")
                    or previous_result.get("unit") != current_result.get("unit")):
                value_status = "indeterminate"
            else:
                value_status = ("match" if previous_result.get("value") == current_result.get("value")
                                else "mismatch")

        try:
            if previous_result is None:
                comparison = {"decision_impact": "indeterminate",
                              "reason": "No captured prior calculation is available"}
            else:
                comparison = metric_helper.compare_results(previous_result, current_result)
                if not isinstance(comparison, dict):
                    comparison = {"decision_impact": "indeterminate",
                                  "reason": "Metric comparison returned an invalid result"}
        except (ris.Error, OSError, ValueError, TypeError, KeyError) as exc:
            comparison = {"decision_impact": "indeterminate", "reason": str(exc)}

        threshold = definition.get("threshold") if isinstance(definition, dict) else None
        threshold_context = (f"threshold {threshold!r}" if threshold is not None
                             else "reported metric value; no threshold is registered")
        impact = {
            "registered": metric.get("decision_impact"),
            "replay": comparison.get("decision_impact"),
            "reported_vs_replay": ("not_reported" if reported_status == "not_reported"
                                   else claim_comparison.get("decision_impact")),
            "affected_threshold": threshold,
        }
        if reported_status in {"mismatch", "indeterminate"}:
            if reported_status == "mismatch":
                recheck_reasons.append(
                    f"Metric {metric_id} reported {reported!r} but replayed as {current_result.get('value')!r}; review the affected {threshold_context}.")
            else:
                recheck_reasons.append(
                    f"Metric {metric_id} claim could not be confirmed ({reported_status}); review the affected {threshold_context}.")
        if calculation_status in {"mismatch", "indeterminate"}:
            recheck_reasons.append(
                f"Metric {metric_id} calculation replay is {calculation_status}; review the affected {threshold_context}.")
        impact_changed = comparison.get("decision_impact")
        if impact_changed == "threshold_crossed":
            recheck_reasons.append(
                f"Metric {metric_id} replay crossed the affected threshold {threshold!r}; review required.")
        elif impact_changed == "indeterminate":
            recheck_reasons.append(
                f"Metric {metric_id} threshold impact is indeterminate for {threshold!r}; review required.")
        if claim_comparison.get("decision_impact") == "threshold_crossed":
            recheck_reasons.append(
                f"Metric {metric_id} reported value and replay fall on opposite sides of threshold {threshold!r}; review required.")

        replays.append({
            "metric_id": metric_id,
            "definition": definition,
            "input": input_path or metric.get("input"),
            "reported": reported,
            "reported_status": reported_status,
            "registered_reported_status": metric.get("reported_status"),
            "result": current_result,
            "previous_result": previous_result,
            "calculation_status": calculation_status,
            "value_status": value_status,
            "input_status": input_status,
            "decision_impact": impact,
            "replay_comparison": comparison,
            "reported_comparison": claim_comparison,
        })

    return {"metric_replays": replays,
            "evidence_checks": evidence_checks,
            "recheck_reasons": recheck_reasons}


def _combine_evidence_checks(evidence: dict, metric_checks: list[dict]) -> dict:
    if not metric_checks:
        return evidence
    checks = [*evidence.get("evidence_checks", []), *metric_checks]
    bad = {check.get("status") for check in checks} & {"missing", "changed"}
    if bad:
        status = "recheck" if len(bad) > 1 else ("missing" if "missing" in bad else "changed")
    elif any(check.get("status") == "unverified" for check in checks):
        status = "unverified"
    else:
        status = "bytes_match"
    evidence["evidence_checks"] = checks
    evidence["evidence_status"] = status
    if bad:
        evidence["review_rationale"] = [
            "Attached evidence bytes or explicitly registered metric inputs changed or could not be read; review required."]
    elif status == "unverified":
        evidence["review_rationale"] = [
            "At least one metric input has no captured digest; review required."]
    else:
        evidence["review_rationale"] = [
            "Attached evidence and metric input bytes match their captured digests; scientific review is still required."]
    return evidence


def _assessment(ris, source: dict, observation: dict, target: dict,
                source_is_current: bool, current_source_revision: int,
                target_is_current: bool, current_target_revision: int,
                evidence: dict, metric_replays: list[dict] | None = None) -> dict:
    conditions = _compare_conditions(source, observation, target)
    reasons: list[str] = []
    if not conditions["exact_match"]:
        if conditions["missing_in_target"]:
            reasons.append("Target is missing source scope condition(s): " + ", ".join(conditions["missing_in_target"]))
        if conditions["extra_in_target"]:
            reasons.append("Target has condition(s) outside the source evidence scope: " + ", ".join(conditions["extra_in_target"]))
        if conditions["changed_values"]:
            reasons.extend(f"Condition {item['condition']!r} changed from {item['source']!r} to {item['target']!r}"
                           for item in conditions["changed_values"])
        if conditions["planned_not_observed"]:
            reasons.append("Source observation does not record planned condition(s): " + ", ".join(conditions["planned_not_observed"]))
        if conditions["unknown_source"]:
            reasons.extend(f"Source condition {item['condition']!r} is explicitly unknown ({item['value']!r})"
                           for item in conditions["unknown_source"])
        if conditions["unknown_target"]:
            reasons.extend(f"Target condition {item['condition']!r} is explicitly unknown ({item['value']!r})"
                           for item in conditions["unknown_target"])
        reasons.extend(conditions["conflicts"] and [
            f"Source study and observation disagree on condition {item['condition']!r}"
            for item in conditions["conflicts"]] or [])
        reasons.extend(conditions["source_study_gaps"])
        reasons.extend(conditions["source_observation_gaps"])
        reasons.extend(conditions["target_gaps"])

    evidence_kind = observation.get("evidence_kind")
    if evidence_kind in UNVERIFIED_EVIDENCE_KINDS:
        reasons.append(f"Evidence kind {evidence_kind!r} is not verified support")
    elif evidence_kind not in SUPPORTED_EVIDENCE_KINDS:
        reasons.append(f"Evidence kind {evidence_kind!r} is missing or unsupported")
    if not source_is_current:
        reasons.append(f"Pinned source revision {source['revision']} is historical; current source revision is {current_source_revision}")
    if not target_is_current:
        reasons.append(f"Target snapshot revision {target['revision']} is stale; current revision is {current_target_revision}")
    reasons.extend(evidence["recheck_reasons"])

    requires_recheck = bool(reasons)
    if not requires_recheck:
        reasons.append("Recorded source and target condition maps match exactly")
    limitations = [str(item) for item in observation.get("limitations", [])]
    if evidence_kind == "publication":
        limitations.append("Publication evidence still requires review of the cited publication and its scope.")
    if evidence_kind == "derived":
        limitations.append("Derived evidence remains an inference and may require recalculation for the target.")
    if evidence_kind in UNVERIFIED_EVIDENCE_KINDS:
        limitations.append("Assumption or unresolved evidence is not verified support.")
    limitations.extend([
        "Applicability reflects recorded scope conditions only; it does not establish scientific transfer.",
        "Recommendations and candidate choices are not promoted by this assessment.",
    ])
    has_metric_inputs = any(check.get("kind") == "metric_input" for check in evidence["evidence_checks"])
    if evidence["evidence_status"] == "bytes_match":
        if has_metric_inputs:
            limitations.append("Attached evidence and explicitly registered metric-input bytes matched their captured digests; calculation validity and scientific transfer still require human review.")
        else:
            limitations.append("Attached bytes matched the recorded digests; scientific validity and transfer still require human review.")
    elif evidence["evidence_status"] in {"changed", "missing", "recheck"}:
        if has_metric_inputs:
            limitations.append("At least one attached evidence file or registered metric input could not be confirmed against its captured digest.")
        else:
            limitations.append("At least one attached evidence file could not be confirmed against its recorded digest.")
    if metric_replays:
        limitations.append("Numeric reproduction is limited to the registered definition and selected input snapshot; it does not update a research decision or establish scientific transfer.")
    assessment = {
        "status": "recheck" if requires_recheck else "scope_match",
        "assessment_scope": "recorded_conditions",
        "evidence_status": evidence["evidence_status"],
        "review_required": True,
        "evidence_verification_variant": evidence["verification_variant"],
        "evidence_checks": evidence["evidence_checks"],
        "rationale": [*reasons, *evidence["review_rationale"]],
        "condition_comparison": conditions,
        "limitations": list(dict.fromkeys(limitations)),
        "target_is_current": target_is_current,
        "current_target_revision": current_target_revision,
        "source_is_current": source_is_current,
        "current_source_revision": current_source_revision,
        "transfer_claimed": False,
        "recommendations_promoted": False,
    }
    if metric_replays:
        assessment["metric_replays"] = metric_replays
        assessment["numeric_reproduction_scope"] = "explicitly_registered_observation_metrics"
    return assessment


def _prepare(ris, root: Path, study, source_id: str, revision: int,
             observation_id: str, target_id: str, *,
             source_project: str | Path | None = None,
             target_revision: int | None = None,
             verify_evidence: bool = False) -> dict:
    source_id = _validate_id(ris, source_id, "Source study ID")
    target_id = _validate_id(ris, target_id, "Target study ID")
    observation_id = _validate_id(ris, observation_id, "Observation ID")
    revision = _revision(ris, revision, "--revision", required=True)
    target_revision = _revision(ris, target_revision, "--target-revision")
    if type(verify_evidence) is not bool:
        _error(ris, "verify_evidence must be a boolean")
    source_root = _selected_source_root(ris, root, source_project)
    source = _load_study(ris, source_root, study, source_id, revision, "Source")
    if source["revision"] != revision:
        _error(ris, "Source study reader did not return the requested pinned revision")
    observation = _read_observation(ris, source, observation_id)
    evidence = _verify_attached_evidence(ris, source_root, observation, verify_evidence)
    metric_replay = {"metric_replays": [], "evidence_checks": [], "recheck_reasons": []}
    if verify_evidence and "metrics" in observation:
        metric_replay = _replay_registered_metrics(ris, source_root, observation)
        evidence = _combine_evidence_checks(evidence, metric_replay["evidence_checks"])
        evidence["recheck_reasons"].extend(metric_replay["recheck_reasons"])
    source_current = _load_study(ris, source_root, study, source_id, None, "Current source")
    source_is_current = source["revision"] == source_current["revision"]
    target, current_target, target_is_current = _target_read(ris, root, study, target_id, target_revision)
    assessment = _assessment(ris, source, observation, target, source_is_current,
                             source_current["revision"], target_is_current, current_target["revision"],
                             evidence, metric_replay["metric_replays"])
    observation_digest = _canonical_digest(observation)
    source_cfg = ris.config(source_root)
    target_cfg = ris.config(root)
    return {
        "assessment": assessment,
        "source": {
            "project_id": source["project_id"],
            "project_path": str(source_root),
            "study_id": source["id"],
            "revision": source["revision"],
            "current_revision": source_current["revision"],
            "is_current": source_is_current,
            "freshness_checked_at": datetime.now(timezone.utc).isoformat(),
            "path": source["path"],
            "research_relative_path": _research_relative_path(ris, source_cfg, source["path"], "Source"),
            "observation_id": observation["id"],
            "observation_digest": observation_digest,
            "observation": observation,
            "study_conditions": source.get("conditions", {}),
            "observation_locator": observation["locator"],
        },
        "target": {
            "project_id": current_target["project_id"],
            "study_id": current_target["id"],
            "revision": target["revision"],
            "current_revision": current_target["revision"],
            "is_current": target_is_current,
            "path": target["path"],
            "research_relative_path": _research_relative_path(ris, target_cfg, target["path"], "Target"),
            "context": _target_context(target),
        },
        "source_root": source_root,
        "target_snapshot": target,
    }


def assess_knowledge(ris, root: Path, study, source_id: str, revision: int,
                     observation_id: str, target_id: str, *,
                     source_project: str | Path | None = None,
                     target_revision: int | None = None,
                     verify_evidence: bool = False) -> dict:
    """Read two selected study snapshots and assess recorded scope without saving anything."""
    prepared = _prepare(ris, root, study, source_id, revision, observation_id, target_id,
                        source_project=source_project, target_revision=target_revision,
                        verify_evidence=verify_evidence)
    return {
        "status": prepared["assessment"]["status"],
        "assessment_scope": prepared["assessment"]["assessment_scope"],
        "evidence_status": prepared["assessment"]["evidence_status"],
        "review_required": True,
        "assessment": prepared["assessment"],
        "source": prepared["source"],
        "target": prepared["target"],
    }


def _quote(text: object) -> str:
    value = "" if text is None else str(text)
    return "\n".join("> " + line for line in value.splitlines()) if value else "> *(empty)*"


def _knowledge_note(ris, root: Path, prepared: dict, identity_digest: str,
                    payload_digest: str) -> str:
    source = prepared["source"]
    target = prepared["target"]
    observation = source["observation"]
    assessment = prepared["assessment"]
    cfg = ris.config(root)
    same_project_source = (source["project_id"] == target["project_id"]
                           and Path(source["project_path"]).resolve() == root.resolve())
    record_id = "KN-" + identity_digest[:32]
    created = datetime.now(timezone.utc).isoformat()
    source_link = Path("../") / Path(source["research_relative_path"]) if same_project_source else None
    target_link = Path("../") / Path(target["research_relative_path"])

    title = f"Evidence reuse {source['study_id']} {source['observation_id']} → {target['study_id']}"
    sections = [
        f"# {title}",
        "## Scope assessment",
        f"Assessment scope: `{assessment['assessment_scope']}`",
        f"Status: **{assessment['status']}**",
        f"Evidence status: **{assessment['evidence_status']}**",
        "Review required: **YES**",
        "",
        "Rationale:",
        *[_quote(reason) for reason in assessment["rationale"]],
        "",
        "This record assesses recorded condition overlap only. It does not establish scientific transfer or promote recommendations.",
        "",
        "## Target context",
        f"Target study: {target['study_id']} (revision {target['revision']})",
    ]
    sections.append(f"Target study note: [open](<{target_link.as_posix()}>)")
    sections.extend([
        "Target goal:", _quote(target["context"].get("goal", "Not recorded")),
        "", "Target criteria:", _quote(json.dumps(target["context"].get("criteria", []), ensure_ascii=False)),
        "", "Target conditions:", _quote(json.dumps(assessment["condition_comparison"]["target_conditions"], ensure_ascii=False, sort_keys=True)),
        "", "Target context snapshot (preserved):",
        _quote(json.dumps(target["context"], ensure_ascii=False, sort_keys=True, indent=2)),
        "", "## Source observation",
        f"Source study: {source['study_id']} (revision {source['revision']}); observation {source['observation_id']}",
    ])
    if source_link is not None:
        sections.append(f"Source study note: [open](<{source_link.as_posix()}>)")
    else:
        sections.append("Source project path:")
        sections.append(_quote(f"{source['project_path']} ({source['project_id']})"))
        external_source_note = Path(source["project_path"]) / source["path"]
        external_link = quote(external_source_note.as_posix(), safe="/:")
        sections.append(f"Source study note: [open](<{external_link}>)")
        sections.append(f"Source study path within research: {source['research_relative_path']}")
    sections.append(f"Pinned revision: {source['revision']}; current revision when checked: {source['current_revision']}")
    sections.extend([
        f"Evidence kind: {observation.get('evidence_kind', 'unknown')}",
        f"Observation digest (SHA-256): {source['observation_digest']}",
        f"Locator: {_quote(observation['locator'])}",
        "Finding:", _quote(observation["finding"]),
        "", "Observation record (all fields preserved):",
        _quote(json.dumps(observation, ensure_ascii=False, sort_keys=True, indent=2)),
    ])
    metric_replays = assessment.get("metric_replays")
    if isinstance(metric_replays, list) and metric_replays:
        sections.extend([
            "", "## Numeric reproduction",
            "Registered observation metrics were recalculated from the explicitly referenced source-project inputs. These results are review evidence only; they do not change the source study or its research decision.",
            _quote(json.dumps(metric_replays, ensure_ascii=False, sort_keys=True, indent=2)),
        ])
    sections.extend(["", "## Limitations", *[_quote(item) for item in assessment["limitations"]]])
    body = "\n".join(sections).rstrip() + "\n"
    metadata = {
        "ris_id": record_id,
        "project_id": cfg["project_id"],
        "kind": "finding",
        "status": "draft",
        "created": created,
        "knowledge_record": True,
        "knowledge_assessment_status": assessment["status"],
        "assessment_scope": assessment["assessment_scope"],
        "evidence_status": assessment["evidence_status"],
        "evidence_verification_variant": assessment["evidence_verification_variant"],
        "evidence_checks": assessment["evidence_checks"],
        "review_required": True,
        "knowledge_rationale": assessment["rationale"],
        "knowledge_payload_sha256": payload_digest,
        "knowledge_body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "source_project_id": source["project_id"],
        "source_project_path": None if same_project_source else source["project_path"],
        "source_study_id": source["study_id"],
        "source_revision": source["revision"],
        "source_current_revision_at_save": source["current_revision"],
        "source_freshness_checked_at": source["freshness_checked_at"],
        "source_study_path": source["research_relative_path"],
        "source_observation_id": source["observation_id"],
        "source_observation_sha256": source["observation_digest"],
        "source_locator": source["observation_locator"],
        "source_evidence_kind": observation.get("evidence_kind"),
        "source_observation": observation,
        "source_conditions": assessment["condition_comparison"]["source_scope_conditions"],
        "target_study_id": target["study_id"],
        "target_revision": target["revision"],
        "target_study_path": target["research_relative_path"],
        "target_context": target["context"],
        "target_conditions": assessment["condition_comparison"]["target_conditions"],
        "transfer_claimed": False,
        "recommendations_promoted": False,
    }
    if isinstance(metric_replays, list) and metric_replays:
        metadata["knowledge_metric_replays"] = metric_replays
    metadata["knowledge_metadata_sha256"] = _metadata_digest(metadata)
    return "---\n" + ris.yaml_mapping(metadata) + "---\n\n" + body


def _identity(prepared: dict) -> dict:
    source = prepared["source"]
    target = prepared["target"]
    return {
        "target_project_id": target["project_id"],
        "source_project_id": source["project_id"],
        "source_study_id": source["study_id"],
        "source_revision": source["revision"],
        "source_current_revision": source["current_revision"],
        "source_observation_id": source["observation_id"],
        "target_study_id": target["study_id"],
        "target_revision": target["revision"],
        "evidence_verification_variant": prepared["assessment"]["evidence_verification_variant"],
        "evidence_checks_sha256": _canonical_digest(prepared["assessment"]["evidence_checks"]),
    }


def _payload(prepared: dict) -> dict:
    return {
        "identity": _identity(prepared),
        "assessment": prepared["assessment"],
        "source_observation": prepared["source"]["observation"],
        "source_observation_sha256": prepared["source"]["observation_digest"],
        "source_locator": prepared["source"]["observation_locator"],
        "target_context": prepared["target"]["context"],
    }


def _same_existing(ris, path: Path, expected_text: str) -> bool:
    if not path.is_file() or path.is_symlink():
        _error(ris, "Deterministic knowledge path is occupied by a non-regular file; no overwrite performed")
    text = path.read_text(encoding="utf-8")
    metadata = ris.frontmatter(text)
    expected_metadata = ris.frontmatter(expected_text)
    _validate_saved_note_integrity(ris, path, text, metadata)
    if (metadata.get("project_id") != expected_metadata.get("project_id")
            or metadata.get("ris_id") != expected_metadata.get("ris_id")
            or metadata.get("kind") != "finding" or metadata.get("knowledge_record") is not True):
        _error(ris, "Deterministic knowledge path contains a conflicting or unmanaged note; no overwrite performed")
    # The payload digest pins semantic source/target content. The body digest pins the exact
    # originally written rendering, so later display-format changes don't invalidate the note.
    volatile_fields = {
        "created", "source_freshness_checked_at", "knowledge_body_sha256",
        "knowledge_metadata_sha256",
        # External project roots can move; preserve the original pointer in the existing note.
        "source_project_path",
    }
    metadata_without_created = {key: value for key, value in metadata.items() if key not in volatile_fields}
    expected_without_created = {key: value for key, value in expected_metadata.items() if key not in volatile_fields}
    if metadata_without_created != expected_without_created:
        _error(ris, "Existing knowledge record differs for the same source and target revisions; no overwrite performed")
    return True


def _validate_saved_note_integrity(ris, path: Path, text: str, metadata: dict) -> None:
    match = re.match(r"\A---\r?\n.*?\r?\n---(?:\r?\n|$)", text, re.S)
    if not match:
        _error(ris, f"Saved knowledge note lost its managed frontmatter: {path}")
    actual_body = text[match.end():]
    if actual_body.startswith("\r\n"):
        actual_body = actual_body[2:]
    elif actual_body.startswith("\n"):
        actual_body = actual_body[1:]
    actual_body_digest = hashlib.sha256(actual_body.encode("utf-8")).hexdigest()
    if metadata.get("knowledge_body_sha256") != actual_body_digest:
        _error(ris, f"Saved knowledge note body integrity conflict: {path}")
    stored_metadata_digest = metadata.get("knowledge_metadata_sha256")
    if not isinstance(stored_metadata_digest, str) or stored_metadata_digest != _metadata_digest(metadata):
        _error(ris, f"Saved knowledge note metadata integrity conflict: {path}")
    if (metadata.get("knowledge_assessment_status") not in {"scope_match", "recheck"}
            or metadata.get("assessment_scope") != "recorded_conditions"
            or metadata.get("review_required") is not True
            or not isinstance(metadata.get("evidence_checks"), list)):
        _error(ris, f"Saved knowledge note assessment contract conflict: {path}")
    if ("knowledge_metric_replays" in metadata
            and not isinstance(metadata["knowledge_metric_replays"], list)):
        _error(ris, f"Saved knowledge note metric replay metadata conflict: {path}")

    required = ("project_id", "source_project_id", "source_study_id", "source_revision",
                "source_current_revision_at_save", "source_observation_id", "target_study_id", "target_revision",
                "evidence_verification_variant", "evidence_checks")
    if any(field not in metadata for field in required):
        _error(ris, f"Saved knowledge note provenance is incomplete: {path}")
    identity = {
        "target_project_id": metadata["project_id"],
        "source_project_id": metadata["source_project_id"],
        "source_study_id": metadata["source_study_id"],
        "source_revision": metadata["source_revision"],
        "source_current_revision": metadata["source_current_revision_at_save"],
        "source_observation_id": metadata["source_observation_id"],
        "target_study_id": metadata["target_study_id"],
        "target_revision": metadata["target_revision"],
        "evidence_verification_variant": metadata["evidence_verification_variant"],
        "evidence_checks_sha256": _canonical_digest(metadata["evidence_checks"]),
    }
    identity_digest = _canonical_digest(identity)
    if (path.name != f"knowledge-{identity_digest[:32]}.md"
            or metadata.get("ris_id") != "KN-" + identity_digest[:32]):
        _error(ris, f"Saved knowledge note identity conflict: {path}")


def _reuse_result(prepared: dict, status: str, relative: str, record_id: str,
                  digest: str, target_revision: int) -> dict:
    assessment = prepared["assessment"]
    result = {
        "status": status,
        "assessment_status": assessment["status"],
        "assessment_scope": assessment["assessment_scope"],
        "evidence_status": assessment["evidence_status"],
        "evidence_verification_variant": assessment["evidence_verification_variant"],
        "evidence_checks": assessment["evidence_checks"],
        "review_required": True,
        "path": relative,
        "ris_id": record_id,
        "sha256": digest,
        "source_observation_sha256": prepared["source"]["observation_digest"],
        "source_current_revision": prepared["source"]["current_revision"],
        "target_revision": target_revision,
        "rationale": assessment["rationale"],
        "transfer_claimed": False,
    }
    if assessment.get("metric_replays"):
        result["metric_replays"] = assessment["metric_replays"]
    return result


def reuse_knowledge(ris, root: Path, study, source_id: str, revision: int,
                    observation_id: str, target_id: str, *,
                    source_project: str | Path | None = None,
                    target_revision: int | None = None,
                    verify_evidence: bool = False) -> dict:
    """Explicitly save an immutable, idempotent managed finding in the target project."""
    prepared = _prepare(ris, root, study, source_id, revision, observation_id, target_id,
                        source_project=source_project, target_revision=target_revision,
                        verify_evidence=verify_evidence)
    target = prepared["target"]
    if not target["is_current"]:
        _error(ris, "Cannot save against a stale target study revision; reassess the current target")

    cfg = ris.config(root)
    findings_relative = f"{cfg['research_dir']}/findings"
    ris.inside(root, findings_relative)
    identity_digest = _canonical_digest(_identity(prepared))
    payload_digest = _canonical_digest(_payload(prepared))
    record_id = "KN-" + identity_digest[:32]
    relative = f"{findings_relative}/knowledge-{identity_digest[:32]}.md"
    path = ris.inside(root, relative)
    text = _knowledge_note(ris, root, prepared, identity_digest, payload_digest)

    with ris.project_lock(root):
        cfg = ris.config(root)
        current = _load_study(ris, root, study, target["study_id"], None, "Target")
        if current["revision"] != target["revision"]:
            _error(ris, f"Target study changed from revision {target['revision']} to {current['revision']} during reuse; reassess")
        source_root = prepared["source_root"]
        pinned_source = _load_study(ris, source_root, study,
                                    prepared["source"]["study_id"],
                                    prepared["source"]["revision"], "Pinned source")
        pinned_observation = _read_observation(ris, pinned_source, prepared["source"]["observation_id"])
        if _canonical_digest(pinned_observation) != prepared["source"]["observation_digest"]:
            _error(ris, "Pinned source observation changed during reuse; no finding was saved")
        if (prepared["assessment"]["evidence_verification_variant"] == "verify_attached_files"
                and pinned_observation.get("evidence_files")):
            latest_evidence = _verify_attached_evidence(ris, source_root, pinned_observation, True)
            expected_attached_checks = [check for check in prepared["assessment"]["evidence_checks"]
                                        if check.get("kind") != "metric_input"]
            if _canonical_digest(latest_evidence["evidence_checks"]) != _canonical_digest(expected_attached_checks):
                _error(ris, "Attached evidence changed during reuse; reassess before saving")
        if (prepared["assessment"]["evidence_verification_variant"] == "verify_attached_files"
                and prepared["assessment"].get("metric_replays")):
            latest_metrics = _replay_registered_metrics(ris, source_root, pinned_observation)
            expected_metric_checks = [check for check in prepared["assessment"]["evidence_checks"]
                                      if check.get("kind") == "metric_input"]
            if _canonical_digest(latest_metrics["evidence_checks"]) != _canonical_digest(expected_metric_checks):
                _error(ris, "Registered metric input changed during reuse; reassess before saving")
        latest_source = _load_study(ris, source_root, study,
                                    prepared["source"]["study_id"], None, "Current source")
        if latest_source["revision"] != prepared["source"]["current_revision"]:
            _error(ris, f"Source study changed from revision {prepared['source']['current_revision']} to {latest_source['revision']} during reuse; reassess")
        # Keep storage confined to the configured managed findings directory.
        findings = ris.inside(root, f"{cfg['research_dir']}/findings")
        if not findings.is_dir():
            _error(ris, "Managed findings directory is missing")
        path = ris.inside(root, relative)
        if path.exists():
            _same_existing(ris, path, text)
            return _reuse_result(prepared, "already_saved", relative, record_id,
                                 hashlib.sha256(path.read_bytes()).hexdigest(), target["revision"])
        try:
            ris.atomic_note_write(path, text.encode("utf-8"))
        except FileExistsError:
            # An external writer may race despite the cooperative project lock.
            _same_existing(ris, path, text)
            return _reuse_result(prepared, "already_saved", relative, record_id,
                                 hashlib.sha256(path.read_bytes()).hexdigest(), target["revision"])
    return _reuse_result(prepared, "saved", relative, record_id,
                         hashlib.sha256(text.encode("utf-8")).hexdigest(), target["revision"])


def list_saved_knowledge_links(ris, root: Path, target_id: str, study,
                               target_revision: int | None = None) -> dict:
    """List saved findings for one target study in this project; does not scan other projects."""
    target_id = _validate_id(ris, target_id, "Target study ID")
    target_revision = _revision(ris, target_revision, "target_revision")
    selected, current, selected_is_current = _target_read(ris, root, study, target_id, target_revision)
    cfg = ris.config(root)
    folder = ris.inside(root, f"{cfg['research_dir']}/findings")
    if not folder.is_dir():
        return {
            "target": {"project_id": cfg["project_id"], "study_id": target_id,
                       "revision": selected["revision"], "path": selected["path"]},
            "current_revision": current["revision"],
            "selected_revision_is_current": selected_is_current,
            "links": [],
        }
    links = []
    source_current_cache = {}
    for path in sorted(folder.iterdir()):
        if not re.fullmatch(r"knowledge-[0-9a-f]{32}\.md", path.name):
            continue
        if path.is_symlink():
            _error(ris, f"Symlink is not a managed finding path: {path.relative_to(root)}")
        if not path.is_file():
            _error(ris, f"Deterministic knowledge path is not a regular file: {path.relative_to(root)}")
        relative = str(path.relative_to(root))
        managed_path = ris.inside(root, relative)
        note_text = managed_path.read_text(encoding="utf-8")
        metadata = ris.frontmatter(note_text)
        if metadata.get("target_study_id") != target_id:
            continue
        if metadata.get("knowledge_record") is not True:
            _error(ris, f"Saved knowledge note lost its managed record marker: {relative}")
        _validate_saved_note_integrity(ris, managed_path, note_text, metadata)
        if metadata.get("project_id") != cfg["project_id"]:
            _error(ris, f"Saved knowledge note has a different target project identity: {relative}")
        saved_revision = metadata.get("target_revision")
        stale = type(saved_revision) is not int or saved_revision != current["revision"]
        saved_status = metadata.get("knowledge_assessment_status")
        if saved_status not in ("scope_match", "recheck"):
            _error(ris, f"Saved knowledge note has an invalid assessment status: {relative}")
        evidence_status = metadata.get("evidence_status")
        if evidence_status not in {"not_checked", "unverified", "bytes_match", "missing", "changed", "recheck"}:
            _error(ris, f"Saved knowledge note has an invalid evidence status: {relative}")
        rationale = list(metadata.get("knowledge_rationale", []))
        current_status = saved_status
        next_actions = ["human_review_required"]
        if stale:
            rationale = [*rationale,
                         f"Target study advanced from saved revision {saved_revision} to current revision {current['revision']}; review against the current target."]
            current_status = "recheck"
            next_actions.append("review_against_current_target")

        source_project_id = metadata.get("source_project_id")
        source_revision = metadata.get("source_revision")
        source_freshness = "not_refreshed"
        source_current_revision = None
        source_freshness_checked_at = metadata.get("source_freshness_checked_at")
        source_project_path = metadata.get("source_project_path")
        if source_project_path is None and source_project_id == cfg["project_id"]:
            source_study_id = metadata.get("source_study_id")
            if source_study_id not in source_current_cache:
                try:
                    source_snapshot = study.read_study(ris, root, source_study_id, None)
                    if source_snapshot.get("project_id") != cfg["project_id"]:
                        raise ris.Error("Source project identity mismatch")
                    source_current_cache[source_study_id] = {"revision": source_snapshot.get("revision")}
                except (ris.Error, OSError, ValueError) as exc:
                    source_current_cache[source_study_id] = {"error": str(exc)}
            source_status = source_current_cache[source_study_id]
            if "error" in source_status:
                source_freshness = "unavailable"
                rationale.append(f"Could not confirm current source study revision: {source_status['error']}")
                current_status = "recheck"
                next_actions.append("inspect_source_study")
            else:
                source_current_revision = source_status["revision"]
                source_freshness = "current" if source_current_revision == source_revision else "advanced"
                if source_freshness == "advanced":
                    rationale.append(
                        f"Source study advanced from pinned revision {source_revision} to current revision {source_current_revision}; review the pinned evidence.")
                    current_status = "recheck"
                    next_actions.append("review_pinned_source_revision")
        elif metadata.get("source_current_revision_at_save") != source_revision:
            rationale.append(
                "External source was already newer than the pinned revision when saved; review the pinned evidence.")
            current_status = "recheck"
            next_actions.append("review_pinned_source_revision")
        else:
            next_actions.append("refresh_external_source_when_explicitly_selected")

        link = {
            "path": relative,
            "current_status": current_status,
            "assessment_scope": metadata.get("assessment_scope"),
            "evidence_status": evidence_status,
            "review_required": True,
            "ris_id": metadata.get("ris_id"),
            "source_project_id": source_project_id,
            "source_project_path": source_project_path,
            "source_study_id": metadata.get("source_study_id"),
            "source_revision": source_revision,
            "source_current_revision_at_save": metadata.get("source_current_revision_at_save"),
            "source_current_revision": source_current_revision,
            "source_freshness": source_freshness,
            "source_freshness_checked_at": source_freshness_checked_at,
            "source_observation_id": metadata.get("source_observation_id"),
            "source_observation_sha256": metadata.get("source_observation_sha256"),
            "target_study_id": target_id,
            "target_revision": saved_revision,
            "saved_status": saved_status,
            "evidence_verification_variant": metadata.get("evidence_verification_variant"),
            "evidence_checks": metadata.get("evidence_checks", []),
            "evidence_freshness": "not_refreshed" if evidence_status == "bytes_match" else "not_checked",
            "stale_target": stale,
            "permanent_invalidity": False,
            "next_action": next_actions[0] if next_actions else None,
            "next_actions": next_actions,
            "external_source_not_refreshed": source_freshness == "not_refreshed",
            "rationale": rationale,
        }
        if "knowledge_metric_replays" in metadata:
            # Historical display exposes the saved capture only. It does not reopen metric inputs.
            link["metric_replays"] = metadata["knowledge_metric_replays"]
            link["metric_replay_freshness"] = "not_refreshed"
        links.append(link)
    return {
        "target": {"project_id": cfg["project_id"], "study_id": target_id,
                   "revision": selected["revision"], "path": selected["path"]},
        "current_revision": current["revision"],
        "selected_revision_is_current": selected_is_current,
        "links": links,
    }


def add_parser(sub: argparse._SubParsersAction) -> None:
    knowledge = sub.add_parser("knowledge", help="Assess and explicitly reuse study evidence")
    actions = knowledge.add_subparsers(dest="knowledge_action", required=True)
    for action in ("assess", "reuse"):
        command = actions.add_parser(action, help=(
            "Read-only scope assessment" if action == "assess"
            else "Save an immutable finding in the selected target project"))
        command.add_argument("source", help="Source study ID")
        command.add_argument("--revision", type=int, required=True,
                             help="Pin the source study revision")
        command.add_argument("--observation", required=True,
                             help="Observation ID from the pinned source revision")
        command.add_argument("--target", required=True, help="Target study ID in --project")
        command.add_argument("--target-revision", type=int,
                             help="Assess this target revision; reuse requires it to remain current")
        command.add_argument("--source-project", type=Path,
                             help="Explicitly select one external source project")
        command.add_argument("--verify-evidence", action="store_true",
                             help="Verify explicitly attached files and replay registered metrics for the selected observation")


def dispatch(ris, root: Path, args, study) -> dict:
    common = {
        "source_project": args.source_project,
        "target_revision": args.target_revision,
        "verify_evidence": args.verify_evidence,
    }
    if args.knowledge_action == "assess":
        return assess_knowledge(ris, root, study, args.source, args.revision,
                                args.observation, args.target, **common)
    if args.knowledge_action == "reuse":
        return reuse_knowledge(ris, root, study, args.source, args.revision,
                               args.observation, args.target, **common)
    _error(ris, "Unknown knowledge action")
