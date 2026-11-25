"""Conditional strategy records in existing originating notes; no strategy database."""
import hashlib
import json
import re

BEGIN = '<!-- ris:strategy -->\n```json\n'
END = '\n```\n<!-- /ris:strategy -->'
APPLICATION_BEGIN = '<!-- ris:strategy-application -->\n```json\n'
APPLICATION_END = '\n```\n<!-- /ris:strategy-application -->'


def evidence(ris, root, items):
    if not isinstance(items, list) or not items:
        raise ris.Error('At least one local work evidence capture is required')
    checked = []
    ris_delivery = ris.companion('ris_delivery')
    for item in items:
        if not isinstance(item, dict) or set(item) != {'path', 'sha256', 'action', 'outcome'}:
            raise ris.Error('Work evidence needs path, sha256, action, outcome')
        for key in item:
            if not isinstance(item[key], str) or not item[key].strip():
                raise ris.Error('Work evidence fields must be nonempty strings')
        _, raw = ris_delivery.read_file(ris, root, item['path'])
        if hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ris.Error('Work evidence changed or hash mismatch')
        checked.append(dict(item, verification='local_bytes_match', action_execution='asserted_not_independently_observed'))
    return checked


def records(ris, text):
    if text.count(BEGIN) != text.count(END):
        raise ris.Error('Malformed originating strategy section')
    values = []
    for section in text.split(BEGIN)[1:]:
        try:
            value = json.loads(section.split(END, 1)[0])
        except (ValueError, TypeError) as exc:
            raise ris.Error('Malformed originating strategy JSON') from exc
        if (not isinstance(value,dict) or not isinstance(value.get('id'),str)
                or not isinstance(value.get('project_id'),str)
                or not isinstance(value.get('conditions'),dict) or not value['conditions']
                or any(not isinstance(k,str) or not isinstance(v,str) or not k.strip() or not v.strip()
                       for k,v in value['conditions'].items())
                or not isinstance(value.get('work_evidence'),list) or not value['work_evidence']):
            raise ris.Error('Malformed originating strategy record fields')
        for item in value['work_evidence']:
            if (not isinstance(item,dict) or set(item) != {'path','sha256','action','outcome'}
                    or any(not isinstance(v,str) or not v.strip() for v in item.values())):
                raise ris.Error('Malformed originating strategy work evidence')
        values.append(value)
    return values


def record(ris, root, body, expected_hash, authorized):
    cfg = ris.config(root)
    if cfg['recording_policy'] == 'manual' and not authorized:
        raise ris.Error('Manual policy requires explicit recording authority')
    required = {'id','origin_note','origin_question','input_revision','conditions','method','observed_outcome',
                'failure_cases','competing_explanation','confidence_limits','reopening_trigger','work_evidence'}
    if not isinstance(body, dict) or set(body) != required:
        raise ris.Error('Strategy requires the documented complete originating lesson fields')
    for key in required - {'conditions','work_evidence','failure_cases'}:
        if not isinstance(body[key], str) or not body[key].strip():
            raise ris.Error('Strategy '+key+' must be explicit')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', body['id']):
        raise ris.Error('Invalid strategy ID')
    if not isinstance(body['conditions'], dict) or not body['conditions'] or any(
            not isinstance(k,str) or not isinstance(v,str) or not k.strip() or not v.strip()
            for k,v in body['conditions'].items()):
        raise ris.Error('Strategy conditions must be a nonempty explicit map')
    if not isinstance(body['failure_cases'],list) or any(not isinstance(v,str) for v in body['failure_cases']):
        raise ris.Error('failure_cases must be a list')
    checked = evidence(ris, root, body['work_evidence'])
    path = ris.inside(root, body['origin_note'])
    raw = path.read_bytes()
    metadata = ris.frontmatter(raw.decode())
    if metadata.get('kind') not in {'finding','plan','study'} or metadata.get('project_id') != cfg['project_id']:
        raise ris.Error('Use an existing same-project finding, plan or study originating note')
    ris_knowledge = ris.companion('ris_knowledge')
    if not ris_knowledge.is_local_knowledge_metadata(metadata, cfg['project_id']):
        raise ris.Error('External strategy history is inert')
    prior = records(ris, raw.decode())
    if any(item['id'] == body['id'] for item in prior):
        raise ris.Error('Strategy ID already recorded; preserve history and use a new revision ID')
    value = dict(body, project_id=cfg['project_id'], checked_evidence=checked, scientific_transfer='unverified')
    rendered = raw.decode()+'\n\n'+BEGIN+json.dumps(value, ensure_ascii=False, indent=2)+END+'\n'
    return ris.safe_update(root, body['origin_note'], expected_hash, rendered)


def applications(ris, text, project_id, strategy_id):
    if text.count(APPLICATION_BEGIN) != text.count(APPLICATION_END):
        raise ris.Error('Malformed strategy application section')
    result = []
    for section in text.split(APPLICATION_BEGIN)[1:]:
        try:
            item = json.loads(section.split(APPLICATION_END,1)[0])
        except (ValueError,TypeError) as exc:
            raise ris.Error('Malformed strategy application JSON') from exc
        if not isinstance(item,dict) or not isinstance(item.get('strategy_id'),str):
            raise ris.Error('Malformed strategy application record')
        if item.get('project_id') == project_id and item['strategy_id'] == strategy_id:
            result.append(item)
    return result


def retrieve(ris, root, query, conditions, limit=20):
    if not isinstance(conditions,dict) or any(not isinstance(k,str) or not isinstance(v,str) for k,v in conditions.items()):
        raise ris.Error('Target conditions must map strings to strings')
    if not isinstance(query,str) or not query.strip() or not 1 <= limit <= 100:
        raise ris.Error('Search requires query and limit 1..100')
    results = []
    scanned = 0
    cfg = ris.config(root)
    for path, metadata, text in ris.notes(root):
        if metadata.get('project_id') != cfg['project_id']:
            continue
        if metadata.get('kind') not in {'finding','plan','study'}:
            continue
        for item in records(ris,text):
            scanned += 1
            if item.get('project_id') != cfg['project_id']:
                continue
            if not all(term in json.dumps(item,ensure_ascii=False).casefold() for term in query.casefold().split()):
                continue
            mismatch = {k: {'source': v, 'target': conditions.get(k)}
                        for k,v in item['conditions'].items() if conditions.get(k) != v or v.casefold() in {'unknown','unresolved','?'}}
            extra = sorted(set(conditions)-set(item['conditions']))
            freshness = 'bytes_match'
            try:
                evidence(ris, root, item['work_evidence'])
            except (ris.Error, OSError, ValueError):
                freshness = 'changed_or_unavailable'
            status = 'review_required' if not mismatch and not extra and freshness == 'bytes_match' else 'not_applicable_without_recheck'
            results.append({'strategy':item, 'origin_note':str(path.relative_to(root)),
                            'origin_sha256':hashlib.sha256(text.encode()).hexdigest(),
                            'application_history':applications(ris,text,cfg['project_id'],item['id']),
                            'applicability':status, 'mismatches':mismatch, 'extra_target_conditions':extra,
                            'evidence_freshness':freshness, 'transfer_verdict':'unverified',
                            'nonapplication': None if status == 'review_required' else 'Retain current strategy until conditions/evidence are rechecked'})
    results.sort(key=lambda item:(item['origin_note'],item['strategy']['id']))
    return {'results':results[:limit], 'matched':len(results), 'scanned_lessons':scanned,
            'same_project_only':True, 'causal_benefit':'not_established'}


def application(ris, root, body, expected_hash, authorized):
    """Append the inspected transfer/nonapplication to the originating lesson note."""
    cfg = ris.config(root)
    if cfg['recording_policy'] == 'manual' and not authorized:
        raise ris.Error('Manual policy requires explicit recording authority')
    required = {'origin_note','strategy_id','target_question','target_revision','target_conditions',
                'baseline_next_action','retrieval_changed_action','actual_action','observed_result',
                'negative_control','verdict','rationale','work_evidence'}
    if not isinstance(body,dict) or set(body) != required:
        raise ris.Error('Application requires complete target, counterfactual, action, control and verdict fields')
    for key in required - {'target_conditions','work_evidence'}:
        if not isinstance(body[key],str) or not body[key].strip():
            raise ris.Error('Application '+key+' must be explicit')
    if body['verdict'] not in {'supported within conditions','conditional','rejected','unverified','not applied'}:
        raise ris.Error('Unknown strategy application verdict')
    checked = evidence(ris,root,body['work_evidence'])
    target = retrieve(ris,root,body['strategy_id'],body['target_conditions'],100)
    selected = [item for item in target['results'] if item['strategy']['id'] == body['strategy_id']
                and item['origin_note'] == body['origin_note']]
    if len(selected) != 1:
        raise ris.Error('Select an existing same-project originating lesson')
    if selected[0]['applicability'] != 'review_required' and body['verdict'] == 'supported within conditions':
        raise ris.Error('Mismatched or stale lesson cannot be recorded as supported')
    path = ris.inside(root,body['origin_note'])
    text = path.read_text(encoding='utf-8')
    value = dict(body,project_id=cfg['project_id'],checked_evidence=checked,
                 applicability=selected[0]['applicability'],causal_benefit='not_established')
    return ris.safe_update(root,body['origin_note'],expected_hash,text+'\n\n<!-- ris:strategy-application -->\n```json\n'+json.dumps(value,ensure_ascii=False,indent=2)+'\n```\n<!-- /ris:strategy-application -->\n')
