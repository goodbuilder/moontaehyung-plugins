#!/usr/bin/env python3
"""Project-local research records. Standard library only; never starts a server or a model."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from uuid import uuid4

SCHEMA_VERSION=1
TEMPLATE_VERSION=1
KINDS={'literature','concept','plan','finding','decision'}
DIRECTORIES={'literature':'literature','concept':'concepts','plan':'plans','finding':'findings','decision':'decisions'}
START='<!-- RIS:BEGIN -->'
END='<!-- RIS:END -->'
STATE_PATH='.ris/state.json'
RUN_STATES={'RECEIVED','FRAMING','RESEARCHING','PLANNING','AUDITING','REWORK_RESEARCH','REWORK_PLAN','USER_DECISION','BLOCKED','COMPLETE'}
TASK_STATES={'PENDING','READY','IN_PROGRESS','PASS','FAIL','BLOCKED','NOT_RUN','CANCELLED'}
GATE_STATES={'PASS','FAIL','BLOCKED','NOT_RUN'}
TASK_TYPES={'research','planning','audit','verification','coordination'}

class Error(Exception): pass

def timestamp(): return datetime.now(timezone.utc).isoformat()
def sha(data): return hashlib.sha256(data).hexdigest()

def inside(root:Path, relative:str)->Path:
    if Path(relative).is_absolute(): raise Error('Use a project-relative path')
    candidate=root/relative
    # Resolve only after rejecting every symlink segment, including dangling links.
    p=root
    for part in Path(relative).parts:
        if part=='..': raise Error('Parent traversal is not allowed')
        p=p/part
        if p.is_symlink(): raise Error(f'Symlink is not a managed research path: {relative}')
    resolved=candidate.resolve()
    if not resolved.is_relative_to(root): raise Error('Path leaves the project')
    return resolved


def config(root:Path)->dict:
    p=inside(root,'.ris/project.yaml')
    if not p.exists(): raise Error('Project is not initialized; ask to initialize RIS first')
    # The generated document is a YAML mapping with JSON scalar values.
    result={}
    for line in p.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.lstrip().startswith('#'): continue
        key,sep,value=line.partition(':')
        if not sep or not re.fullmatch(r'[a-z_]+',key) or key in result: raise Error('Unsupported project.yaml syntax; keep generated scalar fields')
        try: result[key]=json.loads(value.strip())
        except ValueError as e: raise Error(f'Invalid scalar in project.yaml: {key}') from e
    if type(result.get('schema_version')) is not int or result['schema_version']!=SCHEMA_VERSION: raise Error('Unsupported schema version; existing files were not changed')
    if result.get('template_version')!=TEMPLATE_VERSION: raise Error('Template version differs; compare migration changes before writing')
    if not isinstance(result.get('project_id'),str) or not result['project_id']: raise Error('Missing project identity')
    if result.get('recording_policy') not in ('manual','milestones'): raise Error('Unknown recording policy')
    if result.get('research_dir')!='research': raise Error('Custom research roots are not supported in version 1')
    if result.get('exploration_mode','autonomous') not in ('autonomous','guided'): raise Error('Unknown exploration mode')
    if result.get('active_plan'):
        active=inside(root,result['active_plan'])
        if not active.is_relative_to(inside(root,'research/plans')) or active.suffix!='.md': raise Error('Invalid active plan')
    return result


def state_reference(root:Path, reference:str, label:str)->Path:
    if not isinstance(reference,str) or not reference.strip():
        raise Error(f'{label} must be a non-empty project-relative reference')
    relative=reference.split('#',1)[0]
    if not relative: raise Error(f'{label} must include an artifact path')
    path=inside(root,relative)
    if not path.is_file(): raise Error(f'{label} target is missing: {relative}')
    return path


def validate_state(root:Path, value:dict)->dict:
    cfg=config(root)
    required={'schema_version','project_id','run_id','status','goal_ref','tasks','quality_gates',
              'pending_user_decisions','blocked_items','rework_count','updated_at'}
    optional={'active_plan_ref'}
    if not isinstance(value,dict): raise Error('Orchestration state must be a JSON object')
    missing=required-set(value);extra=set(value)-(required|optional)
    if missing: raise Error('State is missing fields: '+', '.join(sorted(missing)))
    if extra: raise Error('State has unsupported fields: '+', '.join(sorted(extra)))
    if type(value['schema_version']) is not int or value['schema_version']!=1:
        raise Error('Unsupported orchestration state schema version')
    for key in ('project_id','run_id'):
        if not isinstance(value[key],str) or not value[key].strip(): raise Error(f'State {key} must be a non-empty string')
    if value['project_id']!=cfg['project_id']: raise Error('Orchestration state project identity mismatch')
    if not isinstance(value['status'],str) or value['status'] not in RUN_STATES: raise Error('Unknown orchestration run status')
    state_reference(root,value['goal_ref'],'goal_ref')
    if value.get('active_plan_ref'):
        active=state_reference(root,value['active_plan_ref'],'active_plan_ref')
        if not active.is_relative_to(inside(root,'research/plans')) or active.suffix!='.md':
            raise Error('active_plan_ref must point to a project research/plans Markdown note')
        metadata=frontmatter(active.read_text(encoding='utf-8'))
        if metadata.get('project_id')!=cfg['project_id'] or metadata.get('kind')!='plan':
            raise Error('active_plan_ref must identify this project’s managed plan')
    if type(value['rework_count']) is not int or value['rework_count']<0:
        raise Error('rework_count must be a non-negative integer')
    if not isinstance(value['updated_at'],str): raise Error('updated_at must be an ISO date-time string')
    try:
        parsed=datetime.fromisoformat(value['updated_at'].replace('Z','+00:00'))
        if parsed.tzinfo is None: raise ValueError('timezone required')
    except ValueError as e: raise Error('updated_at must be an ISO date-time with timezone') from e
    if not isinstance(value['tasks'],list): raise Error('tasks must be an array')
    task_ids=set()
    for task in value['tasks']:
        if not isinstance(task,dict): raise Error('Each task must be a JSON object')
        task_required={'id','type','owner','status','depends_on','artifact_refs','audit_status','attempt','invalidated_by'}
        task_optional={'question_ref'}
        absent=task_required-set(task);unsupported=set(task)-(task_required|task_optional)
        if absent: raise Error('Task is missing fields: '+', '.join(sorted(absent)))
        if unsupported: raise Error('Task has unsupported fields: '+', '.join(sorted(unsupported)))
        for key in ('id','owner'):
            if not isinstance(task[key],str) or not task[key].strip(): raise Error(f'Task {key} must be a non-empty string')
        if not isinstance(task['type'],str) or task['type'] not in TASK_TYPES: raise Error(f"Unknown type for task {task['id']}")
        if task['id'] in task_ids: raise Error('Duplicate task id: '+task['id'])
        task_ids.add(task['id'])
        if not isinstance(task['status'],str) or task['status'] not in TASK_STATES: raise Error(f"Unknown status for task {task['id']}")
        if not isinstance(task['audit_status'],str) or task['audit_status'] not in GATE_STATES: raise Error(f"Unknown audit_status for task {task['id']}")
        if type(task['attempt']) is not int or task['attempt']<1: raise Error(f"Task {task['id']} attempt must be a positive integer")
        for key in ('depends_on','artifact_refs','invalidated_by'):
            items=task[key]
            if not isinstance(items,list) or any(not isinstance(x,str) or not x.strip() for x in items):
                raise Error(f"Task {task['id']} {key} must be an array of non-empty strings")
            if len(set(items))!=len(items):
                raise Error(f"Task {task['id']} {key} must not contain duplicates")
        if 'question_ref' in task: state_reference(root,task['question_ref'],f"Task {task['id']} question_ref")
        for ref in task['artifact_refs']: state_reference(root,ref,f"Task {task['id']} artifact_ref")
    for task in value['tasks']:
        for dependency in task['depends_on']:
            if dependency not in task_ids: raise Error(f"Task {task['id']} has unknown dependency: {dependency}")
            if dependency==task['id']: raise Error(f"Task {task['id']} cannot depend on itself")
    visiting=set();visited=set();by_id={task['id']:task for task in value['tasks']}
    def visit(task_id):
        if task_id in visiting: raise Error('Task dependencies contain a cycle')
        if task_id in visited: return
        visiting.add(task_id)
        for dependency in by_id[task_id]['depends_on']: visit(dependency)
        visiting.remove(task_id);visited.add(task_id)
    for task_id in by_id: visit(task_id)
    if not isinstance(value['quality_gates'],dict): raise Error('quality_gates must be a JSON object')
    for key,status in value['quality_gates'].items():
        if not isinstance(key,str) or not key.strip() or not isinstance(status,str) or status not in GATE_STATES:
            raise Error('Each quality gate needs a name and PASS, FAIL, BLOCKED, or NOT_RUN status')
    if not isinstance(value['pending_user_decisions'],list): raise Error('pending_user_decisions must be an array')
    for ref in value['pending_user_decisions']: state_reference(root,ref,'pending_user_decisions reference')
    if not isinstance(value['blocked_items'],list): raise Error('blocked_items must be an array')
    for item in value['blocked_items']:
        if not isinstance(item,dict) or set(item)!={'ref','reason'}:
            raise Error('Each blocked item must contain only ref and reason')
        state_reference(root,item['ref'],'blocked item reference')
        if not isinstance(item['reason'],str) or not item['reason'].strip(): raise Error('Blocked-item reason must be non-empty')
    return value


def read_state_snapshot(root:Path)->dict:
    path=inside(root,STATE_PATH)
    if not path.is_file(): raise Error('Orchestration state is not initialized')
    data=path.read_bytes()
    try: value=json.loads(data.decode('utf-8'))
    except (json.JSONDecodeError,UnicodeError) as e: raise Error('Orchestration state is not valid UTF-8 JSON') from e
    return {'state':validate_state(root,value),'sha256':sha(data)}


def read_state(root:Path)->dict:
    return read_state_snapshot(root)['state']


def initialize_state(root:Path,run_id:str|None=None,goal_ref:str='research/CONTEXT.md',active_plan_ref:str|None=None)->dict:
    cfg=config(root);path=inside(root,STATE_PATH)
    if active_plan_ref is None: active_plan_ref=cfg.get('active_plan') or None
    value={'schema_version':1,'project_id':cfg['project_id'],
           'run_id':run_id or 'RISRUN-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid4().hex[:8],
           'status':'RECEIVED','goal_ref':goal_ref,'tasks':[],'quality_gates':{},
           'pending_user_decisions':[],'blocked_items':[],'rework_count':0,'updated_at':timestamp()}
    if active_plan_ref: value['active_plan_ref']=active_plan_ref
    validate_state(root,value)
    with lock(root):
        if path.exists(): raise Error('Orchestration state already exists; read it before updating')
        write_new(path,json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    return {'status':'initialized','path':STATE_PATH,'run_id':value['run_id'],'project_id':value['project_id']}


def gate():
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    sys.modules['ris']=sys.modules[__name__]  # one module object, one Error class
    import role_gate
    return role_gate


def update_state(root:Path,expected_hash:str,text:str)->dict:
    path=inside(root,STATE_PATH)
    with lock(root):
        if not path.is_file(): raise Error('Orchestration state is not initialized')
        before=path.read_bytes()
        if sha(before)!=expected_hash: raise Error('Orchestration state changed; reload before updating')
        try: previous=json.loads(before.decode('utf-8'));value=json.loads(text)
        except (json.JSONDecodeError,UnicodeError) as e: raise Error('State update must contain valid UTF-8 JSON') from e
        validate_state(root,value)
        if not isinstance(previous,dict) or previous.get('project_id')!=value['project_id'] or previous.get('run_id')!=value['run_id']:
            raise Error('A state update must preserve project_id and run_id')
        value['updated_at']=timestamp();validate_state(root,value)
        gate().require_complete(root,value)
        history=inside(root,'.ris/history');history.mkdir(exist_ok=True)
        backup=history/('state-'+sha(before)+'.json')
        if not backup.exists(): write_new(backup,before.decode('utf-8'))
        if path.read_bytes()!=before: raise Error('State changed during update; original retained')
        after=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
        path.write_bytes(after)
    return {'status':'updated','path':STATE_PATH,'run_id':value['run_id'],'sha256':sha(after),'backup':str(backup.relative_to(root))}


def yaml_mapping(values:dict)->str:
    return ''.join(f'{key}: {json.dumps(value,ensure_ascii=False)}\n' for key,value in values.items())


def frontmatter(text:str)->dict:
    match=re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)',text,re.S)
    if not match: return {}
    fields={}
    for line in match[1].splitlines():
        if not line.strip() or line.lstrip().startswith('#'): continue
        key,sep,value=line.partition(':')
        if not sep: continue
        if key in fields: raise Error(f'Duplicate frontmatter field: {key}')
        try: fields[key]=json.loads(value.strip())
        except ValueError: fields[key]=value.strip()
    return fields


def note(project_id:str,kind:str,title:str,body:str,related:list[str]|None=None)->str:
    meta={'ris_id':str(uuid4()),'project_id':project_id,'kind':kind,'status':'draft','created':timestamp()}
    if related: meta['related_ids']=related
    return '---\n'+yaml_mapping(meta)+'---\n\n# '+title+'\n\n'+body.rstrip()+'\n'


def hook()->str:
    return f'''{START}
## RIS research continuity

For research work in this project, use the shared `$ris` skill when available.
Read `research/INDEX.md` and `research/CONTEXT.md` before resuming a research question.
`.ris/project.yaml` defines identity and recording policy. It does not authorize access to another project.
Keep source code/data in their existing locations and link them from research notes.
Do not treat generated explanations as understood, observed reads as verified, or missing search hits as absence.
If `$ris` is unavailable, follow these files directly and disclose the missing shared capability.
{END}
'''


def templates(project_id:str,name:str,goal:str)->dict[str,str]:
    return {
      'research/INDEX.md':note(project_id,'index',name+' — 연구 진입점',f'''## 목표
{goal or '아직 정하지 않았습니다.'}

## 현재 연구 상태
- [현재 이해·판단·다음 행동](CONTEXT.md)

## 연구 기록
- [문헌 리뷰](literature/)
- [개념·학습](concepts/)
- [계획·분기](plans/)
- [조사·실험 결과](findings/)
- [판단과 변경 이유](decisions/)

## 원본 도구·자료
Zotero 컬렉션, 기존 코드·데이터·산출물 위치는 확인한 뒤 연결합니다.

## 사용 원칙
프로젝트 루트를 Obsidian Vault로 열 수 있습니다. 전용 플러그인은 필요하지 않습니다.
기록 정책은 기본 수동입니다. 모든 대화나 전체 프로젝트를 자동 수집하지 않습니다.
'''),
      'research/CONTEXT.md':note(project_id,'context','현재 연구 맥락','''## 지금 해결할 질문
아직 정하지 않았습니다.

## 현재 이해와 근거
아직 확인된 기록이 없습니다. 설명을 읽은 것과 이해·적용·검증은 구분합니다.

## 현재 판단과 적용 조건
아직 채택한 판단이 없습니다.

## 배제·보류한 접근과 이유
아직 없습니다.

## 미해결 문제·불확실성
아직 정리하지 않았습니다.

## 다음 행동
첫 연구 질문과 기존 자료 위치를 정합니다.

## 에이전트 맥락의 관측 범위
이 문서를 제공받는 것과 관련 원문을 실제 조회하는 것은 다릅니다.
''')}


@contextmanager
def lock(root:Path):
    """Cooperative RIS writers only. Does not lock Obsidian or user editors."""
    folder=inside(root,'.ris')
    folder.mkdir(exist_ok=True)
    path=inside(root,'.ris/write.lock')
    with path.open('a') as f:
        fcntl.flock(f,fcntl.LOCK_EX)
        try: yield
        finally: fcntl.flock(f,fcntl.LOCK_UN)


def write_new(path:Path,text:str):
    with path.open('x',encoding='utf-8',newline='') as f:
        f.write(text);f.flush();os.fsync(f.fileno())


def initialize(root:Path,name:str|None=None,goal:str='',attach:bool=False,dry_run:bool=False)->dict:
    if not root.is_dir(): raise Error('Project directory must already exist')
    cfg=inside(root,'.ris/project.yaml')
    if cfg.exists():
        checked=check(root)
        if checked['errors']: raise Error('Existing RIS needs review: '+'; '.join(checked['errors']))
        attached=attach_agents(root,dry_run) if attach else None
        return {'status':'already_initialized','project_id':config(root)['project_id'],'changed':bool(attached and attached['status']=='attached'),'agents':attached}
    identity=str(uuid4())
    values={'schema_version':SCHEMA_VERSION,'template_version':TEMPLATE_VERSION,'project_id':identity,'name':name or root.name,'research_dir':'research','recording_policy':'manual','created':timestamp()}
    docs=templates(identity,name or root.name,goal)
    files={**docs,'.ris/project.yaml':yaml_mapping(values)}
    paths=[inside(root,p) for p in files]
    directories=[inside(root,'research')]+[inside(root,'research/'+d) for d in DIRECTORIES.values()]
    collisions=[str(p.relative_to(root)) for p in paths if p.exists()]
    for p in [inside(root,'.ris')]+directories:
        if p.exists() and not p.is_dir(): collisions.append(str(p.relative_to(root)))
    if collisions: raise Error('Existing files need an explicit adoption plan; nothing overwritten: '+', '.join(collisions))
    if attach: validate_agents(root)
    if dry_run:return {'status':'preview','files':list(files),'directories':[str(p.relative_to(root)) for p in directories],'attach_agents':attach}
    # config is created last as the completion marker. No live project metadata is committed mid-init.
    created=[]
    try:
        with lock(root):
            if cfg.exists(): raise Error('Another initializer completed; rerun without changing files')
            for p in directories:p.mkdir(parents=True,exist_ok=True)
            for relative,text in files.items():
                p=inside(root,relative);p.parent.mkdir(parents=True,exist_ok=True)
                write_new(p,text);created.append(p)
            if attach:attach_agents(root)
    except Exception:
        # Only remove files created by this call if they still match our generated bytes.
        for p in reversed(created):
            relative=str(p.relative_to(root))
            if p.exists() and p.read_text(encoding='utf-8')==files[relative]:p.unlink()
        raise
    return {'status':'initialized','project_id':identity,'files':list(files),'recording_policy':'manual','agents_attached':attach}


def validate_agents(root:Path):
    path=inside(root,'AGENTS.md')
    if path.exists():
        if not path.is_file(): raise Error('AGENTS.md is not a file')
        text=path.read_text(encoding='utf-8')
        if text.count(START)!=text.count(END) or text.count(START)>1: raise Error('Malformed RIS section in AGENTS.md')
        if START in text:
            a=text.index(START);b=text.index(END)+len(END)
            if text[a:b].strip()!=hook().strip(): raise Error('Existing RIS instruction block differs; review instead of overwrite')


def attach_agents(root:Path,dry_run:bool=False)->dict:
    validate_agents(root)
    path=inside(root,'AGENTS.md')
    existing=path.read_bytes() if path.exists() else b''
    if START.encode() in existing:return {'status':'already_attached'}
    if dry_run:return {'status':'preview','append':hook()}
    if path.exists():
        # Save an exact preimage and avoid replacing a file edited by other tools.
        history=inside(root,'.ris/history');history.mkdir(parents=True,exist_ok=True)
        backup=history/('AGENTS-'+sha(existing)+'.md')
        if not backup.exists():write_new(backup,existing.decode('utf-8'))
        with path.open('r+b') as f:
            fcntl.flock(f,fcntl.LOCK_EX)
            if f.read()!=existing:raise Error('AGENTS.md changed; no instruction block appended')
            f.seek(0,2)
            f.write((b'\n' if existing.endswith(b'\n') else b'\n\n')+hook().encode());f.flush();os.fsync(f.fileno())
    else: write_new(path,hook())
    return {'status':'attached','backup':str(backup.relative_to(root)) if existing else None}


def notes(root:Path)->list[tuple[Path,dict,str]]:
    cfg=config(root);folder=inside(root,cfg['research_dir']);items=[]
    if not folder.is_dir():raise Error('Research directory is missing')
    for p in sorted(folder.rglob('*.md')):
        p=inside(root,str(p.relative_to(root)))
        text=p.read_text(encoding='utf-8')
        items.append((p,frontmatter(text),text))
    return items


def check(root:Path)->dict:
    cfg=config(root);errors=[];warnings=[];seen={};count=0;state_info=None
    for required in ('research/INDEX.md','research/CONTEXT.md'):
        if not inside(root,required).is_file():errors.append('Missing '+required)
    if cfg.get('active_plan') and not inside(root,cfg['active_plan']).is_file():errors.append('Missing active plan '+cfg['active_plan'])
    for d in DIRECTORIES.values():
        if not inside(root,'research/'+d).is_dir():errors.append('Missing directory research/'+d)
    for path,meta,text in notes(root):
        count+=1;relative=str(path.relative_to(root));rid=meta.get('ris_id')
        if not rid:
            warnings.append(relative+': unmanaged Markdown; no ris_id');continue
        if not isinstance(rid,str):
            errors.append(relative+': ris_id must be a string');continue
        if rid in seen:errors.append(f'Duplicate ris_id: {relative} and {seen[rid]}')
        seen[rid]=relative
        if meta.get('project_id')!=cfg['project_id']:errors.append(relative+': project identity mismatch')
        for target in re.findall(r'(?<!!)\[[^\]]*\]\(([^\s)]+)\)',text):
            target=target.split('#',1)[0]
            if not target or re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:',target):continue
            from urllib.parse import unquote
            candidate=(path.parent/unquote(target.strip('<>'))).resolve()
            if not candidate.is_relative_to(root):
                warnings.append(relative+': external local link '+target)
            elif not candidate.exists():warnings.append(relative+': missing link '+target)
    for _,meta,_ in notes(root):
        for rid in meta.get('related_ids',[]) if isinstance(meta.get('related_ids',[]),list) else []:
            if rid not in seen:errors.append('Unknown related record ID: '+str(rid))
    try:validate_agents(root)
    except Error as e:errors.append(str(e))
    try:
        state_path=inside(root,STATE_PATH)
        if state_path.exists():
            state=read_state(root);state_info={'run_id':state['run_id'],'status':state['status']}
    except Error as e:errors.append('Invalid orchestration state: '+str(e))
    return {'project_id':cfg['project_id'],'schema_version':cfg['schema_version'],'template_version':cfg['template_version'],'recording_policy':cfg['recording_policy'],'notes':count,'orchestration_state':state_info,'errors':errors,'warnings':warnings,'ok':not errors}


def add_record(root:Path,kind:str,title:str,body:str,related:list[str]|None=None)->dict:
    cfg=config(root)
    if kind not in KINDS or not title.strip() or '\n' in title:raise Error('Use a supported kind and a single-line title')
    with lock(root):
        known={meta.get('ris_id') for _,meta,_ in notes(root) if isinstance(meta.get('ris_id'),str)}
        if any(r not in known for r in (related or [])):raise Error('Related ID is not in this project')
        text=note(cfg['project_id'],kind,title,body,related)
        rid=frontmatter(text)['ris_id']
        name=datetime.now(timezone.utc).strftime('%Y%m%d')+'-'+rid+'.md'
        path=inside(root,'research/'+DIRECTORIES[kind]+'/'+name)
        path.parent.mkdir(parents=True,exist_ok=True);write_new(path,text)
        return {'path':str(path.relative_to(root)),'ris_id':rid,'status':'draft','context_updated':False}


def context(root:Path,include:list[str]|None=None,max_chars:int=20000)->dict:
    cfg=config(root)
    if max_chars<1000:raise Error('Context budget must be at least 1000 characters')
    state_path=inside(root,STATE_PATH)
    orchestration_state=read_state(root) if state_path.exists() else None
    active_plan_ref=(orchestration_state or {}).get('active_plan_ref') or cfg.get('active_plan')
    active_plan=active_plan_ref.split('#',1)[0] if active_plan_ref else None
    selected=list(dict.fromkeys(['research/INDEX.md','research/CONTEXT.md']+([active_plan] if active_plan else [])+(include or [])))
    # Metadata is an inventory, not proof that any source or concept was read or understood.
    inventory=[{'path':str(p.relative_to(root)),'ris_id':m.get('ris_id'),'kind':m.get('kind'),'status':m.get('status')} for p,m,_ in notes(root)]
    result=[];omitted=[];used=0
    for relative in selected:
        path=inside(root,relative)
        if not path.is_file() or path.suffix!='.md':raise Error('Selected context note is missing or not Markdown: '+relative)
        if not path.is_relative_to(inside(root,'research')):raise Error('Context notes must belong to this project research directory')
        data=path.read_bytes();text=data.decode('utf-8');meta=frontmatter(text)
        if meta.get('project_id')!=cfg['project_id']:raise Error('Selected note has different project identity: '+relative)
        if used+len(text)>max_chars:omitted.append({'path':relative,'reason':'character_budget'});continue
        result.append({'path':relative,'sha256':sha(data),'text':text});used+=len(text)
    included={r['path'] for r in result};omitted_paths={r['path'] for r in omitted}
    omitted += [{'path':r['path'],'reason':'not_selected'} for r in inventory if r['path'] not in included|omitted_paths]
    return {'project':cfg,'prepared_at':timestamp(),'mode':'prepared_snapshot','observed_read':False,'understanding_assessed':False,'character_budget':max_chars,'characters_included':used,'records':result,'omitted':omitted,'orchestration_state':orchestration_state,
            'limitations':['This snapshot includes selected notes only, not the full project or agent internal context.','File inventory is not evidence of source review.','Linked Zotero/PDF/code sources were not read by this command.','Orchestration state contains bookkeeping and references, not the content of linked evidence.']}


def propose(root:Path,relative:str,expected_hash:str,body:str)->dict:
    cfg=config(root);path=inside(root,relative)
    if not path.is_relative_to(inside(root,'research')) or path.suffix!='.md' or not path.is_file():raise Error('Select an existing research Markdown note')
    data=path.read_bytes()
    if sha(data)!=expected_hash:raise Error('Note changed since it was read; reload before proposing')
    meta=frontmatter(data.decode('utf-8'))
    if meta.get('project_id')!=cfg['project_id']:raise Error('Project identity mismatch')
    # Preserve original bytes; review/merge stays explicit while recording policy is undecided.
    with lock(root):
        folder=inside(root,'.ris/proposals');folder.mkdir(parents=True,exist_ok=True)
        proposal=folder/(str(uuid4())+'.json')
        value={'schema_version':1,'project_id':cfg['project_id'],'target':relative,'base_sha256':expected_hash,'created':timestamp(),'proposed_body':body,'status':'proposed','original_unchanged':True}
        write_new(proposal,json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    return {'proposal':str(proposal.relative_to(root)),'status':'proposed','original_unchanged':True}


def safe_update(root:Path,relative:str,expected_hash:str,text:str)->dict:
    cfg=config(root);path=inside(root,relative)
    if not path.is_file() or not path.is_relative_to(inside(root,'research')) or path.suffix!='.md':
        raise Error('Select an existing research Markdown note')
    with lock(root):
        data=path.read_bytes()
        if sha(data)!=expected_hash:raise Error('Note changed; reload before updating')
        before=frontmatter(data.decode('utf-8'));after=frontmatter(text)
        if not before.get('ris_id') or before.get('project_id')!=cfg['project_id']:
            raise Error('Expected a managed note in this project')
        if any(after.get(k)!=before.get(k) for k in ('ris_id','project_id','kind','created')):
            raise Error('Preserve note identity, kind and creation date')
        history=inside(root,'.ris/history');history.mkdir(exist_ok=True)
        backup=history/(sha(data)+'.md')
        if not backup.exists():write_new(backup,data.decode('utf-8'))
        if path.read_bytes()!=data:raise Error('External edit detected; original retained')
        # Cooperative writers only: Obsidian can still race after this comparison.
        path.write_text(text,encoding='utf-8')
    return {'status':'updated','path':relative,'sha256':sha(text.encode()),'backup':str(backup.relative_to(root))}


def configure(root:Path,expected_hash:str,recording_policy=None,exploration_mode=None,active_plan=None)->dict:
    cfg=config(root);path=inside(root,'.ris/project.yaml')
    if recording_policy is not None and recording_policy not in ('manual','milestones'):raise Error('Unknown recording policy')
    if exploration_mode is not None and exploration_mode not in ('autonomous','guided'):raise Error('Unknown exploration mode')
    if recording_policy is not None:cfg['recording_policy']=recording_policy
    if exploration_mode is not None:cfg['exploration_mode']=exploration_mode
    if active_plan is not None:
        p=inside(root,active_plan)
        if not p.is_file() or not p.is_relative_to(inside(root,'research/plans')) or p.suffix!='.md':
            raise Error('Active plan must be an existing project research/plans Markdown note')
        metadata=frontmatter(p.read_text(encoding='utf-8'))
        if metadata.get('project_id')!=cfg['project_id'] or metadata.get('kind')!='plan':raise Error('Expected this project’s managed plan')
        cfg['active_plan']=active_plan
    with lock(root):
        data=path.read_bytes()
        if sha(data)!=expected_hash:raise Error('Configuration changed; reload before updating')
        history=inside(root,'.ris/history');history.mkdir(exist_ok=True)
        backup=history/(sha(data)+'.yaml')
        if not backup.exists():write_new(backup,data.decode())
        if path.read_bytes()!=data:raise Error('External edit detected')
        path.write_text(yaml_mapping(cfg),encoding='utf-8')
    return {'status':'configured','project':cfg}


def main(argv=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',default='.',help='Explicit project root; no global active-project state')
    sub=parser.add_subparsers(dest='command',required=True)
    init=sub.add_parser('init');init.add_argument('--name');init.add_argument('--goal',default='');init.add_argument('--attach-agents',action='store_true');init.add_argument('--dry-run',action='store_true')
    sub.add_parser('check');sub.add_parser('status')
    ctx=sub.add_parser('context');ctx.add_argument('--include',action='append',default=[]);ctx.add_argument('--max-chars',type=int,default=20000)
    rec=sub.add_parser('record');rec.add_argument('--kind',choices=sorted(KINDS),required=True);rec.add_argument('--title',required=True);rec.add_argument('--body-file',default='-');rec.add_argument('--related',action='append',default=[])
    prop=sub.add_parser('propose');prop.add_argument('target');prop.add_argument('--expected-hash',required=True);prop.add_argument('--body-file',default='-')
    att=sub.add_parser('attach');att.add_argument('--dry-run',action='store_true')
    update=sub.add_parser('update');update.add_argument('target');update.add_argument('--expected-hash',required=True);update.add_argument('--body-file',required=True)
    settings=sub.add_parser('configure');settings.add_argument('--expected-hash',required=True);settings.add_argument('--recording-policy',choices=['manual','milestones']);settings.add_argument('--exploration-mode',choices=['autonomous','guided']);settings.add_argument('--active-plan')
    state=sub.add_parser('state');state_sub=state.add_subparsers(dest='state_action',required=True)
    state_init=state_sub.add_parser('init');state_init.add_argument('--run-id');state_init.add_argument('--goal-ref',default='research/CONTEXT.md');state_init.add_argument('--active-plan-ref')
    state_sub.add_parser('read')
    state_update=state_sub.add_parser('update');state_update.add_argument('--expected-hash',required=True);state_update.add_argument('--body-file',required=True)
    g=sub.add_parser('gate');g_sub=g.add_subparsers(dest='gate_action',required=True)
    gs=g_sub.add_parser('start');gs.add_argument('--client',default='unknown')
    ga=g_sub.add_parser('assign');ga.add_argument('--task',required=True)
    gr=g_sub.add_parser('result');gr.add_argument('--body-file',default='-');gr.add_argument('--agent-id',required=True)
    g_sub.add_parser('verdict');g_sub.add_parser('release')
    gh=g_sub.add_parser('hook');gh.add_argument('--client',required=True)
    args=parser.parse_args(argv);root=Path(args.project).expanduser().resolve()
    try:
        if args.command=='init':value=initialize(root,args.name,args.goal,args.attach_agents,args.dry_run)
        elif args.command in ('check','status'):value=check(root)
        elif args.command=='context':value=context(root,args.include,args.max_chars)
        elif args.command=='configure':value=configure(root,args.expected_hash,args.recording_policy,args.exploration_mode,args.active_plan)
        elif args.command=='update':value=safe_update(root,args.target,args.expected_hash,Path(args.body_file).read_text(encoding='utf-8'))
        elif args.command=='state':
            if args.state_action=='init':value=initialize_state(root,args.run_id,args.goal_ref,args.active_plan_ref)
            elif args.state_action=='read':value=read_state_snapshot(root)
            else:value=update_state(root,args.expected_hash,Path(args.body_file).read_text(encoding='utf-8'))
        elif args.command=='gate':
            rg=gate()
            if args.gate_action=='hook':
                try:
                    out=rg.handle_hook(root,json.loads(sys.stdin.read() or '{}'),args.client)
                    if out: print(json.dumps(out,ensure_ascii=False))
                except (Error,OSError,ValueError) as e: print('role-gate hook skipped: '+str(e),file=sys.stderr)
                return 0  # a hook fault must not wedge the client; COMPLETE stays refused by state update
            rid=lambda:rg.active_run_id(root) or (_ for _ in ()).throw(Error('No active gate run'))
            if args.gate_action=='start':value=rg.start(root,args.client)
            elif args.gate_action=='assign':value=rg.assign(root,rid(),args.task)
            elif args.gate_action=='result':
                body=sys.stdin.read() if args.body_file=='-' else Path(args.body_file).read_text(encoding='utf-8')
                value=rg.submit_result(root,json.loads(body),args.agent_id)
            elif args.gate_action=='release':value=rg.release(root)
            else:
                value=rg.verdict(root,rid());print(json.dumps(value,ensure_ascii=False,indent=2));return 0 if value['complete'] else 1
        elif args.command=='attach':
            config(root)
            with lock(root):value=attach_agents(root,args.dry_run)
        else:
            body=sys.stdin.read() if args.body_file=='-' else Path(args.body_file).read_text(encoding='utf-8')
            if args.command=='record':value=add_record(root,args.kind,args.title,body,args.related)
            else:value=propose(root,args.target,args.expected_hash,body)
        print(json.dumps(value,ensure_ascii=False,indent=2))
        return 1 if isinstance(value,dict) and value.get('ok') is False else 0
    except (Error,OSError,UnicodeError,ValueError) as e:
        print(json.dumps({'error':str(e)},ensure_ascii=False),file=sys.stderr);return 2

if __name__=='__main__':sys.exit(main())
