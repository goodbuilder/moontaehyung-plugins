#!/usr/bin/env python3
"""Project-local research records. Standard library only; never starts a server or a model."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
from functools import lru_cache
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
from types import SimpleNamespace
from uuid import uuid4

SCHEMA_VERSION=2
RECORDING_POLICIES=('manual','milestones','significant')
LEGACY_SCHEMA_VERSION=1
TEMPLATE_VERSION=1
RESEARCH_DIRS={LEGACY_SCHEMA_VERSION:'research',SCHEMA_VERSION:'.ris/research'}
LAYOUT_MIGRATION_MARKER='.ris/layout-migration.json'
KINDS={'literature','concept','plan','map','finding','decision'}
DIRECTORIES={'literature':'literature','concept':'concepts','plan':'plans','map':'plans','finding':'findings','decision':'decisions'}
START='<!-- RIS:BEGIN -->'
END='<!-- RIS:END -->'
STATE_PATH='.ris/state.json'
RUN_STATES={'RECEIVED','FRAMING','RESEARCHING','PLANNING','AUDITING','REWORK_RESEARCH','REWORK_PLAN','USER_DECISION','BLOCKED','COMPLETE'}
TASK_STATES={'PENDING','READY','IN_PROGRESS','PASS','FAIL','BLOCKED','NOT_RUN','CANCELLED'}
GATE_STATES={'PASS','FAIL','BLOCKED','NOT_RUN'}
TASK_TYPES={'research','planning','audit','verification','coordination'}
EXPLORE_PATH='research/exploration/log.md'
EXPLORE_KINDS={'query','read'}
READ_SCOPES={'snippet','abstract','full','code','data'}
SUMMARY_PATH='research/exploration/summary.md'
SUMMARY_SECTIONS=['탐색한 접근 계열','기각·보류한 후보와 이유','미탐색 프런티어','검수 요청']
SUMMARY_LIMIT=6000
MIN_DISTINCT_QUERIES=3
STATS_BEGIN='<!-- RIS:STATS -->'
STATS_END='<!-- /RIS:STATS -->'
ENTRY_REF=re.compile(r'\b[QRU]-\d{4,}\b')
QUESTION_ID_RE=re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}')
EXPLORE_ROW=re.compile(r'^\| ([QRU]-\d{4,}) \| (\S+) \| (query|read|reuse) \| ([a-z0-9_.-]+) \| (.+?) \| (-|[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}) \|$')
EXPLORE_ROW_LEGACY=re.compile(r'^\| ([QR]-\d{4,}) \| (\S+) \| (query|read) \| ([a-z0-9_.-]+) \| (.+) \|$')
EXPLORE_TABLE_HEADER='| ID | 시각(UTC) | 종류 | 채널/범위 | 내용 |'
EXPLORE_TABLE_SEPARATOR='|---|---|---|---|---|'
EXPLORE_SCOPED_HEADER='| ID | 시각(UTC) | 종류 | 채널/범위 | 내용 | 질문 ID |'
EXPLORE_SCOPED_SEPARATOR='|---|---|---|---|---|---|'

class Error(Exception): pass

class NoteConflict(Error):
    """Another editor changed a note after the caller selected its preimage."""

def timestamp(): return datetime.now(timezone.utc).isoformat()
def sha(data): return hashlib.sha256(data).hexdigest()


def research_path(cfg:dict, relative:str)->str:
    """Map a v1-style research-relative path to this project's configured research root."""
    if relative=='research': return cfg['research_dir']
    if relative.startswith('research/'): return cfg['research_dir']+relative[len('research'):]
    return relative


def handoff_path_for_version(version:int)->str:
    return '.ris/HANDOFF.md' if version==SCHEMA_VERSION else 'HANDOFF.md'


def handoff_path(cfg:dict)->str:
    return handoff_path_for_version(cfg['schema_version'])


def layout_output(cfg:dict)->dict:
    return {'research_dir':cfg['research_dir'],'handoff_path':handoff_path(cfg)}


def confirm_layout_current(root:Path,cfg:dict):
    current=config(root)
    if (current['project_id'],current['schema_version'],current['research_dir'])!=(cfg['project_id'],cfg['schema_version'],cfg['research_dir']):
        raise Error('Project storage layout changed while reading; reload and retry')

def inside(root:Path, relative:str)->Path:
    if Path(relative).is_absolute(): raise Error('Use a project-relative path')
    candidate=root/relative
    # Resolve only after rejecting every symlink segment, including dangling links.
    p=root
    for part in Path(relative).parts:
        if part=='..': raise Error('Parent traversal is not allowed')
        if part in {'.aws','.ssh','.gnupg','.git'}:
            raise Error('Private identity and repository metadata paths are outside research scope')
        p=p/part
        if p.is_symlink(): raise Error(f'Symlink is not a managed research path: {relative}')
        # A nested independently initialized RIS project has its own authority.
        if part != '.ris' and ((p / '.ris').is_symlink() or (p / '.ris' / 'project.yaml').is_file()):
            raise Error('Path enters a different RIS project')
    resolved=candidate.resolve()
    if not resolved.is_relative_to(root): raise Error('Path leaves the project')
    return resolved


def study_evidence_hash(root: Path, relative: str) -> dict:
    """Fingerprint an explicitly selected project file; never infer a file from a source citation."""
    if not isinstance(relative, str) or not relative.strip():
        raise Error('Specify a project-relative evidence filename')
    path = inside(root, relative)
    if not path.is_file():
        raise Error('Evidence file is missing or not a regular file: ' + relative)
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise Error('Expected a regular evidence file: ' + relative)
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
        after = os.fstat(stream.fileno())
    current = inside(root, relative).stat()
    def signature(st):
        return st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns
    if signature(before) != signature(after) or signature(after) != signature(current):
        raise Error('Evidence file changed while reading: ' + relative)
    return {'path': path.relative_to(root).as_posix(), 'sha256': digest.hexdigest()}


def config(root:Path)->dict:
    marker=inside(root,LAYOUT_MIGRATION_MARKER)
    if marker.exists(): raise Error('Research layout migration is incomplete; resolve '+LAYOUT_MIGRATION_MARKER+' before using this project')
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
    version=result.get('schema_version')
    if type(version) is not int or version not in RESEARCH_DIRS: raise Error('Unsupported schema version; existing files were not changed')
    if result.get('template_version')!=TEMPLATE_VERSION: raise Error('Template version differs; compare migration changes before writing')
    if not isinstance(result.get('project_id'),str) or not result['project_id']: raise Error('Missing project identity')
    if result.get('recording_policy') not in RECORDING_POLICIES: raise Error('Unknown recording policy')
    if result.get('research_dir')!=RESEARCH_DIRS[version]: raise Error(f'Invalid research_dir for schema version {version}')
    # Resolve the configured roots through the same no-symlink boundary used for all managed paths.
    inside(root,result['research_dir'])
    inside(root,handoff_path(result))
    if result.get('exploration_mode','autonomous') not in ('autonomous','guided'): raise Error('Unknown exploration mode')
    if result.get('active_plan'):
        active=inside(root,result['active_plan'])
        if not active.is_relative_to(inside(root,research_path(result,'research/plans'))) or active.suffix!='.md': raise Error('Invalid active plan')
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
        if not active.is_relative_to(inside(root,research_path(cfg,'research/plans'))) or active.suffix!='.md':
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
    state=validate_state(root,value)
    cfg=config(root)
    confirm_layout_current(root,cfg)
    return {'state':state,'sha256':sha(data)}


def read_state(root:Path)->dict:
    return read_state_snapshot(root)['state']


def initialize_state(root:Path,run_id:str|None=None,goal_ref:str|None=None,active_plan_ref:str|None=None)->dict:
    path=inside(root,STATE_PATH)
    with project_lock(root):
        cfg=config(root)
        actual_goal_ref=goal_ref if goal_ref is not None else research_path(cfg,'research/CONTEXT.md')
        actual_plan_ref=active_plan_ref if active_plan_ref is not None else cfg.get('active_plan') or None
        value={'schema_version':1,'project_id':cfg['project_id'],
               'run_id':run_id or 'RISRUN-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid4().hex[:8],
               'status':'RECEIVED','goal_ref':actual_goal_ref,'tasks':[],'quality_gates':{},
               'pending_user_decisions':[],'blocked_items':[],'rework_count':0,'updated_at':timestamp()}
        if actual_plan_ref: value['active_plan_ref']=actual_plan_ref
        validate_state(root,value)
        if path.exists(): raise Error('Orchestration state already exists; read it before updating')
        write_new(path,json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    return {'status':'initialized','path':STATE_PATH,'run_id':value['run_id'],'project_id':value['project_id'],
            'goal_ref':value['goal_ref'],'active_plan_ref':value.get('active_plan_ref')}


def update_state(root:Path,expected_hash:str,text:str)->dict:
    path=inside(root,STATE_PATH)
    with project_lock(root):
        if not path.is_file(): raise Error('Orchestration state is not initialized')
        before=path.read_bytes()
        if sha(before)!=expected_hash: raise Error('Orchestration state changed; reload before updating')
        try: previous=json.loads(before.decode('utf-8'));value=json.loads(text)
        except (json.JSONDecodeError,UnicodeError) as e: raise Error('State update must contain valid UTF-8 JSON') from e
        validate_state(root,value)
        if not isinstance(previous,dict) or previous.get('project_id')!=value['project_id'] or previous.get('run_id')!=value['run_id']:
            raise Error('A state update must preserve project_id and run_id')
        value['updated_at']=timestamp();validate_state(root,value)
        history=inside(root,'.ris/history');history.mkdir(exist_ok=True)
        backup=history/('state-'+sha(before)+'.json')
        if not backup.exists(): write_new(backup,before.decode('utf-8'))
        after=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
        atomic_note_write(path,after,expected=before)
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


def hook(research_dir:str='research',handoff:str='HANDOFF.md')->str:
    if research_dir=='research' and handoff=='HANDOFF.md':
        # Keep schema 1 instructions byte-for-byte compatible with existing project attachments.
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
    return f'''{START}
## RIS research continuity

For research work in this project, use the shared `$ris` skill when available.
Read `{handoff}`, `{research_dir}/INDEX.md`, and `{research_dir}/CONTEXT.md` before resuming a research question.
`.ris/project.yaml` defines identity and recording policy. It does not authorize access to another project.
Keep source code/data in their existing locations and link them from research notes.
Do not treat generated explanations as understood, observed reads as verified, or missing search hits as absence.
If `$ris` is unavailable, follow the project-bound paths above and disclose the missing shared capability.
{END}
'''


def templates(project_id:str,name:str,goal:str,research_dir:str='research')->dict[str,str]:
    index_path=research_dir+'/INDEX.md'
    context_path=research_dir+'/CONTEXT.md'
    return {
      index_path:note(project_id,'index',name+' — 연구 진입점',f'''## 목표
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
      context_path:note(project_id,'context','현재 연구 맥락','''## 지금 해결할 질문
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
        try:
            if inside(root,LAYOUT_MIGRATION_MARKER).exists():
                raise Error('Research layout migration is incomplete; resolve '+LAYOUT_MIGRATION_MARKER+' before writing')
            yield
        finally: fcntl.flock(f,fcntl.LOCK_UN)


@contextmanager
def project_lock(root:Path):
    """Serialize an initialized-project write without creating .ris for an uninitialized root."""
    config(root)
    with lock(root):
        config(root)
        yield


def write_new(path:Path,text:str):
    with path.open('x',encoding='utf-8',newline='') as f:
        f.write(text);f.flush();os.fsync(f.fileno())


def atomic_note_write(path: Path, content: bytes, *, expected: bytes | None = None):
    """Publish complete bytes under the caller's project lock, or exclusively create a note."""
    temp = path.with_name('.ris-note-' + uuid4().hex + '.tmp')
    mode = 0o666 if expected is None else 0o600
    fd = os.open(temp, os.O_WRONLY | os.O_EXCL | os.O_CREAT, mode)
    try:
        with os.fdopen(fd, 'wb') as stream:
            if expected is not None:
                os.fchmod(stream.fileno(), stat.S_IMODE(path.stat().st_mode) & 0o777)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if expected is None:
            os.link(temp, path)  # FileExistsError preserves the winning note.
        else:
            if path.read_bytes() != expected:
                raise NoteConflict(f'Note changed after preflight: {path}')
            # External editors do not share the RIS lock; the comparison precedes OS replacement.
            os.replace(temp, path)
        temp.unlink(missing_ok=True)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temp.unlink(missing_ok=True)


def initialize(root:Path,name:str|None=None,goal:str='',attach:bool=False,dry_run:bool=False,recording_policy:str|None=None)->dict:
    if not root.is_dir(): raise Error('Project directory must already exist')
    if inside(root,LAYOUT_MIGRATION_MARKER).exists(): raise Error('Research layout migration is incomplete; resolve '+LAYOUT_MIGRATION_MARKER+' before initializing')
    if recording_policy is not None and recording_policy not in RECORDING_POLICIES:
        raise Error('Unknown recording policy')
    cfg=inside(root,'.ris/project.yaml')
    if cfg.exists():
        checked=check(root)
        if checked['errors']: raise Error('Existing RIS needs review: '+'; '.join(checked['errors']))
        existing=config(root)
        if recording_policy and recording_policy != existing['recording_policy']:
            raise Error('Existing policy differs; review before an explicit configure operation')
        if attach:
            with project_lock(root):
                attached=attach_agents(root,dry_run)
                existing=config(root)
        else:
            attached=None
            confirm_layout_current(root,existing)
        return {'status':'already_initialized','project_id':existing['project_id'],'changed':bool(attached and attached['status']=='attached'),'agents':attached,**layout_output(existing)}
    identity=str(uuid4())
    research_dir=RESEARCH_DIRS[SCHEMA_VERSION]
    handoff=handoff_path_for_version(SCHEMA_VERSION)
    values={'schema_version':SCHEMA_VERSION,'template_version':TEMPLATE_VERSION,'project_id':identity,'name':name or root.name,'research_dir':research_dir,'recording_policy':recording_policy or 'significant','created':timestamp()}
    docs=templates(identity,name or root.name,goal,research_dir)
    files={**docs,'.ris/project.yaml':yaml_mapping(values)}
    paths=[inside(root,p) for p in files]
    handoff_target=inside(root,handoff)
    directories=[inside(root,research_dir)]+[inside(root,research_dir+'/'+d) for d in dict.fromkeys(DIRECTORIES.values())]
    collisions=[str(p.relative_to(root)) for p in paths if p.exists()]
    if handoff_target.exists(): collisions.append(handoff)
    if inside(root,STATE_PATH).exists(): collisions.append(STATE_PATH)
    for p in [inside(root,'.ris')]+directories:
        if p.exists() and not p.is_dir(): collisions.append(str(p.relative_to(root)))
    if collisions: raise Error('Existing files need an explicit adoption plan; nothing overwritten: '+', '.join(collisions))
    if attach: validate_agents(root,research_dir,handoff)
    if dry_run:return {'status':'preview','recording_policy':values['recording_policy'],'files':list(files),'directories':[str(p.relative_to(root)) for p in directories],'attach_agents':attach,'research_dir':research_dir,'handoff_path':handoff}
    # config is created last as the completion marker. No live project metadata is committed mid-init.
    created=[]
    try:
        with lock(root):
            if cfg.exists(): raise Error('Another initializer completed; rerun without changing files')
            for p in directories:p.mkdir(parents=True,exist_ok=True)
            for relative,text in files.items():
                p=inside(root,relative);p.parent.mkdir(parents=True,exist_ok=True)
                write_new(p,text);created.append(p)
            if attach:attach_agents(root,research_dir=research_dir,handoff=handoff)
    except Exception:
        # Only remove files created by this call if they still match our generated bytes.
        for p in reversed(created):
            relative=str(p.relative_to(root))
            if p.exists() and p.read_text(encoding='utf-8')==files[relative]:p.unlink()
        raise
    return {'status':'initialized','project_id':identity,'files':list(files),'recording_policy':recording_policy or 'significant','agents_attached':attach,'research_dir':research_dir,'handoff_path':handoff}


def validate_agents(root:Path,research_dir:str='research',handoff:str='HANDOFF.md'):
    path=inside(root,'AGENTS.md')
    if path.exists():
        if not path.is_file(): raise Error('AGENTS.md is not a file')
        text=path.read_text(encoding='utf-8')
        if text.count(START)!=text.count(END) or text.count(START)>1: raise Error('Malformed RIS section in AGENTS.md')
        if START in text:
            a=text.index(START);b=text.index(END)+len(END)
            if text[a:b].strip()!=hook(research_dir,handoff).strip(): raise Error('Existing RIS instruction block differs; review instead of overwrite')


def attach_agents(root:Path,dry_run:bool=False,research_dir:str|None=None,handoff:str|None=None)->dict:
    if research_dir is None or handoff is None:
        cfg=config(root)
        research_dir=cfg['research_dir']
        handoff=handoff_path(cfg)
    validate_agents(root,research_dir,handoff)
    path=inside(root,'AGENTS.md')
    existing=path.read_bytes() if path.exists() else b''
    if START.encode() in existing:return {'status':'already_attached'}
    if dry_run:return {'status':'preview','path':'AGENTS.md','append':hook(research_dir,handoff)}
    if path.exists():
        # Save an exact preimage and avoid replacing a file edited by other tools.
        history=inside(root,'.ris/history');history.mkdir(parents=True,exist_ok=True)
        backup=history/('AGENTS-'+sha(existing)+'.md')
        if not backup.exists():write_new(backup,existing.decode('utf-8'))
        with path.open('r+b') as f:
            fcntl.flock(f,fcntl.LOCK_EX)
            if f.read()!=existing:raise Error('AGENTS.md changed; no instruction block appended')
            f.seek(0,2)
            f.write((b'\n' if existing.endswith(b'\n') else b'\n\n')+hook(research_dir,handoff).encode());f.flush();os.fsync(f.fileno())
    else: write_new(path,hook(research_dir,handoff))
    return {'status':'attached','backup':str(backup.relative_to(root)) if existing else None}


def note_header(path: Path) -> str:
    """Read only the frontmatter for a navigation inventory."""
    with path.open('rb') as stream:
        if stream.readline(8).rstrip(b'\r\n') != b'---':
            return ''
        header = bytearray(b'---\n')
        while len(header) <= 65536:
            line = stream.readline(65537 - len(header))
            if not line:
                break
            header.extend(line)
            if line.rstrip(b'\r\n') == b'---':
                return header.decode('utf-8')
    return ''


def notes(root:Path, *, metadata_only:bool=False)->list[tuple[Path,dict,str]]:
    cfg=config(root);folder=inside(root,cfg['research_dir']);items=[]
    if not folder.is_dir():raise Error('Research directory is missing')
    for p in sorted(folder.rglob('*')):
        if p.is_symlink(): raise Error('Symlink is not a managed research path: '+str(p.relative_to(root)))
        if p.suffix!='.md' or not p.is_file(): continue
        p=inside(root,str(p.relative_to(root)))
        text=note_header(p) if metadata_only else p.read_text(encoding='utf-8')
        meta=frontmatter(text)
        if companion('ris_knowledge').is_local_knowledge_metadata(meta,cfg['project_id']):
            items.append((p,meta,text))
    return items


def exclusion_basis(section: str, rows: list[dict]) -> tuple[list[dict], list[str]]:
    """Describe what each item cites. The meaning of the underlying evidence remains a review task."""
    by_id = {row['id']: row for row in rows}
    items, warnings = [], []
    for text in section.splitlines():
        bullet = re.match(r'^\s*[-*]\s+(.+)', text)
        if not bullet or bullet[1].strip() == '없음':
            continue
        item = bullet[1].strip()
        ids = list(dict.fromkeys(ENTRY_REF.findall(item)))
        reads = {}
        for entry_id in ids:
            row = by_id.get(entry_id, {})
            if row.get('kind') == 'reuse':
                row = by_id.get(row['text'], {})
            if row.get('kind') == 'read':
                reads[row['id']] = row['via']
        tag = re.match(r'^\[(기각|보류|사용자 결정|rejected|deferred|user decision)\]\s*', item, re.I)
        kind = tag[1].lower() if tag else 'unclassified'
        decision_ref = re.search(r'\[[^\]]+\]\(([^)]+)\)', item) if kind in ('사용자 결정', 'user decision') else None
        if decision_ref:
            basis = 'reported_decision_link'
        elif reads:
            basis = 'read_linked'
        elif ids and all(by_id.get(i, {}).get('kind') == 'query' for i in ids):
            basis = 'query_only'
        else:
            basis = 'no_resolved_read'
        items.append({'item': item, 'disposition': kind, 'basis': basis, 'entry_ids': ids,
                      'read_scopes': reads, 'decision_link': decision_ref[1] if decision_ref else None})
        if kind in ('기각', 'rejected') and not reads:
            warnings.append(f'Rejected item has no linked read. Review its basis: {item}')
        elif kind == 'unclassified' and basis == 'query_only':
            warnings.append(f'Only a query is linked. Mark a deferral or supply the basis for exclusion: {item}')
        elif kind in ('사용자 결정', 'user decision') and decision_ref is None:
            warnings.append(f'Link the recorded user decision for this item: {item}')
    return items, warnings


def exploration_checklist(rows:list[dict],summary:str|None,warnings:list[str])->dict:
    """Mechanical parts of the return checklist. Counts and structure only: it cannot judge query
    quality, whether a source was understood, or whether an option list is complete. Warnings are
    raised only once a summary exists, because that is when the agent claims a checkpoint."""
    queries={re.sub(r'\s+',' ',r['text']).casefold() for r in rows if r['kind']=='query'}
    opened=sum(r['kind']=='read' and r['via']!='snippet' for r in rows)
    result={'distinct_queries':len(queries),'queries_meet_minimum':len(queries)>=MIN_DISTINCT_QUERIES,
            'sources_opened_beyond_snippet':opened,'summary_structure':None,'review_requests_declared':None}
    if summary is None: return result
    if not result['queries_meet_minimum']:
        warnings.append(f'Checklist (b): {len(queries)} distinct search quer{"y" if len(queries)==1 else "ies"} logged; at least {MIN_DISTINCT_QUERIES} are expected before ranking')
    if not opened:
        warnings.append('Checklist (j): no source opened beyond a snippet; top candidates and ranking-deciding figures need primary text')
    body=re.sub(re.escape(STATS_BEGIN)+r'.*?'+re.escape(STATS_END),'',re.sub(r'\A---\r?\n.*?\r?\n---\r?\n','',summary,flags=re.S),flags=re.S)
    body=re.sub(r'(?m)^# .*$','',body,count=1).strip('\n')
    try:
        sections=summary_sections(body);result['summary_structure']='ok'
    except Error as e:
        warnings.append('Summary structure: '+str(e));result['summary_structure']='invalid';return result
    if len(body)>SUMMARY_LIMIT: warnings.append(f'Summary body is {len(body)} characters; limit is {SUMMARY_LIMIT}')
    result['exclusion_basis'], basis_warnings = exclusion_basis(sections[SUMMARY_SECTIONS[1]], rows)
    warnings.extend(basis_warnings)
    unevidenced = [item for item in result['exclusion_basis']
                   if not item['entry_ids'] and not item['decision_link']]
    declared=sections[SUMMARY_SECTIONS[3]].strip()!='없음'
    result['review_requests_declared']=declared
    if unevidenced and not declared:
        warnings.append(f'{len(unevidenced)} rejected/deferred item(s) cite no log ID but 검수 요청 is 없음; list them for review')
    return result


def validated_question_id(value:str|None)->str|None:
    if value is None:return None
    value=value.strip()
    if not QUESTION_ID_RE.fullmatch(value):
        raise Error('Question ID must be 1-64 characters: a letter or digit followed by letters, digits, _, ., :, or -')
    return value


def empty_exploration_counts()->dict:
    return {'queries':0,'reads':0,'reads_beyond_snippet':0}


def empty_question_scope()->dict:
    return {'new':empty_exploration_counts(),
            'reused':{'read_ids':[],'reads':0,'reads_beyond_snippet':0}}


def resolve_reused_reads(rows: list[dict], errors: list[str]) -> dict[str, dict]:
    """Resolve each valid reuse event to the earlier read in the same log snapshot."""
    by_id = {}
    duplicate_ids = set()
    for position, row in enumerate(rows):
        if row['id'] in by_id:
            duplicate_ids.add(row['id'])
        else:
            by_id[row['id']] = (position, row)
    errors.extend('Duplicate exploration log ID: ' + entry_id for entry_id in sorted(duplicate_ids))
    resolved = {}
    seen_links=set()
    for index,row in enumerate(rows):
        if row['kind']!='reuse':continue
        question=row.get('question')
        if question is None:
            errors.append('Exploration reuse entry has no question ID: '+row['id']);continue
        source_id=row['text'].strip()
        if not re.fullmatch(r'R-\d{4,}',source_id):
            errors.append('Exploration reuse entry must reference an R-ID: '+row['id']);continue
        match = by_id.get(source_id)
        if match is None or match[1]['kind'] != 'read':
            errors.append('Exploration reuse entry references an unknown read: '+source_id);continue
        position, source = match
        if position >= index:
            errors.append('Exploration reuse entry must follow its source read: '+source_id);continue
        if source.get('question')==question:
            errors.append('Exploration reuse entry repeats a read already scoped to the same question: '+source_id);continue
        link=(question,source_id)
        if link in seen_links:
            errors.append('Duplicate exploration reuse link: '+question+' -> '+source_id);continue
        seen_links.add(link)
        resolved[row['id']] = source
    return resolved


def exploration_scopes(rows: list[dict], errors: list[str]) -> tuple[dict, dict[str, dict]]:
    unassigned = empty_exploration_counts()
    scopes = {}
    reused_sources = resolve_reused_reads(rows, errors)
    for row in rows:
        if row['kind'] == 'reuse':
            if row['id'] in reused_sources:
                source = reused_sources[row['id']]
                reused = scopes.setdefault(row['question'], empty_question_scope())['reused']
                reused['read_ids'].append(source['id'])
                reused['reads'] += 1
                reused['reads_beyond_snippet'] += source['via'] != 'snippet'
            continue
        question = row.get('question')
        counts = unassigned if question is None else scopes.setdefault(question, empty_question_scope())['new']
        if row['kind'] == 'query':
            counts['queries'] += 1
        else:
            counts['reads'] += 1
            counts['reads_beyond_snippet'] += row['via'] != 'snippet'
    return unassigned, scopes


def question_scope_checklist(rows:list[dict],question:str,scope:dict,summary:str|None,warnings:list[str])->tuple[dict,list[str]]:
    queries={re.sub(r'\s+',' ',r['text']).casefold() for r in rows
             if r['kind']=='query' and r.get('question')==question}
    opened=scope['new']['reads_beyond_snippet']+scope['reused']['reads_beyond_snippet']
    checklist={'distinct_queries':len(queries),'queries_meet_minimum':len(queries)>=MIN_DISTINCT_QUERIES,
               'sources_opened_beyond_snippet':opened}
    scoped_warnings=[]
    if summary is not None:
        if not checklist['queries_meet_minimum']:
            scoped_warnings.append(f'Question {question}: {len(queries)} distinct queries logged; at least {MIN_DISTINCT_QUERIES} are expected before ranking')
        if not opened:
            scoped_warnings.append(f'Question {question}: no source opened beyond a snippet; top candidates and ranking-deciding figures need primary text')
        warnings.extend(scoped_warnings)
    return checklist,scoped_warnings


def check(root:Path,question:str|None=None)->dict:
    question=validated_question_id(question)
    cfg=config(root);errors=[];warnings=[];seen={};count=0;state_info=None
    for required in (research_path(cfg,'research/INDEX.md'),research_path(cfg,'research/CONTEXT.md')):
        if not inside(root,required).is_file():errors.append('Missing '+required)
    if cfg.get('active_plan') and not inside(root,cfg['active_plan']).is_file():errors.append('Missing active plan '+cfg['active_plan'])
    for d in dict.fromkeys(DIRECTORIES.values()):
        directory=research_path(cfg,'research/'+d)
        if not inside(root,directory).is_dir():errors.append('Missing directory '+directory)
    inventory = notes(root)
    for path,meta,text in inventory:
        count+=1;relative=str(path.relative_to(root));rid=meta.get('ris_id')
        if not rid:
            warnings.append(relative+': unmanaged Markdown; no ris_id');continue
        if not isinstance(rid,str):
            errors.append(relative+': ris_id must be a string');continue
        if rid in seen:errors.append(f'Duplicate ris_id: {relative} and {seen[rid]}')
        seen[rid]=relative
        if meta.get('project_id')!=cfg['project_id']:errors.append(relative+': project identity mismatch')
        if meta.get('study_schema_version') is not None or meta.get('kind') == 'study':
            try:
                study_id = path.stem.removeprefix('study-')
                expected_path = research_path(cfg, 'research/decisions/study-' + study_id + '.md')
                if relative != expected_path:
                    raise Error('Canonical study path differs from its filename or directory')
                companion('ris_study').read_study(helper_api(), root, study_id)
            except (Error, OSError, ValueError) as exc:
                errors.append(f'{relative}: {exc}')
        for target in re.findall(r'(?<!!)\[[^\]]*\]\(([^\s)]+)\)',text):
            target=target.split('#',1)[0]
            if not target or re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:',target):continue
            from urllib.parse import unquote
            candidate=(path.parent/unquote(target.strip('<>'))).resolve()
            if not candidate.is_relative_to(root):
                warnings.append(relative+': external local link '+target)
            elif not candidate.exists():warnings.append(relative+': missing link '+target)
    for _,meta,_ in inventory:
        for rid in meta.get('related_ids',[]) if isinstance(meta.get('related_ids',[]),list) else []:
            if rid not in seen:errors.append('Unknown related record ID: '+str(rid))
    try:validate_agents(root,cfg['research_dir'],handoff_path(cfg))
    except Error as e:errors.append(str(e))
    try:
        state_path=inside(root,STATE_PATH)
        if state_path.exists():
            state=read_state(root);state_info={'run_id':state['run_id'],'status':state['status']}
    except Error as e:errors.append('Invalid orchestration state: '+str(e))
    exploration=None
    try:
        log_relative=research_path(cfg,EXPLORE_PATH)
        summary_relative=research_path(cfg,SUMMARY_PATH)
        log_path=inside(root,log_relative)
        if log_path.exists() or question is not None:
            rows=[]
            if log_path.exists():
                rows,bad=exploration_rows(log_path.read_text(encoding='utf-8'))
                for place in bad:warnings.append(f'{log_relative}: malformed entry at {place}')
            summary_file=inside(root,summary_relative)
            summary_text=summary_file.read_text(encoding='utf-8') if summary_file.exists() else None
            exploration={'queries':sum(r['kind']=='query' for r in rows),'reads':sum(r['kind']=='read' for r in rows),'reads_beyond_snippet':sum(r['kind']=='read' and r['via']!='snippet' for r in rows),'summary':None}
            unassigned,scopes=exploration_scopes(rows,errors)
            if question is not None or scopes:
                exploration['unassigned']=unassigned
                exploration['by_question']=scopes
            if summary_text is not None:
                m=re.search(r'반영한 로그 위치:(.*)',summary_text)
                covered={p:int(n) for p,n in re.findall(r'([QRU])-(\d+)',m[1])} if m else {}
                behind=sum(int(r['id'][2:])>covered.get(r['id'][0],0) for r in rows)
                exploration['summary']={'entries_since_summary':behind}
                if behind:warnings.append(f'Exploration summary is behind the log by {behind} entr{"y" if behind==1 else "ies"}')
            elif rows:warnings.append('Exploration log has entries but no summary yet')
            for sid in sorted(set(ENTRY_REF.findall(summary_text) if summary_text is not None else [])-{r['id'] for r in rows}):
                errors.append('Exploration summary cites unknown log ID: '+sid)
            exploration['checklist']=exploration_checklist(rows,summary_text,warnings)
            if question is not None:
                scope=scopes.get(question,empty_question_scope())
                scope={'question_id':question,**scope}
                checklist,scope_warnings=question_scope_checklist(rows,question,scope,summary_text,warnings)
                scope['checklist']=checklist
                scope['warnings']=scope_warnings
                exploration['question_scope']=scope
    except (Error,OSError,UnicodeError) as e:errors.append('Invalid exploration log: '+str(e))
    confirm_layout_current(root,cfg)
    return {'project_id':cfg['project_id'],'schema_version':cfg['schema_version'],'template_version':cfg['template_version'],'recording_policy':cfg['recording_policy'],'notes':count,'orchestration_state':state_info,'exploration_log':exploration,'errors':errors,'warnings':warnings,'ok':not errors,**layout_output(cfg)}


def add_record(root:Path,kind:str,title:str,body:str,related:list[str]|None=None,owner:str|None=None)->dict:
    cfg=config(root)
    if kind not in KINDS or not title.strip() or '\n' in title:raise Error('Use a supported kind and a single-line title')
    if owner is not None and (kind, owner) not in {('map','researcher'), ('plan','planner')}:
        raise Error('Create a Research Map as researcher or a Research Plan as planner')
    with project_lock(root):
        cfg=config(root)
        known={meta.get('ris_id') for _,meta,_ in notes(root)
               if meta.get('project_id')==cfg['project_id'] and isinstance(meta.get('ris_id'),str)}
        if any(r not in known for r in (related or [])):raise Error('Related ID is not in this project')
        text=note(cfg['project_id'],kind,title,body,related)
        if owner is not None:
            companion('ris_artifacts').check_update(owner,kind,'',text,dedicated=True)
            text=text.replace('---\n', '---\nartifact_owner: '+json.dumps(owner)+'\n', 1)
        rid=frontmatter(text)['ris_id']
        name=datetime.now(timezone.utc).strftime('%Y%m%d')+'-'+rid+'.md'
        path=inside(root,research_path(cfg,'research/'+DIRECTORIES[kind]+'/'+name))
        path.parent.mkdir(parents=True,exist_ok=True);write_new(path,text)
        return {'path':str(path.relative_to(root)),'ris_id':rid,'status':'draft','context_updated':False}


def clean_cell(value:str)->str:
    return re.sub(r'\s+',' ',value).strip().replace('|','\\|')


def exploration_rows(text:str)->tuple[list[dict],list[str]]:
    """Parse the work-log table. Returns rows and lines that look like entries but are malformed."""
    rows=[];bad=[]
    for number,line in enumerate(text.splitlines(),1):
        if not re.match(r'^\|\s*[QRU]-',line): continue
        m=EXPLORE_ROW.match(line)
        question=None
        if m:
            entry_id,at,kind,via,entry_text,question_cell=m.groups()
            question=None if question_cell=='-' else question_cell
        else:
            m=EXPLORE_ROW_LEGACY.match(line)
            if not m: bad.append(f'line {number}');continue
            entry_id,at,kind,via,entry_text=m.groups()
        expected_prefix={'query':'Q','read':'R','reuse':'U'}[kind]
        if entry_id[0]!=expected_prefix or (question is not None and not QUESTION_ID_RE.fullmatch(question)):
            bad.append(f'line {number}');continue
        if kind=='reuse' and (question is None or via!='reuse' or not re.fullmatch(r'R-\d{4,}',entry_text)):
            bad.append(f'line {number}');continue
        rows.append({'id':entry_id,'at':at,'kind':kind,'via':via,'text':entry_text,'question':question})
    return rows,bad


def add_exploration(root:Path,kind:str|None,text:str|None,via:str|None,
                    question:str|None=None,reuse:list[str]|None=None)->dict:
    """Append a query/read and optional question tag or persistent reuse links to the work log."""
    cfg=config(root)
    question=validated_question_id(question)
    reuse=list(dict.fromkeys(reuse or []))
    if reuse and question is None:raise Error('A question ID is required when recording reused reads')
    if kind is None:
        if text is not None or via is not None or not reuse:raise Error('Provide a query/read entry or at least one --reuse R-ID with --question')
    else:
        if kind not in EXPLORE_KINDS: raise Error('Use kind query or read')
        if text is None or via is None:raise Error('A query/read entry requires both --via and --text')
        text=clean_cell(text)
        if not text or len(text)>1000: raise Error('Entry text must be 1-1000 characters')
        via=via.strip()
        if kind=='read' and via not in READ_SCOPES: raise Error('Read scope must be one of: '+', '.join(sorted(READ_SCOPES)))
        if kind=='query' and not re.fullmatch(r'[a-z0-9_.-]{1,32}',via): raise Error('Query channel must be a short lowercase label such as web, zotero, code')
    for source_id in reuse:
        if not re.fullmatch(r'R-\d{4,}',source_id):raise Error('Reuse references must be R-IDs such as R-0001')
    with project_lock(root):
        cfg=config(root)
        log_relative=research_path(cfg,EXPLORE_PATH)
        path=inside(root,log_relative)
        exists=path.exists()
        if exists:
            current=path.read_text(encoding='utf-8')
            meta=frontmatter(current)
            if meta.get('project_id')!=cfg['project_id']: raise Error('Exploration log has a different project identity')
            rows,_=exploration_rows(current)
        else:
            current=''
            rows=[]
        by_id={row['id']:row for row in rows}
        existing_reuses={(row.get('question'),row['text']) for row in rows if row['kind']=='reuse'}
        for source_id in reuse:
            source=by_id.get(source_id)
            if source is None or source['kind']!='read':raise Error('Reuse reference is not an existing read in this project: '+source_id)
            if source.get('question')==question:raise Error('Read is already scoped to this question; do not also mark it reused: '+source_id)
        new_reuses=[source_id for source_id in reuse if (question,source_id) not in existing_reuses]

        extended_table=question is not None or bool(reuse) or EXPLORE_SCOPED_HEADER in current
        new_log=not exists
        if new_log:
            header=EXPLORE_SCOPED_HEADER+'\n'+EXPLORE_SCOPED_SEPARATOR if extended_table else EXPLORE_TABLE_HEADER+'\n'+EXPLORE_TABLE_SEPARATOR
            body='검색 질의와 실제로 연 출처의 작업 기록입니다. 대화 내용은 기록하지 않습니다. 열람 범위: snippet(검색 결과 조각), abstract, full, code, data.\n\n'+header+'\n'
            current=note(cfg['project_id'],'exploration','탐색 작업 기록',body)

        entry_id=None
        lines=[]
        if kind is not None:
            prefix='Q' if kind=='query' else 'R'
            number=max([int(r['id'][2:]) for r in rows if r['id'][0]==prefix]+[0])+1
            entry_id=f'{prefix}-{number:04d}'
            if extended_table:
                line=f'| {entry_id} | {timestamp()} | {kind} | {via} | {text} | {question or "-"} |\n'
            else:
                line=f'| {entry_id} | {timestamp()} | {kind} | {via} | {text} |\n'
            lines.append(line)
        reuse_event_ids=[]
        next_reuse=max([int(r['id'][2:]) for r in rows if r['id'].startswith('U-')]+[0])+1
        for source_id in new_reuses:
            reuse_event_id=f'U-{next_reuse:04d}';next_reuse+=1
            reuse_event_ids.append(reuse_event_id)
            lines.append(f'| {reuse_event_id} | {timestamp()} | reuse | reuse | {source_id} | {question} |\n')

        table_prefix=''
        if extended_table and not new_log and EXPLORE_SCOPED_HEADER not in current:
            separator='\n' if current.endswith('\n') else '\n\n'
            table_prefix=separator+'## 질문 범위가 있는 항목\n\n'+EXPLORE_SCOPED_HEADER+'\n'+EXPLORE_SCOPED_SEPARATOR+'\n'
        if lines:
            if new_log:
                path.parent.mkdir(parents=True,exist_ok=True)
                write_new(path,current+''.join(lines))
            else:
                with path.open('a',encoding='utf-8',newline='') as f:
                    if table_prefix:
                        f.write(table_prefix)
                    elif not current.endswith('\n'):
                        f.write('\n')
                    f.write(''.join(lines));f.flush();os.fsync(f.fileno())
        if question is None and not reuse and kind is not None:
            return {'path':log_relative,'id':entry_id,'kind':kind}
        result={'path':log_relative,'question_id':question,'reused':reuse,'reuse_events':reuse_event_ids}
        if entry_id is not None:result.update({'id':entry_id,'kind':kind})
        elif reuse:result['kind']='reuse'
        return result


def summary_sections(body:str)->dict[str,str]:
    parts=re.split(r'(?m)^## (.*?)\s*$',body)
    if parts[0].strip(): raise Error('Put all text under the four required sections')
    names=parts[1::2];contents=parts[2::2]
    if names!=SUMMARY_SECTIONS: raise Error('Use exactly these sections, in this order: '+' | '.join(SUMMARY_SECTIONS))
    for name,content in zip(names,contents):
        if not content.strip(): raise Error(f'Section is empty (write 없음 if nothing applies): {name}')
    return dict(zip(names,contents))


def add_summary(root:Path,body:str,expected_hash:str|None=None)->dict:
    """Write the human-readable exploration summary. The agent supplies the four sections; the helper
    computes the statistics block from the work log and rejects references to entries that do not exist."""
    body=body.strip('\n')
    if len(body)>SUMMARY_LIMIT: raise Error(f'Summary body is {len(body)} characters; limit is {SUMMARY_LIMIT}. Keep the highest-priority items and say how many were omitted')
    if STATS_BEGIN in body or STATS_END in body: raise Error('The statistics block is generated; do not write it')
    sections=summary_sections(body)
    def summary_material(cfg):
        log_path=inside(root,research_path(cfg,EXPLORE_PATH))
        if log_path.exists():
            log_text=log_path.read_text(encoding='utf-8')
            if frontmatter(log_text).get('project_id')!=cfg['project_id']: raise Error('Exploration log has a different project identity')
            rows=exploration_rows(log_text)[0]
        else: rows=[]
        unknown=sorted(set(ENTRY_REF.findall(body))-{r['id'] for r in rows})
        if unknown: raise Error('Unknown exploration log IDs: '+', '.join(unknown))
        bases, basis_warnings = exclusion_basis(sections[SUMMARY_SECTIONS[1]], rows)
        bare = [item for item in bases if not item['entry_ids'] and not item['decision_link']]
        scope_errors=[]
        unassigned,scopes=exploration_scopes(rows,scope_errors)
        scope_rows=[f"| 미지정 | {unassigned['queries']} | {unassigned['reads']} | 0 |"]
        scope_rows.extend(f"| {question} | {scope['new']['queries']} | {scope['new']['reads']} | {scope['reused']['reads']} |"
                          for question,scope in sorted(scopes.items()))
        heading = '질문별 누계 (질의 / 신규 열람 / 재사용 열람)'
        table = '| 질문 ID | 질의 | 신규 열람 | 재사용 열람 |\n|---|---:|---:|---:|\n' + '\n'.join(scope_rows)
        scope_table = (f'<details><summary>{heading} · 질문 {len(scopes)}개</summary>\n\n{table}\n\n</details>'
                       if len(scopes) > 8 else f'{heading}\n\n{table}')
        last={p:max([int(r['id'][2:]) for r in rows if r['id'][0]==p]+[0]) for p in 'QRU'}
        through=' '.join(f'{p}-{last[p]:04d}' for p in 'QRU' if last[p]) or '없음'
        stats=(f'{STATS_BEGIN}\n'
               f"- 프로젝트 누계: 질의 {sum(r['kind']=='query' for r in rows)}건 · 열람 {sum(r['kind']=='read' for r in rows)}건 "
               f"(snippet 초과 {sum(r['kind']=='read' and r['via']!='snippet' for r in rows)}건) — 도구가 로그에서 계산\n"
               f'{scope_table}\n'
               f'- 이 요약이 반영한 로그 위치: {through}\n'
               f"- 기각·보류 항목의 연결 근거: 검색 기록만 {sum(i['basis']=='query_only' for i in bases)}건"
               f" · 열람 기록 {sum(i['basis']=='read_linked' for i in bases)}건"
               f" · 명시한 결정 링크 {sum(i['basis']=='reported_decision_link' for i in bases)}건"
               f" · 확인된 연결 없음 {sum(i['basis']=='no_resolved_read' for i in bases)}건\n"
               f'- 갱신: {timestamp()}\n{STATS_END}')
        return bases,basis_warnings,bare,through,stats,scope_errors

    cfg=config(root);summary_relative=research_path(cfg,SUMMARY_PATH)
    bases,basis_warnings,bare,through,stats,scope_errors=summary_material(cfg)
    path=inside(root,summary_relative)
    if path.exists():
        if not expected_hash: raise Error('Summary exists; pass --expected-hash of the current file')
        data=path.read_bytes()
        if sha(data)!=expected_hash: raise Error('Summary changed; reload and carry forward any human edits')
        text=data.decode('utf-8');m=re.match(r'\A---\r?\n.*?\r?\n---\r?\n',text,re.S)
        if not m: raise Error('Summary lost its frontmatter')
        new=text[:m.end()]+'\n# 탐색 요약\n\n'+stats+'\n\n'+body+'\n'
        result=safe_update(root,summary_relative,expected_hash,new);status='updated'
    else:
        if expected_hash: raise Error('No summary exists yet; omit --expected-hash')
        with project_lock(root):
            cfg=config(root);summary_relative=research_path(cfg,SUMMARY_PATH)
            bases,basis_warnings,bare,through,stats,scope_errors=summary_material(cfg)
            path=inside(root,summary_relative)
            if path.exists(): raise Error('Summary was created concurrently; reload it')
            new=note(cfg['project_id'],'exploration-summary','탐색 요약',stats+'\n\n'+body)
            path.parent.mkdir(parents=True,exist_ok=True);write_new(path,new)
        result={'sha256':sha(new.encode())};status='created'
    warnings=[f'{len(bare)} rejected/deferred item(s) cite no log ID; each is a review request'] if bare else []
    warnings.extend(basis_warnings)
    warnings.extend('Question-scope statistics: '+issue for issue in scope_errors)
    return {'status':status,'path':summary_relative,'sha256':result['sha256'],'log_through':through,'rejected_without_evidence':len(bare),'exclusion_basis':bases,'warnings':warnings}


def exploration_snapshot(root: Path, cfg: dict):
    """Read a single identified log revision without opening any referenced source."""
    if not inside(root, cfg['research_dir']).is_dir():
        raise Error('Research directory is missing')
    relative = research_path(cfg, EXPLORE_PATH)
    path = inside(root, relative)
    rows = []
    malformed = []
    digest = None
    if path.exists():
        data = path.read_bytes()
        log = data.decode('utf-8')
        meta = frontmatter(log)
        if meta.get('project_id') != cfg['project_id'] or meta.get('kind') != 'exploration':
            raise Error('Expected this project’s exploration log at ' + relative)
        digest = sha(data)
        rows, malformed = exploration_rows(log)
    return relative, digest, rows, malformed


def read_uses(root: Path, cfg: dict, read_id: str, max_chars: int) -> dict:
    if not re.fullmatch(r'R-\d{4,}', read_id):
        raise Error('Specify a read ID such as R-0001')
    path, digest, rows, malformed = exploration_snapshot(root, cfg)
    ids = {read_id}
    ids.update(row['id'] for row in rows if row['kind'] == 'reuse' and row['text'] == read_id)
    selected = [row for row in rows if row['id'] in ids]
    errors = []
    links = resolve_reused_reads(selected, errors)
    if errors:
        raise Error(path + ': ' + '; '.join(errors))
    source = next((r for r in selected if r['id'] == read_id and r['kind'] == 'read'), None)
    if source is None:
        raise Error('Read ID is missing from this project: ' + read_id)
    if source['via'] not in READ_SCOPES:
        raise Error('Unknown read scope for ' + read_id)
    questions = []
    if source['question']:
        questions.append({'question_id': source['question'], 'event_id': read_id, 'reused': False})
    questions.extend({'question_id': row['question'], 'event_id': row['id'], 'reused': True}
                     for row in selected if row['id'] in links)
    result = {'mode': 'read_uses', 'project_id': cfg['project_id'], 'read_id': read_id,
              'log_path': path, 'log_sha256': digest, 'scope': source['via'],
              'locator': source['text'].replace(r'\|', '|'), 'total_questions': len(questions)}
    result.update(bounded_fields([('questions', questions)], max_chars))
    if malformed:
        result['warnings'] = [f'{len(malformed)} malformed log row(s) skipped; run check for line numbers']
    confirm_layout_current(root, cfg)
    return result


def question_context(root: Path, cfg: dict, question: str, max_chars: int) -> dict:
    """Prepare a bounded view of one question from a single exploration log snapshot."""
    relative, digest, rows, malformed = exploration_snapshot(root, cfg)

    events = [row for row in rows if row['question'] == question]
    relevant_ids = {row['id'] for row in events}
    relevant_ids.update(row['text'] for row in events if row['kind'] == 'reuse')
    # Include every occurrence of a requested ID so an ambiguous locator cannot be returned.
    errors = []
    reused_sources = resolve_reused_reads([row for row in rows if row['id'] in relevant_ids], errors)
    if errors:
        raise Error(relative + ': ' + '; '.join(errors))

    entries = []
    included = 0
    required = 0
    for event in events:
        if event['kind'] == 'query':
            entry = {'kind': 'query', 'id': event['id'], 'channel': event['via'],
                     'query': event['text'].replace(r'\|', '|'), 'at': event['at']}
        else:
            reused = event['kind'] == 'reuse'
            source = reused_sources[event['id']] if reused else event
            if source['via'] not in READ_SCOPES:
                raise Error('Unknown read scope for ' + source['id'] + ' in ' + relative)
            entry = {'kind': 'read', 'id': source['id'], 'scope': source['via'],
                     'locator': source['text'].replace(r'\|', '|'), 'at': source['at'], 'reused': reused}
            if reused:
                entry.update(reuse_id=event['id'], reused_at=event['at'], source_question=source['question'])
        required += len(json.dumps(entry, ensure_ascii=False, separators=(',', ':')))
        if required <= max_chars:
            entries.append(entry)
            included = required

    confirm_layout_current(root, cfg)
    return {
        'mode': 'question_context', 'project_id': cfg['project_id'], 'question_id': question,
        'log_path': relative, 'log_sha256': digest, 'entries': entries, 'total_entries': len(events),
        'omitted_entries': len(events) - len(entries), 'character_budget': max_chars,
        'characters_included': included, 'characters_required': required,
        'warnings': [f'{len(malformed)} malformed log row(s) skipped; run check for line numbers'] if malformed else [],
    }


def bounded_fields(fields, max_chars: int) -> dict:
    """Return complete sections and an exact character budget for retrieving every section."""
    result = {}
    omitted = []
    used = required = 0
    for key, value in fields:
        size = len(json.dumps({key: value}, ensure_ascii=False, separators=(',', ':')))
        required += size
        if used + size <= max_chars:
            result[key] = value
            used += size
        else:
            omitted.append(key)
    return {**result, 'character_budget': max_chars, 'characters_included': used,
            'characters_required': required, 'omitted_fields': omitted}


def verified_study_results(snapshot: dict) -> dict | None:
    if snapshot.get('result_rule') or any(item.get('metrics') for item in snapshot.get('observations', [])):
        return companion('ris_results').build_results(snapshot)
    return None


def dispatch_study(root: Path, args):
    api = helper_api()
    study = companion('ris_study')
    if args.study_action == 'results':
        snapshot = study.read_study(api, root, args.id, args.revision)
        results = companion('ris_results')
        explicit_rule = None
        if args.all_metrics or args.any_metrics:
            explicit_rule = results.normalize_rule(api, {
                'mode': 'all' if args.all_metrics else 'any',
                'metric_ids': args.all_metrics or args.any_metrics,
            })
        return results.build_results(snapshot, rule=explicit_rule)
    response = study.dispatch(api, root, args)
    if report := verified_study_results(response):
        return {'verified_results': report, **response}
    return response


def study_context(root: Path, cfg: dict, study_id: str, max_chars: int) -> dict:
    api = helper_api()
    study = companion('ris_study')
    snapshot = study.read_study(api, root, study_id)
    knowledge = companion('ris_knowledge').list_saved_knowledge_links(
        api, root, study_id, study, target_revision=snapshot['revision'])
    if knowledge['current_revision'] != snapshot['revision']:
        raise Error('Study changed while preparing context; retry')
    fields = [(key, snapshot[key]) for key in ('goal', 'recommendation', 'user_decision', 'rationale',
              'metric_review', 'next_action', 'criteria', 'conditions', 'evaluations', 'next_test', 'active_test',
              'test', 'hypotheses', 'active_hypothesis_ids', 'retired_hypothesis_ids',
              'indistinguishable_groups', 'prediction_warnings', 'amendments', 'observations') if key in snapshot]
    if report := verified_study_results(snapshot):
        fields.insert(0, ('verified_summary', report['summary']))
        fields.insert(1, ('overall_result', report['overall']))
        fields.append(('criterion_results', report['criterion_results']))
    fields.append(('reused_knowledge', knowledge['links']))
    confirm_layout_current(root, cfg)
    return {'mode': 'study_context', 'project_id': cfg['project_id'], 'study_id': snapshot['id'],
            'revision': snapshot['revision'], 'path': snapshot['path'], **bounded_fields(fields, max_chars)}


def context(root:Path,include:list[str]|None=None,max_chars:int=20000,*,question:str|None=None,
            study_id:str|None=None,read_id:str|None=None)->dict:
    cfg=config(root)
    if max_chars<1000:raise Error('Context budget must be at least 1000 characters')
    question = validated_question_id(question)
    if sum((bool(include), question is not None, study_id is not None, read_id is not None)) > 1:
        raise Error('Choose one context selector')
    if study_id is not None:
        return study_context(root, cfg, study_id, max_chars)
    if read_id is not None:
        return read_uses(root, cfg, read_id, max_chars)
    if question is not None:
        view = question_context(root, cfg, question, max_chars)
        recovery = companion('ris_recovery')
        if inside(root, recovery.PATH).is_file():
            ledger, _ = recovery.read(helper_api(), root)
            node = ledger['nodes'].get(question)
            if node:
                view['recovery'] = {'path': recovery.PATH, 'revision': ledger['revision'],
                                    'active': node['active'], 'count': node['count'],
                                    'observed_count': node.get('observed_count', 0),
                                    'exhaustive': node['exhaustive']}
        findings = companion('ris_findings')
        relative = findings.location(helper_api(), cfg, question)
        if inside(root, relative).is_file():
            projection = findings.projected_context(helper_api(), root, relative)
            if projection is not None:
                value = json.loads(projection)
                view['knowledge_ref'] = {'path': relative, 'revision': value['revision'],
                                         'sha256': value['file_sha256']}
                view['characters_required'] += len(projection)
                if len(projection) <= max_chars - view['characters_included']:
                    view['knowledge'] = value
                    view['characters_included'] += len(projection)
                else:
                    view['warnings'].append('Knowledge projection exceeds budget; inspect findings by node ID')
        return view
    state_path=inside(root,STATE_PATH)
    orchestration_state=read_state(root) if state_path.exists() else None
    active_plan_ref=(orchestration_state or {}).get('active_plan_ref') or cfg.get('active_plan')
    active_plan=active_plan_ref.split('#',1)[0] if active_plan_ref else None
    research_root=inside(root,cfg['research_dir'])
    selected=list(dict.fromkeys([research_path(cfg,'research/INDEX.md'),research_path(cfg,'research/CONTEXT.md')]+([active_plan] if active_plan else [])+(include or [])))
    # Metadata is an inventory, not proof that any source or concept was read or understood.
    inventory=[{'path':str(p.relative_to(root)),'ris_id':m.get('ris_id'),'kind':m.get('kind'),'status':m.get('status')} for p,m,_ in notes(root,metadata_only=True) if m.get('project_id') == cfg['project_id']]
    result=[];omitted=[];used=0
    for relative in selected:
        path=inside(root,relative)
        if not path.is_file() or path.suffix!='.md':raise Error('Selected context note is missing or not Markdown: '+relative)
        if not path.is_relative_to(research_root):raise Error('Context notes must belong to this project research directory')
        data=path.read_bytes();text=data.decode('utf-8');meta=frontmatter(text)
        if meta.get('project_id')!=cfg['project_id']:raise Error('Selected note has different project identity: '+relative)
        if not companion('ris_knowledge').is_local_knowledge_metadata(meta,cfg['project_id']):
            raise Error('Historical external knowledge is unavailable to this project')
        projection = companion('ris_findings').projected_context(helper_api(),root,relative)
        extra = {}
        if projection is not None:
            if json.loads(projection)['file_sha256'] != sha(data):
                raise Error('Findings changed during context preparation; reload')
            text = projection
            extra['representation'] = 'current_findings_projection'
        if used+len(text)>max_chars:omitted.append({'path':relative,'reason':'character_budget'});continue
        result.append({'path':relative,'sha256':sha(data),'text':text,**extra});used+=len(text)
    included={r['path'] for r in result};omitted_paths={r['path'] for r in omitted}
    omitted += [{'path':r['path'],'reason':'not_selected'} for r in inventory if r['path'] not in included|omitted_paths]
    confirm_layout_current(root,cfg)
    return {'project':cfg,'prepared_at':timestamp(),'mode':'prepared_snapshot','observed_read':False,'understanding_assessed':False,'character_budget':max_chars,'characters_included':used,'records':result,'omitted':omitted,'orchestration_state':orchestration_state,**layout_output(cfg),
            'limitations':['This snapshot includes selected notes only, not the full project or agent internal context.','File inventory is not evidence of source review.','Linked Zotero/PDF/code sources were not read by this command.','Orchestration state contains bookkeeping and references, not the content of linked evidence.']}


def propose(root:Path,relative:str,expected_hash:str,body:str)->dict:
    # Preserve original bytes; review/merge stays explicit while recording policy is undecided.
    with project_lock(root):
        cfg=config(root);path=inside(root,relative)
        if not path.is_relative_to(inside(root,cfg['research_dir'])) or path.suffix!='.md' or not path.is_file():raise Error('Research layout changed; select a current research Markdown note')
        data=path.read_bytes()
        if sha(data)!=expected_hash:raise Error('Note changed since it was read; reload before proposing')
        meta=frontmatter(data.decode('utf-8'))
        if meta.get('project_id')!=cfg['project_id']:raise Error('Project identity mismatch')
        folder=inside(root,'.ris/proposals');folder.mkdir(parents=True,exist_ok=True)
        proposal=folder/(str(uuid4())+'.json')
        value={'schema_version':1,'project_id':cfg['project_id'],'target':relative,'base_sha256':expected_hash,'created':timestamp(),'proposed_body':body,'status':'proposed','original_unchanged':True}
        write_new(proposal,json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    return {'proposal':str(proposal.relative_to(root)),'status':'proposed','original_unchanged':True}


def safe_update(root:Path,relative:str,expected_hash:str,text:str,owner:str|None=None,shared_source:bool=False)->dict:
    if shared_source and owner is None:raise Error('--shared-source requires --owner')
    with project_lock(root):
        cfg=config(root);path=inside(root,relative)
        if not path.is_file() or not path.is_relative_to(inside(root,cfg['research_dir'])) or path.suffix!='.md':
            raise Error('Select an existing research Markdown note in the current research layout')
        data=path.read_bytes()
        if sha(data)!=expected_hash:raise Error('Note changed; reload before updating')
        before=frontmatter(data.decode('utf-8'));after=frontmatter(text)
        if not before.get('ris_id') or before.get('project_id')!=cfg['project_id']:
            raise Error('Expected a managed note in this project')
        if any(after.get(k)!=before.get(k) for k in ('ris_id','project_id','kind','created')):
            raise Error('Preserve note identity, kind and creation date')
        if after.get('artifact_owner') != before.get('artifact_owner'):
            raise Error('Preserve the canonical artifact owner')
        if owner is not None and before.get('artifact_owner'):
            if owner != before['artifact_owner'] or shared_source:
                raise Error('Select the dedicated canonical source for this role')
        if owner is not None:
            companion('ris_artifacts').check_update(owner, before['kind'], data.decode('utf-8'), text, shared_source,
                                                     dedicated=bool(before.get('artifact_owner')))
        if before.get('kind') == 'study' or before.get('study_schema_version') is not None:
            companion('ris_study').validate_note_edit(helper_api(), data.decode('utf-8'), text)
        if before.get('knowledge_record') is True and text.encode('utf-8') != data:
            raise Error('A saved knowledge finding is revision-pinned. Record a new assessment or related note.')
        history=inside(root,'.ris/history');history.mkdir(exist_ok=True)
        backup=history/(sha(data)+'.md')
        if not backup.exists():write_new(backup,data.decode('utf-8'))
        if path.read_bytes()!=data:raise Error('External edit detected; original retained')
        # Cooperative writers only: Obsidian can still race after this comparison.
        atomic_note_write(path, text.encode('utf-8'), expected=data)
    return {'status':'updated','path':relative,'sha256':sha(text.encode()),'backup':str(backup.relative_to(root))}


def configure(root:Path,expected_hash:str,recording_policy=None,exploration_mode=None,active_plan=None)->dict:
    path=inside(root,'.ris/project.yaml')
    if recording_policy is not None and recording_policy not in RECORDING_POLICIES:raise Error('Unknown recording policy')
    if exploration_mode is not None and exploration_mode not in ('autonomous','guided'):raise Error('Unknown exploration mode')
    with project_lock(root):
        data=path.read_bytes()
        if sha(data)!=expected_hash:raise Error('Configuration changed; reload before updating')
        cfg=config(root)
        if recording_policy is not None:cfg['recording_policy']=recording_policy
        if exploration_mode is not None:cfg['exploration_mode']=exploration_mode
        if active_plan is not None:
            p=inside(root,active_plan)
            if not p.is_file() or not p.is_relative_to(inside(root,research_path(cfg,'research/plans'))) or p.suffix!='.md':
                raise Error('Active plan must be an existing project research/plans Markdown note')
            metadata=frontmatter(p.read_text(encoding='utf-8'))
            if metadata.get('project_id')!=cfg['project_id'] or metadata.get('kind')!='plan':raise Error('Expected this project’s managed plan')
            cfg['active_plan']=active_plan
        history=inside(root,'.ris/history');history.mkdir(exist_ok=True)
        backup=history/(sha(data)+'.yaml')
        if not backup.exists():write_new(backup,data.decode())
        atomic_note_write(path,yaml_mapping(cfg).encode('utf-8'),expected=data)
    return {'status':'configured','project':cfg}


@lru_cache(maxsize=None)
def companion(name: str):
    """Load a bundled helper alongside this particular installation."""
    module_path = Path(__file__).with_name(name + '.py')
    spec = importlib.util.spec_from_file_location(f'{__name__}.{name}', module_path)
    if spec is None or spec.loader is None:
        raise Error('Unable to load bundled helper: ' + str(module_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def helper_api():
    # Direct callers may load this script from a path without registering its module name.
    return sys.modules.get(__name__) or SimpleNamespace(**globals())


def run_layout_migration(root:Path,apply:bool=False,include_handoff:bool=False)->dict:
    return companion('ris_layout_migration').migrate_layout(root,apply=apply,include_handoff=include_handoff)


def main(argv=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',default='.',help='Explicit project root; no global active-project state')
    sub=parser.add_subparsers(dest='command',required=True)
    study_actions = companion('ris_study').add_parser(sub)
    result_cmd = study_actions.add_parser('results', help='Read the criterion table and its generated summary')
    result_cmd.add_argument('id')
    result_cmd.add_argument('--revision', type=int, help='Read one historical study revision')
    composition = result_cmd.add_mutually_exclusive_group()
    composition.add_argument('--all', dest='all_metrics', nargs='+', metavar='METRIC_ID',
                             help='Preview a rule requiring all named metrics to pass')
    composition.add_argument('--any', dest='any_metrics', nargs='+', metavar='METRIC_ID',
                             help='Preview a rule requiring at least one named metric to pass')
    result_cmd.add_argument('--format', choices=('json', 'markdown'), default='json')
    companion('ris_study_views').add_parser(sub)
    companion('ris_knowledge').add_parser(sub)
    companion('ris_metrics').add_parser(sub)
    companion('ris_recovery').add_parser(sub)
    companion('ris_delivery').add_parser(sub)
    companion('ris_findings').add_parser(sub)
    companion('ris_learning').add_parser(sub)
    companion('ris_simulation').add_parser(sub)
    companion('ris_coordination').add_parser(sub)
    companion('ris_views').add_parser(sub)
    init=sub.add_parser('init');init.add_argument('--name');init.add_argument('--goal',default='');init.add_argument('--attach-agents',action='store_true');init.add_argument('--dry-run',action='store_true')
    init.add_argument('--recording-policy',choices=RECORDING_POLICIES,help='New project only; significant by default')
    migrate=sub.add_parser('migrate-layout',help='Preview schema 1 to schema 2 storage migration; pass --apply to write')
    migrate.add_argument('--apply',action='store_true',help='Apply the migration; without this flag only inspect planned changes')
    migrate.add_argument('--include-handoff',action='store_true',help='Explicitly include the legacy root HANDOFF.md in the preview and migration plan')
    check_parser=sub.add_parser('check');check_parser.add_argument('--question',help='Report exploration scoped to this question ID')
    sub.add_parser('status')
    ctx = sub.add_parser('context')
    selection = ctx.add_mutually_exclusive_group()
    selection.add_argument('--include', action='append', default=[], help='Include a project note in the default snapshot')
    selection.add_argument('--question', help='Resume one question with its queries, source locators and explicit reuse')
    selection.add_argument('--study', help='Resume a study with its hypotheses, results and current recommendation')
    selection.add_argument('--read', help='Find questions linked to one exploration read ID')
    ctx.add_argument('--max-chars', type=int, default=20000)
    mi=sub.add_parser('map-index',help='Read compact IDs, parents and titles for Researcher placement review')
    mi.add_argument('target');mi.add_argument('--node',action='append',default=[],help='Also read the detail cells for this node')
    rec=sub.add_parser('record');rec.add_argument('--kind',choices=sorted(KINDS),required=True);rec.add_argument('--title',required=True);rec.add_argument('--body-file',default='-');rec.add_argument('--related',action='append',default=[])
    rec.add_argument('--owner',choices=('researcher','planner'),help='Create a separate, role-owned map or plan source')
    exp=sub.add_parser('explore');exp.add_argument('--kind',choices=sorted(EXPLORE_KINDS));exp.add_argument('--via',help='query: channel label (web, zotero, code); read: snippet|abstract|full|code|data');exp.add_argument('--text');exp.add_argument('--question',help='Associate this entry with a question ID');exp.add_argument('--reuse',action='append',default=[],help='Reuse an existing read ID (repeatable; requires --question)')
    summ=sub.add_parser('summarize');summ.add_argument('--body-file',default='-');summ.add_argument('--expected-hash')
    prop=sub.add_parser('propose');prop.add_argument('target');prop.add_argument('--expected-hash',required=True);prop.add_argument('--body-file',default='-')
    att=sub.add_parser('attach');att.add_argument('--dry-run',action='store_true')
    update=sub.add_parser('update');update.add_argument('target');update.add_argument('--expected-hash',required=True);update.add_argument('--body-file',required=True)
    settings=sub.add_parser('configure');settings.add_argument('--expected-hash',required=True);settings.add_argument('--recording-policy',choices=RECORDING_POLICIES);settings.add_argument('--exploration-mode',choices=['autonomous','guided']);settings.add_argument('--active-plan')
    update.add_argument('--owner',choices=('researcher','planner'),help='Protect the other role’s content when saving a Research Map or Research Plan')
    update.add_argument('--shared-source',action='store_true',help='Use legacy combined-source boundaries, including for custom map headings')
    state=sub.add_parser('state');state_sub=state.add_subparsers(dest='state_action',required=True)
    state_init=state_sub.add_parser('init');state_init.add_argument('--run-id');state_init.add_argument('--goal-ref');state_init.add_argument('--active-plan-ref')
    state_sub.add_parser('read')
    state_update=state_sub.add_parser('update');state_update.add_argument('--expected-hash',required=True);state_update.add_argument('--body-file',required=True)
    args=parser.parse_args(argv);root=Path(args.project).expanduser().resolve()
    try:
        # Older helpers accept absolute input filenames. Bind them to this CLI project before
        # dispatch so a named request body or metric definition cannot import a sibling project.
        for field in ('body_file', 'metrics_file', 'definition'):
            filename = getattr(args, field, None)
            if not filename or filename == '-':
                continue
            selected = Path(filename)
            if selected.is_absolute():
                if not selected.is_relative_to(root):
                    raise Error('Stage the authorized input inside the selected project or use supported stdin')
                selected = selected.relative_to(root)
            setattr(args, field, str(inside(root, str(selected))))
        if args.command=='init':value=initialize(root,args.name,args.goal,args.attach_agents,args.dry_run,args.recording_policy)
        elif args.command=='study':value=dispatch_study(root,args)
        elif args.command=='study-link':value=companion('ris_study_views').dispatch(helper_api(),root,args,companion('ris_study'))
        elif args.command=='knowledge':value=companion('ris_knowledge').dispatch(helper_api(),root,args,companion('ris_study'))
        elif args.command=='view':value=companion('ris_views').dispatch(helper_api(),root,args)
        elif args.command=='coordinate':value=companion('ris_coordination').run(helper_api(),root,args)
        elif args.command=='simulate':value=companion('ris_simulation').dispatch(helper_api(),root,args)
        elif args.command in ('learning','findings'):
            value=companion('ris_'+args.command).dispatch(helper_api(),root,args)
        elif args.command=='delivery':value=companion('ris_delivery').dispatch(helper_api(),root,args)
        elif args.command=='recovery':value=companion('ris_recovery').dispatch(helper_api(),root,args)
        elif args.command=='metric':value=companion('ris_metrics').dispatch(helper_api(),root,args)
        elif args.command=='migrate-layout':value=run_layout_migration(root,args.apply,args.include_handoff)
        elif args.command=='check':value=check(root,args.question)
        elif args.command=='status':value=check(root)
        elif args.command=='context':value=context(root,args.include,args.max_chars,question=args.question,
                                                   study_id=args.study,read_id=args.read)
        elif args.command=='explore':value=add_exploration(root,args.kind,args.text,args.via,args.question,args.reuse)
        elif args.command=='configure':value=configure(root,args.expected_hash,args.recording_policy,args.exploration_mode,args.active_plan)
        elif args.command=='map-index':
            cfg=config(root);path=inside(root,args.target)
            if path.suffix != '.md' or not path.is_relative_to(inside(root,cfg['research_dir'])):
                raise Error('Select a managed Research Map Markdown source in this project')
            raw=path.read_bytes();source=raw.decode('utf-8');metadata=frontmatter(source)
            if metadata.get('kind') not in ('map','plan') or metadata.get('project_id')!=cfg['project_id']:
                raise Error('Expected this project’s Research Map or combined plan/map')
            value=companion('ris_artifacts').compact_index(source,set(args.node))
            value.update(path=args.target,sha256=sha(raw))
        elif args.command=='update':value=safe_update(root,args.target,args.expected_hash,Path(args.body_file).read_bytes().decode('utf-8'),args.owner,args.shared_source)
        elif args.command=='state':
            if args.state_action=='init':value=initialize_state(root,args.run_id,args.goal_ref,args.active_plan_ref)
            elif args.state_action=='read':value=read_state_snapshot(root)
            else:value=update_state(root,args.expected_hash,Path(args.body_file).read_text(encoding='utf-8'))
        elif args.command=='attach':
            config(root)
            with project_lock(root):value=attach_agents(root,args.dry_run)
        else:
            body=sys.stdin.read() if args.body_file=='-' else Path(args.body_file).read_text(encoding='utf-8')
            if args.command=='summarize':value=add_summary(root,body,args.expected_hash)
            elif args.command=='record':value=add_record(root,args.kind,args.title,body,args.related,args.owner)
            else:value=propose(root,args.target,args.expected_hash,body)
        if args.command == 'delivery' and args.format == 'markdown' and value.get('ok') is not False:
            print(companion('ris_delivery').render(value))
        elif args.command == 'study' and args.study_action == 'results' and args.format == 'markdown':
            print(companion('ris_results').render_results(value))
        else:
            print(json.dumps(value,ensure_ascii=False,indent=2))
        return 1 if isinstance(value,dict) and value.get('ok') is False else 0
    except (Error,OSError,UnicodeError,ValueError) as e:
        print(json.dumps({'error':str(e)},ensure_ascii=False),file=sys.stderr);return 2

if __name__=='__main__':sys.exit(main())
