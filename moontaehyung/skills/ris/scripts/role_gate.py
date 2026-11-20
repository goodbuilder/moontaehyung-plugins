#!/usr/bin/env python3
"""Shared RIS role-gate judge. Standard library only.

Decides whether a RIS run may be COMPLETE: every required role was actually called, returned a
result for its own assignment (token + input hash), and the delivered canon/HTML versions match.
Used by the CLI (`ris.py gate ...`), by Codex/Claude hooks, and by `ris.py state update`.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import sys
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ris  # noqa: E402

Error = ris.Error
GATE_DIR = '.ris/role-gate'
PROFILES = {
    'research-map': [
        ('RG-RESEARCH', 'researcher', []),
        ('RG-PLAN', 'planner', ['RG-RESEARCH']),
        ('RG-DESIGN', 'designer', ['RG-PLAN']),
        ('RG-VERIFY', 'engineer', ['RG-DESIGN']),
        ('RG-AUDIT', 'auditor', ['RG-VERIFY']),
    ]
}
AGENT_TOOLS = {'Agent', 'Task', 'spawn_agent'}
MAX_REPEAT = 2
RESULT_RE = re.compile(r'RIS_RESULT\s*(\{.*\})', re.S)
ASSIGN_RE = re.compile(r'RIS_ASSIGN\s+run=([A-Za-z0-9._-]+)\s+task=([A-Z0-9-]+)\s+token=([0-9a-f]+)\s+input_hash=([0-9a-f]+)')


def profile_of(root: Path):
    try: cfg = ris.config(root)
    except Error: return None
    value = cfg.get('role_gate_profile')
    if value is None: return None
    if value not in PROFILES: raise Error(f'Unknown role_gate_profile: {value}')
    return value


def run_path(root: Path, run_id: str) -> Path:
    if not re.fullmatch(r'[A-Za-z0-9._-]+', run_id): raise Error('Unsafe run id')
    return ris.inside(root, f'{GATE_DIR}/{run_id}.json')


def load(root: Path, run_id: str):
    p = run_path(root, run_id)
    return json.loads(p.read_text(encoding='utf-8')) if p.is_file() else None


def save(root: Path, run: dict):
    """Atomic replace; callers hold the project lock."""
    folder = ris.inside(root, GATE_DIR); folder.mkdir(parents=True, exist_ok=True)
    p = run_path(root, run['run_id']); tmp = p.with_suffix('.tmp')
    tmp.write_text(json.dumps(run, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with tmp.open('rb') as f: os.fsync(f.fileno())
    os.replace(tmp, p)


def file_sha(root: Path, ref):
    try: return ris.sha(ris.inside(root, ref).read_bytes())
    except (Error, OSError, TypeError): return None


def active_run_id(root: Path):
    """The run id of the current orchestration state when it has a gate record."""
    try: rid = ris.read_state(root)['run_id']
    except Error: return None
    return rid if run_path(root, rid).is_file() else None


TASK_TYPE = {'researcher': 'research', 'planner': 'planning', 'designer': 'coordination',
             'engineer': 'verification', 'auditor': 'audit'}
STATE_STATUS = {'PENDING': 'PENDING', 'ASSIGNED': 'IN_PROGRESS', 'PASS': 'PASS', 'FAIL': 'FAIL'}


def sync_state(root: Path):
    """Mirror gate tasks into .ris/state.json (task list and status live there). Call outside the lock."""
    snap = ris.read_state_snapshot(root)
    value = snap['state']; rid = value['run_id']; run = load(root, rid)
    if run is None: return
    wanted = {}
    for tid, t in run['tasks'].items():
        art = (t['result'] or {}).get('artifacts', {}) if t['status'] == 'PASS' else {}
        refs = [art[k] for k in ('canon_ref', 'html_ref') if file_sha(root, art.get(k)) is not None]
        wanted[tid] = {'id': tid, 'type': TASK_TYPE[t['role']], 'owner': t['role'], 'status': STATE_STATUS[t['status']],
                       'depends_on': list(t['depends_on']), 'artifact_refs': refs,
                       'audit_status': 'PASS' if t['role'] == 'auditor' and t['status'] == 'PASS' else 'NOT_RUN',
                       'attempt': 1, 'invalidated_by': []}
    current = {t['id']: t for t in value['tasks']}
    if all(current.get(k) == v for k, v in wanted.items()): return
    value['tasks'] = [t for t in value['tasks'] if t['id'] not in wanted] + list(wanted.values())
    ris.update_state(root, snap['sha256'], json.dumps(value, ensure_ascii=False))


def start(root: Path, client: str = 'unknown', session_id: str = '') -> dict:
    prof = profile_of(root)
    if not prof: raise Error('role_gate_profile is not configured for this project')
    if not (root / ris.STATE_PATH).exists(): ris.initialize_state(root)
    rid = ris.read_state(root)['run_id']
    with ris.lock(root):
        run = load(root, rid)
        if run is None:
            run = {'run_id': rid, 'profile': prof, 'client': client, 'session_id': session_id,
                   'created_at': ris.timestamp(), 'repeat': {'missing': '', 'count': 0}, 'stopped': False,
                   'tasks': {t: {'role': r, 'depends_on': d, 'status': 'PENDING', 'token': None,
                                 'input_hash': None, 'call': None, 'returned': None, 'result': None}
                             for t, r, d in PROFILES[prof]}}
            save(root, run)
        elif not run.get('session_id') and session_id:
            run['session_id'] = session_id; save(root, run)
    sync_state(root)
    return run


def release(root: Path) -> dict:
    """Let the next session adopt the active run (e.g. after an abandoned session)."""
    rid = active_run_id(root)
    if not rid: raise Error('No active gate run')
    with ris.lock(root):
        run = load(root, rid); run['session_id'] = ''; run['stopped'] = False; run['repeat'] = {'missing': '', 'count': 0}
        save(root, run)
    return {'released': rid}


def result_hash(task: dict) -> str:
    return ris.sha(json.dumps(task['result'], sort_keys=True, ensure_ascii=False).encode())


def codex_task_name(token: str) -> str:
    return 'ris_' + ris.sha(token.encode())[:24]


def assign(root: Path, run_id: str, task_id: str) -> dict:
    with ris.lock(root):
        run = load(root, run_id)
        if run is None or task_id not in run['tasks']: raise Error('Unknown run or task')
        t = run['tasks'][task_id]
        for dep in t['depends_on']:
            if run['tasks'][dep]['status'] != 'PASS': raise Error(f'Dependency not passed: {dep}')
        basis = {'run': run_id, 'task': task_id, 'deps': {d: result_hash(run['tasks'][d]) for d in t['depends_on']}}
        t.update(token=uuid4().hex, input_hash=ris.sha(json.dumps(basis, sort_keys=True).encode()),
                 status='ASSIGNED', call=None, returned=None, result=None)
        save(root, run)
    sync_state(root)
    return {'run_id': run_id, 'task_id': task_id, 'token': t['token'], 'input_hash': t['input_hash'],
            'codex_task_name': codex_task_name(t['token']),
            'line': f"RIS_ASSIGN run={run_id} task={task_id} token={t['token']} input_hash={t['input_hash']}"}


def role_matches(role: str, agent_type: str) -> bool:
    """Only an agent definition named for the role may do the role's task (e.g. `plugin:researcher`)."""
    return (agent_type or '').strip().lower().rsplit(':', 1)[-1] == role


def agent_type_of(tool_input: dict) -> str:
    for k in ('subagent_type', 'agent_type', 'agent_name', 'role'):
        if isinstance(tool_input.get(k), str) and tool_input[k]: return tool_input[k]
    return ''


def record_call(root: Path, text: str, agent_type: str = '', agent_id: str = '') -> bool:
    m = ASSIGN_RE.search(text or '')
    if not m: return False
    rid, tid, token, ih = m.groups()
    with ris.lock(root):
        run = load(root, rid)
        t = run and run['tasks'].get(tid)
        if not t or t['token'] != token or t['input_hash'] != ih or t['call']: return False
        if not role_matches(t['role'], agent_type): return False  # wrong or unknown agent type: not a valid call
        t['call'] = {'agent_id': agent_id, 'agent_type': agent_type, 'at': ris.timestamp()}
        save(root, run)
    return True


def bind_agent(root: Path, text: str, agent_id: str) -> str | None:
    """Tie the spawned agent's real id to the call carrying this assignment; replay any result it already sent."""
    m = ASSIGN_RE.search(text or '')
    if not m or not agent_id: return None
    rid, tid = m.group(1), m.group(2)
    with ris.lock(root):
        run = load(root, rid); t = run and run['tasks'].get(tid)
        if not t or not t['call']: return None
        started = run.get('starts', {}).get(agent_id)
        if started and not role_matches(t['role'], started): return None  # the agent that actually started is the wrong type
        if t['call'].get('agent_id') and t['call']['agent_id'] != agent_id: return None
        t['call']['agent_id'] = agent_id
        pending = run.get('pending', {}).pop(agent_id, None)
        save(root, run)
    if pending: ingest(root, pending['text'], agent_id, pending['agent_type'])
    return tid


def stash_or_ingest(root: Path, text: str, agent_id: str, agent_type: str):
    """SubagentStop/Handback: the result counts only for the agent whose id is bound to a call."""
    if not agent_id: return  # no real id, nothing to bind a result to
    for rid in [active_run_id(root)]:
        run = rid and load(root, rid)
        if not run: return
        if any(t['call'] and t['call'].get('agent_id') == agent_id for t in run['tasks'].values()):
            ingest(root, text, agent_id, agent_type); return
        with ris.lock(root):
            run = load(root, rid); run.setdefault('pending', {})[agent_id] = {'text': text, 'agent_type': agent_type}
            save(root, run)
        ingest(root, text, agent_id, agent_type)


ROLE_FIELDS = {
    'researcher': ('sources', 'contrary'),
    'planner': ('canon_ref', 'canon_sha', 'branch_ids', 'project_plan_check'),
    'designer': ('html_ref', 'html_sha', 'canon_sha'),
    'engineer': ('html_sha', 'firefox'),
    'auditor': ('html_sha', 'canon_sha', 'scope', 'verdict'),
}


HEX64 = re.compile(r'[0-9a-f]{64}')


def placeholder(v) -> bool:
    return isinstance(v, str) and (re.fullmatch(r'\s*<[^<>]*>\s*', v) is not None or '<real' in v or '<string' in v)


def check_well_formed(payload: dict):
    """A PASS carrying template text or non-hash *_sha values is rejected without consuming the token."""
    if payload.get('status') != 'PASS': return
    art = payload.get('artifacts') or {}
    if not isinstance(art, dict): raise Error('artifacts must be an object')
    bad = [k for k, v in art.items() if k.endswith('_sha') and not (isinstance(v, str) and HEX64.fullmatch(v))]
    bad += [k for k, v in list(art.items()) + [('evidence', payload.get('evidence'))] if placeholder(v)]
    if bad: raise Error('Malformed PASS result (placeholder or invalid hash): ' + ', '.join(sorted(set(bad))))


def submit_result(root: Path, payload: dict, agent_id: str = '', agent_type: str = '', via_call: bool = False) -> dict:
    """Accept a RIS_RESULT only for the exact, single-use assignment that was actually called."""
    try: rid, tid, token = payload['run_id'], payload['task_id'], payload['token']
    except (KeyError, TypeError): raise Error('RIS_RESULT needs run_id, task_id, token, input_hash')
    check_well_formed(payload)
    with ris.lock(root):
        run = load(root, rid)
        t = run and run['tasks'].get(tid)
        if not t: raise Error('Result for unknown run or task')
        if t['token'] != token: raise Error('Token mismatch or already consumed')
        if payload.get('input_hash') != t['input_hash']: raise Error('Input hash mismatch (stale input)')
        if not t['call']: raise Error('No observed agent call for this assignment')
        if agent_type and not role_matches(t['role'], agent_type): raise Error(f"Result from {agent_type}, not the {t['role']} role")
        bound = t['call'].get('agent_id')
        if bound and agent_id != bound: raise Error('Result from a different agent than the one called')
        if t['call'].get('codex_named'):
            started = run.get('starts', {}).get(agent_id)
            if (not t['call'].get('confirmed') or not agent_id or not role_matches(t['role'], started)
                    or not role_matches(t['role'], agent_type)):
                raise Error('Codex result does not match a confirmed spawn')
            t['call']['agent_id'] = agent_id
            run.get('pending', {}).pop(agent_id, None)
        elif not bound and not via_call:
            raise Error('Result not tied to the spawned agent')
        t['returned'] = {'agent_id': agent_id or bound or '', 'agent_type': agent_type or t['call'].get('agent_type', ''), 'at': ris.timestamp()}
        t['token'] = None  # single use
        status = payload.get('status')
        art = payload.get('artifacts') or {}
        ok = status == 'PASS' and payload.get('evidence') and all(art.get(k) for k in ROLE_FIELDS[t['role']])
        if t['role'] == 'auditor' and payload.get('blocking'): ok = False
        t['result'] = payload
        t['status'] = 'PASS' if ok else 'FAIL'
        save(root, run)
    sync_state(root)
    return {'task_id': tid, 'status': t['status']}


def verdict(root: Path, run_id: str) -> dict:
    run = load(root, run_id)
    if run is None: return {'complete': False, 'missing': [{'task': '*', 'why': 'no gate record', 'next': 'start the gate'}]}
    missing = []
    for tid, t in run['tasks'].items():
        if not t['call']: missing.append({'task': tid, 'why': 'agent not called', 'next': f"assign and call {t['role']}"})
        elif not t['returned']: missing.append({'task': tid, 'why': 'no result returned', 'next': f"collect RIS_RESULT from {t['role']}"})
        elif t['status'] != 'PASS': missing.append({'task': tid, 'why': 'result not PASS or evidence incomplete', 'next': f"rework {t['role']}"})
    if not missing:
        a = {k: run['tasks'][k]['result']['artifacts'] for k in run['tasks']}
        canon, html = a['RG-PLAN'], a['RG-DESIGN']
        cur_canon, cur_html = file_sha(root, canon['canon_ref']), file_sha(root, html['html_ref'])
        checks = [
            (cur_canon == canon['canon_sha'], 'RG-PLAN', 'canon changed after planning'),
            (html['canon_sha'] == canon['canon_sha'], 'RG-DESIGN', 'HTML not built from current canon'),
            (cur_html == html['html_sha'], 'RG-DESIGN', 'HTML changed after generation'),
            (a['RG-VERIFY']['html_sha'] == cur_html, 'RG-VERIFY', 'browser check does not match delivered HTML'),
            (a['RG-AUDIT']['html_sha'] == cur_html and a['RG-AUDIT']['canon_sha'] == cur_canon, 'RG-AUDIT', 'audit does not match delivered version'),
        ]
        for ok, tid, why in checks:
            if not ok: missing.append({'task': tid, 'why': why, 'next': 're-run this task and later ones'})
    return {'complete': not missing, 'missing': missing}


def require_complete(root: Path, state_value: dict):
    """Called by `state update`: refuse COMPLETE while a gated run is unproven."""
    if state_value.get('status') != 'COMPLETE': return
    if not profile_of(root): return
    v = verdict(root, state_value['run_id'])  # no record at all also counts as unproven
    if not v['complete']:
        raise Error('COMPLETE refused by role gate: ' + '; '.join(f"{m['task']}: {m['why']}" for m in v['missing']))


def invokes_ris(prompt: str) -> bool:
    """True for `/ris ...`, `$ris ...`, `RIS ...`, `/plugin:ris ...`; not for sentences that merely mention RIS."""
    words = (prompt or '').strip().split(None, 1)
    if not words: return False
    return words[0].lstrip('/$@').rstrip(':,').rsplit(':', 1)[-1].lower() == 'ris'


def owner_of(root: Path) -> str:
    rid = active_run_id(root)
    run = rid and load(root, rid)
    return (run or {}).get('session_id', '')


def found_agent_id(value) -> str:
    if isinstance(value, dict):
        for k in ('agentId', 'agent_id'):
            if isinstance(value.get(k), str) and value[k]: return value[k]
        for v in value.values():
            r = found_agent_id(v)
            if r: return r
    elif isinstance(value, list):
        for v in value:
            r = found_agent_id(v)
            if r: return r
    return ''


def first_line(prompt: str) -> str:
    return (prompt or '').strip().split('\n', 1)[0].strip()


def codex_named_spawn(root, rid, event, payload):
    """Correlate a task-name-only spawn response using the original assignment token."""
    args = payload.get('tool_input') or {}
    call_id = payload.get('tool_use_id')
    name = args.get('task_name')
    if not call_id or not isinstance(name, str) or not name or payload.get('agent_id'):
        return None
    with ris.lock(root):
        run = load(root, rid)
        role = agent_type_of(args)
        if event == 'PreToolUse':
            message = args.get('message')
            marker = ASSIGN_RE.search(message) if isinstance(message, str) else None
            assigned = [(tid, task) for tid, task in run['tasks'].items()
                        if task['status'] == 'ASSIGNED' and role_matches(task['role'], role)]
            if not marker and not assigned:
                return None
            if len(assigned) == 1:
                tid, task = assigned[0]
                if (task['token'] and name == codex_task_name(task['token'])
                        and (not marker or marker.groups() == (rid, tid, task['token'], task['input_hash']))
                        and not task['call'] and args.get('fork_turns') == 'none'):
                    task['call'] = {'agent_id': '', 'agent_type': role, 'at': ris.timestamp(),
                                    'tool_use_id': call_id, 'task_name': name,
                                    'codex_named': True, 'confirmed': False}
                    save(root, run)
                    return None
            return {'decision': 'block', 'reason':
                    'RIS: use the assigned role, codex_task_name as task_name, fork_turns="none", and include the RIS_ASSIGN line in '
                    'the original message. For a failed or stale attempt, run gate assign again.'}
        response = payload.get('tool_response')
        if isinstance(response, str):
            try: response = json.loads(response)
            except ValueError: return None
        if not isinstance(response, dict) or response.get('task_name') not in (name, '/root/' + name):
            return None
        calls = [t['call'] for t in run['tasks'].values() if t['call']
                 and t['call'].get('tool_use_id') == call_id and t['call'].get('task_name') == name]
        if len(calls) != 1: return None
        calls[0]['confirmed'] = True
        save(root, run)
        pending = list(run.get('pending', {}).items())
    for aid, result in pending:
        ingest(root, result['text'], aid, result['agent_type'])
    return None


def handle_hook(root: Path, payload: dict, client: str) -> dict | None:
    """Translate one client hook payload. Returns hook JSON output or None."""
    event = payload.get('hook_event_name', '')
    session = str(payload.get('session_id', ''))
    simple = ris.inside(root, f'{GATE_DIR}/.simple-{re.sub(r"[^A-Za-z0-9_-]", "", session) or "x"}')
    if not profile_of(root): return None
    if event == 'UserPromptSubmit':
        prompt = payload.get('prompt', '')
        folder = ris.inside(root, GATE_DIR); folder.mkdir(parents=True, exist_ok=True)
        if first_line(prompt) == 'RIS-SIMPLE':
            simple.write_text('1'); return None
        simple.unlink(missing_ok=True)
        if not (invokes_ris(prompt) or active_run_id(root)): return None
        owner = owner_of(root)
        if owner and owner != session:
            return {'hookSpecificOutput': {'hookEventName': 'UserPromptSubmit', 'additionalContext':
                    'RIS role gate: the active run belongs to another session; this session is not gated. '
                    'Run `ris.py gate release` to take it over.'}}
        run = start(root, client, session)
        v = verdict(root, run['run_id'])
        todo = ', '.join(f"{k}({t['role']})" for k, t in run['tasks'].items() if t['status'] != 'PASS')
        return {'hookSpecificOutput': {'hookEventName': 'UserPromptSubmit', 'additionalContext':
                f"RIS role gate active, run {run['run_id']}. Required tasks: {todo or 'none'}. "
                "Assign each with `ris.py gate assign --task <ID>` and put the printed RIS_ASSIGN line in the agent prompt; "
                "for Codex named spawns set task_name to codex_task_name and fork_turns=none. The agent must return RIS_RESULT. COMPLETE is refused until the gate passes."
                if not v['complete'] else 'RIS role gate: all required tasks already proven.'}}
    rid = active_run_id(root)
    if not rid: return None
    owner = owner_of(root)
    if owner and session and owner != session: return None  # one active top-level session per project
    if event == 'SubagentStart':
        with ris.lock(root):
            run = load(root, rid); run.setdefault('starts', {})[str(payload.get('agent_id', ''))] = str(payload.get('agent_type', ''))
            save(root, run)
        return None
    if client == 'codex' and event in ('PreToolUse', 'PostToolUse') and payload.get('tool_name') == 'collaborationspawn_agent':
        return codex_named_spawn(root, rid, event, payload)
    if event in ('PreToolUse', 'PostToolUse') and payload.get('tool_name') in AGENT_TOOLS:
        text = json.dumps(payload.get('tool_input', {}), ensure_ascii=False)
        if event == 'PreToolUse': record_call(root, text, agent_type_of(payload.get('tool_input') or {}))
        else:
            resp = payload.get('tool_response', '')
            aid = found_agent_id(resp)
            line = ASSIGN_RE.search(text)
            if line: bind_agent(root, line.group(0), aid)
            ingest(root, '\n'.join(strings(resp)), aid, '', via_call_token=line.group(3) if line else None)
        return None
    if event in ('SubagentStop', 'SubagentHandback'):
        stash_or_ingest(root, str(payload.get('last_assistant_message') or payload.get('report') or ''),
                        str(payload.get('agent_id', '')), str(payload.get('agent_type', '')))
        return None
    if event == 'Stop':
        if simple.exists(): simple.unlink(); return None
        run = load(root, rid); v = verdict(root, rid)
        if v['complete'] or run.get('stopped'): return None
        sig = ';'.join(f"{m['task']}:{m['why']}" for m in v['missing'])
        with ris.lock(root):
            run = load(root, rid)
            rep = run['repeat']
            rep['count'] = rep['count'] + 1 if rep['missing'] == sig else 1
            rep['missing'] = sig
            if rep['count'] > MAX_REPEAT: run['stopped'] = True
            save(root, run)
        if run['stopped']: return None  # no progress: leave incomplete, stop auto-continue
        m = v['missing'][0]
        return {'decision': 'block', 'reason': f"RIS role gate: {m['task']} — {m['why']}. Next: {m['next']}."}
    return None


def strings(value):
    if isinstance(value, str): yield value
    elif isinstance(value, dict):
        for v in value.values(): yield from strings(v)
    elif isinstance(value, list):
        for v in value: yield from strings(v)


def ingest(root: Path, text: str, agent_id: str = '', agent_type: str = '', via_call_token: str | None = None):
    decoder = json.JSONDecoder()
    for m in re.finditer(r'RIS_RESULT\s*(?=\{)', text):
        try: payload, _ = decoder.raw_decode(text, m.end())
        except ValueError: continue
        # A tool response is the return of its own call only when it carries that call's token.
        direct = via_call_token is not None and isinstance(payload, dict) and payload.get('token') == via_call_token
        try: submit_result(root, payload, agent_id, agent_type, via_call=direct)
        except (Error, KeyError, AttributeError, TypeError): continue
