#!/usr/bin/env python3
"""Validate Markdown decision graphs and render a portable, read-only exploration map."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

BLOCK = re.compile(r'^```project-plan\s*\n(.*?)^```\s*$', re.M | re.S)


def inside(root, relative):
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('Use a project-relative path without parent traversal')
    cursor = root
    for part in p.parts:
        cursor /= part
        if cursor.is_symlink():
            raise ValueError('Managed paths must not contain symlinks')
    if not cursor.resolve().is_relative_to(root):
        raise ValueError('Path leaves project')
    return cursor


def selected_ids(value):
    """Normalize legacy scalar selections without changing the source representation."""
    if value is None:return []
    if isinstance(value,str):return [value]
    if isinstance(value,list) and all(isinstance(v,str) for v in value):return value
    raise ValueError('Selections must be an option ID or a list of option IDs')


def validate_selections(node,value):
    selected=selected_ids(value)
    if len(selected)!=len(set(selected)):raise ValueError('Duplicate selected option in one decision')
    if node.get('selection_mode','single')=='single' and len(selected)>1:
        raise ValueError('Single-select decision cannot contain multiple selections')
    known={o['id'] for o in node.get('options',[])}
    if any(oid not in known for oid in selected):raise ValueError('Selection is not an option')
    return selected


def validate(g):
    if g.get('schema_version') != 1 or not g.get('plan_id') or not g.get('goal'):
        raise ValueError('Expected schema_version 1, stable plan_id and goal')
    nodes = g.get('nodes', [])
    ids = [n['id'] for n in nodes]
    if any(not isinstance(i,str) or not i for i in ids):
        raise ValueError('Node IDs must be nonempty strings')
    if not nodes or len(ids) != len(set(ids)):
        raise ValueError('Nodes must be nonempty and have unique IDs')
    by_id = {n['id']: n for n in nodes}
    for n in nodes:
        if n.get('kind') not in ('outcome', 'decision', 'milestone', 'gate') or not n.get('title'):
            raise ValueError('Every node needs kind and title')
        if n.get('status') not in ('unexplored', 'provisional', 'confirmed', 'deferred', 'rejected', 'superseded'):
            raise ValueError('Unknown node status')
        if n['kind'] == 'outcome' and not n.get('success_criteria'):
            raise ValueError('Outcome needs success_criteria')
        if 'component' in n and (not isinstance(n['component'],str) or not n['component'].strip()):
            raise ValueError('Component label must be a nonempty string')
        options = n.get('options', [])
        option_ids = [o['id'] for o in options]
        if len(option_ids) != len(set(option_ids)):
            raise ValueError('Duplicate option ID')
        if n['kind'] == 'decision':
            if len(options) < 2 and not n.get('alternatives_limit_reason'):
                raise ValueError('Decision needs alternatives or impossibility reason')
            for o in options:
                if not all(isinstance(o.get(k),str) and o[k].strip() for k in ('id', 'title', 'forecast', 'conditions', 'resources', 'risk', 'uncertainty', 'verification')):
                    raise ValueError('Option needs forecast, conditions, resources, risk, uncertainty and verification')
                for estimate in o.get('estimates', []):
                    if type(estimate.get('value')) not in (int,float) or not all(estimate.get(k) for k in ('unit','derivation','conditions','source')) or estimate['source'] not in g.get('sources', {}):
                        raise ValueError('Numeric estimates need unit, derivation, conditions and source')
                for ref in o.get('evidence', []):
                    if ref not in g.get('sources', {}):
                        raise ValueError('Unknown evidence source: '+ref)
        if n.get('selection_mode','single') not in ('single','multiple'):
            raise ValueError('Unknown selection mode')
        validate_selections(n,n.get('selected'))
        if n.get('selected') and not n.get('selection_reason'):
            raise ValueError('Selection needs rationale')
        if n.get('status') == 'confirmed' and n['kind'] == 'decision' and not n.get('selected'):
            raise ValueError('Confirmed decision needs a selection')
        for obs in n.get('observations', []):
            if not all(obs.get(k) for k in ('date','result','difference','evidence')):
                raise ValueError('Observation needs date, result, difference and evidence')
    if g.get('current_node') and g['current_node'] not in by_id:
        raise ValueError('Unknown current node')
    for key, s in g.get('sources', {}).items():
        if not all(s.get(k) for k in ('title', 'locator', 'retrieved', 'review_scope')):
            raise ValueError('Source needs title, locator, retrieved date and actual review_scope: '+key)
        if re.match(r'^[a-z][a-z0-9+.-]*:', s['locator'], re.I) and not s['locator'].startswith(('https://', 'http://', 'zotero://', 'obsidian://')):
            raise ValueError('Unsupported evidence URI')
    for e in g.get('edges', []):
        if e['from'] not in by_id or e['to'] not in by_id:
            raise ValueError('Unknown edge endpoint')
        if e.get('relation') not in ('CHOOSE', 'AND', 'IF'):
            raise ValueError('Unknown relation')
        if e.get('option') and e['option'] not in [o['id'] for o in by_id[e['from']].get('options', [])]:
            raise ValueError('Edge refers to unknown option')
        if e['relation'] == 'IF' and not e.get('condition'):
            raise ValueError('IF needs an explicit condition')
    reachable={n['id'] for n in nodes if n['kind']=='outcome'}
    if not reachable:raise ValueError('Plan needs at least one outcome element')
    while True:
        extended=reachable | {e['to'] for e in g.get('edges',[]) if e['from'] in reachable}
        if extended==reachable:break
        reachable=extended
    if any(n['kind']=='decision' and n['id'] not in reachable for n in nodes):
        raise ValueError('Every decision must connect to an outcome')
    candidates=g.get('candidates',[])
    if not isinstance(candidates,list):raise ValueError('Candidates must be a list')
    candidate_ids=set()
    for candidate in candidates:
        cid=candidate.get('id')
        if not isinstance(cid,str) or not cid or cid in candidate_ids or not candidate.get('title'):
            raise ValueError('Candidates need unique nonempty IDs and titles')
        candidate_ids.add(cid)
        selections=candidate.get('selections',{})
        if not isinstance(selections,dict):raise ValueError('Candidate selections must be a decision mapping')
        for nid,value in selections.items():
            if nid not in by_id or by_id[nid]['kind']!='decision':raise ValueError('Unknown candidate decision')
            validate_selections(by_id[nid],value)
    if g.get('current_candidate') is not None and g['current_candidate'] not in candidate_ids:
        raise ValueError('Unknown current candidate')
    for pair in g.get('incompatible', []):
        if len(pair) != 2:
            raise ValueError('Incompatibility needs two [node, option] pairs')
        for nid, oid in pair:
            if nid not in by_id or oid not in [o['id'] for o in by_id[nid].get('options', [])]:
                raise ValueError('Unknown incompatible selection')
        if all(oid in selected_ids(by_id[nid].get('selected')) for nid,oid in pair):
            raise ValueError('Recorded selections conflict')
        for candidate in candidates:
            if all(oid in selected_ids(candidate.get('selections',{}).get(nid)) for nid,oid in pair):
                raise ValueError('Recorded selections conflict in candidate '+candidate['id'])
    return g


def audit(g):
    """Expose coverage and unfinished options, without treating node counts as quality scores."""
    import heapq
    by_id={n['id']:n for n in g['nodes']}
    frontiers={(f['node'],f['option']):f for f in g.get('exploration_frontier',[])}
    for (nid,oid),f in frontiers.items():
        if nid not in by_id or oid not in [o['id'] for o in by_id[nid].get('options',[])]:
            raise ValueError('Unknown exploration frontier option')
        if not f.get('reason') or not f.get('next_action'):
            raise ValueError('Frontier needs substantive reason and next_action')
    distances={n['id']:0 for n in g['nodes'] if n['kind']=='outcome'}
    queue=[(0,nid) for nid in distances];heapq.heapify(queue)
    while queue:
        depth,nid=heapq.heappop(queue)
        if distances[nid]!=depth:continue
        for e in g.get('edges',[]):
            if e['from']!=nid:continue
            cost=depth+(by_id[e['to']]['kind']=='decision')
            if cost<distances.get(e['to'],float('inf')):
                distances[e['to']]=cost;heapq.heappush(queue,(cost,e['to']))
    unfinished=[];expanded=0
    for n in g['nodes']:
        if n['kind']!='decision':continue
        for o in n['options']:
            outgoing=[e for e in g.get('edges',[]) if e['from']==n['id'] and e.get('option')==o['id']]
            if outgoing:expanded+=1
            elif (n['id'],o['id']) not in frontiers:
                unfinished.append({'node':n['id'],'option':o['id'],'issue':'No option-specific downstream path or documented frontier'})
    depth=max(distances.values(),default=0)
    warnings=[]
    if depth<=1:warnings.append('Only one decision stage is visible; explain the boundary or investigate downstream choices')
    if unfinished:warnings.append('Some options lack consequence expansion or a documented stopping reason')
    return {'decision_nodes':sum(n['kind']=='decision' for n in g['nodes']),
            'options':sum(len(n.get('options',[])) for n in g['nodes']),
            'expanded_options':expanded,'decision_stages_shortest_paths':depth,
            'frontier':g.get('exploration_frontier',[]),'unexplained_options':unfinished,'warnings':warnings,
            'limits':'Structural inventory only; no proof of research coverage or evidence quality'}


def load(root, relative):
    path = inside(root, relative)
    data = path.read_bytes()
    blocks = BLOCK.findall(data.decode('utf-8'))
    if len(blocks) != 1:
        raise ValueError('Expected exactly one project-plan JSON code block')
    return validate(json.loads(blocks[0])), hashlib.sha256(data).hexdigest()


def render(root, source, output):
    g, digest = load(root, source)
    target = inside(root, output)
    if target.suffix != '.html' or target == inside(root, source):
        raise ValueError('Output must be a different HTML file')
    if target.exists() and not target.read_text().startswith('<!-- project-plan-generated -->'):
        raise ValueError('Refusing to replace a handwritten file')
    from datetime import datetime, timezone
    payload = {'graph': g, 'source': source, 'sha256': digest, 'generated': datetime.now(timezone.utc).isoformat(), 'audit': audit(g)}
    template = Path(__file__).with_name('map.html').read_text(encoding='utf-8')
    safe = json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    result = template.replace('/*PLAN_DATA*/null', safe)
    if load(root, source)[1] != digest:
        raise ValueError('Source changed during rendering; retry')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(result, encoding='utf-8')
    return {'output': output, 'source_sha256': digest, 'plan_id': g['plan_id']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', required=True)
    sub = p.add_subparsers(dest='command', required=True)
    for command in ('check', 'audit', 'render'):
        s = sub.add_parser(command); s.add_argument('source')
        if command == 'render': s.add_argument('--output', required=True)
    a = p.parse_args(); root = Path(a.project).resolve()
    try:
        result = render(root, a.source, a.output) if a.command == 'render' else {'ok': True, 'plan_id': load(root, a.source)[0]['plan_id']}
        if a.command=='audit':result=audit(load(root,a.source)[0])
        if a.command=='check':result['exploration']=audit(load(root,a.source)[0])
        print(json.dumps(result, ensure_ascii=False)); return 0
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr); return 2


if __name__ == '__main__':
    sys.exit(main())
