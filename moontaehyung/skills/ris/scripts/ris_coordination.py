"""Bounded local scheduling and CAS task claims; no model/provider execution or daemon."""
import argparse
import copy
from functools import cache
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path


def amount(ris, value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ris.Error('Resource amount must be a finite nonnegative number')
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ris.Error('Invalid resource amount') from exc
    if not result.is_finite() or result < 0:
        raise ris.Error('Resource amount must be finite and nonnegative')
    return result


def artifact(ris, root, item):
    if not isinstance(item, dict) or set(item) != {'path', 'sha256'}:
        raise ris.Error('Artifact requires path and sha256')
    path = ris.state_reference(root, item['path'], 'coordination artifact')
    if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
        raise ris.Error('Coordination artifact changed')
    return item['path']


def load(ris, root, envelope_ref):
    """Resource evidence is caller supplied, never inferred from provider/account settings."""
    snap = ris.read_state_snapshot(root)
    path = ris.state_reference(root, envelope_ref, 'coordination envelope')
    raw = path.read_bytes()
    try:
        body = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ris.Error('Invalid coordination envelope JSON') from exc
    required = {'schema_version', 'project_id', 'run_id', 'state_sha256', 'approval_context',
                'priority', 'task_order', 'resources', 'demands', 'decision_blocks',
                'external_effects', 'recoveries'}
    if (not isinstance(body, dict) or not required <= set(body) or set(body) - required - {'blocked_scopes'}
            or type(body['schema_version']) is not int or body['schema_version'] != 1):
        raise ris.Error('Unsupported coordination envelope')
    state = snap['state']
    if body['project_id'] != state['project_id'] or body['run_id'] != state['run_id']:
        raise ris.Error('Coordination project/run mismatch')
    if body['state_sha256'] != snap['sha256']:
        raise ris.Error('Stale resource accounting: refresh against current authoritative state')
    artifact(ris, root, body['approval_context'])
    if (not isinstance(body['priority'], dict) or set(body['priority']) != {'quality', 'cost', 'time'}
            or any(not isinstance(v, str) or not v.strip() for v in body['priority'].values())):
        raise ris.Error('Preserve explicit user quality/cost/time priorities')
    tasks = {t['id']: t for t in state['tasks']}
    order = body['task_order']
    if not isinstance(order, list) or any(not isinstance(t, str) for t in order) or len(set(order)) != len(order) or set(order) != set(tasks):
        raise ris.Error('task_order must list every existing task exactly once')
    if not isinstance(body['resources'], dict) or not body['resources']:
        raise ris.Error('Resource accounting is unknown')
    for name, resource in body['resources'].items():
        if not isinstance(name, str) or not name.strip() or not isinstance(resource, dict) or set(resource) != {'unit', 'limit', 'spent', 'reserved', 'known'}:
            raise ris.Error('Resource needs unit, limit, spent, reserved, known')
        if resource['known'] is not True or not isinstance(resource['unit'], str) or not resource['unit'].strip():
            raise ris.Error('Unknown resource accounting/unit')
        for key in ('limit', 'spent', 'reserved'):
            amount(ris, resource[key])
        if amount(ris, resource['spent']) + amount(ris, resource['reserved']) > amount(ris, resource['limit']):
            raise ris.Error('Resource accounting exceeds limit')
    if not isinstance(body['demands'], dict) or set(body['demands']) != set(tasks):
        raise ris.Error('Every task requires explicit resource demands')
    for demand in body['demands'].values():
        if not isinstance(demand, dict) or set(demand) != set(body['resources']):
            raise ris.Error('Task demand must specify every resource, including explicit zero')
        for value in demand.values():
            amount(ris, value)
    if state['status'] == 'USER_DECISION' and not state['pending_user_decisions']:
        raise ris.Error('USER_DECISION scope is unknown')
    decisions = body['decision_blocks']
    if not isinstance(decisions, dict) or set(decisions) != set(state['pending_user_decisions']):
        raise ris.Error('Pending decisions need explicit affected task scope')
    for ids in decisions.values():
        if not isinstance(ids, list) or any(not isinstance(t, str) or t not in tasks for t in ids):
            raise ris.Error('Decision scope must reference existing task IDs')
    if 'blocked_scopes' in body:
        scopes = body['blocked_scopes']
        if not isinstance(scopes, dict) or set(scopes) != {item['ref'] for item in state['blocked_items']}:
            raise ris.Error('Blocked scopes must match all current blocked-item references')
        for ids in scopes.values():
            if not isinstance(ids, list) or not ids or any(not isinstance(t, str) or t not in tasks for t in ids):
                raise ris.Error('Blocked scope needs nonempty existing task IDs')
    effects = body['external_effects']
    if not isinstance(effects, dict) or set(effects) - set(tasks):
        raise ris.Error('External effects must reference existing tasks')
    for effect in effects.values():
        if not isinstance(effect, dict) or set(effect) != {'status', 'evidence'} or not isinstance(effect['status'], str) or effect['status'] not in {'PENDING', 'UNKNOWN', 'CONFIRMED_NONE', 'CONFIRMED_DONE'}:
            raise ris.Error('Invalid external effect accounting')
        artifact(ris, root, effect['evidence'])
    if not isinstance(body['recoveries'], dict) or set(body['recoveries']) - set(tasks):
        raise ris.Error('Recovery policy must reference existing tasks')
    for policy in body['recoveries'].values():
        if (not isinstance(policy, dict) or set(policy) != {'failure_kind', 'max_attempts', 'evidence'}
                or not isinstance(policy['failure_kind'], str) or policy['failure_kind'] not in {'transient_tool', 'internal_exploration'}
                or type(policy['max_attempts']) is not int or policy['max_attempts'] < 1):
            raise ris.Error('Recovery requires bounded known local failure policy')
        artifact(ris, root, policy['evidence'])
    # Hash-pinned prior grants preserve held/spent ceilings across fresh snapshots.
    held = {name: Decimal(0) for name in body['resources']}
    spent = dict(held)
    for task in state['tasks']:
        grants = [ref for ref in task['artifact_refs'] if '#coordination-sha256=' in ref]
        if task['status'] == 'IN_PROGRESS' and not grants:
            raise ris.Error('Unknown active task reservation')
        for index, ref in enumerate(grants):
            prior_path, digest = ref.rsplit('#coordination-sha256=', 1)
            prior_raw = ris.state_reference(root, prior_path, 'prior claim').read_bytes()
            if hashlib.sha256(prior_raw).hexdigest() != digest:
                raise ris.Error('Prior reservation snapshot changed')
            try:
                prior = json.loads(prior_raw)
                if not isinstance(prior, dict) or not isinstance(prior.get('demands'), dict) or not isinstance(prior.get('resources'), dict):
                    raise ValueError('structure')
                demand = prior['demands'][task['id']]
                if not isinstance(demand, dict) or any(not isinstance(prior['resources'].get(n), dict) for n in held):
                    raise ValueError('resource structure')
                if prior['project_id'] != state['project_id'] or prior['run_id'] != state['run_id']:
                    raise ValueError('identity')
                if set(demand) != set(held) or any(prior['resources'][n]['unit'] != body['resources'][n]['unit'] for n in held):
                    raise ValueError('units')
            except (KeyError, TypeError, ValueError) as exc:
                raise ris.Error('Invalid prior resource reservation') from exc
            target = held if task['status'] == 'IN_PROGRESS' and index == len(grants)-1 else spent
            for name in target: target[name] += amount(ris, demand[name])
    for name, resource in body['resources'].items():
        if amount(ris, resource['reserved']) < held[name] or amount(ris, resource['spent']) < spent[name]:
            raise ris.Error('Fresh accounting omits prior held/spent reservation ceilings')
    return snap, body, hashlib.sha256(raw).hexdigest()


def project(ris, root, envelope_ref, mode='research', limit=20):
    if not isinstance(mode, str) or mode not in {'research', 'concise'} or type(limit) is not int or not 1 <= limit <= 100:
        raise ris.Error('Use research/concise mode and result limit 1..100')
    if mode == 'concise':
        return {'state_sha256': None, 'mode': mode, 'selected': [],
                'dispositions': [], 'tasks_total': None,
                'reason': 'concise_response_no_dispatch', 'authority': 'no_execution',
                'provider_charge_enforcement': False}
    if not envelope_ref:
        raise ris.Error('Research scheduling requires existing accounting envelope')
    snap, body, digest = load(ris, root, envelope_ref)
    state = snap['state']; tasks = {t['id']: t for t in state['tasks']}
    decision_tasks = {t for ids in body['decision_blocks'].values() for t in ids}
    scopes = body.get('blocked_scopes')
    ambiguous_hold = ((state['status'] == 'BLOCKED' and not state['blocked_items'])
                      or (bool(state['blocked_items']) and scopes is None))
    held_tasks = {t for ids in (scopes or {}).values() for t in ids}
    remaining = {name: amount(ris, r['limit']) - amount(ris, r['spent']) - amount(ris, r['reserved']) for name, r in body['resources'].items()}
    selected = []; dispositions = []
    @cache
    def valid_dependency(task_id):
        task = tasks[task_id]
        return (task['status'] == 'PASS' and not task['invalidated_by']
                and task['audit_status'] not in {'FAIL', 'BLOCKED'}
                and task_id not in decision_tasks and task_id not in held_tasks and not ambiguous_hold
                and body['external_effects'].get(task_id, {}).get('status') not in {'PENDING', 'UNKNOWN'}
                and all(valid_dependency(dep) for dep in task['depends_on']))
    for task_id in body['task_order']:
        task = tasks[task_id]; reasons = []; action = 'claim'
        effect = body['external_effects'].get(task_id)
        if ambiguous_hold: reasons.append('BLOCKED_scope_unresolved')
        if task_id in held_tasks: reasons.append('BLOCKED_scoped')
        if state['status'] == 'COMPLETE': reasons.append('run_complete')
        if task['invalidated_by']: reasons.append('invalidated_requires_rework')
        if task_id in decision_tasks: reasons.append('USER_DECISION')
        for dependency in task['depends_on']:
            if not valid_dependency(dependency):
                reasons.append('dependency_not_valid:' + dependency)
        if effect and effect['status'] in {'PENDING', 'UNKNOWN', 'CONFIRMED_DONE'}:
            reasons.append('external_effect_' + effect['status'])
        if task['status'] == 'FAIL':
            policy = body['recoveries'].get(task_id)
            if not policy or task['attempt'] >= policy['max_attempts']:
                reasons.append('failure_requires_recovery_or_attempt_limit')
            else:
                action = 'recover'
        elif task['status'] not in {'PENDING', 'READY', 'NOT_RUN'}:
            reasons.append('task_' + task['status'])
        if task['audit_status'] == 'BLOCKED' or (task['audit_status'] == 'FAIL' and action != 'recover'):
            reasons.append('audit_blocked')
        demand = body['demands'][task_id]
        # Exhausted resources prohibit further usage of that resource, not zero-demand local work.
        for name in remaining:
            if amount(ris, demand[name]) > remaining[name]:
                reasons.append('resource_limit:' + name)
        if not reasons:
            selected.append({'task_id': task_id, 'action': action, 'attempt': task['attempt'] + (action == 'recover'), 'demand': demand})
            for name in remaining: remaining[name] -= amount(ris, demand[name])
        dispositions.append({'task_id': task_id, 'reasons': reasons})
    return {'state_sha256': snap['sha256'], 'envelope_sha256': digest, 'envelope_ref': envelope_ref,
            'project_id': state['project_id'], 'run_id': state['run_id'], 'mode': mode,
            'priority': body['priority'], 'selected': selected[:limit], 'selected_total': len(selected),
            'dispositions': dispositions[:limit], 'tasks_total': len(tasks), 'omitted': max(0, len(tasks) - limit),
            'remaining_after_projection': {k: str(v) for k, v in remaining.items()},
            'pending_user_decisions': state['pending_user_decisions'],
            'authority': 'advisory_until_CAS_claim', 'provider_charge_enforcement': False}


def claim(ris, root, envelope_ref, task_id, expected_hash, mode='research'):
    """Reserve ONE selected task via existing authoritative state CAS before controlled dispatch.

    Every claim consumes the envelope's state hash. It cannot be reused for another task;
    refresh external accounting before further claims, including after completion/failure.
    """
    projection = project(ris, root, envelope_ref, mode=mode, limit=100)
    if projection['state_sha256'] != expected_hash:
        raise ris.Error('Stale claim: reload authoritative state')
    selected = {item['task_id']: item for item in projection['selected']}
    if task_id not in selected:
        raise ris.Error('Task is not dispatchable under current scope/resources')
    snapshot = ris.read_state_snapshot(root)
    if snapshot['sha256'] != expected_hash:
        raise ris.Error('State changed before claim')
    state = copy.deepcopy(snapshot['state'])
    task = next(t for t in state['tasks'] if t['id'] == task_id)
    task['status'] = 'IN_PROGRESS'; task['attempt'] = selected[task_id]['attempt']
    receipt_ref = envelope_ref + '#coordination-sha256=' + projection['envelope_sha256']
    if receipt_ref not in task['artifact_refs']: task['artifact_refs'].append(receipt_ref)
    # Existing CAS serializes compliant state writers. Recheck evidence around commit;
    # changed evidence leaves IN_PROGRESS held but never returns a dispatchable receipt.
    artifact(ris, root, {'path': envelope_ref, 'sha256': projection['envelope_sha256']})
    _, envelope_body, current_digest = load(ris, root, envelope_ref)
    if current_digest != projection['envelope_sha256']:
        raise ris.Error('Coordination envelope changed before claim')
    evidence_refs = [envelope_body['approval_context']]
    evidence_refs += [effect['evidence'] for effect in envelope_body['external_effects'].values()]
    evidence_refs += [policy['evidence'] for policy in envelope_body['recoveries'].values()]
    for item in evidence_refs: artifact(ris, root, item)
    result = ris.update_state(root, expected_hash, json.dumps(state, ensure_ascii=False))
    for item in evidence_refs: artifact(ris, root, item)
    artifact(ris, root, {'path': envelope_ref, 'sha256': projection['envelope_sha256']})
    if ris.read_state_snapshot(root)['sha256'] != result['sha256']:
        raise ris.Error('Claim changed before receipt; do not dispatch')
    return {'claim': result, 'task_id': task_id, 'attempt': task['attempt'],
            'resource_reservation': selected[task_id]['demand'], 'envelope_sha256': projection['envelope_sha256'],
            'dispatched': False, 'execution_authority': False, 'next': 'controlled_dispatch_once; refresh accounting before another claim',
            'priority': projection['priority']}


def add_parser(sub):
    p = sub.add_parser('coordinate', help='Bounded local scheduling/claim; no model execution')
    p.add_argument('--envelope', help='Required for research; unused for concise response')
    p.add_argument('--mode', choices=('research', 'concise'), default='research')
    p.add_argument('--limit', type=int, default=20)
    p.add_argument('--claim', metavar='TASK_ID')
    p.add_argument('--expected-hash')


def run(ris, root, args):
    if args.claim:
        if not args.expected_hash: raise ris.Error('Claim requires current --expected-hash')
        return claim(ris, root, args.envelope, args.claim, args.expected_hash, args.mode)
    return project(ris, root, args.envelope, args.mode, args.limit)


if __name__ == '__main__':
    import ris
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest='command', required=True); add_parser(sub)
    args = parser.parse_args()
    try:
        print(json.dumps(run(ris, args.project.resolve(), args), ensure_ascii=False, indent=2))
    except (ris.Error, OSError, ValueError) as exc:
        parser.exit(2, 'Coordination error: ' + str(exc) + '\n')
