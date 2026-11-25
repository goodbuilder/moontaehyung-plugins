"""Deterministic, explicitly authorized recovery continuity; no model or research execution."""
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

PATH = '.ris/recovery.json'
EXCLUDED = {'retry', 'resume', 'explanation', 'render', 'self', 'audit', 'new-goal'}
KINDS = EXCLUDED | {'deepen', 'input', 'input-and-deepen'}

EVENT_FIELDS = {
    'create': {'node', 'history_complete'},
    'request': {'node_id', 'request_id', 'request_ref', 'kind', 'input_ref'},
    'delivered': {'node_id', 'result_ref'},
    'exhaustive-complete': {'node_id', 'result_ref'},
    'reconcile-history': {'node_id', 'count', 'evidence_ref'},
    'rename': {'node_id', 'label', 'rationale'},
    'split': {'parents', 'children', 'history_applicability', 'rationale'},
    'merge': {'parents', 'children', 'history_applicability', 'rationale'},
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def read(ris, root):
    cfg = ris.config(root)
    path = ris.inside(root, PATH)
    raw = path.read_bytes() if path.exists() else None
    value = json.loads(raw) if raw is not None else {'schema_version': 1, 'project_id': cfg['project_id'], 'revision': 0, 'nodes': {}, 'events': []}
    if not isinstance(value, dict) or value.get('schema_version') != 1 or value.get('project_id') != cfg['project_id']:
        raise ris.Error('Unsupported recovery schema or project identity')
    if type(value.get('revision')) is not int or not isinstance(value.get('nodes'), dict) or not isinstance(value.get('events'), list):
        raise ris.Error('Invalid recovery ledger')
    for node_id, node in value['nodes'].items():
        if not isinstance(node, dict) or node.get('id') != node_id:
            raise ris.Error('Invalid recovery node identity')
        count = node.get('count')
        if count is not None and (type(count) is not int or count < 0):
            raise ris.Error('Invalid recovery count')
        if type(node.get('observed_count', 0)) is not int or node.get('observed_count', 0) < 0:
            raise ris.Error('Invalid observed recovery count')
        if any(type(node.get(k)) is not bool for k in ('active', 'delivered', 'exhaustive')):
            raise ris.Error('Invalid recovery node state')
    if any(not isinstance(e, dict) or not isinstance(e.get('event'), dict) or not isinstance(e.get('result'), dict) or not isinstance(e.get('id'), str) or not isinstance(e.get('fingerprint'), str) for e in value['events']):
        raise ris.Error('Invalid recovery history')
    return value, raw


def snapshot(ris, root):
    value, raw = read(ris, root)
    return {'path': PATH, 'hash': hashlib.sha256(raw).hexdigest() if raw is not None else 'missing', 'ledger': value}


def text(ris, value, field):
    if not isinstance(value, str) or not value.strip():
        raise ris.Error(field + ' must be a nonempty string')
    return value


def identity(ris, value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}', value):
        raise ris.Error('Invalid stable ID')
    return value


def node_new(ris, body, count=None):
    if not isinstance(body, dict):
        raise ris.Error('Node must be a JSON object')
    if set(body) - {'id', 'label', 'scope', 'conditions'}:
        raise ris.Error('Unexpected node field; store only continuity metadata')
    identity(ris, body.get('id'))
    ris.validated_question_id(body['id'])
    text(ris, body.get('label'), 'label')
    text(ris, body.get('scope'), 'scope')
    text(ris, body.get('conditions'), 'conditions')
    return {key: body[key] for key in ('id', 'label', 'scope', 'conditions')} | {'count': count, 'observed_count': 0, 'delivered': False, 'exhaustive': False, 'active': True, 'parents': []}


def applicable_requests(ledger, selected):
    """Follow only explicitly preserved lineage. Count a shared request once after a merge."""
    lineage = {node['id'] for node in selected}
    for record in reversed(ledger['events']):
        event = record['event']
        if event.get('operation') not in ('split', 'merge'):
            continue
        if event.get('history_applicability') == 'preserve' and any(
                child['id'] in lineage for child in event['children']):
            lineage.update(event['parents'])
    return {record['event']['request_id'] for record in ledger['events']
            if record['event'].get('operation') == 'request'
            and record['event']['node_id'] in lineage and record['result'].get('counted')}


def recovery_action(node, minimum_count):
    if node['exhaustive']:
        return 'meta_recovery'
    if minimum_count >= 3:
        return 'exhaustive_now'
    if minimum_count == 2:
        return 'unused_frontier'
    return 'assess_exhaustive'


def transition(ris, ledger, event):
    op = event.get('operation')
    nodes = ledger['nodes']
    if op == 'create':
        body = event.get('node', {})
        complete = event.get('history_complete', False)
        if type(complete) is not bool:
            raise ris.Error('history_complete must be boolean')
        node = node_new(ris, body, 0 if complete else None)
        if node['id'] in nodes:
            raise ris.Error('Stable node ID already exists')
        nodes[node['id']] = node
        return {'action': 'created', 'count': node['count']}
    if op in ('split', 'merge'):
        parents = event.get('parents')
        children = event.get('children')
        if not isinstance(parents, list) or not parents or any(not isinstance(p, str) for p in parents) or len(set(parents)) != len(parents):
            raise ris.Error('Distinct parent IDs required')
        if not isinstance(children, list) or not children:
            raise ris.Error('Explicit child nodes with scope and conditions required')
        if (op == 'split' and (len(parents) != 1 or len(children) < 2)) or (op == 'merge' and (len(parents) < 2 or len(children) != 1)):
            raise ris.Error('split needs one parent and multiple children; merge needs multiple parents and one child')
        text(ris, event.get('rationale'), 'semantic rationale')
        selected = [get_node(ris, nodes, p) for p in parents]
        applicability = event.get('history_applicability', 'unknown')
        if applicability not in ('preserve', 'unknown'):
            raise ris.Error('history_applicability must be preserve or unknown')
        count = None
        observed = 0
        if applicability == 'preserve':
            if len(selected) == 1:
                count = selected[0]['count']
                observed = selected[0].get('observed_count', 0)
            else:
                histories = [applicable_requests(ledger, [parent]) for parent in selected]
                observed = len(set.union(*histories))
                if all(n['count'] == len(history) for n, history in zip(selected, histories)):
                    count = observed
                else:
                    # The overlap of any pre-ledger histories cannot be reconstructed.
                    observed = max(observed, *(n['count'] or n.get('observed_count', 0) for n in selected))
        for body in children:
            node = node_new(ris, body, count)
            if node['id'] in nodes:
                raise ris.Error('Child ID already exists')
            node.update(observed_count=observed, parents=parents[:],
                        delivered=applicability == 'preserve' and all(n['delivered'] for n in selected),
                        exhaustive=applicability == 'preserve' and all(n['exhaustive'] for n in selected))
            nodes[node['id']] = node
        for node in selected:
            node['active'] = False
        return {'action': op, 'count': count}
    node = get_node(ris, nodes, event.get('node_id'))
    if op == 'reconcile-history':
        count = event.get('count')
        if type(count) is not int or count < 0:
            raise ris.Error('Reconciled count must be a nonnegative integer')
        if node['count'] is not None:
            raise ris.Error('Only unknown history can be reconciled')
        if count < node.get('observed_count', 0):
            raise ris.Error('Reconciled total cannot be below observed genuine requests')
        text(ris, event.get('evidence_ref'), 'complete history evidence_ref')
        node['count'] = count
        return {'action': 'history_reconciled', 'count': count}
    if op == 'rename':
        node['label'] = text(ris, event.get('label'), 'label')
        text(ris, event.get('rationale'), 'semantic rationale')
        return {'action': 'renamed', 'count': node['count']}
    if op == 'delivered':
        text(ris, event.get('result_ref'), 'result_ref')
        node['delivered'] = True
        return {'action': 'delivery_recorded', 'count': node['count']}
    if op == 'exhaustive-complete':
        text(ris, event.get('result_ref'), 'result_ref')
        node['exhaustive'] = True
        node['delivered'] = True
        return {'action': 'exhaustive_recorded', 'count': node['count']}
    if op != 'request':
        raise ris.Error('Unknown recovery operation')
    kind = event.get('kind')
    if not isinstance(kind, str) or kind not in KINDS:
        raise ris.Error('Unknown request kind')
    identity(ris, event.get('request_id'))
    text(ris, event.get('request_ref'), 'request_ref')
    if kind == 'input-and-deepen':
        text(ris, event.get('input_ref'), 'input_ref')
    if kind in EXCLUDED or kind == 'input' or not node['delivered']:
        return {'action': 'continue', 'count': node['count'], 'counted': False}
    node['observed_count'] = node.get('observed_count', 0) + 1
    if node['count'] is None:
        return {'action': recovery_action(node, node['observed_count']), 'count': None,
                'observed_count': node['observed_count'], 'history_unknown': True, 'counted': True}
    node['count'] += 1
    return {'action': recovery_action(node, node['count']), 'count': node['count'], 'counted': True}


def get_node(ris, nodes, node_id):
    identity(ris, node_id)
    if node_id not in nodes or not nodes[node_id]['active']:
        raise ris.Error('Unknown or retired node; explicitly select an active stable ID')
    return nodes[node_id]


def apply(ris, root, event, expected_hash, authorized=False):
    if not isinstance(event, dict):
        raise ris.Error('Event must be a JSON object')
    event_id = identity(ris, event.get('id'))
    operation = event.get('operation')
    if not isinstance(operation, str) or operation not in EVENT_FIELDS:
        raise ris.Error('Unknown recovery operation')
    if set(event) - {'id', 'operation'} - EVENT_FIELDS[operation]:
        raise ris.Error('Unexpected event field; store only continuity metadata')
    fingerprint = digest(event)
    with ris.project_lock(root):
        cfg = ris.config(root)
        if cfg['recording_policy'] == 'manual' and not authorized:
            raise ris.Error('Manual policy requires explicit recording authority: --record-authorized')
        current = snapshot(ris, root)
        ledger = current['ledger']
        for saved in ledger['events']:
            if saved['id'] == event_id:
                if saved['fingerprint'] != fingerprint:
                    raise ris.Error('Event ID reused with different content')
                return {'duplicate': True, 'hash': current['hash'], 'result': saved['result'], 'revision': ledger['revision']}
        if event.get('operation') == 'request':
            identity(ris, event.get('request_id'))
            for saved in ledger['events']:
                prior = saved['event']
                if prior.get('operation') == 'request' and prior.get('request_id') == event['request_id']:
                    comparable = {k: v for k, v in event.items() if k != 'id'}
                    same_node_retry = event.get('kind') == 'retry' and event.get('node_id') == prior['node_id']
                    if not same_node_retry and comparable != {k: v for k, v in prior.items() if k != 'id'}:
                        raise ris.Error('Request ID reused with different content')
                    return {'duplicate': True, 'hash': current['hash'], 'result': saved['result'], 'revision': ledger['revision']}
        if expected_hash != current['hash']:
            raise ris.Error('Recovery CAS conflict; read current ledger and reconsider event')
        updated = copy.deepcopy(ledger)
        result = transition(ris, updated, event)
        updated['revision'] += 1
        updated['events'].append({'id': event_id, 'fingerprint': fingerprint, 'event': event, 'result': result})
        raw = (json.dumps(updated, ensure_ascii=False, indent=2) + '\n').encode()
        path = ris.inside(root, PATH)
        previous = path.read_bytes() if path.exists() else None
        if (hashlib.sha256(previous).hexdigest() if previous is not None else 'missing') != current['hash']:
            raise ris.Error('Recovery changed during transaction')
        ris.atomic_note_write(path, raw, expected=previous)
        return {'duplicate': False, 'hash': hashlib.sha256(raw).hexdigest(), 'revision': updated['revision'], 'result': result}


def add_parser(sub):
    parser = sub.add_parser('recovery', help='Read or explicitly record deterministic node/request continuity')
    actions = parser.add_subparsers(dest='recovery_action', required=True)
    actions.add_parser('read')
    write = actions.add_parser('apply')
    write.add_argument('--expected-hash', required=True)
    write.add_argument('--body-file', required=True)
    write.add_argument('--record-authorized', action='store_true', help='Assert user-authorized recording under manual policy')


def dispatch(ris, root, args):
    if args.recovery_action == 'read':
        return snapshot(ris, root)
    body = sys.stdin.read() if args.body_file == '-' else Path(args.body_file).read_text(encoding='utf-8')
    return apply(ris, root, json.loads(body), args.expected_hash, args.record_authorized)
