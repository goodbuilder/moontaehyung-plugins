import argparse
import importlib.util
from pathlib import Path
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
spec = importlib.util.spec_from_file_location('learning', SCRIPTS / 'ris_learning.py')
learning = importlib.util.module_from_spec(spec)
spec.loader.exec_module(learning)

class Host:
    class Error(Exception):
        pass


@pytest.fixture(autouse=True)
def host_root(tmp_path, monkeypatch):
    tmp_path.chmod(0o700)
    monkeypatch.setenv('RIS_LEARNING_PROFILE_ROOT', str(tmp_path))


def call(*args):
    parser = argparse.ArgumentParser()
    learning.add_parser(parser.add_subparsers(dest='command'))
    return learning.dispatch(Host, None, parser.parse_args(['learning', *map(str, args)]))


def test_explicit_consent_inspect_change_delete(tmp_path):
    path = tmp_path / 'learning-profile.json'
    with pytest.raises(SystemExit):
        call('create', '--profile', path)
    created = call('create', '--profile', path, '--consent', learning.CONSENT)
    assert path.stat().st_mode & 0o777 == 0o600
    changed = call('set', '--profile', path, '--expected-hash', created['profile_hash'],
                   '--concept', 'causality', '--dimension', 'definition', '--level', 'learning', '--evidence', 'inferred')
    assert call('inspect', '--profile', path) == changed
    with pytest.raises(Host.Error, match='changed'):
        call('delete', '--profile', path, '--expected-hash', created['profile_hash'])
    assert call('delete', '--profile', path, '--expected-hash', changed['profile_hash'])['consent_revoked']
    assert not path.exists()


def test_confirmation_is_not_inference(tmp_path):
    path = tmp_path / 'learning-profile.json'
    created = call('create', '--profile', path, '--consent', learning.CONSENT)
    common = ['set', '--profile', path, '--expected-hash', created['profile_hash'],
              '--concept', 'uncertainty', '--dimension', 'application', '--level', 'confirmed']
    with pytest.raises(Host.Error):
        call(*common, '--evidence', 'inferred')
    with pytest.raises(Host.Error):
        call(*common, '--evidence', 'demonstration-confirmed-by-user')
    saved = call(*common, '--evidence', 'demonstration-confirmed-by-user', '--user-confirmed')
    assert saved['profile']['concepts']['uncertainty']['application']['level'] == 'confirmed'


def test_reject_hidden_project_channels(tmp_path):
    valid = {'schema': 1, 'consent': learning.CONSENT, 'concepts': {}}
    for field in ('project_id', 'history', 'path', 'notes', 'source'):
        with pytest.raises(ValueError):
            learning.validate(dict(valid, **{field: 'secret'}))
    with pytest.raises(ValueError):
        learning.validate(dict(valid, concepts={'project-123': {'level': 'learning', 'evidence': 'none'}}))
    with pytest.raises(ValueError):
        learning.validate(dict(valid, concepts={'causality': {'level': 'learning', 'evidence': 'none', 'notes': 'secret'}}))
    target = tmp_path / 'target'
    target.write_text('{}')
    link = tmp_path / 'link'
    link.symlink_to(target)
    with pytest.raises(Host.Error):
        call('inspect', '--profile', link)


@pytest.mark.parametrize('mode', learning.MODES)
@pytest.mark.parametrize('view', ['researcher', 'designer', 'teach-me'])
def test_turn_local_contract_no_profile_access(mode, view, monkeypatch):
    def forbidden(*args):
        raise AssertionError('session opened filesystem')
    monkeypatch.setattr(learning, 'read_profile', forbidden)
    result = call('session', '--mode', mode, '--view', view, '--intent', 'project goal', '--contribution', 'my hypothesis')
    assert result['project_local']['contribution'] == 'my hypothesis'
    assert result['profile_access'] is False and result['persisted'] is False


def test_host_binding_and_coherence(tmp_path, monkeypatch):
    foreign = tmp_path / 'private.json'
    foreign.write_text('not JSON private content')
    with pytest.raises(Host.Error, match='host-provisioned'):
        call('inspect', '--profile', foreign)
    monkeypatch.delenv('RIS_LEARNING_PROFILE_ROOT')
    with pytest.raises(Host.Error, match='Trusted host'):
        call('inspect', '--profile', tmp_path / 'learning-profile.json')
    with pytest.raises(ValueError, match='Incoherent'):
        learning.validate({'schema': 1, 'consent': learning.CONSENT, 'concepts': {
            'causality': {'application': {'level': 'practiced', 'evidence': 'inferred', 'confirmed_at': None}}}})


def test_real_cli_session():
    import subprocess
    import sys
    result = subprocess.run([sys.executable, str(SCRIPTS / 'ris.py'), 'learning', 'session',
                             '--mode', 'assist', '--view', 'designer', '--intent', 'synthetic intent',
                             '--contribution', 'synthetic contribution'], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    import json
    output = json.loads(result.stdout)
    assert output['persisted'] is False and output['profile_access'] is False


def test_no_project_history_reader_and_no_overwrite(tmp_path):
    class ProjectHost:
        Error = Host.Error
        def config(self, *args):
            raise AssertionError('project history/config must not be accessed')
    parser = argparse.ArgumentParser()
    learning.add_parser(parser.add_subparsers(dest='command'))
    args = parser.parse_args(['learning', 'create', '--profile', str(tmp_path / 'learning-profile.json'),
                              '--consent', learning.CONSENT])
    learning.dispatch(ProjectHost(), None, args)
    original = args.profile.read_bytes()
    with pytest.raises(Host.Error):
        learning.dispatch(ProjectHost(), None, args)
    assert args.profile.read_bytes() == original


def test_real_cli_disposable_profile_lifecycle(tmp_path):
    import subprocess
    import sys
    import json
    path = tmp_path / 'learning-profile.json'
    def cli(*args):
        result = subprocess.run([sys.executable, str(SCRIPTS / 'ris.py'), 'learning', *map(str, args)],
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)
    created = cli('create', '--profile', path, '--consent', learning.CONSENT)
    updated = cli('set', '--profile', path, '--expected-hash', created['profile_hash'],
                  '--concept', 'tradeoffs', '--dimension', 'limits', '--level', 'confirmed',
                  '--evidence', 'demonstration-confirmed-by-user', '--user-confirmed')
    assert updated['profile']['concepts']['tradeoffs']['limits']['confirmed_at'].endswith('Z')
    assert cli('inspect', '--profile', path) == updated
    assert cli('delete', '--profile', path, '--expected-hash', updated['profile_hash'])['deleted']
    assert not path.exists()


def test_adaptive_optional_lesson_has_worked_application_and_no_profile_access(monkeypatch):
    import json
    monkeypatch.setattr(learning, 'read_profile', lambda *_: pytest.fail('profile read'))
    view={'schema':1,'consent':learning.CONSENT,'concepts':{'uncertainty': {
        'definition':{'level':'practiced','evidence':'self-report','confirmed_at':None},
        'explanation':{'level':'practiced','evidence':'self-report','confirmed_at':None},
        'calculation':{'level':'learning','evidence':'inferred','confirmed_at':None},
        'application':{'level':'practiced','evidence':'self-report','confirmed_at':None},
        'limits':{'level':'practiced','evidence':'self-report','confirmed_at':None}}}}
    args=['lesson','--concept','uncertainty','--dimension-view',json.dumps(view)]
    assert not call(*args,'--mode','delegated','--requested')['teaching']
    assert not call(*args,'--mode','assist')['teaching']
    taught=call(*args,'--mode','assist','--requested')
    assert taught['focus_dimension']=='calculation'
    assert '10-2=8' in taught['worked_application']['calculation']
    assert taught['worked_application']['synthetic']
    assert taught['profile_updated'] is False and 'NOT_ASSESSED' in taught['ability_assessment']
    with pytest.raises(Host.Error):
        call(*['lesson','--concept','uncertainty','--dimension-view',json.dumps(dict(view,project_history='forbidden'))], '--mode','assist','--requested')


def test_real_cli_project_contributions_canonical_cas_and_goal_approval(tmp_path,monkeypatch):
    import subprocess,sys,json,hashlib
    project=tmp_path/'project';project.mkdir()
    monkeypatch.delenv('RIS_LEARNING_PROFILE_ROOT')
    def cli(*args,ok=True):
        result=subprocess.run([sys.executable,str(SCRIPTS/'ris.py'),'--project',str(project),*map(str,args)],capture_output=True,text=True)
        if ok:
            assert result.returncode==0,result.stderr
            return json.loads(result.stdout)
        assert result.returncode!=0,result.stdout
        return result.stderr
    cli('init','--recording-policy','manual')
    context=project/'.ris/research/CONTEXT.md'
    before=context.read_bytes();digest=hashlib.sha256(before).hexdigest()
    pid=json.loads(next(line.split(':',1)[1] for line in (project/'.ris/project.yaml').read_text().splitlines() if line.startswith('project_id:')))
    payload={'project_id':pid,'attributed_to':'synthetic researcher','contributor':'user','intent':'Compare synthetic options',
             'purpose':{'status':'USER_STATED','text':'Understand measurement limits'},
             'constraints':['No real experiment'],'hypotheses':['Timing is irregular'],
             'observations':['Synthetic rows lack timestamps'],
             'decision':{'kind':'USER_DEFERS','reason':'Need evidence'},'goal_change':None}
    selected=project/'input.json';selected.write_text(json.dumps(payload))
    base=['learning','contribute','--input','input.json','--expected-hash',digest]
    assert 'policy' in cli(*base,ok=False)
    result=cli(*base,'--authorize-record')
    assert result['profile_access'] is False and result['project_local']
    assert result['path']=='.ris/research/CONTEXT.md'
    text=context.read_text();assert 'Synthetic rows lack timestamps' in text
    assert 'ATTRIBUTED_NOT_INDEPENDENTLY_VERIFIED' in text
    assert 'Context changed' in cli(*base,'--authorize-record',ok=False)
    assert any(p.read_bytes()==before for p in (project/'.ris/history').glob('*.md'))
    digest=hashlib.sha256(context.read_bytes()).hexdigest()
    payload['purpose']={'status':'INFERRED','text':'Maybe optimize speed'}
    payload['goal_change']='Evaluate synthetic sampling uncertainty.'
    payload['decision']={'kind':'USER_ACCEPTS','reason':'Explicit synthetic user decision'}
    selected.write_text(json.dumps(payload))
    base=['learning','contribute','--input','input.json','--expected-hash',digest,'--authorize-record']
    assert 'explicit user approval' in cli(*base,ok=False)
    unchanged=context.read_bytes()
    payload['contributor']='agent';selected.write_text(json.dumps(payload))
    assert 'user decision' in cli(*base,'--user-approved-goal-change',ok=False)
    assert context.read_bytes()==unchanged
    payload['contributor']='user';selected.write_text(json.dumps(payload))
    result=cli(*base,'--user-approved-goal-change')
    assert result['contribution_stamp']['goal_changed_by_explicit_user_decision']
    assert '## 지금 해결할 질문\nEvaluate synthetic sampling uncertainty.' in context.read_text()
    # User hypothesis/observation is still attributed, never promoted to global ability.
    assert not list(project.rglob('learning-profile.json'))
    assert result['path'].endswith('CONTEXT.md')


def test_erase_selected_dimension_or_concept_preserves_others(tmp_path):
    path=tmp_path/'learning-profile.json'
    state=call('create','--profile',path,'--consent',learning.CONSENT)
    for concept,dimension in [('uncertainty','definition'),('uncertainty','limits'),('causality','application')]:
        state=call('set','--profile',path,'--expected-hash',state['profile_hash'],'--concept',concept,'--dimension',dimension,'--level','learning','--evidence','inferred')
    state=call('erase','--profile',path,'--expected-hash',state['profile_hash'],'--concept','uncertainty','--dimension','definition')
    assert set(state['profile']['concepts']['uncertainty'])=={'limits'}
    assert 'causality' in state['profile']['concepts']
    state=call('erase','--profile',path,'--expected-hash',state['profile_hash'],'--concept','uncertainty')
    assert set(state['profile']['concepts'])=={'causality'}


def test_registered_cli_differentiates_dimensions_and_skips_confirmed_basics():
    import json,subprocess,sys
    confirmed={'level':'confirmed','evidence':'demonstration-confirmed-by-user','confirmed_at':'2026-01-01T00:00:00Z'}
    outputs={}
    for focus in (*learning.DIMENSIONS,'transfer'):
        dimensions={d:dict(confirmed) for d in learning.DIMENSIONS}
        if focus!='transfer': dimensions[focus]={'level':'unknown','evidence':'none','confirmed_at':None}
        view={'schema':1,'consent':learning.CONSENT,'concepts':{'uncertainty':dimensions}}
        result=subprocess.run([sys.executable,str(SCRIPTS/'ris.py'),'learning','lesson','--mode','assist','--requested','--concept','uncertainty','--dimension-view',json.dumps(view)],capture_output=True,text=True)
        assert result.returncode==0,result.stderr
        outputs[focus]=json.loads(result.stdout)
        assert outputs[focus]['focus_dimension']==focus
    assert 'prerequisite' in outputs['definition']['worked_application']
    assert 'calculation' in outputs['calculation']['worked_application']
    assert 'worked_decision' in outputs['application']['worked_application']
    assert 'counterexample' in outputs['limits']['worked_application']
    assert len({json.dumps(x.get('practice')) for x in outputs.values()})==6
    assert outputs['transfer']['basics_skipped'] and 'worked_application' not in outputs['transfer']
    assert 'transfer_task' in outputs['transfer']


def test_contribution_identity_and_policy_reduction_fail_closed(tmp_path):
    import json,hashlib
    from types import SimpleNamespace
    spec=importlib.util.spec_from_file_location('learning_policy_ris',SCRIPTS/'ris.py')
    ris=importlib.util.module_from_spec(spec);spec.loader.exec_module(ris)
    project=tmp_path/'project';project.mkdir();ris.initialize(project,recording_policy='significant')
    cfg=ris.config(project)
    context=project/'.ris/research/CONTEXT.md';before=context.read_bytes()
    payload={'project_id':'other-project','attributed_to':'fixture','contributor':'user','intent':'synthetic',
             'purpose':{'status':'USER_STATED','text':'synthetic'},'constraints':[],'hypotheses':[],'observations':[],
             'decision':{'kind':'NO_DECISION','reason':'fixture'},'goal_change':None}
    source=project/'input.json';source.write_text(json.dumps(payload))
    args=argparse.Namespace(input='input.json',expected_hash=hashlib.sha256(before).hexdigest(),authorize_record=False,user_approved_goal_change=False)
    with pytest.raises(ris.Error,match='exact project'):
        learning.contribution(ris,project,args)
    payload['project_id']=cfg['project_id'];source.write_text(json.dumps(payload))
    calls=[]
    def changing_config(root):
        calls.append(True)
        return dict(cfg,recording_policy='significant' if len(calls)==1 else 'manual')
    proxy=SimpleNamespace(**vars(ris));proxy.config=changing_config
    with pytest.raises(ris.Error,match='recording policy changed'):
        learning.contribution(proxy,project,args)
    assert context.read_bytes()==before
