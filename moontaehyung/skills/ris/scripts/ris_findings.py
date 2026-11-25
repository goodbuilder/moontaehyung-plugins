"""Governed knowledge ledger: one canonical Markdown file, with retained revisions."""
from contextlib import nullcontext
from urllib.parse import quote, unquote
import base64
import copy
import hashlib
import json
import re
BEGIN = '<!-- ris:findings -->\n```json\n'
END = '\n```\n<!-- /ris:findings -->'

def add_parser(sub):
    p = sub.add_parser('findings', help='Propose, review and integrate canonical research knowledge')
    p.add_argument('action', choices=('inspect', 'propose', 'accept', 'return', 'integrate', 'obligate', 'deliver', 'review-edit', 'resolve', 'disposition', 'search'))
    p.add_argument('--question', default='default', help='Stable project-local question ID; independent ledger scope')
    p.add_argument('--query')
    p.add_argument('--cursor', help='Opaque project/query-bound discovery continuation')
    p.add_argument('--target-conditions', help='Project-relative JSON {project_id, conditions} for read-only comparison')
    p.add_argument('--node-id')
    p.add_argument('--limit', type=int, default=20)
    p.add_argument('--input', help='Project-relative JSON payload')
    p.add_argument('--expected-revision', type=int)
    p.add_argument('--idempotency-key')
    p.add_argument('--authorize-record', action='store_true')

def digest(data):
    return hashlib.sha256(data).hexdigest()

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def location(api, cfg, question='default'):
    if not isinstance(question, str) or api.validated_question_id(question) != question:
        raise api.Error('Use an exact validated research question ID')
    name = 'knowledge.md' if question == 'default' else 'knowledge-' + quote(question, safe='') + '.md'
    return api.research_path(cfg, 'research/findings/' + name)

def canonical_question_for_path(api, root, relative):
    """Recognize managed identity or explicit marker, preserving old unrelated notes."""
    from pathlib import Path
    cfg = api.config(root)
    relative = api.inside(root, relative).relative_to(root).as_posix()
    path = Path(relative)
    if path.parent.as_posix() != api.research_path(cfg, 'research/findings'):
        return None
    if path.name == 'knowledge.md':
        question = 'default'
    elif path.name.startswith('knowledge-') and path.name.endswith('.md'):
        question = unquote(path.name[len('knowledge-'):-3])
        try:
            if location(api, cfg, question) != relative:
                return None
        except api.Error:
            return None
    else:
        return None
    delivery = api.companion('ris_delivery')
    (_, data) = delivery.read_file(api, root, relative)
    text = data.decode('utf-8')
    metadata = api.frontmatter(text)
    identity = 'findings-' + cfg['project_id'] + '-' + question
    if metadata.get('ris_id') == identity or BEGIN in text:
        return question
    if isinstance(metadata.get('ris_id'), str) and metadata['ris_id'].startswith('findings-'):
        raise api.Error('Governed findings identity does not match this project/question')
    return None

def parse(api, data, cfg):
    text = data.decode('utf-8')
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        raise api.Error('Canonical findings block is missing or ambiguous; restore from reviewed history')
    try:
        value = json.loads(text.split(BEGIN, 1)[1].split(END, 1)[0])
    except ValueError as exc:
        raise api.Error('Invalid canonical findings JSON') from exc
    if not isinstance(value, dict):
        raise api.Error('Canonical findings block must be an object')
    if value.get('project_id') != cfg['project_id'] or type(value.get('schema_version')) is not int or value.get('schema_version') != 1:
        raise api.Error('Findings project/schema mismatch')
    if type(value.get('revision')) is not int or value['revision'] < 1:
        raise api.Error('Invalid findings revision')
    narrative = text.split(END, 1)[1]
    return (value, narrative)

def validate_finding(api, item):
    required = {'id', 'statement', 'status', 'conditions', 'provenance', 'axes', 'relations'}
    if not isinstance(item, dict) or set(item) != required:
        raise api.Error('Finding requires exactly id, statement, status, conditions, provenance, axes, relations')
    if not isinstance(item['id'], str) or not re.fullmatch('[A-Za-z0-9_-]{1,64}', item['id']):
        raise api.Error('Invalid finding ID')
    if not isinstance(item['statement'], str) or not item['statement'].strip():
        raise api.Error('Finding statement is required')
    if item['status'] not in ('CONFIRMED', 'ASSUMED', 'INFERRED', 'UNKNOWN', 'NOT_RUN', 'BLOCKED'):
        raise api.Error('Unknown finding status')
    for field in ('conditions', 'axes'):
        if not isinstance(item[field], dict) or any((not isinstance(k, str) or not isinstance(v, str) or (not v.strip()) for (k, v) in item[field].items())):
            raise api.Error(field + ' must map names to explicit strings, including unknown when unresolved')
    if not isinstance(item['provenance'], list) or not item['provenance']:
        raise api.Error('At least one explicit provenance locator is required')
    for source in item['provenance']:
        if not isinstance(source, dict) or set(source) != {'source', 'locator', 'revision', 'limitations'} or any((not isinstance(source[k], str) or not source[k].strip() for k in ('source', 'locator', 'revision'))) or (not isinstance(source['limitations'], list)) or any((not isinstance(x, str) for x in source['limitations'])):
            raise api.Error('Provenance requires source, locator, revision, limitations (no inferred citations)')
    if not isinstance(item['relations'], list):
        raise api.Error('Relations must be an array')
    for relation in item['relations']:
        if not isinstance(relation, dict) or set(relation) != {'kind', 'target', 'conditions', 'evidence'} or relation['kind'] not in ('supports', 'contradicts', 'depends_on', 'supersedes') or (not isinstance(relation['target'], str)):
            raise api.Error('Invalid typed finding relation; require kind, target, conditions, evidence')
        if not isinstance(relation['conditions'], dict) or not isinstance(relation['evidence'], list) or (not relation['evidence']) or any((not isinstance(x, str) or not x.strip() for x in relation['evidence'])) or any((not isinstance(k, str) or not isinstance(v, str) or (not v.strip()) for (k, v) in relation['conditions'].items())):
            raise api.Error('Relation conditions and explicit evidence locators are required')

def header(project_id, question):
    return '---\nris_id: ' + json.dumps('findings-' + project_id + '-' + question) + '\nproject_id: ' + json.dumps(project_id) + '\nkind: "finding"\nstatus: "governed"\ncreated: "ledger-v1"\n---\n\n# Research knowledge\n\n'

def render(value, narrative):
    return header(value['project_id'], value.get('question_id', 'default')) + BEGIN + json.dumps(value, ensure_ascii=False, indent=2) + END + narrative

def summary(value, narrative, data, args, dirty=False):
    nodes = value['proposals']
    query = (getattr(args, 'query', None) or '').casefold()
    node_id = getattr(args, 'node_id', None)
    selected = [x for x in nodes if (not node_id or x['finding']['id'] == node_id) and (not query or query in canonical(x).casefold())]
    limit = getattr(args, 'limit', 20)
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('limit must be 1..100')
    return {'project_id': value['project_id'], 'question_id': value.get('question_id', 'default'), 'revision': value['revision'], 'direct_edit_pending': dirty, 'file_sha256': digest(data or b''), 'proposals': selected[:limit], 'total_matching': len(selected), 'truncated': len(selected) > limit, 'obligations': value['obligations'][:limit], 'total_obligations': len(value['obligations']), 'delivery': value.get('delivery'), 'resume': 'review-edit' if dirty else 'Review open obligations and pending proposal states', 'history_entries': len(value['history'])}

def validate_ledger(api, value):
    if not isinstance(value.get('proposals'), list) or not isinstance(value.get('obligations'), list) or (not isinstance(value.get('history'), list)) or (not isinstance(value.get('operations'), dict)):
        raise api.Error('Malformed ledger collections; restore reviewed history')
    if not isinstance(value.get('narrative_sha256'), str):
        raise api.Error('Malformed narrative integrity marker')
    if any((not isinstance(k, str) or not isinstance(v, str) for (k, v) in value['operations'].items())):
        raise api.Error('Malformed operation history')
    delivery = value.get('delivery')
    if delivery is not None and (not isinstance(delivery, dict) or not isinstance(delivery.get('draft'), str) or (not isinstance(delivery.get('sha256'), str))):
        raise api.Error('Malformed delivery receipt')
    if any((not isinstance(item, dict) for item in value['history'])):
        raise api.Error('Malformed revision history entries')
    ids = set()
    for node in value['proposals']:
        if not isinstance(node, dict) or not {'finding', 'owner', 'state'} <= set(node):
            raise api.Error('Malformed finding node')
        validate_finding(api, node['finding'])
        if node['finding']['id'] in ids:
            raise api.Error('Duplicate finding ID')
        ids.add(node['finding']['id'])
        if node['state'] not in ('PROPOSED', 'RECORDED', 'RETURNED', 'INTEGRATED', 'UNVERIFIED'):
            raise api.Error('Invalid node state')
        if not isinstance(node['owner'], str) or not node['owner'].strip():
            raise api.Error('Node owner is required')
        if node['state'] in ('RECORDED', 'RETURNED', 'INTEGRATED'):
            if type(node.get('accepted_revision')) is not int or node['accepted_revision'] < 1:
                raise api.Error('Recorded node requires accepted revision')
        if node['state'] in ('RETURNED', 'INTEGRATED'):
            if not isinstance(node.get('return_receipt'), dict) or not isinstance(node['return_receipt'].get('transcript_sha256'), str) or (not isinstance(node['return_receipt'].get('verified_passages'), list)) or (node.get('return_finding_sha256') != digest(canonical(node['finding']).encode())):
                raise api.Error('Returned node requires a current pinned transcript')
        disposition = node.get('disposition')
        if disposition is not None:
            if not isinstance(disposition, dict) or disposition.get('disposition') not in ('USER_DELIVERY', 'USED_INTERNAL', 'EXCLUDED', 'DEFERRED') or type(disposition.get('decision_critical')) is not bool:
                raise api.Error('Malformed finding disposition')
            if any((not isinstance(disposition.get(k), str) or not disposition[k].strip() for k in ('specified_by', 'reason', 'condition'))) or disposition['specified_by'] == node['owner']:
                raise api.Error('Invalid independent disposition')
            if disposition['decision_critical'] and disposition['disposition'] not in ('USER_DELIVERY', 'DEFERRED'):
                raise api.Error('Decision-critical disposition cannot exclude delivery')
            if disposition['disposition'] == 'DEFERRED' and (not isinstance(disposition.get('uncertainty_text'), str) or not disposition['uncertainty_text'].strip()):
                raise api.Error('Deferral requires material uncertainty text')
    for node in value['proposals']:
        for relation in node['finding']['relations']:
            if relation['target'] not in ids or relation['target'] == node['finding']['id']:
                raise api.Error('Relation requires an existing different node target')
    seen = set()
    for obligation in value['obligations']:
        if not isinstance(obligation, dict) or not {'id', 'finding_ids', 'specified_by', 'state', 'text', 'expected_scope', 'question'} <= set(obligation):
            raise api.Error('Malformed obligation')
        if not isinstance(obligation['id'], str) or not obligation['id'] or obligation['id'] in seen:
            raise api.Error('Duplicate/invalid obligation ID')
        seen.add(obligation['id'])
        if obligation['state'] not in ('OPEN', 'CURRENT', 'INVALIDATED'):
            raise api.Error('Invalid obligation state')
        if not isinstance(obligation['specified_by'], str) or not obligation['specified_by'].strip() or (not isinstance(obligation['question'], str)) or (not obligation['question'].strip()):
            raise api.Error('Obligation reviewer/question required')
        if not isinstance(obligation['expected_scope'], dict) or any((not isinstance(k, str) or not isinstance(v, str) or (not v.strip()) for (k, v) in obligation['expected_scope'].items())):
            raise api.Error('Invalid obligation expected_scope')
        if not isinstance(obligation['finding_ids'], list) or any((not isinstance(x, str) or x not in ids for x in obligation['finding_ids'])):
            raise api.Error('Obligation refers to missing findings')
        if not isinstance(obligation['text'], str):
            raise api.Error('Invalid obligation text')

def impacts(value, changed):
    affected = set(changed)
    while True:
        more = {node['finding']['id'] for node in value['proposals'] if any((rel['target'] in affected for rel in node['finding']['relations']))}
        if more <= affected:
            break
        affected |= more
    for obligation in value['obligations']:
        if affected.intersection(obligation['finding_ids']):
            obligation['state'] = 'INVALIDATED'
    if affected:
        value.pop('delivery', None)
    return sorted(affected)

def delta(before, after):
    """Retain per-item preimages rather than repeated ledger-sized snapshots."""
    changes = []
    for collection in ('proposals', 'obligations'):
        old = {x['finding']['id'] if collection == 'proposals' else x['id']: x for x in before[collection]}
        new = {x['finding']['id'] if collection == 'proposals' else x['id']: x for x in after[collection]}
        for key in sorted(old.keys() | new.keys()):
            if old.get(key) != new.get(key):
                changes.append({'collection': collection, 'id': key, 'before': old.get(key), 'after': new.get(key)})
    if before.get('delivery') != after.get('delivery'):
        changes.append({'collection': 'delivery', 'before': before.get('delivery'), 'after': after.get('delivery')})
    return changes

def dispatch(api, root, args, _generated_payload=None):
    delivery = api.companion('ris_delivery')
    cfg = api.config(root)
    if args.action == 'search':
        return search(api, root, args)
    if args.action != 'inspect' and (not args.authorize_record) and (cfg['recording_policy'] != 'significant'):
        raise api.Error('Recording policy requires explicit --authorize-record')
    question = getattr(args, 'question', 'default')
    relative = location(api, cfg, question)
    path = api.inside(root, relative)
    with nullcontext() if args.action == 'inspect' else api.project_lock(root):
        if api.config(root) != cfg:
            raise api.Error('Project configuration changed; reload before proceeding')
        data = delivery.read_file(api, root, relative)[1] if path.exists() else None
        (value, narrative) = parse(api, data, cfg) if data is not None else ({'schema_version': 1, 'project_id': cfg['project_id'], 'question_id': question, 'revision': 0, 'proposals': [], 'obligations': [], 'history': [], 'operations': {}, 'narrative_sha256': digest(b'\n')}, '\n')
        validate_ledger(api, value)
        if value.get('question_id', 'default') != question:
            raise api.Error('Question binding mismatch')
        dirty = data is not None and (data != render(value, narrative).encode() or value.get('content_sha256') != digest(canonical({k: v for (k, v) in value.items() if k != 'content_sha256'}).encode())) or digest(narrative.encode()) != value['narrative_sha256']
        if args.action == 'inspect':
            result = dict(summary(value, narrative, data, args, dirty), path=relative)
            result['evidence_checks'] = {x['finding']['id']: evidence_checks(api, root, x) for x in result['proposals']}
            result['reuse_status'] = {ident: 'CURRENT' if all((c['status'] == 'CURRENT' for c in checks)) else 'UNKNOWN' for (ident, checks) in result['evidence_checks'].items()}
            if value.get('delivery'):
                try:
                    (_, draft) = delivery.read_file(api, root, value['delivery']['draft'])
                    result['delivery_current'] = not dirty and digest(draft) == value['delivery']['sha256'] and all((check['status'] == 'CURRENT' for node in value['proposals'] for check in evidence_checks(api, root, node) if check['kind'] == 'project-file'))
                except (OSError, api.Error):
                    result['delivery_current'] = False
            return result
        if _generated_payload is not None:
            if args.action != 'propose':
                raise api.Error('Generated hook only supports typed proposals')
            payload = copy.deepcopy(_generated_payload)
        else:
            if not args.input:
                raise api.Error('--input is required for a mutation')
            (_, input_bytes) = delivery.read_file(api, root, args.input)
            try:
                payload = json.loads(input_bytes)
            except (ValueError, UnicodeDecodeError) as exc:
                raise api.Error('Input must be valid UTF-8 JSON') from exc
        if not isinstance(payload, dict) or payload.get('project_id') != cfg['project_id'] or payload.get('question_id', 'default') != question:
            raise api.Error('Input must bind to this project_id')
        key = args.idempotency_key
        if not isinstance(key, str) or not key or len(key) > 128:
            raise api.Error('A bounded --idempotency-key is required')
        operation = digest(canonical({'action': args.action, 'payload': payload}).encode())
        if dirty and args.action != 'review-edit':
            raise api.Error('Direct edit pending; review exact bytes before further writes')
        if key in value['operations']:
            if value['operations'][key] != operation:
                raise api.Error('Idempotency key was already used for different content')
            return dict(summary(value, narrative, data, args, dirty), replay=True)
        if type(args.expected_revision) is not int or args.expected_revision < 0:
            raise api.Error('Expected revision must be a nonnegative integer')
        if args.expected_revision != value['revision']:
            raise api.Error('Findings revision changed; inspect and review again')
        if not args.authorize_record and cfg['recording_policy'] != 'significant':
            raise api.Error('Recording policy requires explicit --authorize-record')
        before = copy.deepcopy(value)
        action = args.action
        affected = []
        if action == 'propose':
            item = payload.get('finding')
            validate_finding(api, item)
            if any((x['finding']['id'] == item['id'] for x in value['proposals'])):
                raise api.Error('Finding ID already exists; use a new ID and supersedes relation')
            if not isinstance(payload.get('owner'), str) or not payload['owner'].strip():
                raise api.Error('Proposal owner is required')
            candidates = duplicate_candidates(item, value['proposals'])
            if any((c['kind'] == 'EXACT_CONDITIONED_DUPLICATE' for c in candidates)):
                resolution = payload.get('duplicate_resolution')
                exact_ids = {c['id'] for c in candidates if c['kind'] == 'EXACT_CONDITIONED_DUPLICATE'}
                if not valid_duplicate_resolution(resolution, payload['owner'], exact_ids):
                    raise api.Error('Exact conditioned duplicate requires independent KEEP_SEPARATE resolution; no automatic merge')
            value['proposals'].append({'finding': item, 'owner': payload['owner'], 'state': 'PROPOSED'})
            if candidates:
                value['proposals'][-1]['duplicate_candidates'] = candidates
                if payload.get('duplicate_resolution'):
                    value['proposals'][-1]['duplicate_resolution'] = payload['duplicate_resolution']
            superseded = {r['target'] for r in item['relations'] if r['kind'] == 'supersedes'}
            if superseded:
                affected = impacts(value, superseded)
            value.pop('delivery', None)
        elif action in ('accept', 'return', 'integrate'):
            matches = [x for x in value['proposals'] if x['finding']['id'] == payload.get('id')]
            if len(matches) != 1:
                raise api.Error('Select one existing proposal')
            node = matches[0]
            (required, following) = {'accept': (('PROPOSED', 'UNVERIFIED'), 'RECORDED'), 'return': (('RECORDED', 'RETURNED'), 'RETURNED'), 'integrate': (('RETURNED',), 'INTEGRATED')}[action]
            if node['state'] not in required:
                raise api.Error('Proposal transition requires ' + ','.join(required))
            if payload.get('owner') != node['owner']:
                raise api.Error('Transition must bind to designated owner')
            if not isinstance(payload.get('note'), str) or not payload['note'].strip():
                raise api.Error('Owner receipt/integration note is required')
            if action == 'return':
                if payload.get('finding_revision') != node.get('accepted_revision'):
                    raise api.Error('Owner return must pin the accepted finding revision')
                transcript = payload.get('transcript')
                if not isinstance(transcript, str) or not transcript.strip():
                    raise api.Error('Actual owner return transcript is required')
                required = [node['finding']['statement']] + [limitation for source in node['finding']['provenance'] for limitation in source['limitations'] if limitation.strip()]
                scope = condition_passage(node['finding'])
                if scope:
                    required.append(scope)
                paragraphs = delivery.paragraphs(transcript)
                if any((not delivery.contains(paragraphs, text) for text in required)):
                    raise api.Error('Owner return omits finding facts or limitations; correct transcript and retry')
                node['return_receipt'] = {'owner': node['owner'], 'finding_revision': node['accepted_revision'], 'transcript_sha256': digest(transcript.encode()), 'verified_passages': required}
                node['return_finding_sha256'] = digest(canonical(node['finding']).encode())
            if action == 'integrate' and node.get('return_finding_sha256') != digest(canonical(node['finding']).encode()):
                raise api.Error('Owner receipt is stale; obtain corrected return first')
            if action == 'accept':
                node['accepted_revision'] = value['revision'] + 1
            node['state'] = following
            node[action + '_note'] = payload['note']
            affected = impacts(value, {node['finding']['id']})
        elif action == 'obligate':
            incoming = payload.get('obligation')
            if not isinstance(incoming, dict) or not {'id', 'specified_by'} <= set(incoming):
                raise api.Error('Obligation id and specified_by are required')
            if any((x['id'] == incoming['id'] for x in value['obligations'])):
                raise api.Error('Obligation ID must be new; resolve an existing frozen obligation')
            obligation = {'id': incoming['id'], 'specified_by': incoming['specified_by'], 'question': incoming.get('question', incoming.get('text', '')), 'expected_scope': incoming.get('expected_scope', {}), 'finding_ids': [], 'text': '', 'state': 'OPEN'}
            if not obligation['expected_scope']:
                raise api.Error('Freeze a nonempty expected_scope axes map before resolving findings')
            value['obligations'].append(obligation)
            value.pop('delivery', None)
        elif action == 'resolve':
            matches = [x for x in value['obligations'] if x['id'] == payload.get('id')]
            if len(matches) != 1:
                raise api.Error('Select an existing frozen obligation')
            obligation = matches[0]
            if payload.get('specified_by') != obligation['specified_by']:
                raise api.Error('Frozen obligation reviewer must resolve it')
            ids = payload.get('finding_ids')
            if not isinstance(ids, list) or not ids or any((not isinstance(x, str) for x in ids)) or (len(set(ids)) != len(ids)):
                raise api.Error('Resolution requires unique finding IDs')
            for fid in ids:
                node = next((x for x in value['proposals'] if x['finding']['id'] == fid), None)
                if not node or node['state'] != 'INTEGRATED':
                    raise api.Error('Obligations require integrated findings')
                if node['owner'] == obligation['specified_by']:
                    raise api.Error('Obligation requires independent reviewer')
                if any((node['finding']['axes'].get(k) != v for (k, v) in obligation['expected_scope'].items())):
                    raise api.Error('Finding does not satisfy frozen expected_scope')
            text = payload.get('text')
            if not isinstance(text, str) or not text.strip():
                raise api.Error('Independent reviewer must specify delivery text')
            obligation.update(finding_ids=ids, text=text, state='CURRENT')
            value.pop('delivery', None)
        elif action == 'disposition':
            node = next((x for x in value['proposals'] if x['finding']['id'] == payload.get('id')), None)
            if not node or node['state'] != 'INTEGRATED':
                raise api.Error('Disposition requires an integrated finding')
            reviewer = payload.get('specified_by')
            if not isinstance(reviewer, str) or not reviewer.strip() or reviewer == node['owner']:
                raise api.Error('Disposition requires independent reviewer')
            kind = payload.get('disposition')
            if kind not in ('USER_DELIVERY', 'USED_INTERNAL', 'EXCLUDED', 'DEFERRED'):
                raise api.Error('Unknown disposition')
            if type(payload.get('decision_critical')) is not bool:
                raise api.Error('Reviewer must explicitly classify decision_critical')
            if payload['decision_critical'] and kind not in ('USER_DELIVERY', 'DEFERRED'):
                raise api.Error('Decision-critical findings require user delivery or reviewed deferral')
            if any((not isinstance(payload.get(k), str) or not payload[k].strip() for k in ('reason', 'condition'))):
                raise api.Error('Disposition reason and condition are required')
            if kind == 'DEFERRED' and (not isinstance(payload.get('uncertainty_text'), str) or not payload['uncertainty_text'].strip()):
                raise api.Error('Deferral requires material uncertainty text for the answer')
            node['disposition'] = {k: payload[k] for k in ('specified_by', 'disposition', 'decision_critical', 'reason', 'condition')}
            if kind == 'DEFERRED':
                node['disposition']['uncertainty_text'] = payload['uncertainty_text']
            value.pop('delivery', None)
        elif action == 'deliver':
            if not value['obligations'] or any((x['state'] != 'CURRENT' for x in value['obligations'])):
                raise api.Error('No current independently specified delivery obligations; unanswered or invalidated scope remains')
            if any((x['state'] != 'INTEGRATED' for x in value['proposals'])):
                raise api.Error('Pending/unreturned/unverified findings remain; integrate every decision-bearing fact')
            covered = {fid for x in value['obligations'] for fid in x['finding_ids']}
            if any(('disposition' not in x for x in value['proposals'])):
                raise api.Error('Every integrated finding needs an independent disposition')
            if any((x['disposition']['disposition'] == 'USER_DELIVERY' and x['finding']['id'] not in covered for x in value['proposals'])):
                raise api.Error('Every user-delivery finding needs an independent obligation')
            if not isinstance(payload.get('draft'), str) or not payload['draft']:
                raise api.Error('Draft path is required')
            (_, draft_bytes) = delivery.read_file(api, root, payload['draft'])
            paragraphs = delivery.paragraphs(draft_bytes.decode('utf-8'))
            required = [(x['id'], x['text']) for x in value['obligations']]
            for node in value['proposals']:
                if node['disposition']['disposition'] == 'DEFERRED':
                    required.append((node['finding']['id'] + ':uncertainty', node['disposition']['uncertainty_text']))
                if node['disposition']['disposition'] != 'USER_DELIVERY':
                    continue
                finding = node['finding']
                required.append((finding['id'], finding['statement']))
                scope = condition_passage(finding)
                if scope:
                    required.append((finding['id'] + ':conditions', scope))
                required.extend(((finding['id'] + ':limitation', limitation) for source in finding['provenance'] for limitation in source['limitations'] if limitation.strip()))
            missed = [ident for (ident, text) in required if not delivery.contains(paragraphs, text)]
            if missed:
                raise api.Error('Draft omits required facts/limitations/passages: ' + ', '.join(missed))
            if any((check['status'] != 'CURRENT' for node in value['proposals'] for check in evidence_checks(api, root, node) if check['kind'] == 'project-file')):
                raise api.Error('Project-file evidence is missing or stale; update provenance and review before delivery')
            value['delivery'] = {'draft': payload['draft'], 'sha256': digest(draft_bytes), 'scope': 'Exact transport; no semantic/scientific validation', 'revision': value['revision'] + 1}
        elif action == 'review-edit':
            if not data or payload.get('file_sha256') != digest(data):
                raise api.Error('Review must pin exact inspected file bytes')
            if not isinstance(payload.get('reason'), str) or not payload['reason'].strip():
                raise api.Error('Review reason is required')
            folder = api.inside(root, '.ris/history')
            folder.mkdir(exist_ok=True)
            backup = api.inside(root, '.ris/history/' + digest(data) + '.md')
            if backup.exists():
                if backup.read_bytes() != data:
                    raise api.Error('History preimage hash collision')
            else:
                api.atomic_note_write(backup, data)
            value['history'].append({'revision': value['revision'], 'direct_edit_preimage': backup.relative_to(root).as_posix(), 'sha256': digest(data), 'review_reason': payload['reason']})
            for node in value['proposals']:
                node['state'] = 'UNVERIFIED'
                node['finding']['status'] = 'UNKNOWN'
                node.pop('disposition', None)
                for field in ('accept_note', 'return_note', 'integrate_note', 'accepted_revision', 'return_receipt', 'return_finding_sha256'):
                    node.pop(field, None)
            for obligation in value['obligations']:
                obligation['state'] = 'INVALIDATED'
            value.pop('delivery', None)
            affected = [x['finding']['id'] for x in value['proposals']]
        validate_ledger(api, value)
        value['history'].append({'revision': value['revision'] + 1, 'action': action, 'idempotency_key': key, 'changes': delta(before, value), 'affected': affected})
        value['revision'] += 1
        value['operations'][key] = operation
        value['narrative_sha256'] = digest(narrative.encode())
        value['content_sha256'] = digest(canonical({k: v for (k, v) in value.items() if k != 'content_sha256'}).encode())
        path.parent.mkdir(parents=True, exist_ok=True)
        output = render(value, narrative).encode()
        api.atomic_note_write(path, output, expected=data)
        return dict(summary(value, narrative, output, args), path=relative)

def evidence_checks(api, root, node):
    """Only explicit file: sources authorize project-file inspection."""
    checks = []
    for source in node['finding']['provenance']:
        if not source['source'].startswith('file:'):
            checks.append({'kind': 'citation', 'source': source['source'], 'status': 'UNKNOWN', 'reason': 'Asserted locator; not independently fetched or verified'})
            continue
        relative = source['source'][5:]
        try:
            actual = api.study_evidence_hash(root, relative)
            current = source['revision'] == 'sha256:' + actual['sha256']
            checks.append({'kind': 'project-file', 'source': source['source'], 'status': 'CURRENT' if current else 'STALE', 'actual_sha256': actual['sha256']})
        except (OSError, api.Error):
            checks.append({'kind': 'project-file', 'source': source['source'], 'status': 'UNKNOWN', 'reason': 'Explicit backing project file is unavailable or unsafe'})
    return checks

def projected_context(api, root, relative, limit=20):
    """Return bounded clean governed context, or None for a different note kind."""
    from types import SimpleNamespace
    question = canonical_question_for_path(api, root, relative)
    if question is None:
        return None
    args = SimpleNamespace(action='inspect', question=question, query=None, node_id=None, limit=limit)
    value = dispatch(api, root, args)
    if value['direct_edit_pending']:
        raise api.Error('Governed findings have pending direct edits; run findings review-edit before retrieval')
    return json.dumps(value, ensure_ascii=False, indent=2)

def search(api, root, args):
    """Bounded project-local discovery; never selects mutation or delivery scope."""
    from types import SimpleNamespace
    query = getattr(args, 'query', None)
    limit = getattr(args, 'limit', 20)
    if not isinstance(query, str) or not query.strip() or len(query) > 500:
        raise api.Error('Search requires a nonempty --query of at most 500 characters')
    if type(limit) is not int or not 1 <= limit <= 100:
        raise api.Error('Search limit must be 1..100')
    cfg = api.config(root)
    target = None
    target_digest = None
    if getattr(args, 'target_conditions', None):
        delivery = api.companion('ris_delivery')
        (_, raw) = delivery.read_file(api, root, args.target_conditions)
        target_digest = digest(raw)
        target_payload = json.loads(raw)
        if not isinstance(target_payload, dict) or target_payload.get('project_id') != cfg['project_id'] or (not isinstance(target_payload.get('conditions'), dict)):
            raise api.Error('Target conditions require this project_id and a conditions map')
        target = target_payload['conditions']
        if any((not isinstance(k, str) or not isinstance(v, str) or (not v.strip()) for (k, v) in target.items())):
            raise api.Error('Target conditions must map names to explicit strings')
    folder = api.inside(root, api.research_path(cfg, 'research/findings'))
    (paths, snapshot) = discovery_snapshot(api, root, folder)
    binding = {'project_id': cfg['project_id'], 'query': query, 'target': digest(canonical(target).encode()), 'snapshot': snapshot}
    (file_index, node_index) = (0, 0)
    skipped_before = 0
    token = getattr(args, 'cursor', None)
    if token:
        try:
            if len(token) > 4096:
                raise ValueError('oversized')
            cursor = json.loads(base64.urlsafe_b64decode(token.encode() + b'=' * (-len(token) % 4)))
            if not isinstance(cursor, dict) or cursor.get('version') != 1 or any((cursor.get(k) != v for (k, v) in binding.items())):
                raise ValueError('binding')
            (file_index, node_index) = (cursor['file'], cursor['node'])
            skipped_before = cursor.get('skipped_before', 0)
            if type(skipped_before) is not int or skipped_before < 0:
                raise ValueError('skipped offset')
            if type(file_index) is not int or type(node_index) is not int or file_index < 0 or (file_index > len(paths)) or (node_index < 0):
                raise ValueError('offset')
        except (ValueError, KeyError, TypeError, UnicodeError) as exc:
            raise api.Error('Discovery cursor is invalid or snapshot changed; restart search without --cursor') from exc
    hits = []
    hit_nodes = []
    skipped = []
    scanned = 0
    scanned_nodes = 0
    while file_index < len(paths) and scanned < 200 and (scanned_nodes < 1000) and (len(hits) < limit):
        path = paths[file_index]
        relative = path.relative_to(root).as_posix()
        scanned += 1
        if path.is_symlink():
            skipped.append({'path': relative, 'reason': 'unsafe-path'})
            file_index += 1
            node_index = 0
            continue
        try:
            question = canonical_question_for_path(api, root, relative)
            if question is None:
                file_index += 1
                node_index = 0
                continue
            selected = SimpleNamespace(action='inspect', question=question, query=None, node_id=None, limit=1)
            result = dispatch(api, root, selected)
        except (api.Error, OSError, ValueError, UnicodeError):
            skipped.append({'path': relative, 'reason': 'invalid-or-unavailable'})
            file_index += 1
            node_index = 0
            continue
        if result['project_id'] != cfg['project_id']:
            raise api.Error('Project identity changed during discovery')
        if result['direct_edit_pending']:
            skipped.append({'path': relative, 'reason': 'pending-direct-edit'})
            file_index += 1
            node_index = 0
            continue
        delivery = api.companion('ris_delivery')
        (_, raw) = delivery.read_file(api, root, relative)
        if digest(raw) != result['file_sha256']:
            raise api.Error('Discovery snapshot changed after inspection; restart search without --cursor')
        (value, _) = parse(api, raw, cfg)
        validate_ledger(api, value)
        nodes = value['proposals']
        if node_index > len(nodes):
            raise api.Error('Discovery cursor node offset is invalid; restart search')
        while node_index < len(nodes) and scanned_nodes < 1000 and (len(hits) < limit):
            node = nodes[node_index]
            node_index += 1
            scanned_nodes += 1
            if query.casefold() not in canonical(node).casefold() or node['state'] in ('PROPOSED', 'UNVERIFIED'):
                continue
            ident = node['finding']['id']
            checks = evidence_checks(api, root, node)
            if any((c['kind'] == 'project-file' and c['status'] != 'CURRENT' for c in checks)):
                skipped.append({'path': relative, 'id': ident, 'reason': 'stale-or-unavailable-project-evidence'})
                continue
            statement = node['finding']['statement']
            hit_nodes.append(node)
            hits.append({'project_id': cfg['project_id'], 'question_id': question, 'revision': value['revision'], 'path': relative, 'id': ident, 'statement_excerpt': statement[:500], 'conditions': dict(list(node['finding']['conditions'].items())[:20]), 'conditions_truncated': len(node['finding']['conditions']) > 20, 'axes': dict(list(node['finding']['axes'].items())[:20]), 'axes_truncated': len(node['finding']['axes']) > 20, 'applicability': compare_conditions(api, node['finding']['conditions'], target), 'inspect': {'question': question, 'node_id': ident}, 'excerpt_truncated': len(statement) > 500, 'status': node['finding']['status'], 'state': node['state'], 'source_freshness': checks, 'reuse_status': 'CURRENT' if all((c['status'] == 'CURRENT' for c in checks)) else 'UNKNOWN'})
        if node_index == len(nodes):
            file_index += 1
            node_index = 0
    if target_digest is not None:
        (_, current_target) = api.companion('ris_delivery').read_file(api, root, args.target_conditions)
        if digest(current_target) != target_digest:
            raise api.Error('Discovery target conditions changed during page creation; restart search without --cursor')
    for (hit, node) in zip(hits, hit_nodes):
        if evidence_checks(api, root, node) != hit['source_freshness']:
            raise api.Error('Discovery evidence changed during page creation; restart search without --cursor')
    (_, after) = discovery_snapshot(api, root, folder)
    if after != snapshot or api.config(root) != cfg:
        raise api.Error('Discovery snapshot changed during page creation; restart search without --cursor')
    skipped_total = skipped_before + len(skipped)
    remaining = file_index < len(paths)
    next_cursor = None
    if remaining:
        state = dict(binding, version=1, file=file_index, node=node_index, skipped_before=skipped_total)
        next_cursor = base64.urlsafe_b64encode(canonical(state).encode()).decode().rstrip('=')
    return {'project_id': cfg['project_id'], 'hits': hits, 'more': remaining, 'next_cursor': next_cursor, 'scan_complete': not remaining and skipped_total == 0, 'traversal_complete': not remaining, 'scanned': scanned, 'scanned_nodes': scanned_nodes, 'skipped': skipped[:100], 'skipped_total': skipped_total, 'skipped_previous_pages': skipped_before, 'skipped_truncated': len(skipped) > 100, 'snapshot': snapshot}

def discovery_snapshot(api, root, folder):
    """Metadata pin catches honest writes without reading unselected file contents."""
    paths = []
    metadata = []
    if folder.exists():
        for path in sorted(folder.iterdir(), key=lambda p: p.name):
            if path.name != 'knowledge.md' and (not (path.name.startswith('knowledge-') and path.name.endswith('.md'))):
                continue
            try:
                info = path.lstat()
            except OSError as exc:
                raise api.Error('Discovery directory changed; restart search') from exc
            paths.append(path)
            metadata.append((path.name, info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns))
    return (paths, digest(canonical(metadata).encode()))

def condition_passage(finding):
    """An exact key/value scope paragraph; never infer which condition is material."""
    conditions = finding['conditions']
    if not conditions or all((condition_token_present(finding['statement'], k, v) for (k, v) in conditions.items())):
        return None
    return 'Conditions: ' + '; '.join((k + '=' + v for (k, v) in sorted(conditions.items()))) + '.'

def duplicate_candidates(finding, nodes):
    candidates = []
    normalized = ' '.join(finding['statement'].casefold().split())
    words = set(re.findall('\\w+', normalized))
    for node in nodes:
        other = node['finding']
        other_normalized = ' '.join(other['statement'].casefold().split())
        other_words = set(re.findall('\\w+', other_normalized))
        same = normalized == other_normalized
        similarity = len(words & other_words) / len(words | other_words) if words | other_words else 0
        if not same and (min(len(words), len(other_words)) < 5 or similarity < 0.8):
            continue
        conditioned = finding['conditions'] == other['conditions'] and finding['axes'] == other['axes']
        candidates.append({'id': other['id'], 'kind': 'EXACT_CONDITIONED_DUPLICATE' if same and conditioned else 'POTENTIAL_DUPLICATE_OR_CONDITION_CONFLICT', 'conditions_equal': finding['conditions'] == other['conditions'], 'axes_equal': finding['axes'] == other['axes'], 'scope': 'Lexical signal only; no semantic merge'})
    return candidates

def compare_conditions(api, source, target):
    if target is None:
        return {'status': 'NOT_ASSESSED', 'reason': 'No target conditions supplied; evidence freshness is separate'}
    unknown = api.companion('ris_knowledge').UNKNOWN_VALUES
    missing = []
    conflicts = []
    for key in sorted(source.keys() | target.keys()):
        left = source.get(key)
        right = target.get(key)
        if left is None or right is None or left.strip().casefold() in unknown or (right.strip().casefold() in unknown):
            missing.append(key)
        elif left != right:
            conflicts.append(key)
    if conflicts:
        return {'status': 'CONFLICT', 'conflicting_keys': conflicts, 'unknown_keys': missing, 'scope': 'Declared string values differ; no causal or semantic equivalence asserted'}
    if missing or not source or (not target):
        return {'status': 'UNKNOWN', 'unknown_keys': missing, 'scope': 'Missing or unresolved declared condition values'}
    return {'status': 'MATCH', 'scope': 'Exact declared key/value equality only; not scientific applicability validation'}

def propose_generated(api, root, question, expected_revision, key, owner, finding, authorized=False):
    """Trusted local producer hook; same governed proposal path, without a staged file."""
    from types import SimpleNamespace
    cfg = api.config(root)
    payload = {'project_id': cfg['project_id'], 'question_id': question, 'owner': owner, 'finding': finding}
    args = SimpleNamespace(action='propose', question=question, expected_revision=expected_revision, idempotency_key=key, authorize_record=authorized, input=None, limit=20, query=None, node_id=None)
    return dispatch(api, root, args, _generated_payload=payload)

def valid_duplicate_resolution(resolution, owner, expected_ids):
    if not isinstance(resolution, dict) or resolution.get('action') != 'KEEP_SEPARATE':
        return False
    if any((not isinstance(resolution.get(k), str) or not resolution[k].strip() for k in ('reviewed_by', 'reason'))) or resolution['reviewed_by'] == owner:
        return False
    ids = resolution.get('candidate_ids')
    return isinstance(ids, list) and all((isinstance(x, str) for x in ids)) and (set(ids) == expected_ids)

def condition_token_present(statement, key, value):
    token = re.escape(key + '=' + value)
    return re.search('(?<![\\w])' + token + '(?=$|[\\s;,)\\]]|[.!?](?=\\s|$))', statement) is not None
