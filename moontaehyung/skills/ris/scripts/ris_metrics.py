#!/usr/bin/env python3
"""Declarative, bounded metrics over project-local CSV and JSONL evidence."""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
import hashlib
import io
import json
import os
import errno
from pathlib import Path
import re
import stat


SCHEMA_VERSION = 1
MAX_INPUT_BYTES = 64 * 1024 * 1024
MAX_DEFINITION_BYTES = 1024 * 1024
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
RATIONAL_RE = re.compile(r"^([+-]?\d+)/([+-]?\d+)$")


def _error(ris, message: str):
    error = getattr(ris, "Error", ValueError)
    return error(message)


def _exact_keys(ris, value: dict, required: set[str], allowed: set[str], label: str) -> None:
    missing = required - set(value)
    extra = set(value) - allowed
    if missing:
        raise _error(ris, f"{label} is missing fields: " + ", ".join(sorted(missing)))
    if extra:
        raise _error(ris, f"{label} has unsupported fields: " + ", ".join(sorted(extra)))


def _decimal(ris, value, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal, str)):
        raise _error(ris, f"{label} must be a finite decimal number or numeric string")
    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise _error(ris, f"{label} must be a finite decimal number or numeric string") from exc
    if not parsed.is_finite():
        raise _error(ris, f"{label} must be finite")
    digits, exponent = parsed.as_tuple().digits, parsed.as_tuple().exponent
    if len(digits) > 1000 or abs(exponent) > 1000:
        raise _error(ris, f"{label} exceeds the supported decimal precision")
    return parsed


def _fraction(value: Decimal) -> Fraction:
    return Fraction(value)


def _canonical_finite_decimal(value: Decimal) -> str:
    """Return a non-exponent decimal spelling without insignificant zeroes."""
    if value == 0:
        return "0"
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text.startswith("."):
        text = "0" + text
    elif text.startswith("-."):
        text = "-0" + text[1:]
    return text


def _fraction_decimal_if_finite(value: Fraction) -> str | None:
    denominator = value.denominator
    twos = fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        return None
    places = max(twos, fives)
    scaled = value.numerator * (2 ** (places - twos)) * (5 ** (places - fives))
    sign = "-" if scaled < 0 else ""
    digits = str(abs(scaled))
    if places == 0:
        return sign + digits
    digits = digits.rjust(places + 1, "0")
    text = sign + digits[:-places] + "." + digits[-places:]
    text = text.rstrip("0").rstrip(".")
    return text


def _fraction_text(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _json_safe_number(ris, value, label: str):
    """Convert a numeric filter to a JSON-safe int/float without NaN or infinity."""
    decimal_value = _decimal(ris, value, label)
    integral = decimal_value.to_integral_value()
    if decimal_value == integral:
        return int(integral)
    safe = float(decimal_value)
    if safe != safe or safe in (float("inf"), float("-inf")):
        raise _error(ris, f"{label} is outside the supported JSON number range")
    if Decimal(str(safe)) != decimal_value:
        raise _error(ris, f"{label} cannot be represented exactly as a JSON-safe numeric filter")
    return safe


def _normalize_filter(ris, value, label: str, input_format: str) -> dict:
    if not isinstance(value, dict):
        raise _error(ris, f"{label} must be an object mapping top-level field names to values")
    result = {}
    for key in value:
        if not isinstance(key, str) or not key:
            raise _error(ris, f"{label} field names must be non-empty strings")
    for key in sorted(value):
        item = value[key]
        if input_format == "csv":
            if not isinstance(item, str):
                raise _error(ris, f"{label}.{key} must be a string for CSV input")
            result[key] = item
        elif isinstance(item, list):
            if item:
                raise _error(ris, f"{label}.{key} supports only the exact empty JSON array [] as an array value")
            result[key] = []
        elif item is None or isinstance(item, (str, bool)):
            result[key] = item
        elif isinstance(item, (int, float, Decimal)) and not isinstance(item, bool):
            result[key] = _json_safe_number(ris, item, f"{label}.{key}")
        else:
            raise _error(ris, f"{label}.{key} must be a JSON scalar or exact empty array []")
    return result


def _normalized_definition(ris, definition) -> dict:
    if not isinstance(definition, dict):
        raise _error(ris, "metric definition must be a JSON object")
    required = {"id", "format", "operation", "where", "unit"}
    allowed = required | {"numerator_where", "threshold"}
    _exact_keys(ris, definition, required, allowed, "metric definition")

    metric_id = definition["id"]
    if not isinstance(metric_id, str) or not SAFE_ID.fullmatch(metric_id):
        raise _error(ris, "metric definition id must match [A-Za-z0-9][A-Za-z0-9_-]{0,63}")
    input_format = definition["format"]
    if not isinstance(input_format, str) or input_format not in {"csv", "jsonl"}:
        raise _error(ris, "metric definition format must be csv or jsonl")
    operation = definition["operation"]
    if not isinstance(operation, str) or operation not in {"count", "ratio"}:
        raise _error(ris, "metric definition operation must be count or ratio")
    unit = definition["unit"]
    if not isinstance(unit, str):
        raise _error(ris, "metric definition unit must be a string")
    if operation == "count" and unit != "rows":
        raise _error(ris, "count metrics must use unit rows")
    if operation == "ratio" and unit not in {"fraction", "percent"}:
        raise _error(ris, "ratio metrics must use unit fraction or percent")
    if operation == "count" and "numerator_where" in definition:
        raise _error(ris, "numerator_where is supported only for ratio metrics")
    if operation == "ratio" and "numerator_where" not in definition:
        raise _error(ris, "ratio metrics must declare numerator_where (use {} to count the full population)")

    result = {
        "id": metric_id,
        "format": input_format,
        "operation": operation,
        "where": _normalize_filter(ris, definition["where"], "where", input_format),
        "unit": unit,
    }
    if operation == "ratio":
        result["numerator_where"] = _normalize_filter(
            ris, definition["numerator_where"], "numerator_where", input_format
        )
    if "threshold" in definition:
        threshold = definition["threshold"]
        if not isinstance(threshold, dict):
            raise _error(ris, "threshold must be an object with op and value")
        _exact_keys(ris, threshold, {"op", "value"}, {"op", "value"}, "threshold")
        op = threshold["op"]
        if not isinstance(op, str) or op not in {"gt", "ge", "lt", "le", "eq"}:
            raise _error(ris, "threshold.op must be gt, ge, lt, le, or eq")
        threshold_decimal = _decimal(ris, threshold["value"], "threshold.value")
        result["threshold"] = {"op": op, "value": _canonical_finite_decimal(threshold_decimal)}
    return result


def normalize_definition(ris, definition) -> dict:
    """Validate and return a stable JSON-serializable metric definition."""
    return _normalized_definition(ris, definition)


def _definition_fingerprint(definition: dict) -> str:
    canonical = json.dumps(
        definition, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_pairs_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key: " + key)
        result[key] = value
    return result


def _reject_json_constant(value):
    raise ValueError("non-standard JSON numeric constant: " + value)


def _json_load(text: str):
    return json.loads(
        text,
        object_pairs_hook=_json_pairs_no_duplicates,
        parse_float=Decimal,
        parse_constant=_reject_json_constant,
    )


def _project_relative_path(ris, root: Path, relative: str) -> tuple[Path, str] | None:
    if not isinstance(relative, str) or not relative:
        raise _error(ris, "input must be an exact project-relative path")
    if relative != relative.strip() or relative.startswith("/") or "\\" in relative:
        raise _error(ris, "input must be an exact project-relative POSIX path")
    parts = relative.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise _error(ris, "input path must not contain empty, dot, or parent components")
    root_path = Path(root).expanduser().resolve(strict=True)
    if not root_path.is_dir():
        raise _error(ris, "project root must be a directory")
    inside = getattr(ris, "inside", None)
    if callable(inside):
        resolved = inside(root_path, relative)
    else:
        candidate = root_path.joinpath(*parts)
        try:
            resolved = candidate.resolve(strict=False)
        except OSError as exc:
            raise _error(ris, "unable to resolve input path: " + str(exc)) from exc
        if not resolved.is_relative_to(root_path):
            raise _error(ris, "input path resolves outside the project root")
    return resolved, relative


def _snapshot_input(ris, root: Path, input_path: str) -> tuple[dict, bytes | None, str | None]:
    selected = _project_relative_path(ris, root, input_path)
    if selected is None:
        return {"path": input_path, "sha256": None}, None, "input file does not exist"
    resolved, relative = selected
    root_path = Path(root).expanduser().resolve(strict=True)
    parts = relative.split("/")
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    nofollow_flag = getattr(os, "O_NOFOLLOW", 0)
    nonblock_flag = getattr(os, "O_NONBLOCK", 0)
    open_flags = os.O_RDONLY | nonblock_flag
    directory_fd = None
    current_directory_fd = None
    file_fd = None
    try:
        directory_fd = os.open(root_path, os.O_RDONLY | directory_flag | nofollow_flag)
        current_directory_fd = directory_fd
        for part in parts[:-1]:
            next_directory_fd = os.open(
                part, os.O_RDONLY | directory_flag | nofollow_flag,
                dir_fd=current_directory_fd,
            )
            if current_directory_fd != directory_fd:
                os.close(current_directory_fd)
            current_directory_fd = next_directory_fd
        file_fd = os.open(
            parts[-1], open_flags | nofollow_flag, dir_fd=current_directory_fd
        )
        if current_directory_fd != directory_fd:
            os.close(current_directory_fd)
            current_directory_fd = None
        stream = os.fdopen(file_fd, "rb")
        file_fd = None
        with stream:
            metadata = os.fstat(stream.fileno())
            if not stat.S_ISREG(metadata.st_mode):
                raise _error(ris, "input path must identify a regular file")
            if metadata.st_size > MAX_INPUT_BYTES:
                return {"path": relative, "sha256": None}, None, (
                    f"input exceeds the {MAX_INPUT_BYTES}-byte processing limit"
                )
            chunks = []
            total = 0
            while True:
                chunk = stream.read(min(1024 * 1024, MAX_INPUT_BYTES + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > MAX_INPUT_BYTES:
                    return {"path": relative, "sha256": None}, None, (
                        f"input exceeds the {MAX_INPUT_BYTES}-byte processing limit"
                    )
            data = b"".join(chunks)
    except OSError as exc:
        if exc.errno in {errno.ELOOP, errno.EMLINK}:
            raise _error(ris, "symlinked input paths are not permitted") from exc
        if isinstance(exc, (FileNotFoundError, NotADirectoryError)) or exc.errno == errno.ENOENT:
            return {"path": relative, "sha256": None}, None, "input file does not exist"
        raise _error(ris, "unable to read input file: " + str(exc)) from exc
    finally:
        if file_fd is not None:
            os.close(file_fd)
        if current_directory_fd is not None and current_directory_fd != directory_fd:
            os.close(current_directory_fd)
        if directory_fd is not None:
            os.close(directory_fd)
    digest = hashlib.sha256(data).hexdigest()
    return {"path": relative, "sha256": digest}, data, None


def _indeterminate(reason: str, input_record=None, *, definition=None, definition_sha256=None,
                   metric_id=None, unit=None, numerator=None, denominator=None) -> dict:
    return {
        "status": "indeterminate",
        "reason": reason,
        "metric_id": metric_id,
        "definition": definition,
        "definition_sha256": definition_sha256,
        "value": None,
        "exact_value": None,
        "value_representation": None,
        "value_rounding": None,
        "numerator": numerator,
        "denominator": denominator,
        "unit": unit,
        "threshold_met": None,
        "input": input_record or {"path": None, "sha256": None},
    }


def _number_equal(expected, actual) -> bool:
    if isinstance(expected, bool) or isinstance(actual, bool):
        return type(expected) is bool and type(actual) is bool and expected is actual
    numeric = (int, float, Decimal)
    if isinstance(expected, numeric) and isinstance(actual, numeric):
        try:
            expected_decimal = Decimal(str(expected))
            actual_decimal = Decimal(str(actual))
            for value in (expected_decimal, actual_decimal):
                if not value.is_finite() or len(value.as_tuple().digits) > 1000 or abs(value.as_tuple().exponent) > 1000:
                    raise ValueError("numeric field exceeds the supported decimal precision")
            return Fraction(expected_decimal) == Fraction(actual_decimal)
        except (InvalidOperation, ValueError, OverflowError):
            raise ValueError("numeric field is not a supported finite decimal")
    if type(expected) is not type(actual):
        return False
    return expected == actual


def _matches(row: dict, filters: dict) -> bool:
    missing = False
    for key, expected in filters.items():
        if key not in row:
            missing = True
            continue
        actual = row[key]
        if isinstance(expected, list):
            if not isinstance(actual, list) or actual != []:
                return False
        elif not _number_equal(expected, actual):
            return False
    if missing:
        raise ValueError("record is missing a field required by the metric filter")
    return True


def _count_rows_csv(data: bytes, definition: dict) -> tuple[int, int | None]:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV input is not valid UTF-8") from exc
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        header = next(reader)
    except StopIteration:
        raise ValueError("CSV input is missing its header row")
    except csv.Error as exc:
        raise ValueError("CSV header is malformed: " + str(exc)) from exc
    if not header or any(not name for name in header):
        raise ValueError("CSV header must contain non-empty column names")
    if len(header) != len(set(header)):
        raise ValueError("CSV header contains duplicate column names")
    required = set(definition["where"])
    if definition["operation"] == "ratio":
        required |= set(definition["numerator_where"])
    absent = required - set(header)
    if absent:
        raise ValueError("CSV input is missing required columns: " + ", ".join(sorted(absent)))

    denominator = 0
    numerator = 0
    try:
        for row_values in reader:
            if len(row_values) != len(header):
                raise ValueError(f"CSV row ending at line {reader.line_num} has {len(row_values)} cells; expected {len(header)}")
            row = dict(zip(header, row_values))
            if _matches(row, definition["where"]):
                denominator += 1
                if definition["operation"] == "ratio" and _matches(row, definition["numerator_where"]):
                    numerator += 1
    except csv.Error as exc:
        raise ValueError("CSV input is malformed: " + str(exc)) from exc
    return denominator, numerator if definition["operation"] == "ratio" else None


def _count_rows_jsonl(data: bytes, definition: dict) -> tuple[int, int | None]:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("JSONL input is not valid UTF-8") from exc
    denominator = 0
    numerator = 0
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = _json_load(line)
        except (json.JSONDecodeError, ValueError) as exc:
            raise ValueError(f"JSONL line {line_number} is malformed: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"JSONL line {line_number} must contain a JSON object")
        try:
            in_population = _matches(row, definition["where"])
            if in_population:
                denominator += 1
                if definition["operation"] == "ratio" and _matches(row, definition["numerator_where"]):
                    numerator += 1
        except ValueError as exc:
            raise ValueError(f"JSONL line {line_number}: {exc}") from exc
    return denominator, numerator if definition["operation"] == "ratio" else None


def _threshold_fraction(definition: dict) -> Fraction | None:
    threshold = definition.get("threshold")
    if threshold is None:
        return None
    return Fraction(Decimal(threshold["value"]))


def _threshold_test(value: Fraction, definition: dict) -> bool | None:
    threshold = definition.get("threshold")
    if threshold is None:
        return None
    target = _threshold_fraction(definition)
    op = threshold["op"]
    if op == "gt":
        return value > target
    if op == "ge":
        return value >= target
    if op == "lt":
        return value < target
    if op == "le":
        return value <= target
    return value == target


def _fraction_display(value: Fraction) -> tuple[str, str, str | None]:
    exact = _fraction_decimal_if_finite(value)
    if exact is not None:
        return exact, "decimal_exact", None
    with localcontext() as context:
        context.prec = 50
        context.rounding = ROUND_HALF_EVEN
        rounded = Decimal(value.numerator) / Decimal(value.denominator)
    return _canonical_finite_decimal(rounded), "decimal_rounded", "50 significant decimal digits, ROUND_HALF_EVEN"


def calculate(ris, root: Path, definition, input_path: str) -> dict:
    """Calculate one metric from one bounded byte snapshot of a project file.

    Unsafe paths and non-file inputs raise ``ris.Error``. Missing inputs and
    malformed definition/data content return an explicit indeterminate record.
    """
    if input_path is None:
        input_record, data, input_error = {"path": None, "sha256": None}, None, "input path was not provided"
    else:
        input_record, data, input_error = _snapshot_input(ris, root, input_path)
    try:
        normalized = normalize_definition(ris, definition)
    except (TypeError, ValueError, AttributeError, getattr(ris, "Error", ValueError)) as exc:
        return _indeterminate(
            "invalid metric definition: " + str(exc), input_record,
            metric_id=(definition.get("id") if isinstance(definition, dict) and isinstance(definition.get("id"), str) else None),
        )
    fingerprint = _definition_fingerprint(normalized)
    base = {
        "metric_id": normalized["id"],
        "definition": normalized,
        "definition_sha256": fingerprint,
        "unit": normalized["unit"],
    }
    if input_error:
        return _indeterminate(
            input_error, input_record, definition=normalized, definition_sha256=fingerprint,
            metric_id=normalized["id"], unit=normalized["unit"],
        )
    try:
        if normalized["format"] == "csv":
            denominator, numerator = _count_rows_csv(data, normalized)
        else:
            denominator, numerator = _count_rows_jsonl(data, normalized)
    except (UnicodeError, ValueError, csv.Error) as exc:
        return _indeterminate(
            str(exc), input_record, definition=normalized, definition_sha256=fingerprint,
            metric_id=normalized["id"], unit=normalized["unit"],
        )

    if normalized["operation"] == "count":
        exact = Fraction(denominator, 1)
        value = str(denominator)
        value_representation = "decimal_exact"
        value_rounding = None
        exact_value = str(denominator)
        output_numerator = None
        output_denominator = denominator
    else:
        if denominator == 0:
            return _indeterminate(
                "ratio denominator is zero; result is indeterminate", input_record,
                definition=normalized, definition_sha256=fingerprint, metric_id=normalized["id"],
                unit=normalized["unit"], numerator=0, denominator=0,
            )
        exact = Fraction(numerator, denominator)
        if normalized["unit"] == "percent":
            exact *= 100
        value, value_representation, value_rounding = _fraction_display(exact)
        exact_value = _fraction_text(exact)
        output_numerator = numerator
        output_denominator = denominator

    result = {
        "status": "ok",
        "reason": None,
        **base,
        "value": value,
        "exact_value": exact_value,
        "value_representation": value_representation,
        "value_rounding": value_rounding,
        "numerator": output_numerator,
        "denominator": output_denominator,
        "threshold_met": _threshold_test(exact, normalized),
        "input": input_record,
    }
    return result


def _validated_result(result) -> tuple[dict, Fraction] | tuple[None, None]:
    if not isinstance(result, dict) or result.get("status") != "ok":
        return None, None
    definition = result.get("definition")
    try:
        normalized = _normalized_definition(_ValidationOnlyRis(), definition)
    except (TypeError, ValueError, AttributeError):
        return None, None
    fingerprint = _definition_fingerprint(normalized)
    if result.get("definition_sha256") != fingerprint or result.get("metric_id") != normalized["id"]:
        return None, None
    if result.get("unit") != normalized["unit"]:
        return None, None
    denominator = result.get("denominator")
    numerator = result.get("numerator")
    if normalized["operation"] == "count":
        if type(denominator) is not int or denominator < 0 or numerator is not None:
            return None, None
        exact = Fraction(denominator, 1)
    else:
        if type(denominator) is not int or denominator <= 0 or type(numerator) is not int or numerator < 0 or numerator > denominator:
            return None, None
        exact = Fraction(numerator, denominator)
        if normalized["unit"] == "percent":
            exact *= 100
    if normalized["operation"] == "count":
        expected_value = str(denominator)
        expected_exact_value = str(denominator)
        expected_representation = "decimal_exact"
        expected_rounding = None
    else:
        expected_value, expected_representation, expected_rounding = _fraction_display(exact)
        expected_exact_value = _fraction_text(exact)
    if (result.get("value") != expected_value
            or result.get("exact_value") != expected_exact_value
            or result.get("value_representation") != expected_representation
            or result.get("value_rounding") != expected_rounding):
        return None, None
    input_record = result.get("input")
    if (not isinstance(input_record, dict)
            or not isinstance(input_record.get("path"), str)
            or not input_record["path"]
            or not re.fullmatch(r"[0-9a-f]{64}", input_record.get("sha256", ""))):
        return None, None
    if result.get("threshold_met") is not _threshold_test(exact, normalized):
        return None, None
    return normalized, exact


class _ValidationOnlyRis:
    class Error(ValueError):
        pass


def _indeterminate_comparison(reason: str, same_definition=None, previous=None, current=None) -> dict:
    return {
        "status": "indeterminate",
        "decision_impact": "indeterminate",
        "same_definition": same_definition,
        "previous_threshold_met": previous,
        "current_threshold_met": current,
        "value_difference": None,
        "exact_value_difference": None,
        "value_difference_representation": None,
        "value_difference_rounding": None,
        "unit": None,
        "reason": reason,
    }


def compare_results(previous, current) -> dict:
    """Compare two result records only when their complete definitions match."""
    previous_definition, previous_value = _validated_result(previous)
    current_definition, current_value = _validated_result(current)
    if previous_definition is None or current_definition is None:
        return _indeterminate_comparison("one or both metric results are invalid or indeterminate")
    previous_fingerprint = _definition_fingerprint(previous_definition)
    current_fingerprint = _definition_fingerprint(current_definition)
    if previous_fingerprint != current_fingerprint:
        return _indeterminate_comparison("metric definitions differ", same_definition=False)
    difference = current_value - previous_value
    displayed_difference, difference_representation, difference_rounding = _fraction_display(difference)
    difference_fields = {
        "value_difference": displayed_difference,
        "exact_value_difference": _fraction_text(difference),
        "value_difference_representation": difference_representation,
        "value_difference_rounding": difference_rounding,
        "unit": previous_definition["unit"],
    }
    if "threshold" not in previous_definition:
        return {
            "status": "ok", "decision_impact": "no_threshold", "same_definition": True,
            "previous_threshold_met": None, "current_threshold_met": None, "reason": None,
            **difference_fields,
        }
    previous_met = _threshold_test(previous_value, previous_definition)
    current_met = _threshold_test(current_value, current_definition)
    return {
        "status": "ok",
        "decision_impact": "threshold_crossed" if previous_met != current_met else "threshold_unchanged",
        "same_definition": True,
        "previous_threshold_met": previous_met,
        "current_threshold_met": current_met,
        **difference_fields,
        "reason": None,
    }


def _parse_reported(ris, reported) -> tuple[Fraction, str]:
    if isinstance(reported, bool) or not isinstance(reported, (str, int, float, Decimal)):
        raise _error(ris, "reported metric value must be an exact numeric scalar")
    text = str(reported).strip()
    if not text:
        raise _error(ris, "reported metric value must be non-empty")
    match = RATIONAL_RE.fullmatch(text)
    if match:
        denominator = int(match.group(2))
        if denominator == 0:
            raise _error(ris, "reported rational denominator must not be zero")
        value = Fraction(int(match.group(1)), denominator)
        return value, _fraction_text(value)
    decimal_value = _decimal(ris, text, "reported metric value")
    exact = Fraction(decimal_value)
    canonical = _fraction_decimal_if_finite(exact)
    return exact, canonical if canonical is not None else _fraction_text(exact)


def normalize_reported(ris, reported) -> str | None:
    """Return a canonical exact decimal/rational spelling for a reported value."""
    if reported is None:
        return None
    _, canonical = _parse_reported(ris, reported)
    return canonical


def compare_reported(definition, result, reported) -> dict:
    """Compare a reported exact value with a computed result and its threshold."""
    if reported is None:
        try:
            normalized = normalize_definition(_ValidationOnlyRis(), definition)
        except (TypeError, ValueError, AttributeError) as exc:
            return {"reported": None, "reported_status": "indeterminate", "decision_impact": "indeterminate", "reason": str(exc)}
        impact = "no_threshold" if "threshold" not in normalized else "indeterminate"
        reason = None if impact == "no_threshold" else "reported value is absent"
        return {"reported": None, "reported_status": "not_reported", "decision_impact": impact, "reason": reason}
    try:
        normalized = normalize_definition(_ValidationOnlyRis(), definition)
        result_definition, computed = _validated_result(result)
        if result_definition is None:
            raise ValueError("computed metric result is invalid or indeterminate")
        fingerprint = _definition_fingerprint(normalized)
        if fingerprint != _definition_fingerprint(result_definition):
            raise ValueError("computed result uses a different metric definition")
        reported_value, canonical_reported = _parse_reported(_ValidationOnlyRis(), reported)
    except (TypeError, ValueError, AttributeError) as exc:
        return {
            "reported": reported if isinstance(reported, str) else None,
            "reported_status": "indeterminate",
            "decision_impact": "indeterminate",
            "reason": str(exc),
        }
    reported_status = "match" if reported_value == computed else "mismatch"
    if "threshold" not in normalized:
        impact = "no_threshold"
    else:
        computed_met = _threshold_test(computed, normalized)
        reported_met = _threshold_test(reported_value, normalized)
        impact = "threshold_unchanged" if computed_met == reported_met else "threshold_crossed"
    return {
        "reported": canonical_reported,
        "reported_status": reported_status,
        "decision_impact": impact,
        "reason": None,
    }


def load_definition_file(ris, file_path: str):
    """Read and parse one bounded JSON definition file with duplicate-key checks."""
    path = Path(file_path).expanduser()
    file_fd = None
    try:
        file_fd = os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
        stream = os.fdopen(file_fd, "rb")
        file_fd = None
        with stream:
            metadata = os.fstat(stream.fileno())
            if not stat.S_ISREG(metadata.st_mode):
                raise _error(ris, "definition path must identify a regular file")
            if metadata.st_size > MAX_DEFINITION_BYTES:
                raise _error(ris, f"definition exceeds the {MAX_DEFINITION_BYTES}-byte limit")
            chunks = []
            total = 0
            while True:
                chunk = stream.read(min(64 * 1024, MAX_DEFINITION_BYTES + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > MAX_DEFINITION_BYTES:
                    raise _error(ris, f"definition exceeds the {MAX_DEFINITION_BYTES}-byte limit")
            data = b"".join(chunks)
    except OSError as exc:
        raise _error(ris, "unable to read metric definition: " + str(exc)) from exc
    finally:
        if file_fd is not None:
            os.close(file_fd)
    try:
        return _json_load(data.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise _error(ris, "metric definition file is malformed: " + str(exc)) from exc


def _study_definition(ris, root: Path, args):
    if args.revision is None or args.revision < 1:
        raise _error(ris, "--revision must be a positive integer when --study is used")
    if not args.observation or not args.metric:
        raise _error(ris, "--study requires --revision, --observation, and --metric")
    study_module = ris.companion("ris_study")
    snapshot = study_module.read_study(ris, root, args.study, args.revision)
    observations = [item for item in snapshot.get("observations", []) if item.get("id") == args.observation]
    if len(observations) != 1:
        raise _error(ris, "observation ID was not found exactly once in the selected study revision")
    metrics = observations[0].get("metrics", [])
    selected = [item for item in metrics if isinstance(item, dict)
                and isinstance(item.get("definition"), dict)
                and item["definition"].get("id") == args.metric]
    if len(selected) != 1:
        raise _error(ris, "metric ID was not found exactly once on the selected observation")
    capture = selected[0]
    if "result" not in capture or "definition" not in capture:
        raise _error(ris, "selected observation metric capture is incomplete")
    return capture


def add_parser(sub) -> None:
    metric = sub.add_parser("metric", help="calculate declarative evidence metrics")
    actions = metric.add_subparsers(dest="metric_action", required=True)
    run = actions.add_parser("run", help="run one metric against a project-local evidence file")
    source = run.add_mutually_exclusive_group(required=True)
    source.add_argument("--definition", help="JSON metric definition file")
    source.add_argument("--study", help="reuse a metric definition captured in a study")
    run.add_argument("--revision", type=int, help="pinned study revision")
    run.add_argument("--observation", help="observation ID containing the captured metric")
    run.add_argument("--metric", help="captured metric definition ID")
    run.add_argument("--input", required=True, help="exact project-relative CSV or JSONL path")
    run.add_argument("--compare-input", help="compare against a second project-relative input snapshot")


def dispatch(ris, root: Path, args) -> dict:
    if args.command != "metric" or getattr(args, "metric_action", None) != "run":
        raise _error(ris, "unsupported metric command")
    capture = None
    if args.study is not None:
        capture = _study_definition(ris, root, args)
        definition = capture["definition"]
    else:
        if any(value is not None for value in (args.revision, args.observation, args.metric)):
            raise _error(ris, "--revision, --observation, and --metric require --study")
        try:
            definition = load_definition_file(ris, args.definition)
        except getattr(ris, "Error", ValueError) as exc:
            if not str(exc).startswith("metric definition file is malformed:"):
                raise
            output = calculate(ris, root, None, args.input)
            output["reason"] = "invalid metric definition: " + str(exc)
            return output

    current = calculate(ris, root, definition, args.input)
    output = dict(current)
    if capture is not None:
        output["previous_comparison"] = compare_results(capture["result"], current)
    if args.compare_input is not None:
        comparison_input = calculate(ris, root, definition, args.compare_input)
        output["compare_input_result"] = comparison_input
        output["input_comparison"] = compare_results(current, comparison_input)
    return output
