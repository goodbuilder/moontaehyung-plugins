#!/usr/bin/env python3
"""Stable navigation links from RIS project notes to canonical study records."""
from __future__ import annotations

import posixpath
from pathlib import Path, PurePosixPath
import re


STUDY_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
SECTION_BEGIN = "<!-- RIS:STUDY-LINKS:BEGIN -->"
SECTION_END = "<!-- RIS:STUDY-LINKS:END -->"


class _Conflict(Exception):
    pass


def add_parser(sub):
    """Register the view command on the parent RIS parser."""
    parser = sub.add_parser(
        "study-link",
        help="Add durable links to a canonical study decision record",
    )
    parser.add_argument("study_id", help="Stable study ID")
    parser.add_argument(
        "--plan",
        help="Also link this project-relative research plan (otherwise use the active plan)",
    )
    parser.add_argument(
        "--allow-legacy-handoff",
        action="store_true",
        help="Allow appending the study link to an unmanaged schema-v1 root HANDOFF.md",
    )
    return parser


def dispatch(ris, root: Path, args, study):
    """Execute ``study-link``; other commands are left to the parent dispatcher."""
    if getattr(args, "command", None) != "study-link":
        return None

    study_id = _validated_study_id(ris, args.study_id)
    cfg = ris.config(root)
    initial = study.read_study(ris, root, study_id)
    _validate_study(ris, root, cfg, study_id, initial)

    with ris.project_lock(root):
        cfg = ris.config(root)
        current = study.read_study(ris, root, study_id)
        _validate_study(ris, root, cfg, study_id, current)
        if current["revision"] != initial["revision"]:
            raise ris.Error(
                f"Study {study_id} changed from revision {initial['revision']} "
                f"to {current['revision']} while preparing links; rerun study-link"
            )

        canonical = current["path"]
        canonical_path = ris.inside(root, canonical)
        if not canonical_path.is_file():
            raise ris.Error(f"Canonical study note is missing: {canonical}")

        targets, skipped = _targets(ris, root, cfg, args)
        prepared = []
        for target in targets:
            item = _prepare_target(
                ris,
                root,
                cfg,
                target,
                study_id,
                canonical,
                allow_legacy_handoff=getattr(args, "allow_legacy_handoff", False),
            )
            if item is not None:
                prepared.append(item)
            elif target["role"] == "handoff":
                existed = ris.inside(root, target["relative"]).exists()
                skipped.append({
                    "target": target["relative"],
                    "reason": (
                        "legacy root handoff is unmanaged; rerun with --allow-legacy-handoff"
                        if existed else
                        "legacy root handoff is absent; rerun with --allow-legacy-handoff to create it"
                    ),
                })

        # All conflicts and path/ownership checks are resolved before the first write.
        processed = []
        written = []
        changed = []
        try:
            for item in prepared:
                status = _apply_target(ris, item)
                changed.append({"path": item["relative"], "status": status, "href": item["href"]})
                processed.append(item["relative"])
                if status in {"created", "updated"}:
                    written.append(item["relative"])
        except (OSError, ris.NoteConflict, _Conflict) as exc:
            pending = [
                item["relative"] for item in prepared
                if item["relative"] not in processed and item["status"] != "already_linked"
            ]
            return {
                "ok": False,
                "status": "partial" if written else "conflict",
                "study": {"id": study_id, "revision": current["revision"], "path": canonical},
                "updated": changed,
                "pending": pending,
                "skipped": skipped,
                "retryable": True,
                "error": str(exc),
                "message": "Rerun study-link after reviewing the listed conflict; completed links are idempotent.",
            }

        ris.confirm_layout_current(root, cfg)
        statuses = {entry["status"] for entry in changed}
        status = "linked" if statuses & {"created", "updated"} else "already_linked"
        plan = next((target for target in targets if target["role"] == "plan"), None)
        map_link = None if plan is None else {
            "label": f"{study_id} · revision {current['revision']} snapshot",
            "href": _relative_link(ris, plan["relative"], canonical),
        }
        return {
            "status": status,
            "study": {"id": study_id, "revision": current["revision"], "path": canonical},
            "map_node_link": map_link,
            "targets": changed,
            "skipped": skipped,
            "retryable": False,
        }


def _validated_study_id(ris, value):
    if not isinstance(value, str) or not STUDY_ID.fullmatch(value):
        raise ris.Error("Study ID must start with a letter or digit and contain only letters, digits, _ or -")
    return value


def _validate_study(ris, root, cfg, study_id, value):
    required = {"id", "revision", "project_id", "path"}
    if not isinstance(value, dict) or not required.issubset(value):
        raise ris.Error("Study reader returned an incomplete canonical study reference")
    if value["id"] != study_id:
        raise ris.Error("Study reader returned a different study ID")
    if value["project_id"] != cfg["project_id"]:
        raise ris.Error("Study project identity mismatch")
    if not isinstance(value["revision"], (str, int)) or isinstance(value["revision"], bool):
        raise ris.Error("Study reader returned an invalid revision")
    if str(value["revision"]).strip() == "":
        raise ris.Error("Study reader returned an empty revision")
    expected = f"{cfg['research_dir']}/decisions/study-{study_id}.md"
    if value["path"] != expected:
        raise ris.Error(f"Study canonical path must be {expected}")
    try:
        path = ris.inside(root, value["path"])
    except (OSError, ValueError) as exc:
        raise ris.Error(f"Invalid canonical study path: {exc}") from exc
    if not path.is_file():
        raise ris.Error(f"Canonical study note is missing: {value['path']}")


def _active_plan(ris, root, cfg):
    state_path = ris.inside(root, getattr(ris, "STATE_PATH", ".ris/state.json"))
    state_ref = None
    if state_path.is_file():
        state_ref = ris.read_state(root).get("active_plan_ref")
    return (state_ref or cfg.get("active_plan"))


def _targets(ris, root, cfg, args):
    research = cfg["research_dir"]
    targets = [
        {"relative": f"{research}/CONTEXT.md", "role": "context"},
        {"relative": ris.handoff_path(cfg), "role": "handoff"},
    ]
    plan = getattr(args, "plan", None)
    if plan is None:
        plan = _active_plan(ris, root, cfg)
    elif not isinstance(plan, str) or not plan.strip():
        raise ris.Error("--plan must name a project-relative research plan")
    else:
        plan = plan.strip()
    skipped = []
    if plan:
        plan = plan.split("#", 1)[0]
        targets.append({"relative": plan, "role": "plan"})
    else:
        skipped.append({"target": "plan", "reason": "no supplied or active plan"})
    return targets, skipped


def _relative_link(ris, doc_relative, canonical_relative):
    doc = PurePosixPath(doc_relative)
    source = PurePosixPath(canonical_relative)
    start = str(doc.parent) if str(doc.parent) != "." else "."
    href = posixpath.relpath(str(source), start)
    if href.startswith("/") or "\\" in href:
        raise ris.Error("Could not build a portable relative study link")
    # Both endpoints were already checked through RIS's no-symlink boundary.
    # Normalize the navigation target without passing its legitimate `..` segments
    # through `ris.inside`, which deliberately rejects parent traversal inputs.
    linked = posixpath.normpath(posixpath.join(start, href))
    if linked.startswith("../") or linked == ".." or linked != canonical_relative:
        raise ris.Error("Study link does not resolve to the canonical note")
    return href


def _entry(study_id, href):
    start = f"<!-- RIS:STUDY-LINK:BEGIN {study_id} -->"
    end = f"<!-- RIS:STUDY-LINK:END {study_id} -->"
    return f"{start}\n- [{study_id} — canonical study record]({href})\n{end}"


def _section(entry):
    return (
        "## Canonical study records\n\n"
        f"{SECTION_BEGIN}\n"
        f"{entry}\n"
        f"{SECTION_END}"
    )


def _line_ending(text):
    return "\r\n" if "\r\n" in text and text.count("\n") == text.count("\r\n") else "\n"


def _append_block(text, block):
    newline = _line_ending(text)
    block = block.replace("\n", newline)
    if not text:
        return block + newline
    separator = newline if text.endswith(("\n", "\r")) else newline * 2
    return text + separator + block + newline


def _block_positions(text, begin, end, ris, label):
    starts = [match.start() for match in re.finditer(re.escape(begin), text)]
    ends = [match.start() for match in re.finditer(re.escape(end), text)]
    if not starts and not ends:
        return None
    if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
        raise ris.Error(f"Malformed or duplicate {label} markers; review the note before retrying")
    return starts[0], ends[0]


def _prepare_target(ris, root, cfg, target, study_id, canonical, allow_legacy_handoff=False):
    relative, role = target["relative"], target["role"]
    path = ris.inside(root, relative)
    canonical_path = ris.inside(root, canonical)
    if not canonical_path.is_file():
        raise ris.Error(f"Canonical study note is missing: {canonical}")

    if role == "context" or role == "plan":
        if not path.is_file():
            raise ris.Error(f"Required managed {role} note is missing: {relative}")
        if role == "plan":
            plan_root = ris.inside(root, f"{cfg['research_dir']}/plans")
            if not path.is_relative_to(plan_root) or path.suffix != ".md":
                raise ris.Error("--plan must point to a Markdown note under this project's research/plans")
        try:
            data = path.read_bytes()
            text = data.decode("utf-8")
        except UnicodeError as exc:
            raise ris.Error(f"{relative} is not valid UTF-8") from exc
        metadata = ris.frontmatter(text)
        expected_kind = "context" if role == "context" else "plan"
        if metadata.get("project_id") != cfg["project_id"] or metadata.get("kind") != expected_kind:
            raise ris.Error(f"Expected this project's managed {role} note at {relative}")
        return _prepared_doc(ris, relative, path, text, data, study_id, canonical)

    version = cfg["schema_version"]
    if path.exists() and not path.is_file():
        raise ris.Error(f"Handoff path is not a regular file: {relative}")
    if path.is_file():
        try:
            data = path.read_bytes()
            text = data.decode("utf-8")
        except UnicodeError as exc:
            raise ris.Error(f"{relative} is not valid UTF-8") from exc
        metadata = ris.frontmatter(text)
        if metadata.get("project_id") and metadata.get("project_id") != cfg["project_id"]:
            raise ris.Error(f"Handoff belongs to another project: {relative}")
        if version == 1:
            managed = metadata.get("project_id") == cfg["project_id"] and metadata.get("kind") == "handoff"
            has_our_link = f"<!-- RIS:STUDY-LINK:BEGIN {study_id} -->" in text
            if not (managed or has_our_link or allow_legacy_handoff):
                return None
        return _prepared_doc(ris, relative, path, text, data, study_id, canonical)

    if version == 2 or allow_legacy_handoff:
        href = _relative_link(ris, relative, canonical)
        body = _section(_entry(study_id, href))
        content = ris.note(cfg["project_id"], "handoff", "RIS research handoff", body)
        return {
            "relative": relative,
            "role": role,
            "path": path,
            "before": None,
            "after": content.encode("utf-8"),
            "href": href,
            "status": "created",
        }
    return None


def _prepared_doc(ris, relative, path, text, data, study_id, canonical):
    href = _relative_link(ris, relative, canonical)
    entry = _entry(study_id, href)
    item_start = f"<!-- RIS:STUDY-LINK:BEGIN {study_id} -->"
    item_end = f"<!-- RIS:STUDY-LINK:END {study_id} -->"
    item = _block_positions(text, item_start, item_end, ris, f"study link for {study_id}")
    if item is not None:
        block = text[item[0]:item[1] + len(item_end)]
        if f"]({href})" not in block:
            raise ris.Error(f"Existing study link for {study_id} conflicts in {relative}; review it before retrying")
        return {
            "relative": relative,
            "path": path,
            "before": data,
            "after": data,
            "href": href,
            "status": "already_linked",
        }

    # Respect a user-authored exact relative link without inserting a duplicate.
    if f"]({href})" in text:
        return {
            "relative": relative,
            "path": path,
            "before": data,
            "after": data,
            "href": href,
            "status": "already_linked",
        }

    section = _block_positions(text, SECTION_BEGIN, SECTION_END, ris, "study-links section")
    if section is None:
        updated = _append_block(text, _section(entry))
    else:
        end_pos = section[1]
        newline = _line_ending(text)
        prefix, suffix = text[:end_pos], text[end_pos:]
        separator = "" if prefix.endswith(("\n", "\r")) else newline
        updated = prefix + separator + entry.replace("\n", newline) + newline + suffix
    return {
        "relative": relative,
        "path": path,
        "before": data,
        "after": updated.encode("utf-8"),
        "href": href,
        "status": "updated",
    }


def _apply_target(ris, item):
    if item["status"] == "already_linked":
        return "already_linked"
    if item["status"] == "created":
        ris.atomic_note_write(item["path"], item["after"])
        return "created"
    ris.atomic_note_write(item["path"], item["after"], expected=item["before"])
    return "updated"
