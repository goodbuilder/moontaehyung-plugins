"""Opt-in, bounded migration from RIS schema 1 storage to schema 2."""
from __future__ import annotations

import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from urllib.parse import quote, unquote, urlsplit, urlunsplit

MARKER = ".ris/layout-migration.json"
LOCK = ".ris/write.lock"
CONFIG = ".ris/project.yaml"
STATE = ".ris/state.json"
PROPOSALS = ".ris/proposals"
HISTORY = ".ris/history"
OLD_RESEARCH = "research"
NEW_RESEARCH = ".ris/research"
OLD_HANDOFF = "HANDOFF.md"
NEW_HANDOFF = ".ris/HANDOFF.md"
AGENTS = "AGENTS.md"
MAX_ENTRIES = 20000
MAX_TEXT_FILE = 8 * 1024 * 1024
MAX_TEXT_TOTAL = 128 * 1024 * 1024
MD_LINK = re.compile(r"(?P<prefix>!?\[[^\]\n]*\]\()(?P<dest><[^>\n]*>|[^)\s]+)(?P<tail>[^)]*\))")
HTML_LINK = re.compile(r"(?P<prefix>\b(?:href|src)=)(?P<quote>[\"'])(?P<dest>.*?)(?P=quote)", re.I)
HTML_CODE = re.compile(r"<!--.*?-->|<(?:script|style|pre|code)\b[^>]*>.*?</(?:script|style|pre|code)\s*>", re.I | re.S)
HASH = re.compile(r"^[0-9a-f]{64}$")
_RIS_MODULE = None


def _contract():
    global _RIS_MODULE
    if _RIS_MODULE is not None:
        return _RIS_MODULE
    path = Path(__file__).with_name("ris.py")
    spec = importlib.util.spec_from_file_location("_ris_layout_contract", path)
    if spec is None or spec.loader is None:
        raise ValueError("Could not load RIS layout contracts")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _RIS_MODULE = module
    return _RIS_MODULE


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _path(root: Path, relative: str) -> Path:
    """Project-relative path check independent of whether the leaf exists."""
    if not isinstance(relative, str) or not relative or relative.startswith("/") or "\\" in relative or "\x00" in relative:
        raise ValueError(f"Invalid project-relative path: {relative}")
    parts = relative.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError(f"Non-canonical or traversing path: {relative}")
    candidate = root
    for part in parts:
        candidate = candidate / part
        try:
            mode = candidate.lstat().st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            raise ValueError(f"Symlink-managed path is not safe: {relative}")
    if not candidate.resolve(strict=False).is_relative_to(root):
        raise ValueError(f"Path leaves the project: {relative}")
    return candidate


def _bytes(path: Path, relative: str, *, required=True) -> bytes | None:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        if required:
            raise ValueError(f"Required file is missing: {relative}")
        return None
    if not stat.S_ISREG(mode):
        raise ValueError(f"Expected a regular file: {relative}")
    return path.read_bytes()


def _sig(path: Path) -> tuple[int, int, int, int, int]:
    st = path.lstat()
    return (st.st_dev, st.st_ino, stat.S_IMODE(st.st_mode), st.st_size, st.st_mtime_ns)


def _map_ref(ris, cfg: dict, reference: str, *, move_handoff=False) -> str:
    path, marker, anchor = reference.partition("#")
    if move_handoff and path == OLD_HANDOFF:
        path = NEW_HANDOFF
        return path + (marker + anchor if marker else "")
    return ris.research_path({**cfg, "schema_version": 2, "research_dir": NEW_RESEARCH}, reference)


def _link_target(root: Path, old_file: Path, new_file: Path, raw: str, *, move_handoff=False) -> tuple[str, Path | None]:
    """Rebase a local link after moving its containing tree; external URLs stay intact."""
    wrapped = raw.startswith("<") and raw.endswith(">")
    url = raw[1:-1] if wrapped else raw
    parts = urlsplit(url)
    if parts.scheme or parts.netloc or not parts.path:
        return raw, None
    if parts.path.startswith("/") or "\\" in parts.path:
        raise ValueError(f"Absolute local link cannot be preserved: {old_file.relative_to(root)} -> {url}")
    decoded = unquote(parts.path)
    old_target = Path(os.path.normpath(str(old_file.parent / decoded)))
    if not old_target.is_relative_to(root):
        raise ValueError(f"Relative link leaves the project: {old_file.relative_to(root)} -> {url}")
    old_rel = old_target.relative_to(root).as_posix()
    if old_rel:
        _path(root, old_rel)
    if old_target.is_relative_to(root / OLD_RESEARCH):
        new_target = root / NEW_RESEARCH / old_target.relative_to(root / OLD_RESEARCH)
    elif move_handoff and old_target == root / OLD_HANDOFF:
        new_target = root / NEW_HANDOFF
    else:
        new_target = old_target
    old_relative = os.path.relpath(old_target, old_file.parent).replace(os.sep, "/")
    new_relative = os.path.relpath(new_target, new_file.parent).replace(os.sep, "/")
    if old_relative == new_relative:
        return raw, old_target
    rel = os.path.relpath(new_target, new_file.parent).replace(os.sep, "/")
    new_url = urlunsplit((parts.scheme, parts.netloc, quote(rel, safe="/:@-._~!$&'()*+,;="), parts.query, parts.fragment))
    if wrapped:
        new_url = "<" + new_url + ">"
    return new_url, old_target


def _rewrite_text_links(root: Path, old_file: Path, new_file: Path, data: bytes, *, html=False, move_handoff=False):
    try:
        text = data.decode("utf-8")
    except UnicodeError as exc:
        raise ValueError(f"Linked text asset is not UTF-8: {old_file.relative_to(root)}") from exc
    pattern = HTML_LINK if html else MD_LINK
    visible = _visible_text(text, html=html)
    changes = []
    targets = set()
    for match in pattern.finditer(visible):
        raw = match.group("dest")
        replacement, target = _link_target(root, old_file, new_file, raw, move_handoff=move_handoff)
        if target is not None:
            targets.add(target.relative_to(root).as_posix())
        if replacement != raw:
            changes.append((match.start("dest"), match.end("dest"), replacement))
    for start, end, value in reversed(changes):
        text = text[:start] + value + text[end:]
    return text.encode("utf-8"), targets, len(changes)


def _visible_text(text: str, *, html=False) -> str:
    """Mask code examples while preserving offsets for link rewriting."""
    chars = list(text)
    def blank(start: int, end: int):
        for i in range(start, end):
            if chars[i] not in "\r\n":
                chars[i] = " "
    if html:
        for match in HTML_CODE.finditer(text):
            blank(match.start(), match.end())
        return "".join(chars)
    offset = 0
    fence = None
    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", content)
        if fence:
            blank(offset, offset + len(line))
            if marker and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence):
                fence = None
        elif marker:
            blank(offset, offset + len(line))
            fence = marker.group(1)
        offset += len(line)
    active = "".join(chars)
    i = 0
    while i < len(active):
        if active[i] != "`":
            i += 1
            continue
        end = i
        while end < len(active) and active[end] == "`":
            end += 1
        token_len = end - i
        search = end
        close = -1
        while search < len(active):
            found = active.find("`", search)
            if found < 0:
                break
            stop = found
            while stop < len(active) and active[stop] == "`":
                stop += 1
            if stop - found == token_len:
                close = stop
                break
            search = stop
        if close > 0:
            blank(i, close)
            i = close
        else:
            i = end
    return "".join(chars)


def _managed_markdown(ris, data: bytes, relative: str, project_id: str) -> bool:
    metadata = ris.frontmatter(data.decode("utf-8"))
    if metadata.get("project_id") not in (None, project_id):
        raise ValueError(f"Foreign project frontmatter in legacy research: {relative}")
    if relative in ("research/exploration/log.md", "research/exploration/summary.md"):
        return metadata.get("project_id") in (None, project_id)
    if relative == "research/constraints.md" and metadata.get("project_id") in (None, project_id):
        return True
    if metadata.get("project_id") != project_id:
        return False
    if not isinstance(metadata.get("ris_id"), str) or not metadata["ris_id"].strip():
        return relative == "research/constraints.md"
    return True


def _inventory(ris, root: Path, folder: Path, project_id: str, *, move_handoff=False):
    entries, texts, links = [], {}, {}
    total_text = 0
    stack = [folder]
    allowed_top = set(ris.DIRECTORIES.values()) | {"exploration", "INDEX.md", "CONTEXT.md", "constraints.md"}
    while stack:
        parent = stack.pop()
        for child in sorted(os.scandir(parent), key=lambda e: e.name):
            path = Path(child.path)
            st = child.stat(follow_symlinks=False)
            if stat.S_ISLNK(st.st_mode):
                raise ValueError(f"Symlink inside research tree is not safe to move: {path.relative_to(root)}")
            rel_tree = path.relative_to(folder).as_posix()
            rel = f"research/{rel_tree}"
            if "/" not in rel_tree and rel_tree not in allowed_top:
                raise ValueError(f"Unmanaged top-level research asset needs review: {rel}")
            if stat.S_ISDIR(st.st_mode):
                kind = "dir"
                stack.append(path)
            elif stat.S_ISREG(st.st_mode):
                kind = "file"
                if path.suffix.lower() in (".md", ".markdown", ".mdown", ".html", ".htm"):
                    if st.st_size > MAX_TEXT_FILE:
                        raise ValueError(f"Text asset exceeds the bounded migration limit: {rel}")
                    total_text += st.st_size
                    if total_text > MAX_TEXT_TOTAL:
                        raise ValueError("Research text assets exceed the bounded migration limit")
                    data = path.read_bytes()
                    try:
                        data.decode("utf-8")
                    except UnicodeError as exc:
                        raise ValueError(f"Research text asset is not UTF-8: {rel}") from exc
                    texts[rel] = data
            else:
                raise ValueError(f"Special file inside research tree is not safe to move: {rel}")
            entries.append({"path": rel_tree, "kind": kind, "dev": st.st_dev, "ino": st.st_ino,
                            "mode": stat.S_IMODE(st.st_mode), "size": st.st_size, "mtime_ns": st.st_mtime_ns})
            if len(entries) > MAX_ENTRIES:
                raise ValueError("Research tree exceeds the bounded migration entry limit")

    for rel, data in texts.items():
        if not rel.lower().endswith((".md", ".markdown", ".mdown")):
            continue
        if not _managed_markdown(ris, data, rel, project_id):
            raise ValueError(f"Unmanaged Markdown in legacy research needs review: {rel}")

    # Check links and calculate the exact note rewrites before any write. Relative
    # links within research keep their spelling; project-local links are rebased.
    updates, linked, linked_by = [], set(), {}
    for rel, data in texts.items():
        if not rel.lower().endswith((".md", ".markdown", ".mdown", ".html", ".htm")):
            continue
        old_file = root / rel
        new_file = root / NEW_RESEARCH / Path(rel).relative_to(OLD_RESEARCH)
        updated, targets, count = _rewrite_text_links(root, old_file, new_file, data,
                                                       html=rel.lower().endswith((".html", ".htm")),
                                                       move_handoff=move_handoff)
        linked |= targets
        linked_by[rel] = targets
        if updated != data:
            updates.append(_update(rel, NEW_RESEARCH + "/" + Path(rel).relative_to(OLD_RESEARCH).as_posix(),
                                   data, updated, "research-" + hashlib.sha256(rel.encode()).hexdigest()[:12],
                                   tree_member=True, moved_file=False, links=count, signature=_sig(old_file)))
    if "research/constraints.md" in texts and not any(
            target == "research/constraints.md" and source != "research/constraints.md"
            for source, targets in linked_by.items() for target in targets):
        raise ValueError("Optional constraints.md is only safe to move when a managed research note links it")
    for name in ("INDEX.md", "CONTEXT.md"):
        if not (folder / name).is_file():
            raise ValueError(f"Legacy research tree is incomplete: research/{name}")
    for name in ris.DIRECTORIES.values():
        sub = folder / name
        if not sub.is_dir() or sub.is_symlink():
            raise ValueError(f"Legacy research tree is incomplete: research/{name}/")
    if (folder / "exploration").exists() and not (folder / "exploration").is_dir():
        raise ValueError("research/exploration must be a directory")

    # Unknown non-Markdown assets are accepted only when a managed note or a
    # related HTML output links to them. Conventional plan HTML outputs are also
    # recognized by the documented RIS naming convention.
    plan_names = {Path(rel).stem for rel in texts if rel.startswith("research/plans/") and rel.lower().endswith(".md")}
    for rel in texts:
        if not rel.lower().endswith((".html", ".htm")):
            continue
        name = Path(rel).name
        conventional = rel.startswith("research/plans/") and (
            name.endswith("연구 계획.html") or name.endswith("연구 지도.html") or Path(rel).stem in plan_names)
        if rel not in linked and not conventional:
            raise ValueError(f"Unlinked HTML asset is ambiguous; link it from a managed plan or use the RIS output naming: {rel}")
        linked.add(rel)
    for item in entries:
        if item["kind"] != "file":
            continue
        rel = "research/" + item["path"]
        if Path(rel).suffix.lower() in (".md", ".markdown", ".mdown", ".html", ".htm"):
            continue
        if rel not in linked:
            raise ValueError(f"Unlinked research attachment is ambiguous; link it from a managed note: {rel}")
    entries.sort(key=lambda item: item["path"])
    return entries, texts, updates


def _update(source, destination, before, after, label, *, tree_member=False, moved_file=False, links=0, signature=None):
    return {"source": source, "destination": destination, "before": before, "after": after,
            "before_sha256": _sha(before), "after_sha256": _sha(after), "label": label,
            "tree_member": tree_member, "moved_file": moved_file, "links": links, "signature": signature}


def _config_bytes(ris, data: bytes, cfg: dict) -> bytes:
    values = {"schema_version": 2, "research_dir": NEW_RESEARCH}
    if cfg.get("active_plan"):
        values["active_plan"] = _map_ref(ris, cfg, cfg["active_plan"])
    try:
        lines = data.decode("utf-8").splitlines(keepends=True)
    except UnicodeError as exc:
        raise ValueError("Project config is not UTF-8") from exc
    output = []
    found = set()
    for raw in lines:
        line = raw.rstrip("\r\n")
        key, sep, _ = line.partition(":")
        if sep and key in values:
            found.add(key)
            newline = "\r\n" if raw.endswith("\r\n") else "\n" if raw.endswith("\n") else ""
            output.append(f"{key}: {json.dumps(values[key], ensure_ascii=False)}{newline}")
        else:
            output.append(raw)
    if not {"schema_version", "research_dir"}.issubset(found):
        raise ValueError("Project config is missing migration fields")
    return "".join(output).encode("utf-8")


def _state_bytes(ris, root: Path, data: bytes, cfg: dict, *, move_handoff=False) -> tuple[bytes, int]:
    try:
        state = json.loads(data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Orchestration state is not valid UTF-8 JSON") from exc
    ris.validate_state(root, state)
    refs = []
    for key in ("goal_ref", "active_plan_ref"):
        if key in state and state[key]:
            refs.append(state[key])
            state[key] = _map_ref(ris, cfg, state[key], move_handoff=move_handoff)
    for ref in state.get("pending_user_decisions", []):
        refs.append(ref)
    state["pending_user_decisions"] = [_map_ref(ris, cfg, r, move_handoff=move_handoff) for r in state.get("pending_user_decisions", [])]
    for item in state.get("blocked_items", []):
        refs.append(item["ref"])
        item["ref"] = _map_ref(ris, cfg, item["ref"], move_handoff=move_handoff)
    for task in state.get("tasks", []):
        if task.get("question_ref"):
            refs.append(task["question_ref"])
            task["question_ref"] = _map_ref(ris, cfg, task["question_ref"], move_handoff=move_handoff)
        refs.extend(task.get("artifact_refs", []))
        task["artifact_refs"] = [_map_ref(ris, cfg, r, move_handoff=move_handoff) for r in task.get("artifact_refs", [])]
    return (json.dumps(state, ensure_ascii=False, indent=2) + "\n").encode("utf-8"), len(refs) + 1


def _proposal_bytes(ris, root: Path, data: bytes, cfg: dict, relative: str) -> tuple[bytes, int]:
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Proposal is not valid UTF-8 JSON: {relative}") from exc
    required = {"schema_version", "project_id", "target", "base_sha256", "created", "proposed_body", "status", "original_unchanged"}
    if not isinstance(value, dict) or set(value) != required or value.get("schema_version") != 1:
        raise ValueError(f"Proposal is incomplete or incompatible: {relative}")
    if value.get("project_id") != cfg["project_id"] or value.get("status") != "proposed" or value.get("original_unchanged") is not True:
        raise ValueError(f"Proposal identity or status is invalid: {relative}")
    if not isinstance(value.get("target"), str) or not value["target"].startswith("research/") or "#" in value["target"]:
        raise ValueError(f"Proposal target is not a legacy research note: {relative}")
    if not isinstance(value.get("base_sha256"), str) or not HASH.fullmatch(value["base_sha256"]) or not isinstance(value.get("proposed_body"), str):
        raise ValueError(f"Proposal metadata is invalid: {relative}")
    target = _path(root, value["target"])
    if not target.is_file() or target.suffix.lower() != ".md":
        raise ValueError(f"Proposal target is missing or not Markdown: {relative}")
    if ris.frontmatter(target.read_text(encoding="utf-8")).get("project_id") != cfg["project_id"]:
        raise ValueError(f"Proposal target identity mismatch: {relative}")
    value["target"] = _map_ref(ris, cfg, value["target"])
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"), 1


def _hook_update(ris, root: Path):
    path = _path(root, AGENTS)
    data = _bytes(path, AGENTS, required=False)
    if data is None:
        return None
    start, end = ris.START.encode(), ris.END.encode()
    if not start in data and not end in data:
        return None
    if data.count(start) != 1 or data.count(end) != 1:
        raise ValueError("Malformed RIS managed block in AGENTS.md")
    a, b = data.index(start), data.index(end) + len(end)
    block = data[a:b]
    old = ris.hook("research", "HANDOFF.md").strip().encode("utf-8")
    new = ris.hook(NEW_RESEARCH, NEW_HANDOFF).strip().encode("utf-8")
    norm = block.replace(b"\r\n", b"\n").replace(b"\r", b"\n").strip()
    if norm == new:
        return None
    if norm != old:
        raise ValueError("RIS managed block in AGENTS.md is not the known legacy hook")
    # Keep user bytes outside the managed block exact and install the canonical v2 hook.
    newline = b"\r\n" if b"\r\n" in block else b"\n"
    replacement = new.replace(b"\n", newline)
    return _update(AGENTS, AGENTS, data, data[:a] + replacement + data[b:], "AGENTS",
                   links=2, signature=_sig(path))


def _handoff_update(ris, root: Path, data: bytes, project_id: str, *, include_handoff=False):
    old_file, new_file = root / OLD_HANDOFF, root / NEW_HANDOFF
    try:
        text = data.decode("utf-8")
    except UnicodeError as exc:
        raise ValueError("Root HANDOFF.md is not UTF-8") from exc
    research_ref = False
    for match in MD_LINK.finditer(_visible_text(text)):
        raw = match.group("dest")
        url = raw[1:-1] if raw.startswith("<") and raw.endswith(">") else raw
        parts = urlsplit(url)
        if parts.scheme or parts.netloc or not parts.path or parts.path.startswith("/"):
            continue
        target = Path(os.path.normpath(str(old_file.parent / unquote(parts.path))))
        if target.is_relative_to(root / OLD_RESEARCH):
            research_ref = True
            break
    metadata = ris.frontmatter(text)
    owned = metadata.get("project_id") == project_id and metadata.get("kind") == "handoff"
    if owned or include_handoff:
        if new_file.exists() or new_file.is_symlink():
            raise ValueError("Migration destination collision: .ris/HANDOFF.md already exists")
        updated, _, count = _rewrite_text_links(root, old_file, new_file, data, move_handoff=True)
        return _update(OLD_HANDOFF, NEW_HANDOFF, data, updated, "HANDOFF", moved_file=True,
                       links=count, signature=_sig(old_file))
    if not research_ref:
        return None
    # A team-owned root handoff stays where it is. Update only concrete relative
    # targets to the moved research tree, with an exact preimage in history.
    updated, _, count = _rewrite_text_links(root, old_file, old_file, data)
    if updated == data:
        return None
    return _update(OLD_HANDOFF, OLD_HANDOFF, data, updated, "HANDOFF-links", links=count,
                   signature=_sig(old_file))


def _backup_path(update: dict) -> str:
    suffix = Path(update["source"]).suffix or ".bin"
    return f"{HISTORY}/layout-{update['label']}-{update['before_sha256']}{suffix}"


def _scan(root: Path, *, include_handoff=False) -> dict:
    ris = _contract()
    marker = _path(root, MARKER)
    if marker.exists():
        raise ValueError(f"Migration marker exists; use migrate-layout --apply to recover: {MARKER}")
    cfg = ris.config(root)
    if cfg["schema_version"] == 2:
        # Do not inspect legacy names after v2 is authoritative. They may be user data.
        research = _path(root, NEW_RESEARCH)
        if not research.is_dir():
            raise ValueError("Schema 2 config points to a missing .ris/research directory")
        handoff = _path(root, NEW_HANDOFF)
        if handoff.exists() and not handoff.is_file():
            raise ValueError("Schema 2 .ris/HANDOFF.md is not a regular file")
        return {"status": "already_current", "project_id": cfg["project_id"], "changes": [],
                "limitations": [], "_root": root, "_updates": []}
    if cfg["schema_version"] != 1 or cfg["research_dir"] != OLD_RESEARCH:
        raise ValueError("Only schema 1 projects using research/ can be migrated")
    reserved_handoff = _path(root, NEW_HANDOFF)
    if reserved_handoff.exists():
        raise ValueError("Migration destination collision: .ris/HANDOFF.md already exists")
    source = _path(root, OLD_RESEARCH)
    dest = _path(root, NEW_RESEARCH)
    if not source.is_dir():
        raise ValueError("Legacy research/ is missing or is not a real directory")
    if dest.exists():
        raise ValueError("Migration destination collision: .ris/research already exists")
    old_handoff_path = _path(root, OLD_HANDOFF)
    handoff_data = _bytes(old_handoff_path, OLD_HANDOFF, required=False)
    handoff_update = _handoff_update(ris, root, handoff_data, cfg["project_id"],
                                     include_handoff=include_handoff) if handoff_data is not None else None
    moved_handoff = bool(handoff_update and handoff_update["moved_file"])
    entries, texts, updates = _inventory(ris, root, source, cfg["project_id"],
                                         move_handoff=moved_handoff)
    old_cfg = _bytes(_path(root, CONFIG), CONFIG)
    new_cfg = _config_bytes(ris, old_cfg, cfg)
    cfg_refs = int(bool(cfg.get("active_plan")))
    if cfg.get("active_plan"):
        active = ris.inside(root, cfg["active_plan"])
        meta = ris.frontmatter(active.read_text(encoding="utf-8"))
        if meta.get("project_id") != cfg["project_id"] or meta.get("kind") != "plan":
            raise ValueError("active_plan must identify this project's managed plan")
    updates.append(_update(CONFIG, CONFIG, old_cfg, new_cfg, "project", links=cfg_refs, signature=_sig(root / CONFIG)))
    changes = [{"move": OLD_RESEARCH, "to": NEW_RESEARCH, "entries": len(entries),
                "notes_relinked": sum(u["tree_member"] for u in updates)}]

    state_path = _path(root, STATE)
    state_data = _bytes(state_path, STATE, required=False)
    if state_data is not None:
        state_after, refs = _state_bytes(ris, root, state_data, cfg, move_handoff=moved_handoff)
        updates.append(_update(STATE, STATE, state_data, state_after, "state", links=refs, signature=_sig(state_path)))
        changes.append({"update": STATE, "references": refs})
    proposals = _path(root, PROPOSALS)
    if proposals.exists():
        if not proposals.is_dir():
            raise ValueError(".ris/proposals must be a directory")
        for p in sorted(proposals.iterdir()):
            if p.is_symlink():
                raise ValueError(f"Symlink in proposals is not safe to migrate: {p.relative_to(root)}")
            if not p.is_file() or p.suffix.lower() != ".json":
                continue
            rel = p.relative_to(root).as_posix()
            before = _bytes(p, rel)
            after, refs = _proposal_bytes(ris, root, before, cfg, rel)
            updates.append(_update(rel, rel, before, after, "proposal-" + p.stem, links=refs, signature=_sig(p)))
            changes.append({"update": rel, "references": refs})

    agents = _hook_update(ris, root)
    if agents:
        updates.append(agents)
        changes.append({"update": AGENTS, "scope": "canonical v2 RIS block only"})
    if handoff_update:
        updates.append(handoff_update)
        if handoff_update["moved_file"]:
            changes.append({"move": OLD_HANDOFF, "to": NEW_HANDOFF, "links_rebased": handoff_update["links"]})
        else:
            changes.append({"update": OLD_HANDOFF, "scope": "relative RIS research links only", "links_rebased": handoff_update["links"]})
    elif handoff_data is not None:
        changes.append({"preserve": OLD_HANDOFF, "reason": "no verified RIS-owned handoff link into legacy research/"})

    history = _path(root, HISTORY)
    if history.exists() and not history.is_dir():
        raise ValueError(".ris/history must be a directory")
    for update in updates:
        update["backup"] = _backup_path(update)
        backup = _path(root, update["backup"])
        existing = _bytes(backup, update["backup"], required=False)
        if existing is not None and existing != update["before"]:
            raise ValueError(f"History destination collision: {update['backup']}")
    limits = [
        "Only config, state, proposals, the known RIS hook, and root HANDOFF links into research/ are migrated; other user-managed files were not searched for inbound links.",
        "Inline Markdown links and HTML href/src links in the moved tree are rebased. Wiki links, raw path mentions, embedded scripts, and links in non-RIS files are outside this bounded scan.",
        "Unmanaged/foreign Markdown and unlinked research attachments are refused. Linked attachments and recognized plan HTML move with their tree; exact preimages are saved in .ris/history.",
        "Proposal base_sha256 values are preserved as historical preimages; a target whose links are rebased may therefore leave its proposal stale, which remains explicit.",
    ]
    if not any(u["source"] == AGENTS for u in updates):
        limits.append("AGENTS.md had no known legacy RIS block; it was left untouched.")
    if not moved_handoff:
        limits.append("A root HANDOFF.md without explicit RIS ownership stays at its original path; only links into research/ are rebased in place, with the exact original in history. Pass --include-handoff to move it explicitly.")
    return {"status": "preview", "project_id": cfg["project_id"],
            "from": {"schema_version": 1, "research_dir": OLD_RESEARCH},
            "to": {"schema_version": 2, "research_dir": NEW_RESEARCH},
            "changes": changes, "limitations": limits, "_root": root,
            "_entries": entries, "_updates": updates, "_moved_handoff": moved_handoff}


def _marker_data(plan: dict, phase: str) -> dict:
    return {"version": 1, "phase": phase, "project_id": plan["project_id"],
            "tree_source": OLD_RESEARCH, "tree_destination": NEW_RESEARCH,
            "move_handoff": bool(plan.get("_moved_handoff")),
            "files": [{k: u[k] for k in ("source", "destination", "backup", "before_sha256", "after_sha256", "tree_member", "moved_file")}
                      for u in plan.get("_updates", [])]}


def _atomic_write(path: Path, data: bytes, mode: int | None = None):
    for parent in path.parents:
        if parent.is_symlink():
            raise ValueError(f"Refusing to write through a symlink: {parent}")
    if path.exists() or path.is_symlink():
        st = path.lstat()
        if not stat.S_ISREG(st.st_mode):
            raise ValueError(f"Refusing to replace an unsafe file: {path}")
        mode = stat.S_IMODE(st.st_mode) if mode is None else mode
    else:
        mode = 0o600 if mode is None else mode
    fd, name = tempfile.mkstemp(prefix="." + path.name + ".layout-", dir=path.parent)
    temp = Path(name)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
        dfd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


def _write_new(path: Path, data: bytes):
    fd, name = tempfile.mkstemp(prefix="." + path.name + ".new-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path, follow_symlinks=False)
        dfd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _write_marker(root: Path, marker: dict):
    path = root / MARKER
    data = (json.dumps(marker, ensure_ascii=False, indent=2) + "\n").encode()
    if path.exists():
        _atomic_write(path, data, 0o600)
    else:
        _write_new(path, data)
    dfd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


def _read_marker(root: Path):
    data = _bytes(_path(root, MARKER), MARKER, required=False)
    if data is None:
        return None
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Migration marker is corrupt; manual inspection is required") from exc
    if not isinstance(value, dict) or set(value) != {"version", "phase", "project_id", "tree_source", "tree_destination", "move_handoff", "files"}:
        raise ValueError("Migration marker has an unsupported shape")
    if (type(value["version"]) is not int or value["version"] != 1 or
            not isinstance(value["phase"], str) or value["phase"] not in {"preparing", "applying", "committed", "recovery_required"}):
        raise ValueError("Migration marker has an unsupported version or phase")
    if (not isinstance(value["project_id"], str) or not value["project_id"].strip() or
            type(value["move_handoff"]) is not bool or value["tree_source"] != OLD_RESEARCH or
            value["tree_destination"] != NEW_RESEARCH or not isinstance(value["files"], list)):
        raise ValueError("Migration marker has unsupported paths")
    allowed = {CONFIG, STATE, AGENTS, OLD_HANDOFF}
    seen, has_config, has_moved_handoff = set(), False, False
    for entry in value["files"]:
        if not isinstance(entry, dict) or set(entry) != {"source", "destination", "backup", "before_sha256", "after_sha256", "tree_member", "moved_file"}:
            raise ValueError("Migration marker has an invalid file record")
        src, dst, backup = entry["source"], entry["destination"], entry["backup"]
        _path(root, src); _path(root, dst); _path(root, backup)
        if not all(isinstance(entry[k], str) for k in ("source", "destination", "backup", "before_sha256", "after_sha256")):
            raise ValueError("Migration marker contains a non-string path or digest")
        if type(entry["tree_member"]) is not bool or type(entry["moved_file"]) is not bool or src in seen:
            raise ValueError("Migration marker contains invalid flags or duplicate source paths")
        seen.add(src)
        proposal = len(Path(src).parts) == 3 and src.startswith(PROPOSALS + "/") and src.endswith(".json") and dst == src
        tree_file = src.startswith(OLD_RESEARCH + "/") and dst == NEW_RESEARCH + src[len(OLD_RESEARCH):]
        handoff = src == OLD_HANDOFF and dst == NEW_HANDOFF and entry["moved_file"] is True
        direct = src == dst and src in allowed
        if not (proposal or tree_file or handoff or direct):
            raise ValueError("Migration marker references a path outside the known RIS-owned set")
        suffix = Path(src).suffix or ".bin"
        if (Path(backup).parent.as_posix() != HISTORY or not Path(backup).name.startswith("layout-") or
                not Path(backup).name.endswith("-" + entry["before_sha256"] + suffix) or
                not HASH.fullmatch(entry["before_sha256"]) or not HASH.fullmatch(entry["after_sha256"])):
            raise ValueError("Migration marker has an invalid preimage record")
        if tree_file != bool(entry["tree_member"]) or (handoff != bool(entry["moved_file"])):
            raise ValueError("Migration marker ownership flags do not match the paths")
        has_config |= src == CONFIG
        has_moved_handoff |= handoff
    if not has_config or value["move_handoff"] != has_moved_handoff:
        raise ValueError("Migration marker is missing its config record or handoff identity")
    return value


def _raw_config(root: Path) -> dict:
    data = _bytes(root / CONFIG, CONFIG)
    values = {}
    try:
        lines = data.decode("utf-8").splitlines()
    except UnicodeError as exc:
        raise ValueError("Project config is not UTF-8 during migration recovery") from exc
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, raw = line.partition(":")
        if sep and key in ("schema_version", "research_dir", "project_id"):
            if key in values:
                raise ValueError("Duplicate recovery config field: " + key)
            try:
                values[key] = json.loads(raw.strip())
            except json.JSONDecodeError as exc:
                raise ValueError("Invalid recovery config field: " + key) from exc
    if set(values) != {"schema_version", "research_dir", "project_id"}:
        raise ValueError("Project config is incomplete during migration recovery")
    return values


def _lock(root: Path):
    path = _path(root, LOCK)
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise ValueError(".ris/write.lock must be a regular file")
    fcntl.flock(fd, fcntl.LOCK_EX)
    return fd


def _verify_preimages(root: Path, plan: dict):
    for update in plan["_updates"]:
        path = root / update["source"]
        if _bytes(path, update["source"]) != update["before"] or _sig(path) != update["signature"]:
            raise ValueError(f"Concurrent edit detected before migration: {update['source']}")
    if not _tree_same(root / OLD_RESEARCH, plan["_entries"]):
        raise ValueError("Research tree changed during migration preflight")


def _tree_snapshot(folder: Path) -> list[dict] | None:
    try:
        actual = []
        stack = [folder]
        while stack:
            parent = stack.pop()
            for child in sorted(os.scandir(parent), key=lambda e: e.name):
                path = Path(child.path); st = child.stat(follow_symlinks=False)
                if stat.S_ISLNK(st.st_mode):
                    return None
                if stat.S_ISDIR(st.st_mode):
                    kind = "dir"; stack.append(path)
                elif stat.S_ISREG(st.st_mode):
                    kind = "file"
                else:
                    return None
                actual.append({"path": path.relative_to(folder).as_posix(), "kind": kind, "dev": st.st_dev,
                               "ino": st.st_ino, "mode": stat.S_IMODE(st.st_mode), "size": st.st_size,
                               "mtime_ns": st.st_mtime_ns})
        return sorted(actual, key=lambda item: item["path"])
    except OSError:
        return None


def _tree_same(folder: Path, expected: list[dict]) -> bool:
    return _tree_snapshot(folder) == expected


def _backups(root: Path, plan: dict):
    history = _path(root, HISTORY)
    if not history.exists():
        history.mkdir()
    if not history.is_dir() or history.is_symlink():
        raise ValueError(".ris/history must be a real directory")
    _verify_preimages(root, plan)
    for update in plan["_updates"]:
        target = root / update["backup"]
        old = _bytes(target, update["backup"], required=False)
        if old is None:
            _write_new(target, update["before"])
        elif old != update["before"]:
            raise ValueError(f"History destination collision: {update['backup']}")


def _apply(root: Path, plan: dict):
    _verify_preimages(root, plan)
    if (root / NEW_RESEARCH).exists():
        raise ValueError("Migration destination appeared during apply")
    os.rename(root / OLD_RESEARCH, root / NEW_RESEARCH)
    if plan["_moved_handoff"]:
        handoff = next(u for u in plan["_updates"] if u["source"] == OLD_HANDOFF)
        _verify_file(root, handoff, handoff["source"])
        if (root / NEW_HANDOFF).exists():
            raise ValueError(".ris/HANDOFF.md appeared during apply")
        os.rename(root / OLD_HANDOFF, root / NEW_HANDOFF)
    for update in plan["_updates"]:
        if update["source"] == CONFIG:
            continue
        if update["moved_file"]:
            current_path = root / update["destination"]
            if not current_path.exists():
                raise ValueError("Handoff disappeared during migration")
        elif update["tree_member"]:
            current_path = root / update["destination"]
        else:
            current_path = root / update["source"]
        if _bytes(current_path, str(current_path.relative_to(root))) != update["before"]:
            raise ValueError(f"Concurrent edit detected during migration: {update['source']}")
        if update["after"] != update["before"]:
            _atomic_write(current_path, update["after"], update["signature"][2])
    _verify_tree_after(root, plan)
    cfg_update = next(u for u in plan["_updates"] if u["source"] == CONFIG)
    _verify_file(root, cfg_update, CONFIG)
    for update in plan["_updates"]:
        if update["source"] == CONFIG or update["tree_member"]:
            continue
        target = root / update["destination"]
        if _sha(_bytes(target, update["destination"])) != update["after_sha256"]:
            raise ValueError(f"Migration artifact verification failed: {update['destination']}")
    _atomic_write(root / CONFIG, cfg_update["after"], cfg_update["signature"][2])
    if _bytes(root / CONFIG, CONFIG) != cfg_update["after"]:
        raise ValueError("Config commit verification failed")


def _verify_file(root: Path, update: dict, rel: str):
    path = root / rel
    if _bytes(path, rel) != update["before"] or _sig(path) != update["signature"]:
        raise ValueError(f"Concurrent edit detected during migration: {rel}")


def _verify_tree_after(root: Path, plan: dict):
    folder = root / NEW_RESEARCH
    actual = _tree_snapshot(folder)
    if actual is None:
        raise ValueError("Research assets changed while the storage tree was moved")
    expected = {item["path"]: item for item in plan["_entries"]}
    current = {item["path"]: item for item in actual}
    rewritten = {Path(u["destination"]).relative_to(NEW_RESEARCH).as_posix(): u
                 for u in plan["_updates"] if u["tree_member"]}
    rewritten_dirs = set()
    for rel in rewritten:
        parent = Path(rel).parent
        while str(parent) != ".":
            rewritten_dirs.add(parent.as_posix())
            parent = parent.parent
    if expected.keys() != current.keys():
        raise ValueError("Research assets changed while the storage tree was moved")
    for rel, before in expected.items():
        after = current[rel]
        update = rewritten.get(rel)
        if update:
            if before["kind"] != after["kind"] or before["mode"] != after["mode"] or after["size"] != len(update["after"]):
                raise ValueError(f"Research note metadata changed while migrating: {rel}")
        elif rel in rewritten_dirs:
            if (before["kind"], before["dev"], before["ino"], before["mode"], before["size"]) != (
                    after["kind"], after["dev"], after["ino"], after["mode"], after["size"]):
                raise ValueError(f"Research directory identity changed while migrating: {rel}")
        elif before != after:
            raise ValueError(f"Research asset changed while migrating: {rel}")
    # Tree member link rewrites are the only intended byte changes.
    for update in plan["_updates"]:
        if not update["tree_member"]:
            continue
        path = root / update["destination"]
        if _sha(_bytes(path, update["destination"])) != update["after_sha256"]:
            raise ValueError(f"Research note link verification failed: {update['destination']}")


def _restore(root: Path, entry: dict):
    src, dst = root / entry["source"], root / entry["destination"]
    if entry["tree_member"]:
        if (root / NEW_RESEARCH).is_dir():
            target = dst
        elif (root / OLD_RESEARCH).is_dir():
            target = src
        else:
            raise ValueError("Research tree is missing during recovery")
    elif entry["moved_file"]:
        src_exists, dst_exists = src.exists() or src.is_symlink(), dst.exists() or dst.is_symlink()
        if src_exists and dst_exists:
            raise ValueError("Both HANDOFF.md paths exist during recovery")
        target = dst if dst_exists else src
    else:
        target = src
    current = _bytes(target, str(target.relative_to(root)), required=False)
    if current is None or _sha(current) not in (entry["before_sha256"], entry["after_sha256"]):
        raise ValueError(f"Concurrent edit makes recovery ambiguous: {target.relative_to(root)}")
    if entry["moved_file"] and target == dst:
        os.rename(dst, src)
        target = src
    if _sha(current) != entry["before_sha256"]:
        before = _bytes(root / entry["backup"], entry["backup"])
        if _sha(before) != entry["before_sha256"]:
            raise ValueError(f"Recovery preimage is missing or corrupt: {entry['backup']}")
        _atomic_write(target, before)


def _recover(root: Path, marker: dict):
    if marker["phase"] == "preparing":
        # No filesystem change is made until the marker advances to applying.
        (root / MARKER).unlink()
        return
    if marker["phase"] == "committed":
        cfg = _raw_config(root)
        config_record = next(entry for entry in marker["files"] if entry["source"] == CONFIG)
        data = _bytes(root / CONFIG, CONFIG)
        if _sha(data) != config_record["after_sha256"]:
            raise ValueError("Committed migration config hash disagrees with marker")
        if cfg["schema_version"] != 2 or cfg["research_dir"] != NEW_RESEARCH or not (root / NEW_RESEARCH).is_dir():
            raise ValueError("Committed marker disagrees with migrated project state")
        for entry in marker["files"]:
            target = root / entry["destination"]
            if _sha(_bytes(target, entry["destination"])) != entry["after_sha256"]:
                raise ValueError(f"Committed artifact disagrees with marker: {entry['destination']}")
        (root / MARKER).unlink()
        return
    failures = []
    for entry in reversed(marker["files"]):
        try:
            _restore(root, entry)
        except (OSError, ValueError) as exc:
            failures.append(str(exc))
    src, dst = root / OLD_RESEARCH, root / NEW_RESEARCH
    if src.exists() and dst.exists():
        failures.append("Both research tree paths exist during recovery")
    elif dst.exists():
        try:
            os.rename(dst, src)
        except OSError as exc:
            failures.append("Could not restore research/: " + str(exc))
    elif not src.is_dir():
        failures.append("Research tree is missing from both paths during recovery")
    if failures:
        marker["phase"] = "recovery_required"
        _write_marker(root, marker)
        raise ValueError("Interrupted migration needs recovery: " + "; ".join(failures))
    (root / MARKER).unlink()


def _public(plan: dict, status: str | None = None):
    result = {k: v for k, v in plan.items() if not k.startswith("_")}
    if status:
        result["status"] = status
    return result


def _run(root: Path, *, include_handoff=False):
    marker = _read_marker(root)
    if marker:
        cfg_bytes = _bytes(root / CONFIG, CONFIG)
        cfg = _raw_config(root)
        if marker["project_id"] != cfg["project_id"]:
            raise ValueError("Migration marker project identity mismatch")
        config_record = next(entry for entry in marker["files"] if entry["source"] == CONFIG)
        if _sha(cfg_bytes) not in (config_record["before_sha256"], config_record["after_sha256"]):
            raise ValueError("Project config changed outside the interrupted migration; recovery is ambiguous")
        if marker["phase"] == "committed" and _sha(cfg_bytes) != config_record["after_sha256"]:
            raise ValueError("Committed migration config hash disagrees with marker")
        _recover(root, marker)
    plan = _scan(root, include_handoff=include_handoff)
    if plan["status"] == "already_current":
        return _public(plan)
    marker = _marker_data(plan, "preparing")
    _write_marker(root, marker)
    try:
        _backups(root, plan)
        marker["phase"] = "applying"
        _write_marker(root, marker)
        _apply(root, plan)
        marker["phase"] = "committed"
        _write_marker(root, marker)
        (root / MARKER).unlink()
        return _public(plan, "migrated")
    except BaseException as original:
        try:
            current = _read_marker(root)
            if current:
                _recover(root, current)
        except BaseException as recovery:
            marker["phase"] = "recovery_required"
            try:
                _write_marker(root, marker)
            except BaseException:
                pass
            if isinstance(original, (KeyboardInterrupt, SystemExit)):
                raise
            raise ValueError(f"Migration failed and recovery needs attention: {recovery}") from original
        if isinstance(original, (KeyboardInterrupt, SystemExit)):
            raise
        raise


def migrate_layout(root: Path, *, apply: bool = False, include_handoff: bool = False) -> dict:
    """Preview by default; apply only when explicitly requested."""
    try:
        root = Path(root).expanduser()
        if not root.is_dir():
            raise ValueError("Project directory must already exist")
        root = root.resolve(strict=True)
        if not apply:
            return _public(_scan(root, include_handoff=include_handoff))
        if not _path(root, CONFIG).is_file():
            raise ValueError("An existing RIS project config is required for migration")
        lock = _path(root, LOCK)
        fd = os.open(lock, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ValueError(".ris/write.lock must be a regular file")
            fcntl.flock(fd, fcntl.LOCK_EX)
            return _run(root, include_handoff=include_handoff)
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
    except Exception as exc:
        ris = _RIS_MODULE
        error_type = getattr(ris, "Error", None) if ris is not None else None
        if error_type is not None and isinstance(exc, error_type):
            raise ValueError(str(exc)) from exc
        raise
