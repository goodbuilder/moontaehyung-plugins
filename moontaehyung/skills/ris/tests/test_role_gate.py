import importlib.util
import json
from pathlib import Path
import pytest

SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
def load(name):
    spec=importlib.util.spec_from_file_location(name,SCRIPTS/f'{name}.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
import sys
ris=load('ris');sys.modules['ris']=ris;rg=load('role_gate')

@pytest.fixture
def project(tmp_path):
    p=tmp_path/'p';p.mkdir();ris.initialize(p,'t','g')
    cfg=p/'.ris/project.yaml';cfg.write_text(cfg.read_text()+'role_gate_profile: "research-map"\n')
    (p/'research/canon.md').write_text('canon v1');(p/'research/map.html').write_text('<html>v1</html>')
    return p

def sha(p,r): return ris.sha((p/r).read_bytes())
ROLES={'RG-RESEARCH':'researcher','RG-PLAN':'planner','RG-DESIGN':'designer','RG-VERIFY':'engineer','RG-AUDIT':'auditor'}
def call(p,task,agent='a1'):
    rid=ris.read_state(p)['run_id'];a=rg.assign(p,rid,task)
    assert rg.record_call(p,json.dumps({'prompt':a['line']}),'moontaehyung:'+ROLES[task],agent);return a
def art(p,task):
    c,h=sha(p,'research/canon.md'),sha(p,'research/map.html')
    return {'RG-RESEARCH':{'sources':['s'],'contrary':'none found'},
     'RG-PLAN':{'canon_ref':'research/canon.md','canon_sha':c,'branch_ids':['B1'],'project_plan_check':'PASS'},
     'RG-DESIGN':{'html_ref':'research/map.html','html_sha':h,'canon_sha':c},
     'RG-VERIFY':{'html_sha':h,'firefox':'PASS'},
     'RG-AUDIT':{'html_sha':h,'canon_sha':c,'scope':'all','verdict':'PASS'}}[task]
def ret(p,a,**kw):
    d={'run_id':a['run_id'],'task_id':a['task_id'],'token':a['token'],'input_hash':a['input_hash'],'status':'PASS','evidence':'e','artifacts':art(p,a['task_id'])}
    d.update(kw);return rg.submit_result(p,d,'a1')
def full(p):
    rg.start(p)
    for t in ['RG-RESEARCH','RG-PLAN','RG-DESIGN','RG-VERIFY','RG-AUDIT']: ret(p,call(p,t))
def complete(p):
    s=ris.read_state_snapshot(p);v=s['state'];v['status']='COMPLETE'
    f=p/'v.json';f.write_text(json.dumps(v));return ris.update_state(p,s['sha256'],f.read_text())

def test_no_call_refuses_complete(project):
    rg.start(project)
    with pytest.raises(ris.Error,match='role gate'):complete(project)

def test_call_without_result_is_incomplete(project):
    rg.start(project);call(project,'RG-RESEARCH')
    v=rg.verdict(project,ris.read_state(project)['run_id'])
    assert not v['complete'] and v['missing'][0]['why']=='no result returned'

def test_result_without_observed_call_rejected(project):
    rg.start(project);rid=ris.read_state(project)['run_id'];a=rg.assign(project,rid,'RG-RESEARCH')
    with pytest.raises(ris.Error,match='No observed'):ret(project,a)

def test_wrong_task_token_and_replay_rejected(project):
    rg.start(project);a=call(project,'RG-RESEARCH')
    with pytest.raises(ris.Error):ret(project,dict(a,token='x'))
    with pytest.raises(ris.Error,match='Input hash'):ret(project,dict(a,input_hash='x'))
    ret(project,a)
    with pytest.raises(ris.Error,match='consumed'):ret(project,a)

def test_stale_run_result_rejected(project):
    rg.start(project);a=call(project,'RG-RESEARCH')
    with pytest.raises(ris.Error):rg.submit_result(project,{'run_id':'OLD','task_id':a['task_id'],'token':a['token'],'input_hash':a['input_hash']})

def test_dependency_order_enforced(project):
    rg.start(project)
    with pytest.raises(ris.Error,match='Dependency'):rg.assign(project,ris.read_state(project)['run_id'],'RG-PLAN')

def test_full_handoff_completes(project):
    full(project);assert complete(project)['status']=='updated'

def test_html_change_invalidates(project):
    full(project);(project/'research/map.html').write_text('<html>v2</html>')
    with pytest.raises(ris.Error,match='HTML changed'):complete(project)

def test_blocking_audit_finding_fails(project):
    rg.start(project)
    for t in ['RG-RESEARCH','RG-PLAN','RG-DESIGN','RG-VERIFY']:ret(project,call(project,t))
    assert ret(project,call(project,'RG-AUDIT'),blocking=['x'])['status']=='FAIL'

def hook(p,**kw): return rg.handle_hook(p,dict(session_id='s',**kw),'test')

def test_hook_registers_and_stop_blocks_then_gives_up(project):
    assert hook(project,hook_event_name='UserPromptSubmit',prompt='RIS 로 조사해')
    assert hook(project,hook_event_name='Stop')['decision']=='block'
    hook(project,hook_event_name='Stop');hook(project,hook_event_name='Stop')
    assert hook(project,hook_event_name='Stop') is None   # no progress -> stop auto-continue
    with pytest.raises(ris.Error):complete(project)       # but still incomplete

def test_hook_pipeline_via_tool_events(project):
    hook(project,hook_event_name='UserPromptSubmit',prompt='RIS')
    rid=ris.read_state(project)['run_id'];a=rg.assign(project,rid,'RG-RESEARCH')
    hook(project,hook_event_name='PreToolUse',tool_name='Agent',tool_input={'prompt':a['line'],'subagent_type':'moontaehyung:researcher'})
    res=dict(run_id=rid,task_id='RG-RESEARCH',token=a['token'],input_hash=a['input_hash'],status='PASS',evidence='e',artifacts=art(project,'RG-RESEARCH'))
    hook(project,hook_event_name='PostToolUse',tool_name='Agent',tool_input={'prompt':a['line'],'subagent_type':'moontaehyung:researcher'},tool_response={'content':[{'text':'done RIS_RESULT '+json.dumps(res)}]})
    assert rg.load(project,rid)['tasks']['RG-RESEARCH']['status']=='PASS'

def test_ris_simple_and_unconfigured_projects_untouched(project,tmp_path):
    hook(project,hook_event_name='UserPromptSubmit',prompt='RIS-SIMPLE\nquick')
    assert not (project/'.ris/state.json').exists()
    assert hook(project,hook_event_name='Stop') is None
    other=tmp_path/'o';other.mkdir();ris.initialize(other)
    assert rg.handle_hook(other,{'hook_event_name':'UserPromptSubmit','prompt':'RIS'},'t') is None
    ris.initialize_state(other);v=ris.read_state(other);v['status']='COMPLETE'
    s=ris.read_state_snapshot(other);(other/'v.json').write_text(json.dumps(v))
    assert ris.update_state(other,s['sha256'],(other/'v.json').read_text())

def test_placeholder_pass_does_not_consume_token_and_real_result_still_lands(project):
    rg.start(project);a=call(project,'RG-RESEARCH');rid=a['run_id']
    tpl=dict(run_id=rid,task_id='RG-RESEARCH',token=a['token'],input_hash=a['input_hash'],status='PASS',evidence='<string>',artifacts={'sources':['<x>'],'contrary':'c'})
    real=dict(tpl,evidence='real',artifacts=art(project,'RG-RESEARCH'))
    with pytest.raises(ris.Error,match='Malformed'):rg.submit_result(project,tpl)
    rg.ingest(project,'RIS_RESULT '+json.dumps(tpl)+'\nfinal:\nRIS_RESULT '+json.dumps(real),'a1')
    assert rg.load(project,rid)['tasks']['RG-RESEARCH']['status']=='PASS'

def test_placeholder_hash_in_verify_is_rejected_and_real_fail_is_recorded(project):
    rg.start(project)
    for t in ['RG-RESEARCH','RG-PLAN','RG-DESIGN']:ret(project,call(project,t))
    a=call(project,'RG-VERIFY')
    bad=dict(run_id=a['run_id'],task_id='RG-VERIFY',token=a['token'],input_hash=a['input_hash'],status='PASS',evidence='x',artifacts={'html_sha':'<real sha256>','firefox':'PASS'})
    fail=dict(bad,status='FAIL',evidence='firefox failed',artifacts={})
    rg.ingest(project,'RIS_RESULT '+json.dumps(bad)+' RIS_RESULT '+json.dumps(fail),'a1')
    assert rg.load(project,a['run_id'])['tasks']['RG-VERIFY']['status']=='FAIL'

def test_lowercase_slash_ris_starts_gate(project):
    for i,prompt in enumerate(['/ris continue','$ris continue','RIS 로 조사해','/moontaehyung:ris continue']):
        p2=project.parent/f'q{i}';p2.mkdir();ris.initialize(p2);c=p2/'.ris/project.yaml';c.write_text(c.read_text()+'role_gate_profile: "research-map"\n')
        assert rg.handle_hook(p2,{'hook_event_name':'UserPromptSubmit','prompt':prompt,'session_id':'s'},'t'),prompt
        assert rg.active_run_id(p2)
        assert len(ris.read_state(p2)['tasks'])==5   # required tasks are registered in state.json

def test_ordinary_prompt_without_ris_does_not_start(project):
    assert hook(project,hook_event_name='UserPromptSubmit',prompt='hello there') is None
    assert hook(project,hook_event_name='UserPromptSubmit',prompt='What is RIS?') is None
    assert not (project/'.ris/state.json').exists()

def test_general_purpose_agent_cannot_be_the_researcher(project):
    rg.start(project);rid=ris.read_state(project)['run_id'];a=rg.assign(project,rid,'RG-RESEARCH')
    hook(project,hook_event_name='PreToolUse',tool_name='Agent',tool_input={'prompt':a['line'],'subagent_type':'general-purpose'})
    assert not rg.load(project,rid)['tasks']['RG-RESEARCH']['call']       # call not accepted
    hook(project,hook_event_name='PreToolUse',tool_name='Agent',tool_input={'prompt':a['line']})
    assert not rg.load(project,rid)['tasks']['RG-RESEARCH']['call']       # unknown type not accepted either

def test_subagent_stop_of_wrong_type_or_other_id_is_rejected(project):
    rg.start(project);a=call(project,'RG-RESEARCH','agent-A')
    res=dict(run_id=a['run_id'],task_id='RG-RESEARCH',token=a['token'],input_hash=a['input_hash'],status='PASS',evidence='e',artifacts=art(project,'RG-RESEARCH'))
    msg='RIS_RESULT '+json.dumps(res)
    hook(project,hook_event_name='SubagentStop',last_assistant_message=msg,agent_id='agent-A',agent_type='general-purpose')
    hook(project,hook_event_name='SubagentStop',last_assistant_message=msg,agent_id='agent-B',agent_type='moontaehyung:researcher')
    assert rg.load(project,a['run_id'])['tasks']['RG-RESEARCH']['status']=='ASSIGNED'   # neither consumed the token
    hook(project,hook_event_name='SubagentStop',last_assistant_message=msg,agent_id='agent-A',agent_type='moontaehyung:researcher')
    t=rg.load(project,a['run_id'])['tasks']['RG-RESEARCH'];assert t['status']=='PASS' and t['returned']['agent_id']=='agent-A'

def test_complete_refused_without_any_gate_record(project):
    ris.initialize_state(project)   # pilot on, hooks never ran
    with pytest.raises(ris.Error,match='role gate'):complete(project)

def test_pre_tool_only_then_unrelated_agent_id_cannot_pass(project):
    rg.start(project);rid=ris.read_state(project)['run_id'];a=rg.assign(project,rid,'RG-RESEARCH')
    hook(project,hook_event_name='PreToolUse',tool_name='Agent',tool_input={'prompt':a['line'],'subagent_type':'moontaehyung:researcher'})
    res=dict(run_id=rid,task_id='RG-RESEARCH',token=a['token'],input_hash=a['input_hash'],status='PASS',evidence='e',artifacts=art(project,'RG-RESEARCH'))
    hook(project,hook_event_name='SubagentStop',last_assistant_message='RIS_RESULT '+json.dumps(res),agent_id='unrelated',agent_type='moontaehyung:researcher')
    assert rg.load(project,rid)['tasks']['RG-RESEARCH']['status']=='ASSIGNED'
    with pytest.raises(ris.Error):rg.submit_result(project,res,'unrelated','moontaehyung:researcher')
    with pytest.raises(ris.Error):rg.submit_result(project,res)           # CLI path without an id

def test_result_before_post_tool_use_is_replayed_for_the_bound_agent_only(project):
    rg.start(project);rid=ris.read_state(project)['run_id'];a=rg.assign(project,rid,'RG-RESEARCH')
    ti={'prompt':a['line'],'subagent_type':'moontaehyung:researcher'}
    res=dict(run_id=rid,task_id='RG-RESEARCH',token=a['token'],input_hash=a['input_hash'],status='PASS',evidence='e',artifacts=art(project,'RG-RESEARCH'))
    hook(project,hook_event_name='PreToolUse',tool_name='Agent',tool_input=ti)
    hook(project,hook_event_name='SubagentStart',agent_id='real',agent_type='moontaehyung:researcher')
    hook(project,hook_event_name='SubagentStop',last_assistant_message='RIS_RESULT '+json.dumps(res),agent_id='real',agent_type='moontaehyung:researcher')
    assert rg.load(project,rid)['tasks']['RG-RESEARCH']['status']=='ASSIGNED'   # stashed until the id is bound
    hook(project,hook_event_name='PostToolUse',tool_name='Agent',tool_input=ti,tool_response={'agentId':'real','content':[{'text':'done'}]})
    t=rg.load(project,rid)['tasks']['RG-RESEARCH'];assert t['status']=='PASS' and t['returned']['agent_id']=='real'

def test_wrong_started_type_cannot_be_bound(project):
    rg.start(project);rid=ris.read_state(project)['run_id'];a=rg.assign(project,rid,'RG-RESEARCH')
    ti={'prompt':a['line'],'subagent_type':'moontaehyung:researcher'}
    hook(project,hook_event_name='PreToolUse',tool_name='Agent',tool_input=ti)
    hook(project,hook_event_name='SubagentStart',agent_id='gp',agent_type='general-purpose')
    hook(project,hook_event_name='PostToolUse',tool_name='Agent',tool_input=ti,tool_response={'agentId':'gp'})
    assert rg.load(project,rid)['tasks']['RG-RESEARCH']['call']['agent_id']==''

def test_second_session_does_not_adopt_the_run(project):
    hook(project,hook_event_name='UserPromptSubmit',prompt='RIS go')
    rid=rg.active_run_id(project)
    out=rg.handle_hook(project,{'hook_event_name':'UserPromptSubmit','prompt':'RIS again','session_id':'other'},'t')
    assert 'another session' in json.dumps(out)
    assert rg.handle_hook(project,{'hook_event_name':'Stop','session_id':'other'},'t') is None
    rg.release(project)
    assert 'role gate active' in json.dumps(rg.handle_hook(project,{'hook_event_name':'UserPromptSubmit','prompt':'RIS again','session_id':'other'},'t'))
    assert rg.load(project,rid)['session_id']=='other'

def test_state_json_mirrors_task_progress(project):
    rg.start(project);ret(project,call(project,'RG-RESEARCH'))
    st={t['id']:t['status'] for t in ris.read_state(project)['tasks']}
    assert st['RG-RESEARCH']=='PASS' and st['RG-PLAN']=='PENDING'

@pytest.mark.parametrize('return_first', [False, True])
@pytest.mark.parametrize('retry', [False, True])
def test_codex_task_name_response_uses_original_assignment(project, return_first, retry):
    def ev(event, **kw):
        return rg.handle_hook(project, dict(session_id='s', hook_event_name=event, **kw), 'codex')

    ev('UserPromptSubmit', prompt='$ris')
    rid = ris.read_state(project)['run_id']

    def prepare(call_id):
        assignment = rg.assign(project, rid, 'RG-RESEARCH')
        spawn = dict(tool_name='collaborationspawn_agent', tool_use_id=call_id,
                     tool_input=dict(task_name=assignment['codex_task_name'], agent_type='researcher',
                                     fork_turns='none', message=assignment['line']))
        return assignment, spawn

    assignment, spawn = prepare('first-call')
    for bad in (dict(task_name='wrong'), dict(agent_type='worker'), dict(fork_turns='all')):
        invalid = dict(spawn, tool_input=dict(spawn['tool_input'], **bad))
        assert ev('PreToolUse', **invalid)['decision'] == 'block'
    spawn['tool_input']['message'] = 'opaque payload'  # actual Codex hook may omit readable marker
    assert ev('PreToolUse', **spawn) is None  # pass through unchanged
    if retry:
        old = assignment
        old_spawn = spawn
        ev('PostToolUse', **spawn, tool_response='{"error":"failed"}')
        assert ev('PreToolUse', **spawn)['decision'] == 'block'
        assignment, spawn = prepare('retry-call')
        assert assignment['token'] != old['token']
        assert ev('PreToolUse', **spawn) is None
        ev('PostToolUse', **old_spawn, tool_response=json.dumps({'task_name':old_spawn['tool_input']['task_name']}))

    def stop(agent, role, token):
        ev('SubagentStart', agent_id=agent, agent_type=role)
        result = {k: assignment[k] for k in ('run_id', 'task_id', 'input_hash')}
        result.update(token=token, status='PASS', evidence='fixture',
                      artifacts=art(project, 'RG-RESEARCH'))
        ev('SubagentStop', agent_id=agent, agent_type=role,
           last_assistant_message='RIS_RESULT ' + json.dumps(result))

    stop('other', 'researcher', old['token'] if retry else 'wrong')
    stop('worker', 'worker', assignment['token'])
    if return_first:
        stop('right', 'researcher', assignment['token'])
    ev('PostToolUse', **dict(spawn, tool_use_id='unrelated'), tool_response=json.dumps({'task_name':spawn['tool_input']['task_name']}))
    assert rg.load(project, rid)['tasks']['RG-RESEARCH']['status'] != 'PASS'
    name = spawn['tool_input']['task_name']
    ev('PostToolUse', **spawn, tool_response=json.dumps({'task_name':'/root/other/' + name}))
    assert not rg.load(project, rid)['tasks']['RG-RESEARCH']['call']['confirmed']
    ev('PostToolUse', **spawn, tool_response=json.dumps({'task_name':'/root/' + name}))
    if not return_first:
        assert rg.load(project, rid)['tasks']['RG-RESEARCH']['status'] != 'PASS'
        stop('right', 'researcher', assignment['token'])
    task = rg.load(project, rid)['tasks']['RG-RESEARCH']
    assert task['status'] == 'PASS'
    assert task['call']['agent_id'] == task['returned']['agent_id'] == 'right'
