"""Optional read-only navigation projections over existing canonical RIS owners."""
from __future__ import annotations
import hashlib
import json
import re
from types import SimpleNamespace

VIEWS = ('research','knowledge','decision','evidence','plan','learning','strategy')
MAX_FILE = 256 * 1024


def add_parser(sub):
    parser = sub.add_parser('view', help='Read-only bounded canonical navigation; never creates a dashboard or authority')
    parser.add_argument('view', choices=VIEWS)
    parser.add_argument('--include', action='append', default=[], help='Explicit project-relative existing managed research note')
    parser.add_argument('--question', default='default')
    parser.add_argument('--study')
    parser.add_argument('--revision', type=int)
    parser.add_argument('--limit', type=int, default=20, choices=range(1,51), metavar='1..50')
    parser.add_argument('--max-chars', type=int, default=16000, choices=range(2000,64001), metavar='2000..64000')
    parser.add_argument('--expected-receipt', help='Reject a changed selected input snapshot')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dispatch(api, root, args):
    cfg = api.config(root)
    if len(args.include) > 20 or any(len(x)>512 for x in args.include):
        raise api.Error('Select at most twenty related notes; no project-wide discovery is performed')
    if args.revision is not None and not args.study:
        raise api.Error('--revision requires --study')
    delivery = api.companion('ris_delivery')
    research = api.inside(root, cfg['research_dir'])
    output = {'view':args.view, 'project_id':cfg['project_id'], 'records':[], 'omitted':[],
              'read_only':True, 'profile_access':False,
              'scope':'Navigation to canonical records; no duplicate claim store or scientific validation'}
    selected = list(args.include)
    if args.view in ('research','learning'):
        selected.insert(0,api.research_path(cfg,'research/CONTEXT.md'))
    if args.view == 'research':
        selected.insert(0,api.research_path(cfg,'research/INDEX.md'))
    if args.view == 'plan':
        active=cfg.get('active_plan')
        if api.inside(root,api.STATE_PATH).exists():
            try:
                if api.inside(root,api.STATE_PATH).stat().st_size>MAX_FILE:
                    raise api.Error('State input exceeds bound')
                state=api.read_state(root)
                active=state.get('active_plan_ref') or active
            except (api.Error,OSError,ValueError):
                output['omitted'].append({'owner':'state','reason':'unavailable_or_invalid'})
        if active: selected.insert(0,active.split('#',1)[0])
    if args.view == 'knowledge':
        selected.insert(0,api.companion('ris_findings').location(api,cfg,args.question))
    if args.study:
        try:
            study=api.companion('ris_study').read_study(api,root,args.study,args.revision)
            selected.insert(0,study['path'])
            output['study_pin']={'study_id':study['id'],'revision':study['revision'],'path':study['path']}
        except (api.Error,OSError,ValueError):
            output['omitted'].append({'owner':'study','reason':'unavailable_or_invalid'})
    if args.view == 'strategy':
        recovery=api.companion('ris_recovery')
        try:
            recovery_path=api.inside(root,recovery.PATH)
            if recovery_path.exists() and recovery_path.stat().st_size>MAX_FILE:
                raise api.Error('Recovery input exceeds bound')
            snap=recovery.snapshot(api,root)
            if snap['hash']!='missing':
                output['recovery_ref']={'path':snap['path'],'sha256':snap['hash'],'revision':snap['ledger']['revision']}
        except (api.Error,OSError,ValueError):
            output['omitted'].append({'owner':'recovery','reason':'unavailable_or_invalid'})
    selected=list(dict.fromkeys(selected))
    for relative in selected:
        if len(output['records']) >= args.limit:
            output['omitted'].append({'path':relative,'reason':'record_limit'})
            continue
        try:
            path=api.inside(root,relative)
            if not path.is_relative_to(research) or path.suffix!='.md':
                raise api.Error('Not a managed project research note')
            if path.stat().st_size > MAX_FILE:
                raise api.Error('Selected note exceeds bounded input size')
            canonical,raw=delivery.read_file(api,root,relative,markdown=True)
            text=raw.decode('utf-8');meta=api.frontmatter(text)
            if meta.get('project_id')!=cfg['project_id'] or not isinstance(meta.get('ris_id'),str) or not meta['ris_id'].strip() or len(meta['ris_id'])>256:
                raise api.Error('Selected note has no matching managed identity')
            allowed={'research':None,'knowledge':{'finding','study'},'decision':{'decision','study'},
                     'evidence':{'source','literature','finding','study'},'plan':{'plan'},
                     'learning':{'context','concept'},'strategy':{'finding','plan','study'}}[args.view]
            if allowed is not None and meta.get('kind') not in allowed:
                raise api.Error('Selected note kind is unrelated to this view')
            record={'path':canonical,'sha256':sha(raw),'ris_id':meta['ris_id'],'kind':meta.get('kind'),
                    'status':meta.get('status'),'official_content':'Follow this exact canonical note revision',
                    'links':[]}
            if meta.get('kind')=='study':
                study_id=re.fullmatch(r'study-([A-Za-z0-9_-]+)\.md',path.name)
                if not study_id:raise api.Error('Study path is noncanonical')
                snapshot=api.companion('ris_study').read_study(api,root,study_id[1],args.revision if args.study==study_id[1] else None)
                record['revision']=snapshot['revision']
            findings=api.companion('ris_findings')
            question=findings.canonical_question_for_path(api,root,canonical)
            if question is not None:
                snapshot=findings.dispatch(api,root,SimpleNamespace(action='inspect',question=question,query=None,node_id=None,limit=args.limit))
                if snapshot['direct_edit_pending'] or snapshot['file_sha256']!=sha(raw):
                    raise api.Error('Governed record dirty or changed')
                record['revision']=snapshot['revision']
                record['nodes']=[{'id':x['finding']['id'],'state':x['state'],'locator':'finding:'+x['finding']['id']} for x in snapshot['proposals']]
                record['total_matching']=snapshot['total_matching']
            if 'ris:strategy' in text:
                lessons=api.companion('ris_strategy').records(api,text)
                if any(x.get('project_id')!=cfg['project_id'] or x.get('origin_note')!=canonical for x in lessons):
                    raise api.Error('Foreign or misbound strategy record')
                record['strategies']=[{'id':x['id'],'origin_note':x['origin_note'],'input_revision':x['input_revision'],'locator':'strategy:'+x['id']} for x in lessons[:args.limit]]
            if args.view=='learning':
                # Projection offers a place to inspect attributed contributions, never profile input.
                record['contribution_sections']=text.count('### Attributed research contribution')
                record['learning_boundary']='Project-local attributed inputs; no inferred competence or global profile lookup'
            # Links remain original canonical navigation; linked targets are never opened implicitly.
            for match in re.finditer(r'\[[^\]\n]{0,200}\]\(([^)\n]{1,512})\)',text):
                href=match[1]
                if '://' in href or href.startswith(('/', '~')): continue
                record['links'].append({'href':href,'opened':False})
                if len(record['links'])>=args.limit:break
            candidate=json.dumps(dict(output,records=output['records']+[record]),ensure_ascii=False,indent=2)
            if len(candidate)>args.max_chars-1200:
                output['omitted'].append({'path':relative,'reason':'character_budget'})
                continue
            output['records'].append(record)
        except (api.Error,OSError,ValueError,TypeError,KeyError):
            output['omitted'].append({'path':relative,'reason':'unavailable_dirty_invalid_or_unrelated'})
    # Detect changes after owner reads; omit transient records rather than mixing revisions.
    retained=[]
    for record in output['records']:
        try:
            _,raw=delivery.read_file(api,root,record['path'],markdown=True)
            if sha(raw)!=record['sha256']:raise api.Error('Transient note revision')
            retained.append(record)
        except (api.Error,OSError,ValueError):
            output['omitted'].append({'path':record['path'],'reason':'changed_during_projection'})
    output['records']=retained
    if output.get('study_pin') and not any(x['path']==output['study_pin']['path'] for x in retained):
        output.pop('study_pin')
    if output.get('recovery_ref'):
        try:
            _,raw=delivery.read_file(api,root,output['recovery_ref']['path'])
            if sha(raw)!=output['recovery_ref']['sha256']:raise api.Error('Transient recovery revision')
        except (api.Error,OSError,ValueError):
            output.pop('recovery_ref')
            output['omitted'].append({'owner':'recovery','reason':'changed_during_projection'})
    output['omitted_total']=len(output['omitted'])
    output['omitted_truncated']=False
    while len(json.dumps(output,ensure_ascii=False,indent=2))>args.max_chars-200 and output['omitted']:
        output['omitted'].pop()
        output['omitted_truncated']=True
    output['receipt']=sha(json.dumps({'project_id':cfg['project_id'],'view':args.view,'selection':{'include':args.include,'question':args.question,'study':args.study,'revision':args.revision,'limit':args.limit},'records':[(x['path'],x['sha256']) for x in retained],
                                     'study':output.get('study_pin'),'recovery':output.get('recovery_ref')},sort_keys=True).encode())
    if api.config(root)!=cfg:
        raise api.Error('Project configuration changed during projection; reload')
    if args.expected_receipt and args.expected_receipt!=output['receipt']:
        raise api.Error('View receipt changed; inspect the current canonical revisions')
    output['empty']=not retained and 'recovery_ref' not in output
    return output
