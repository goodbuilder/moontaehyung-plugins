import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import pytest

SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
def load(name):
    spec=importlib.util.spec_from_file_location(name,SCRIPTS/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
ris=load('ris');views=load('ris_views')

def args(kind,*extra):
    p=argparse.ArgumentParser();views.add_parser(p.add_subparsers(dest='command'))
    return p.parse_args(['view',kind,*extra])

@pytest.fixture
def project(tmp_path):
    ris.initialize(tmp_path,recording_policy='manual')
    return tmp_path

def files(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}

def add_note(root,kind,name,body):
    cfg=ris.config(root);relative=ris.research_path(cfg,'research/'+name)
    path=root/relative;path.parent.mkdir(exist_ok=True,parents=True)
    ris.write_new(path,ris.note(cfg['project_id'],kind,'Synthetic',body))
    return relative

@pytest.mark.parametrize('kind',views.VIEWS)
def test_empty_or_minimal_read_only_views(project,kind,monkeypatch):
    monkeypatch.delenv('RIS_LEARNING_PROFILE_ROOT',raising=False)
    before=files(project)
    result=views.dispatch(ris,project,args(kind))
    assert result['read_only'] and result['profile_access'] is False
    assert len(json.dumps(result,ensure_ascii=False))<=16000
    assert files(project)==before
    assert result['receipt']


def test_related_plan_preserves_identity_link_and_pins(project):
    relative=add_note(project,'plan','plans/p1.md','[Existing map](../maps/stable-map.html#stable-node)\n')
    before=files(project)
    result=views.dispatch(ris,project,args('plan','--include',relative))
    record=result['records'][0]
    assert record['links']==[{'href':'../maps/stable-map.html#stable-node','opened':False}]
    assert record['ris_id']==ris.frontmatter((project/relative).read_text())['ris_id']
    assert files(project)==before
    assert views.dispatch(ris,project,args('plan','--include',relative,'--expected-receipt',result['receipt']))['receipt']==result['receipt']
    (project/relative).write_text((project/relative).read_text()+'\nNew actual revision\n')
    with pytest.raises(ris.Error,match='receipt changed'):
        views.dispatch(ris,project,args('plan','--include',relative,'--expected-receipt',result['receipt']))


def test_unrelated_missing_and_bounded(project):
    relative=add_note(project,'concept','concepts/unrelated.md','No plan here')
    result=views.dispatch(ris,project,args('plan','--include',relative,'--include','.ris/research/missing.md'))
    assert not result['records'] and result['omitted_total']==2
    result=views.dispatch(ris,project,args('plan',*sum((['--include','.ris/research/'+str(i)*100+'.md'] for i in range(20)),[]),'--max-chars','2000'))
    assert len(json.dumps(result,ensure_ascii=False))<=2000 and result['omitted_truncated']


def test_transient_note_omitted(project):
    relative=add_note(project,'plan','plans/p1.md','stable')
    real=ris.companion('ris_delivery');calls=[]
    def read(api,root,selected,**kwargs):
        calls.append(selected)
        if len(calls)==2:(root/selected).write_text((root/selected).read_text()+'\nchanged\n')
        return real.read_file(api,root,selected,**kwargs)
    proxy=SimpleNamespace(**vars(ris))
    proxy.companion=lambda name: SimpleNamespace(read_file=read) if name=='ris_delivery' else ris.companion(name)
    result=views.dispatch(proxy,project,args('plan','--include',relative))
    assert not result['records'] and result['omitted'][-1]['reason']=='changed_during_projection'


def test_dirty_governed_record_omitted(project):
    cfg=ris.config(project);owner=ris.companion('ris_findings')
    payload=project/'payload.json';payload.write_text(json.dumps({'project_id':cfg['project_id'],'obligation':{'id':'q','specified_by':'reviewer','question':'Synthetic question','expected_scope':{'topic':'synthetic'}}}))
    command=[sys.executable,str(SCRIPTS/'ris.py'),'--project',str(project),'findings','obligate','--input','payload.json','--expected-revision','0','--idempotency-key','initial','--authorize-record']
    proc=subprocess.run(command,capture_output=True,text=True);assert proc.returncode==0,proc.stderr
    relative=owner.location(ris,cfg);path=project/relative
    clean=views.dispatch(ris,project,args('knowledge'));assert clean['records'][0]['revision']==1
    path.write_text(path.read_text()+'\nUnreviewed direct edit\n')
    before=files(project)
    dirty=views.dispatch(ris,project,args('knowledge'))
    assert not dirty['records'] and dirty['omitted']
    assert files(project)==before


def test_registered_cli_no_project_changes(project):
    before=files(project)
    result=subprocess.run([sys.executable,str(SCRIPTS/'ris.py'),'--project',str(project),'view','research'],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)['read_only']
    assert files(project)==before


def test_foreign_external_legacy_and_partial_read_rejected_without_content(project,tmp_path):
    cfg=ris.config(project)
    relative=ris.research_path(cfg,'research/plans/foreign.md')
    path=project/relative
    path.write_text('---\nris_id: "foreign-secret-id"\nproject_id: "foreign-project"\nkind: "plan"\n---\n# Foreign secret title\nForeign secret prose\n')
    result=views.dispatch(ris,project,args('plan','--include',relative))
    encoded=json.dumps(result)
    assert not result['records']
    for forbidden in ('foreign-secret-id','foreign-project','Foreign secret title','Foreign secret prose'):
        assert forbidden not in encoded
    path.write_text('---\nris_id: "legacy-secret-id"\nproject_id: '+json.dumps(cfg['project_id'])+'\nsource_project_id: "foreign"\nknowledge_record: true\nkind: "finding"\n---\n# Legacy secret title\nLegacy secret prose\n')
    result=views.dispatch(ris,project,args('knowledge','--include',relative))
    assert all(x['path']!=relative for x in result['records'])
    assert 'legacy-secret-id' not in json.dumps(result) and 'Legacy secret' not in json.dumps(result)
    path.write_text('---\nproject_id: '+json.dumps(cfg['project_id'])+'\n')
    result=views.dispatch(ris,project,args('plan','--include',relative))
    assert not result['records']
    result=views.dispatch(ris,project,args('plan','--include','/etc/hostname'))
    assert not result['records']


def test_receipt_binds_selected_unavailable_inputs(project):
    one=views.dispatch(ris,project,args('plan','--include','.ris/research/plans/one.md'))
    two=views.dispatch(ris,project,args('plan','--include','.ris/research/plans/two.md'))
    assert one['receipt']!=two['receipt']


def test_foreign_strategy_section_is_not_navigation_input(project):
    lesson={'id':'foreign-hidden-strategy','project_id':'foreign-project','conditions':{'a':'b'},
            'origin_note':'.ris/research/plans/p1.md','input_revision':'foreign-revision',
            'work_evidence':[{'path':'foreign-secret.csv','sha256':'x','action':'foreign-action','outcome':'foreign-outcome'}]}
    relative=add_note(project,'plan','plans/p1.md','<!-- ris:strategy -->\n```json\n'+json.dumps(lesson)+'\n```\n<!-- /ris:strategy -->')
    result=views.dispatch(ris,project,args('strategy','--include',relative))
    assert not result['records']
    assert 'foreign-hidden-strategy' not in json.dumps(result) and 'foreign-secret' not in json.dumps(result)
