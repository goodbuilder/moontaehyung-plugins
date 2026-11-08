import copy
import importlib.util
import json
from pathlib import Path
import pytest

BASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('project_plan',BASE/'scripts/project_plan.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)

@pytest.fixture
def graph():
    return json.loads(helper.BLOCK.findall((BASE/'assets/research-plan-example.md').read_text())[0])

def test_shared_node_and_cycle_are_preserved(graph,tmp_path):
    graph['edges'].append({'from':'D-002','to':'D-001','relation':'IF','condition':'データ不足'})
    md=tmp_path/'plan.md';md.write_text('```project-plan\n'+json.dumps(graph)+'\n```\n')
    before=md.read_bytes()
    helper.render(tmp_path,'plan.md','map.html')
    text=(tmp_path/'map.html').read_text()
    assert text.startswith('<!-- project-plan-generated -->')
    assert 'example-wildfire' in text and '/*PLAN_DATA*/null' not in text
    assert md.read_bytes()==before
    assert helper.load(tmp_path,'plan.md')[0]['edges']==graph['edges']

@pytest.mark.parametrize('mutation', ['duplicate','endpoint','option','source','conflict','confirmed','estimate'])
def test_invalid_graph_refused(graph,mutation):
    if mutation=='duplicate':graph['nodes'].append(copy.deepcopy(graph['nodes'][0]))
    if mutation=='endpoint':graph['edges'][0]['to']='MISSING'
    if mutation=='option':graph['edges'][1]['option']='missing'
    if mutation=='source':graph['nodes'][1]['options'][0]['evidence']=['missing']
    if mutation=='conflict':graph['incompatible']=[[['D-001','rgb'],['D-002','missing']]]
    if mutation=='confirmed':graph['nodes'][1]['status']='confirmed'
    if mutation=='estimate':graph['nodes'][1]['options'][0]['estimates']=[{'value':99}]
    with pytest.raises(ValueError):helper.validate(graph)

def test_renderer_preserves_handwritten_files_and_escapes_content(graph,tmp_path):
    graph['goal']='</script><script>alert(1)</script>'
    (tmp_path/'plan.md').write_text('```project-plan\n'+json.dumps(graph)+'\n```\n')
    (tmp_path/'map.html').write_text('human document')
    with pytest.raises(ValueError):helper.render(tmp_path,'plan.md','map.html')
    assert (tmp_path/'map.html').read_text()=='human document'
    helper.render(tmp_path,'plan.md','generated.html')
    assert '</script><script>alert(1)' not in (tmp_path/'generated.html').read_text()
    with pytest.raises(ValueError):helper.render(tmp_path,'plan.md','../escape.html')


def test_disconnected_decision_and_recorded_conflict_are_rejected(graph):
    disconnected=copy.deepcopy(graph);disconnected['edges']=[]
    with pytest.raises(ValueError,match='connect to an outcome'):helper.validate(disconnected)
    graph['nodes'][1].update(selected='rgb',selection_reason='Test confirmed event')
    graph['nodes'][2].update(selected='flight',selection_reason='Test confirmed event')
    graph['incompatible']=[[['D-001','rgb'],['D-002','flight']]]
    with pytest.raises(ValueError,match='Recorded selections conflict'):helper.validate(graph)


def test_audit_exposes_shallow_or_unexplained_frontier(graph):
    report=helper.audit(graph)
    assert report['decision_nodes']==2 and report['options']==4
    assert report['unexplained_options']==[
        {'node':'D-002','option':'public','issue':'No option-specific downstream path or documented frontier'},
        {'node':'D-002','option':'flight','issue':'No option-specific downstream path or documented frontier'}]
    assert report['warnings']
    graph['exploration_frontier']=[{'node':'D-002','option':oid,'reason':'Synthetic fixture ends at the data access probe; actual access not tested','next_action':'Check license or obtain collection authorization'} for oid in ('public','flight')]
    assert not helper.audit(graph)['unexplained_options']
    graph['exploration_frontier'][0]['option']='missing'
    with pytest.raises(ValueError):helper.audit(graph)


def test_audit_depth_terminates_on_cycles_and_shared_nodes(graph):
    graph['edges'].append({'from':'D-002','to':'D-001','relation':'IF','condition':'Replan after failed data access'})
    report=helper.audit(graph)
    assert report['decision_stages_shortest_paths']==2
    assert report['decision_nodes']==2


def test_same_option_can_belong_to_multiple_candidates(graph):
    graph['candidates']=[
        {'id':'A','title':'Candidate A','selections':{'D-001':['rgb'],'D-002':['public']}},
        {'id':'B','title':'Candidate B','selections':{'D-001':['rgb'],'D-002':['flight']}}]
    graph['current_candidate']='B'
    helper.validate(graph)
    assert [c['selections']['D-001'] for c in graph['candidates']]==[['rgb'],['rgb']]


def test_multiple_selection_is_decision_local_and_legacy_scalar_still_works(graph):
    graph['nodes'][1].update(selected='rgb',selection_reason='Legacy choice')
    helper.validate(graph)
    graph['nodes'][2]['selection_mode']='multiple'
    graph['candidates']=[{'id':'A','title':'A','selections':{'D-001':'rgb','D-002':['public','flight']}}]
    helper.validate(graph)
    graph['candidates'][0]['selections']['D-001']=['rgb','fusion']
    with pytest.raises(ValueError,match='Single-select'):helper.validate(graph)


def test_conflicts_checked_within_each_candidate_not_across_them(graph):
    graph['incompatible']=[[['D-001','rgb'],['D-002','flight']]]
    graph['candidates']=[
        {'id':'A','title':'A','selections':{'D-001':['rgb']}},
        {'id':'B','title':'B','selections':{'D-002':['flight']}}]
    helper.validate(graph)
    graph['candidates'][1]['selections']['D-001']=['rgb']
    with pytest.raises(ValueError,match='conflict in candidate B'):helper.validate(graph)


@pytest.mark.parametrize('mutation',['id','node','option','repeat','mode','current'])
def test_invalid_candidate_references_and_modes_refused(graph,mutation):
    graph['candidates']=[{'id':'A','title':'A','selections':{'D-001':['rgb']}}]
    if mutation=='id':graph['candidates'].append(copy.deepcopy(graph['candidates'][0]))
    if mutation=='node':graph['candidates'][0]['selections']={'missing':['rgb']}
    if mutation=='option':graph['candidates'][0]['selections']['D-001']=['missing']
    if mutation=='repeat':graph['candidates'][0]['selections']['D-001']=['rgb','rgb']
    if mutation=='mode':graph['nodes'][1]['selection_mode']='invalid'
    if mutation=='current':graph['current_candidate']='missing'
    with pytest.raises(ValueError):helper.validate(graph)


def test_component_labels_are_optional_and_do_not_change_candidate_memberships(graph):
    graph['nodes'][1]['component']='관측 방식'
    graph['candidates']=[{'id':'A','title':'A','selections':{'D-001':['rgb']}},{'id':'B','title':'B','selections':{'D-001':['rgb']}}]
    before=copy.deepcopy(graph['candidates'])
    helper.validate(graph)
    assert graph['candidates']==before
    graph['nodes'][1]['component']=[]
    with pytest.raises(ValueError,match='Component label'):helper.validate(graph)
