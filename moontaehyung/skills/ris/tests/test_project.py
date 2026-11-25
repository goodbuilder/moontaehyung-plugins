import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

SCRIPT=Path(__file__).resolve().parents[1]/'scripts'/'ris.py'
spec=importlib.util.spec_from_file_location('ris_file_helper',SCRIPT)
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)

@pytest.fixture
def project(tmp_path):
    p=tmp_path/'project';p.mkdir();return p

def research_relative(project,relative):
    return f"{helper.config(project)['research_dir'].rstrip('/')}/{relative.lstrip('/')}"

def research_path(project,relative):
    return project/research_relative(project,relative)

def exploration_log(project):
    return research_path(project,'exploration/log.md')

def exploration_summary(project):
    return research_path(project,'exploration/summary.md')

def make_legacy_v1(project):
    """Convert a fresh fixture to the on-disk schema-1 layout for compatibility checks."""
    helper.initialize(project)
    cfg=helper.config(project)
    (project/cfg['research_dir']).rename(project/'research')
    legacy={key:cfg[key] for key in ('template_version','project_id','name','recording_policy','created')}
    legacy={'schema_version':1,'research_dir':'research',**legacy}
    (project/'.ris/project.yaml').write_text(helper.yaml_mapping(legacy),encoding='utf-8')
    return legacy

def test_preview_is_read_only(project):
    preview=helper.initialize(project,'한글 연구','Goal',attach=True,dry_run=True)
    assert preview['status']=='preview' and list(project.iterdir())==[]

def test_schema2_default_is_private_and_preserves_unrelated_root_research_and_handoff(project):
    root_research=project/'research';root_research.mkdir()
    unrelated=root_research/'CONTEXT.md';unrelated.write_text('Unrelated project research')
    root_handoff=project/'HANDOFF.md';root_handoff.write_text('Human handoff')

    initialized=helper.initialize(project,'Isolated study')
    cfg=helper.config(project)
    expected_handoff='.ris/HANDOFF.md'
    assert cfg['schema_version']==2 and cfg['research_dir']=='.ris/research'
    assert initialized['research_dir']=='.ris/research'
    assert initialized['handoff_path']==expected_handoff
    assert helper.check(project)['research_dir']=='.ris/research'
    assert helper.check(project)['handoff_path']==expected_handoff
    snapshot=helper.context(project)
    assert snapshot['project']['research_dir']=='.ris/research'
    assert snapshot['handoff_path']==expected_handoff
    assert root_research.is_dir() and unrelated.read_text()=='Unrelated project research'
    assert root_handoff.read_text()=='Human handoff'
    assert not (project/'.ris/HANDOFF.md').exists()  # path is lazy until an authorized handoff

def test_schema2_default_creates_no_research_or_handoff_artifacts_at_project_root(project):
    result=helper.initialize(project)
    assert result['research_dir']=='.ris/research'
    assert {path.name for path in project.iterdir()}=={'.ris'}
    assert (project/'.ris/research/INDEX.md').is_file()
    assert not (project/'research').exists()
    assert not (project/'HANDOFF.md').exists()

def test_schema1_keeps_legacy_root_research_and_handoff_paths(project):
    make_legacy_v1(project)
    cfg=helper.config(project)
    assert cfg['schema_version']==1 and cfg['research_dir']=='research'
    handoff=project/'HANDOFF.md';handoff.write_text('Legacy human handoff')
    record=helper.add_record(project,'finding','Legacy result','Still stored in the old layout')
    assert record['path'].startswith('research/findings/')
    assert research_path(project,'CONTEXT.md').is_file()
    context=helper.context(project)
    assert context['project']['research_dir']=='research'
    assert context['handoff_path']=='HANDOFF.md'
    report=helper.check(project)
    assert report['research_dir']=='research' and report['handoff_path']=='HANDOFF.md'
    assert report['schema_version']==1 and report['ok']
    assert handoff.read_text()=='Legacy human handoff'
    helper.initialize_state(project)
    assert helper.read_state(project)['goal_ref']=='research/CONTEXT.md'

@pytest.mark.parametrize('name,args',[
    ('record',('record','--kind','finding','--title','Must fail')),
    ('update',('update','.ris/research/CONTEXT.md','--expected-hash','0'*64,'--body-file','{body}')),
    ('explore',('explore','--kind','query','--via','web','--text','Must fail')),
    ('configure',('configure','--expected-hash','0'*64,'--recording-policy','milestones')),
    ('state-init',('state','init')),
])
def test_uninitialized_write_commands_refuse_without_creating_project_artifacts(tmp_path,name,args):
    project=tmp_path/name;project.mkdir()
    body=tmp_path/'update.md';body.write_text('Proposed update')
    cli_args=[str(SCRIPT),'--project',str(project),*(str(x).replace('{body}',str(body)) for x in args)]
    result=subprocess.run([sys.executable,*cli_args],text=True,capture_output=True)
    assert result.returncode!=0
    assert list(project.iterdir())==[]

def test_init_is_idempotent_and_preserves_human_edits(project):
    first=helper.initialize(project,'연구: "A"','목표')
    before=(project/'.ris/project.yaml').read_bytes()
    context=research_path(project,'CONTEXT.md');context.write_text(context.read_text()+'\n내가 쓴 내용\n')
    result=helper.initialize(project,'Ignored name')
    assert result['status']=='already_initialized'
    assert before==(project/'.ris/project.yaml').read_bytes()
    assert '내가 쓴 내용' in context.read_text()
    assert first['project_id']==helper.config(project)['project_id']
    assert helper.check(project)['ok']

def test_existing_entry_file_requires_adoption_without_partial_writes(project):
    target=project/'.ris/research';target.mkdir(parents=True);index=target/'INDEX.md';index.write_text('Existing research')
    with pytest.raises(helper.Error):helper.initialize(project,attach=True)
    assert index.read_text()=='Existing research'
    assert not (project/'.ris/project.yaml').exists() and not (project/'AGENTS.md').exists()

def test_agents_append_preserves_exact_existing_bytes_and_only_one_hook(project):
    prior=b'# Existing\r\n\r\nDo not change.\r\n'
    (project/'AGENTS.md').write_bytes(prior)
    helper.initialize(project,attach=True)
    assert (project/'AGENTS.md').read_bytes().startswith(prior)
    snapshots=list((project/'.ris/history').glob('AGENTS-*.md'))
    assert len(snapshots)==1 and snapshots[0].read_bytes()==prior
    after=(project/'AGENTS.md').read_bytes();helper.initialize(project,attach=True)
    assert (project/'AGENTS.md').read_bytes()==after

def test_malformed_agents_fails_before_initialization(project):
    (project/'AGENTS.md').write_text('User instructions\n'+helper.START)
    with pytest.raises(helper.Error):helper.initialize(project,attach=True)
    assert not (project/'.ris/project.yaml').exists()

def test_unrelated_projects_do_not_share_context_or_relation_ids(project,tmp_path):
    helper.initialize(project)
    other=tmp_path/'other';other.mkdir();helper.initialize(other)
    record=helper.add_record(project,'finding','Private result','Only in A')
    snapshot=helper.context(other)
    assert 'Private result' not in json.dumps(snapshot)
    with pytest.raises(helper.Error):helper.add_record(other,'decision','Wrong relation','No',[record['ris_id']])
    assert helper.check(project)['project_id']!=helper.check(other)['project_id']

def test_handoff_includes_current_obsidian_content_and_explicit_omissions(project):
    helper.initialize(project)
    record=helper.add_record(project,'finding','Result','Observed failure; interpretation uncertain')
    p=project/record['path'];p.write_text(p.read_text()+'\nObsidian edit\n')
    snapshot=helper.context(project,[record['path']])
    assert 'Obsidian edit' in snapshot['records'][-1]['text']
    assert snapshot['records'][-1]['sha256']==hashlib.sha256(p.read_bytes()).hexdigest()
    assert snapshot['observed_read'] is False and snapshot['understanding_assessed'] is False
    default=helper.context(project)
    assert any(x['path']==record['path'] and x['reason']=='not_selected' for x in default['omitted'])

def test_context_budget_never_silently_truncates_note(project):
    helper.initialize(project)
    record=helper.add_record(project,'concept','Long note','x'*10000)
    snapshot=helper.context(project,[record['path']],max_chars=4000)
    assert snapshot['characters_included']<=4000
    assert any(x['path']==record['path'] and x['reason']=='character_budget' for x in snapshot['omitted'])

def test_proposal_preserves_source_and_rejects_stale_base(project):
    helper.initialize(project)
    target=research_relative(project,'CONTEXT.md')
    p=project/target;before=p.read_bytes();base=hashlib.sha256(before).hexdigest()
    result=helper.propose(project,target,base,'Replacement proposal')
    assert p.read_bytes()==before
    assert json.loads((project/result['proposal']).read_text())['proposed_body']=='Replacement proposal'
    p.write_text(p.read_text()+'\nExternal edit')
    with pytest.raises(helper.Error):helper.propose(project,target,base,'Stale overwrite')
    assert len(list((project/'.ris/proposals').glob('*.json')))==1

def test_duplicate_ids_wrong_project_and_missing_links_are_visible(project):
    helper.initialize(project)
    r=helper.add_record(project,'finding','Result','[missing](not-there.csv)')
    p=project/r['path'];(p.parent/'duplicate.md').write_bytes(p.read_bytes())
    report=helper.check(project)
    assert any('Duplicate ris_id' in x for x in report['errors'])
    assert any('missing link' in x for x in report['warnings'])
    (p.parent/'duplicate.md').unlink()
    text=p.read_text().replace(helper.config(project)['project_id'],'other-project')
    p.write_text(text)
    assert any('project identity mismatch' in x for x in helper.check(project)['errors'])

def test_symlink_and_traversal_refused_without_outside_write(project,tmp_path):
    outside=tmp_path/'outside';outside.mkdir()
    # The unrelated legacy root path is outside the default managed surface.
    (project/'research').symlink_to(outside,target_is_directory=True)
    helper.initialize(project)
    assert list(outside.iterdir())==[]
    managed=project/'.ris/research'
    managed.rename(project/'.ris/research-original')
    managed.symlink_to(outside,target_is_directory=True)
    with pytest.raises(helper.Error):helper.context(project)
    with pytest.raises(helper.Error):helper.add_record(project,'finding','Blocked write','Must stay outside')
    assert list(outside.iterdir())==[]
    with pytest.raises(helper.Error):helper.inside(project,'../escape.md')

def test_initializer_refuses_symlinked_managed_root_without_outside_writes(project,tmp_path):
    outside=tmp_path/'outside';outside.mkdir()
    (project/'.ris').mkdir()
    (project/'.ris/research').symlink_to(outside,target_is_directory=True)
    with pytest.raises(helper.Error):helper.initialize(project)
    assert list(outside.iterdir())==[]
    assert not (project/'.ris/project.yaml').exists()

@pytest.mark.parametrize('collision',['file','symlink'])
def test_initializer_refuses_reserved_handoff_collision_without_partial_writes(project,tmp_path,collision):
    root_research=project/'research';root_research.mkdir()
    unrelated=root_research/'keep.md';unrelated.write_text('Unrelated research')
    root_handoff=project/'HANDOFF.md';root_handoff.write_text('Unrelated handoff')
    ris=project/'.ris';ris.mkdir()
    reserved=ris/'HANDOFF.md'
    if collision=='file':
        reserved.write_text('Existing reserved path')
    else:
        outside=tmp_path/'outside';outside.mkdir()
        sentinel=outside/'keep.md';sentinel.write_text('Outside sentinel')
        reserved.symlink_to(sentinel)

    with pytest.raises(helper.Error):helper.initialize(project)
    assert not (ris/'project.yaml').exists() and not (ris/'research').exists()
    assert unrelated.read_text()=='Unrelated research'
    assert root_handoff.read_text()=='Unrelated handoff'
    if collision=='file':
        assert reserved.read_text()=='Existing reserved path'
    else:
        assert reserved.is_symlink() and sentinel.read_text()=='Outside sentinel'

def test_unknown_version_refused_without_modification(project):
    helper.initialize(project)
    p=project/'.ris/project.yaml';p.write_text(p.read_text().replace('schema_version: 2','schema_version: 999'))
    before=p.read_bytes()
    with pytest.raises(helper.Error):helper.initialize(project)
    assert p.read_bytes()==before

def test_cli_new_session_workflow_uses_only_project_files(project):
    def call(*args,input=None):
        return subprocess.run([sys.executable,str(SCRIPT),'--project',str(project),*args],input=input,text=True,capture_output=True)
    init=call('init','--name','Test study','--attach-agents');assert init.returncode==0,init.stderr
    record=call('record','--kind','finding','--title','Partial result',input='Observed B failed. Next: check assumption C.')
    assert record.returncode==0,record.stderr
    filename=json.loads(record.stdout)['path']
    assert filename.startswith('.ris/research/findings/')
    fresh=call('context','--include',filename)
    assert fresh.returncode==0,fresh.stderr
    assert 'assumption C' in json.loads(fresh.stdout)['records'][-1]['text']
    status=call('status');assert status.returncode==0,status.stderr
    assert json.loads(status.stdout)['research_dir']=='.ris/research'
    assert json.loads(status.stdout)['handoff_path']=='.ris/HANDOFF.md'
    assert call('check').returncode==0
    assert not (project/'ris.sqlite').exists()
    assert not (project/'research').exists() and not (project/'HANDOFF.md').exists()

def test_empty_agents_can_be_attached(project):
    (project/'AGENTS.md').touch()
    helper.initialize(project,attach=True)
    assert helper.START in (project/'AGENTS.md').read_text()
    assert helper.check(project)['ok']

def test_attachment_after_initialization_reports_actual_change(project):
    helper.initialize(project)
    changed=helper.initialize(project,attach=True)
    assert changed['changed'] is True
    assert helper.initialize(project,attach=True)['changed'] is False

def test_handoff_refuses_foreign_frontmatter_even_when_copied_inside_project(project,tmp_path):
    helper.initialize(project)
    other=tmp_path/'other';other.mkdir();helper.initialize(other)
    r=helper.add_record(other,'concept','Other project context','Must not leak')
    relative=research_relative(project,'concepts/copied.md')
    target=project/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((other/r['path']).read_bytes())
    with pytest.raises(helper.Error):helper.context(project,[relative])


def test_milestone_configuration_and_active_plan_resume(project):
    helper.initialize(project)
    plan=helper.add_record(project,'plan','Active graph','Current node D-001; pending dataset probe')
    cfg=project/'.ris/project.yaml';base=hashlib.sha256(cfg.read_bytes()).hexdigest()
    helper.configure(project,base,'milestones','autonomous',plan['path'])
    snapshot=helper.context(project)
    assert snapshot['project']['recording_policy']=='milestones'
    assert 'pending dataset probe' in snapshot['records'][-1]['text']
    with pytest.raises(helper.Error):helper.configure(project,base,'manual')
    with pytest.raises(helper.Error):helper.configure(project,hashlib.sha256(cfg.read_bytes()).hexdigest(),exploration_mode='unknown')


def test_context_resumes_anchored_state_plan(project):
    helper.initialize(project)
    plan=helper.add_record(project,'plan','Active graph','Current node D-001; pending dataset probe')
    reference=plan['path']+'#D-001'
    helper.initialize_state(project,active_plan_ref=reference)
    assert helper.read_state(project)['goal_ref']==research_relative(project,'CONTEXT.md')
    assert helper.check(project)['ok']
    result=subprocess.run(
        [sys.executable,str(SCRIPT),'--project',str(project),'context','--include',plan['path']],
        capture_output=True,encoding='utf-8')
    assert result.returncode==0,result.stderr
    snapshot=json.loads(result.stdout)
    assert snapshot['orchestration_state']['active_plan_ref']==reference
    plans=[record for record in snapshot['records'] if record['path']==plan['path']]
    assert len(plans)==1 and 'pending dataset probe' in plans[0]['text']


def test_configure_reads_utf8_plan_under_ascii_locale(project):
    helper.initialize(project)
    plan=helper.add_record(project,'plan','한글 계획','다음 단계는 자료 접근 확인입니다.')
    cfg=project/'.ris/project.yaml'
    env=os.environ.copy()
    env.update(LC_ALL='C',PYTHONUTF8='0',PYTHONCOERCECLOCALE='0')
    # This helper is stdlib-only; isolate it from locale-sensitive site/.pth startup.
    result=subprocess.run(
        [sys.executable,'-S',str(SCRIPT),'--project',str(project),'configure',
         '--expected-hash',hashlib.sha256(cfg.read_bytes()).hexdigest(),'--active-plan',plan['path']],
        env=env,capture_output=True,encoding='utf-8')
    assert result.returncode==0,result.stderr
    assert helper.config(project)['active_plan']==plan['path']


def test_authorized_update_preserves_identity_and_exact_preimage(project):
    helper.initialize(project)
    target=research_relative(project,'CONTEXT.md')
    path=project/target;original=path.read_bytes();base=hashlib.sha256(original).hexdigest()
    text=original.decode()+'\nConfirmed choice D-001: rgb; next compare evidence.\n'
    result=helper.safe_update(project,target,base,text)
    assert (project/result['backup']).read_bytes()==original
    assert path.read_text()==text
    with pytest.raises(helper.Error):helper.safe_update(project,target,base,'stale')
    current=hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(helper.Error):helper.safe_update(project,target,current,text.replace(helper.config(project)['project_id'],'foreign'))
    assert path.read_text()==text


def test_missing_active_plan_is_visible(project):
    helper.initialize(project)
    r=helper.add_record(project,'plan','Plan','Pending probe')
    p=project/'.ris/project.yaml'
    helper.configure(project,hashlib.sha256(p.read_bytes()).hexdigest(),active_plan=r['path'])
    (project/r['path']).unlink()
    assert any('Missing active plan' in e for e in helper.check(project)['errors'])


def test_exploration_log_records_only_queries_and_reads_and_counts_them(project):
    helper.initialize(project)
    assert helper.check(project)['exploration_log'] is None
    q=helper.add_exploration(project,'query','solid-state battery | cycle life 2025','web')
    r=helper.add_exploration(project,'read','doi:10.1000/x §3 Table 2','full')
    s=helper.add_exploration(project,'read','https://example.org/result','snippet')
    q2=helper.add_exploration(project,'query','same unknown, different wording','zotero')
    assert [q['id'],r['id'],s['id'],q2['id']]==['Q-0001','R-0001','R-0002','Q-0002']
    text=exploration_log(project).read_text(encoding='utf-8')
    assert '\\|' in text and '대화 내용은 기록하지 않습니다' in text
    report=helper.check(project)
    log={k:v for k,v in report['exploration_log'].items() if k!='checklist'}
    assert report['ok'] and log=={'queries':2,'reads':2,'reads_beyond_snippet':1,'summary':None}
    assert not any('unmanaged' in w for w in report['warnings'])

def test_exploration_log_rejects_bad_input_without_writing(project):
    helper.initialize(project)
    for kind,text,via in [('query','','web'),('query','x','Web Search'),('read','x','skimmed'),('note','x','web'),('query','x'*1001,'web')]:
        with pytest.raises(helper.Error):helper.add_exploration(project,kind,text,via)
    assert not exploration_log(project).exists()

def test_exploration_log_survives_human_edits_and_reports_damage(project):
    helper.initialize(project)
    helper.add_exploration(project,'query','first','web')
    path=exploration_log(project)
    path.write_text(path.read_text(encoding='utf-8').rstrip('\n'),encoding='utf-8')  # editor removed final newline
    helper.add_exploration(project,'query','second','web')
    lines=[l for l in path.read_text(encoding='utf-8').splitlines() if l.startswith('| Q-')]
    assert len(lines)==2 and helper.check(project)['ok']
    path.write_text(path.read_text(encoding='utf-8')+'| Q-0002 | duplicate\n| Q-0002 | t | query | web | dup |\n',encoding='utf-8')
    report=helper.check(project)
    assert any('malformed' in w for w in report['warnings']) and any('Duplicate exploration log ID' in e for e in report['errors'])

def test_exploration_log_is_project_scoped_and_cli_works(project,tmp_path):
    def call(root,*args):
        return subprocess.run([sys.executable,str(SCRIPT),'--project',str(root),*args],text=True,capture_output=True)
    other=tmp_path/'other';other.mkdir()
    helper.initialize(project);helper.initialize(other)
    done=call(project,'explore','--kind','query','--via','web','--text','한국어 질의 | 파이프');assert done.returncode==0,done.stderr
    assert json.loads(done.stdout)['id']=='Q-0001'
    assert json.loads(done.stdout)['path']==research_relative(project,'exploration/log.md')
    assert not exploration_log(other).exists() and 'Q-0001' not in json.dumps(helper.context(other))
    shared=exploration_log(other);shared.parent.mkdir(parents=True,exist_ok=True)
    shared.write_bytes(exploration_log(project).read_bytes())  # copied foreign log
    with pytest.raises(helper.Error):helper.add_exploration(other,'query','x','web')


SUMMARY_BODY='''## 탐색한 접근 계열
- 계열 A (Q-0001, R-0001)

## 기각·보류한 후보와 이유
- 후보 X 기각: 목표 조건 미충족 (R-0001)
- 후보 Y 보류: 느낌상 부적합

## 미탐색 프런티어
- 후보 Z의 변형 조건

## 검수 요청
- [근거없는 기각] 후보 Y
'''

def _summary_project(project):
    helper.initialize(project)
    helper.add_exploration(project,'query','unknown A','web')
    helper.add_exploration(project,'read','doi:10.1/x','full')

def test_summary_stats_are_computed_by_the_helper_and_unevidenced_rejections_are_flagged(project):
    _summary_project(project)
    made=helper.add_summary(project,SUMMARY_BODY)
    text=exploration_summary(project).read_text(encoding='utf-8')
    assert made['status']=='created' and made['rejected_without_evidence']==1 and made['warnings']
    assert made['path']==research_relative(project,'exploration/summary.md')
    assert '질의 1건 · 열람 1건 (snippet 초과 1건)' in text and '반영한 로그 위치: Q-0001 R-0001' in text
    report=helper.check(project)
    assert report['ok'] and report['exploration_log']['summary']=={'entries_since_summary':0}
    helper.add_exploration(project,'query','another','web')
    behind=helper.check(project)
    assert behind['exploration_log']['summary']=={'entries_since_summary':1} and any('behind the log' in w for w in behind['warnings'])

def test_summary_rejects_fabricated_ids_bad_structure_and_oversize_without_writing(project):
    _summary_project(project)
    bad=[SUMMARY_BODY.replace('R-0001','R-0099'),
         SUMMARY_BODY.replace('## 미탐색 프런티어\n- 후보 Z의 변형 조건\n\n',''),
         SUMMARY_BODY.replace('- 후보 Z의 변형 조건','   '),
         '서문\n'+SUMMARY_BODY,
         SUMMARY_BODY+'x'*helper.SUMMARY_LIMIT,
         SUMMARY_BODY+helper.STATS_BEGIN]
    for body in bad:
        with pytest.raises(helper.Error):helper.add_summary(project,body)
    assert not exploration_summary(project).exists()

def test_summary_update_requires_current_hash_keeps_identity_and_preimage(project):
    _summary_project(project)
    helper.add_summary(project,SUMMARY_BODY)
    path=exploration_summary(project);first=path.read_bytes()
    with pytest.raises(helper.Error):helper.add_summary(project,SUMMARY_BODY)              # hash omitted
    with pytest.raises(helper.Error):helper.add_summary(project,SUMMARY_BODY,'0'*64)        # stale hash
    updated=helper.add_summary(project,SUMMARY_BODY.replace('후보 Y 보류: 느낌상 부적합','후보 Y 보류: 조건 불명 (Q-0001)'),hashlib.sha256(first).hexdigest())
    assert updated['status']=='updated' and updated['rejected_without_evidence']==0
    assert helper.frontmatter(path.read_text(encoding='utf-8'))['ris_id']==helper.frontmatter(first.decode())['ris_id']
    assert (project/'.ris/history'/(hashlib.sha256(first).hexdigest()+'.md')).read_bytes()==first
    with pytest.raises(helper.Error):helper.add_summary(project,SUMMARY_BODY,hashlib.sha256(first).hexdigest())  # old hash after update

def test_summary_cli_and_missing_summary_warning(project):
    def call(*args,input=None):
        return subprocess.run([sys.executable,str(SCRIPT),'--project',str(project),*args],input=input,text=True,capture_output=True)
    assert call('init').returncode==0
    assert call('explore','--kind','query','--via','web','--text','q').returncode==0
    assert any('no summary yet' in w for w in json.loads(call('check').stdout)['warnings'])
    done=call('summarize',input=SUMMARY_BODY.replace('R-0001','Q-0001').replace('(Q-0001, Q-0001)','(Q-0001)'))
    assert done.returncode==0,done.stderr
    assert json.loads(done.stdout)['status']=='created'
    assert call('summarize',input=SUMMARY_BODY).returncode==2

def test_checklist_warns_on_thin_search_and_snippet_only_reading_but_never_fails_check(project):
    helper.initialize(project)
    helper.add_exploration(project,'query','unknown A','web')
    helper.add_exploration(project,'query','  Unknown   A ','web')
    helper.add_exploration(project,'read','paper snippet','snippet')
    before=helper.check(project)
    assert before['exploration_log']['checklist']['distinct_queries']==1
    assert not any('Checklist' in w for w in before['warnings'])  # no checkpoint claimed yet
    helper.add_summary(project,SUMMARY_BODY.replace('(R-0001)','(Q-0001)'))
    report=helper.check(project)
    checklist=report['exploration_log']['checklist']
    assert report['ok'] and checklist['queries_meet_minimum'] is False and checklist['sources_opened_beyond_snippet']==0
    assert any('Checklist (b)' in w for w in report['warnings']) and any('Checklist (j)' in w for w in report['warnings'])

def test_checklist_is_quiet_when_minimums_are_met_and_flags_hidden_unevidenced_rejections(project):
    helper.initialize(project)
    for q in ('unknown A','unknown A in adjacent field','how practitioners measure A'):helper.add_exploration(project,'query',q,'web')
    helper.add_exploration(project,'read','doi:10.1/x','full')
    hidden=SUMMARY_BODY.replace('- [근거없는 기각] 후보 Y','없음').replace('(Q-0001, R-0001)','(Q-0001, R-0001)')
    helper.add_summary(project,hidden)
    report=helper.check(project)
    checklist=report['exploration_log']['checklist']
    assert checklist['queries_meet_minimum'] and checklist['summary_structure']=='ok' and checklist['review_requests_declared'] is False
    assert not any('Checklist' in w for w in report['warnings'])
    assert any('검수 요청 is 없음' in w for w in report['warnings'])

def test_checklist_reports_a_summary_damaged_by_a_human_edit(project):
    _summary_project(project)
    helper.add_summary(project,SUMMARY_BODY)
    path=exploration_summary(project)
    path.write_text(path.read_text(encoding='utf-8').replace('## 미탐색 프런티어','## 프런티어'),encoding='utf-8')
    report=helper.check(project)
    assert report['exploration_log']['checklist']['summary_structure']=='invalid'
    assert any(w.startswith('Summary structure:') for w in report['warnings'])
