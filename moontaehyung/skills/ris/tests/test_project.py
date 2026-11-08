import hashlib
import importlib.util
import json
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

def test_preview_is_read_only(project):
    preview=helper.initialize(project,'한글 연구','Goal',attach=True,dry_run=True)
    assert preview['status']=='preview' and list(project.iterdir())==[]

def test_init_is_idempotent_and_preserves_human_edits(project):
    first=helper.initialize(project,'연구: "A"','목표')
    before=(project/'.ris/project.yaml').read_bytes()
    context=project/'research/CONTEXT.md';context.write_text(context.read_text()+'\n내가 쓴 내용\n')
    result=helper.initialize(project,'Ignored name')
    assert result['status']=='already_initialized'
    assert before==(project/'.ris/project.yaml').read_bytes()
    assert '내가 쓴 내용' in context.read_text()
    assert first['project_id']==helper.config(project)['project_id']
    assert helper.check(project)['ok']

def test_existing_entry_file_requires_adoption_without_partial_writes(project):
    (project/'research').mkdir();index=project/'research/INDEX.md';index.write_text('Existing research')
    with pytest.raises(helper.Error):helper.initialize(project,attach=True)
    assert index.read_text()=='Existing research'
    assert not (project/'.ris').exists() and not (project/'AGENTS.md').exists()

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
    p=project/'research/CONTEXT.md';before=p.read_bytes();base=hashlib.sha256(before).hexdigest()
    result=helper.propose(project,'research/CONTEXT.md',base,'Replacement proposal')
    assert p.read_bytes()==before
    assert json.loads((project/result['proposal']).read_text())['proposed_body']=='Replacement proposal'
    p.write_text(p.read_text()+'\nExternal edit')
    with pytest.raises(helper.Error):helper.propose(project,'research/CONTEXT.md',base,'Stale overwrite')
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
    (project/'research').symlink_to(outside,target_is_directory=True)
    with pytest.raises(helper.Error):helper.initialize(project)
    assert list(outside.iterdir())==[]
    with pytest.raises(helper.Error):helper.inside(project,'../escape.md')

def test_unknown_version_refused_without_modification(project):
    helper.initialize(project)
    p=project/'.ris/project.yaml';p.write_text(p.read_text().replace('schema_version: 1','schema_version: 999'))
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
    fresh=call('context','--include',filename)
    assert fresh.returncode==0,fresh.stderr
    assert 'assumption C' in json.loads(fresh.stdout)['records'][-1]['text']
    assert call('check').returncode==0
    assert not (project/'ris.sqlite').exists()

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
    target=project/'research/concepts/copied.md';target.write_bytes((other/r['path']).read_bytes())
    with pytest.raises(helper.Error):helper.context(project,['research/concepts/copied.md'])


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


def test_authorized_update_preserves_identity_and_exact_preimage(project):
    helper.initialize(project)
    path=project/'research/CONTEXT.md';original=path.read_bytes();base=hashlib.sha256(original).hexdigest()
    text=original.decode()+'\nConfirmed choice D-001: rgb; next compare evidence.\n'
    result=helper.safe_update(project,'research/CONTEXT.md',base,text)
    assert (project/result['backup']).read_bytes()==original
    assert path.read_text()==text
    with pytest.raises(helper.Error):helper.safe_update(project,'research/CONTEXT.md',base,'stale')
    current=hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(helper.Error):helper.safe_update(project,'research/CONTEXT.md',current,text.replace(helper.config(project)['project_id'],'foreign'))
    assert path.read_text()==text


def test_missing_active_plan_is_visible(project):
    helper.initialize(project)
    r=helper.add_record(project,'plan','Plan','Pending probe')
    p=project/'.ris/project.yaml'
    helper.configure(project,hashlib.sha256(p.read_bytes()).hexdigest(),active_plan=r['path'])
    (project/r['path']).unlink()
    assert any('Missing active plan' in e for e in helper.check(project)['errors'])
