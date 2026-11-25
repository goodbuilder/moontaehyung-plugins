import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
spec = importlib.util.spec_from_file_location('coordination_ris', SCRIPTS / 'ris.py')
ris = importlib.util.module_from_spec(spec); spec.loader.exec_module(ris)
c = ris.companion('ris_coordination')


def task(id, status='READY', deps=None):
    return {'id': id, 'type': 'research', 'owner': 'researcher', 'status': status,
            'depends_on': deps or [], 'artifact_refs': [], 'audit_status': 'NOT_RUN',
            'attempt': 1, 'invalidated_by': []}


@pytest.fixture
def project(tmp_path):
    ris.initialize(tmp_path, 'Coordination test', 'Fixed goal')
    ris.initialize_state(tmp_path)
    (tmp_path / 'approval.md').write_text('Existing user scope; prioritize verified quality within cost/time ceilings.')
    return tmp_path


def put_tasks(root, tasks, **changes):
    snap = ris.read_state_snapshot(root); body = snap['state']
    body.update(changes); body['tasks'] = tasks
    ris.update_state(root, snap['sha256'], json.dumps(body))


def evidence(root, name='approval.md'):
    return {'path': name, 'sha256': hashlib.sha256((root/name).read_bytes()).hexdigest()}


def envelope(root, name='budget-1.json', **changes):
    snap = ris.read_state_snapshot(root)
    body = {'schema_version': 1, 'project_id': snap['state']['project_id'],
            'run_id': snap['state']['run_id'], 'state_sha256': snap['sha256'],
            'approval_context': evidence(root),
            'priority': {'quality': 'preserve required checks', 'cost': 'hard cap 10', 'time': 'no invented deadline'},
            'task_order': [t['id'] for t in snap['state']['tasks']],
            'resources': {'tokens': {'unit': 'cache-inclusive-token', 'limit': 10, 'spent': 0, 'reserved': 0, 'known': True}},
            'demands': {t['id']: {'tokens': 6} for t in snap['state']['tasks']},
            'decision_blocks': {r: [] for r in snap['state']['pending_user_decisions']},
            'external_effects': {}, 'recoveries': {}}
    body.update(changes); (root/name).write_text(json.dumps(body))
    return name, body


def test_s20_failure_detected_and_bounded_recovery_without_user_prompt(project):
    put_tasks(project, [task('failed', 'FAIL'), task('independent')])
    ref, body = envelope(project, recoveries={'failed': {'failure_kind': 'internal_exploration', 'max_attempts': 2, 'evidence': evidence(project)}})
    result = c.project(ris, project, ref)
    assert result['selected'] == [{'task_id': 'failed', 'action': 'recover', 'attempt': 2, 'demand': {'tokens': 6}}]
    claim = c.claim(ris, project, ref, 'failed', result['state_sha256'])
    assert claim['attempt'] == 2 and not claim['dispatched']
    assert ris.read_state(project)['tasks'][0]['status'] == 'IN_PROGRESS'
    assert ris.read_state(project)['pending_user_decisions'] == []


def test_s23_uncertain_external_effect_halts_only_affected_work(project):
    put_tasks(project, [task('failed', 'FAIL'), task('dependent', deps=['failed']), task('independent')])
    ref, _ = envelope(project, recoveries={'failed': {'failure_kind': 'transient_tool', 'max_attempts': 3, 'evidence': evidence(project)}},
                      external_effects={'failed': {'status': 'UNKNOWN', 'evidence': evidence(project)}})
    result = c.project(ris, project, ref)
    assert [t['task_id'] for t in result['selected']] == ['independent']
    assert 'external_effect_UNKNOWN' in result['dispositions'][0]['reasons']
    assert 'dependency_not_valid:failed' in result['dispositions'][1]['reasons']


def test_user_decision_does_not_stop_scoped_independent_work(project):
    put_tasks(project, [task('waiting'), task('continue')], status='USER_DECISION', pending_user_decisions=['approval.md'])
    ref, _ = envelope(project, decision_blocks={'approval.md': ['waiting']})
    result = c.project(ris, project, ref)
    assert [t['task_id'] for t in result['selected']] == ['continue']
    assert result['dispositions'][0]['reasons'] == ['USER_DECISION']


def test_s28_exhausted_unknown_and_stale_preserve_all_state(project):
    put_tasks(project, [task('A')]); before = (project/'.ris/state.json').read_bytes()
    for value in [dict(limit=10, spent=10, reserved=0, known=True), dict(limit=10, spent=0, reserved=0, known=False)]:
        ref, _ = envelope(project, resources={'tokens': value | {'unit': 'cache-inclusive-token'}})
        if value['known']:
            assert not c.project(ris, project, ref)['selected']
            with pytest.raises(ris.Error): c.claim(ris, project, ref, 'A', ris.read_state_snapshot(project)['sha256'])
        else:
            with pytest.raises(ris.Error, match='Unknown'): c.project(ris, project, ref)
        assert (project/'.ris/state.json').read_bytes() == before
    ref, _ = envelope(project)
    put_tasks(project, [task('A'), task('new')])
    with pytest.raises(ris.Error, match='Stale'): c.project(ris, project, ref)


def test_s29_concise_projection_uses_no_roles_artifacts_or_state_writes(project):
    put_tasks(project, [task('A'), task('B')]); ref, _ = envelope(project)
    files = {str(p.relative_to(project)): p.read_bytes() for p in project.rglob('*') if p.is_file()}
    result = c.project(ris, project, None, mode='concise')
    assert result['selected'] == []
    with pytest.raises(ris.Error): c.claim(ris, project, ref, 'A', result['state_sha256'], mode='concise')
    assert files == {str(p.relative_to(project)): p.read_bytes() for p in project.rglob('*') if p.is_file()}


def test_cas_competing_and_duplicate_claim_only_one_reservation(project):
    put_tasks(project, [task('A'), task('B')]); ref, _ = envelope(project)
    sha = ris.read_state_snapshot(project)['sha256']
    def compete(id):
        try: return c.claim(ris, project, ref, id, sha)
        except ris.Error: return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(compete, ['A', 'B']))
    assert sum(r is not None for r in results) == 1
    assert sum(t['status'] == 'IN_PROGRESS' for t in ris.read_state(project)['tasks']) == 1
    with pytest.raises(ris.Error): c.claim(ris, project, ref, 'A', sha)


def test_held_spent_and_mutated_receipts_cannot_be_reallocated(project):
    put_tasks(project, [task('A'), task('B')]); ref, _ = envelope(project)
    c.claim(ris, project, ref, 'A', ris.read_state_snapshot(project)['sha256'])
    fresh, body = envelope(project, 'budget-2.json')
    with pytest.raises(ris.Error, match='omits prior'): c.project(ris, project, fresh)
    body['resources']['tokens']['reserved'] = 6
    (project/fresh).write_text(json.dumps(body))
    assert c.project(ris, project, fresh)['selected'] == []  # only 4 remains
    snap = ris.read_state_snapshot(project); snap['state']['tasks'][0]['status'] = 'FAIL'
    ris.update_state(project, snap['sha256'], json.dumps(snap['state']))
    fresh, body = envelope(project, 'budget-3.json')
    with pytest.raises(ris.Error, match='omits prior'): c.project(ris, project, fresh)
    body['resources']['tokens']['spent'] = 6
    (project/fresh).write_text(json.dumps(body))
    assert c.project(ris, project, fresh)['selected'] == []
    (project/ref).write_text('{}')
    with pytest.raises(ris.Error, match='snapshot changed'): c.project(ris, project, fresh)


def test_transitive_invalidations_unknown_active_and_limit_output(project):
    a = task('A', 'PASS'); a['invalidated_by'] = ['changed-source']
    put_tasks(project, [a, task('B', 'PASS', ['A']), task('C', deps=['B']), task('D')])
    ref, _ = envelope(project)
    result = c.project(ris, project, ref, limit=1)
    assert [t['task_id'] for t in result['selected']] == ['D']
    assert len(result['dispositions']) == 1 and result['omitted'] == 3
    put_tasks(project, [task('legacy', 'IN_PROGRESS'), task('new')]); ref, _ = envelope(project, 'other.json')
    with pytest.raises(ris.Error, match='Unknown active'): c.project(ris, project, ref)


@pytest.mark.parametrize('value', [None, True, 'NaN', '-1', 'Infinity'])
def test_malformed_accounting_never_becomes_zero(project, value):
    put_tasks(project, [task('A')]); ref, body = envelope(project)
    body['resources']['tokens']['spent'] = value; (project/ref).write_text(json.dumps(body))
    with pytest.raises(ris.Error): c.project(ris, project, ref)


def test_cli_independently_runnable_workflow_and_identity_guard(project):
    put_tasks(project, [task('A')]); ref, body = envelope(project)
    cmd = [sys.executable, str(SCRIPTS/'ris_coordination.py'), '--project', str(project), 'coordinate', '--envelope', ref]
    result = subprocess.run(cmd, text=True, capture_output=True, check=True)
    projected = json.loads(result.stdout)
    result = subprocess.run(cmd + ['--claim', 'A', '--expected-hash', projected['state_sha256']], text=True, capture_output=True, check=True)
    assert not json.loads(result.stdout)['dispatched']
    duplicate = subprocess.run(cmd, text=True, capture_output=True)
    assert duplicate.returncode == 2 and 'Stale' in duplicate.stderr
    fresh, body = envelope(project, 'wrong.json'); body['project_id'] = 'other-project'
    (project/fresh).write_text(json.dumps(body))
    with pytest.raises(ris.Error, match='mismatch'): c.project(ris, project, fresh)


def test_recovery_attempt_limit_and_approval_bytes_preserved(project):
    failed = task('failed', 'FAIL'); failed['attempt'] = 2
    put_tasks(project, [failed])
    ref, _ = envelope(project, recoveries={'failed': {'failure_kind': 'internal_exploration', 'max_attempts': 2, 'evidence': evidence(project)}})
    result = c.project(ris, project, ref)
    assert not result['selected']
    before = (project/'.ris/state.json').read_bytes()
    (project/'approval.md').write_text('Externally revised approval context')
    with pytest.raises(ris.Error, match='artifact changed'): c.project(ris, project, ref)
    assert (project/'.ris/state.json').read_bytes() == before


def test_changed_evidence_during_claim_withholds_dispatch_receipt(project, monkeypatch):
    put_tasks(project, [task('A')]); ref, _ = envelope(project)
    sha = ris.read_state_snapshot(project)['sha256']
    original = ris.update_state
    def change_after_commit(*args):
        result = original(*args)
        (project/'approval.md').write_text('Concurrent external edit')
        return result
    monkeypatch.setattr(ris, 'update_state', change_after_commit)
    with pytest.raises(ris.Error, match='artifact changed'): c.claim(ris, project, ref, 'A', sha)
    # Commit is retained/held for reconciliation, never silently retried.
    assert ris.read_state(project)['tasks'][0]['status'] == 'IN_PROGRESS'


def registered(root, *args, timeout=5):
    return subprocess.run([sys.executable, str(SCRIPTS/'ris.py'), '--project', str(root), 'coordinate', *args],
                          text=True, capture_output=True, timeout=timeout)


@pytest.mark.parametrize('initialized', [False, True])
def test_registered_concise_without_state_or_setup(tmp_path, initialized):
    if initialized: ris.initialize(tmp_path, 'No orchestration state', 'Concise purpose')
    before = {str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    result = registered(tmp_path, '--mode', 'concise')
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['state_sha256'] is None
    assert json.loads(result.stdout)['selected'] == []
    assert before == {str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}


def test_exhausted_model_budget_allows_zero_demand_local_work(project):
    put_tasks(project, [task('model'), task('local')])
    ref, body = envelope(project, demands={'model': {'tokens': 1}, 'local': {'tokens': 0}})
    body['resources']['tokens']['spent'] = 10; (project/ref).write_text(json.dumps(body))
    result = registered(project, '--envelope', ref)
    assert result.returncode == 0, result.stderr
    projection = json.loads(result.stdout)
    assert [t['task_id'] for t in projection['selected']] == ['local']
    claim = registered(project, '--envelope', ref, '--claim', 'local', '--expected-hash', projection['state_sha256'])
    assert claim.returncode == 0, claim.stderr
    assert json.loads(claim.stdout)['resource_reservation'] == {'tokens': 0}


def test_global_ambiguous_and_scoped_blocked_holds(project):
    put_tasks(project, [task('held'), task('dependent', deps=['held']), task('local')], status='BLOCKED')
    ref, _ = envelope(project)
    assert c.project(ris, project, ref)['selected'] == []
    put_tasks(project, [task('held', 'PASS'), task('dependent', deps=['held']), task('local')],
              status='BLOCKED', blocked_items=[{'ref': 'approval.md', 'reason': 'Affected branch needs reconciliation'}])
    ref, _ = envelope(project, 'hold-ambiguous.json')
    assert c.project(ris, project, ref)['selected'] == []
    ref, _ = envelope(project, 'hold-scoped.json', blocked_scopes={'approval.md': ['held']})
    result = c.project(ris, project, ref)
    assert [t['task_id'] for t in result['selected']] == ['local']
    assert 'dependency_not_valid:held' in result['dispositions'][1]['reasons']
    claim = registered(project, '--envelope', ref, '--claim', 'held', '--expected-hash', result['state_sha256'])
    assert claim.returncode == 2 and 'Traceback' not in claim.stderr


@pytest.mark.parametrize('field,value', [
    ('external_effects', {'A': {'status': [], 'evidence': {}}}),
    ('recoveries', {'A': {'failure_kind': {}, 'max_attempts': 2, 'evidence': {}}}),
    ('blocked_scopes', {'approval.md': [{}]}),
    ('decision_blocks', {'approval.md': [{}]}),
    ('resources', {'tokens': []}),
    ('demands', {'A': []}),
    ('task_order', [{}]),
    ('approval_context', {'path': [], 'sha256': {}}),
    ('priority', {'quality': [], 'cost': {}, 'time': 1}),
])
def test_registered_malformed_nested_types_are_controlled(project, field, value):
    put_tasks(project, [task('A')])
    ref, body = envelope(project); body[field] = value
    (project/ref).write_text(json.dumps(body))
    result = registered(project, '--envelope', ref)
    assert result.returncode == 2 and 'Traceback' not in result.stderr, result.stderr
    assert json.loads(result.stderr)['error']


def test_shared_dag_dependency_validation_is_bounded(project):
    tasks = [task('root', 'PASS')]; prior = ['root']
    for layer in range(24):
        ids = [f'{layer}-a', f'{layer}-b']
        tasks += [task(id, 'PASS', prior) for id in ids]; prior = ids
    tasks.append(task('ready', deps=prior)); put_tasks(project, tasks)
    ref, _ = envelope(project)
    result = registered(project, '--envelope', ref, timeout=3)
    assert result.returncode == 0, result.stderr
    assert [t['task_id'] for t in json.loads(result.stdout)['selected']] == ['ready']


def test_malformed_prior_claim_demand_is_controlled(project):
    malformed = {'project_id': ris.config(project)['project_id'],
                 'run_id': ris.read_state(project)['run_id'],
                 'demands': {'A': ['tokens']}, 'resources': {'tokens': {'unit': 'cache-inclusive-token'}}}
    raw = json.dumps(malformed).encode(); (project/'prior.json').write_bytes(raw)
    active = task('A', 'IN_PROGRESS')
    active['artifact_refs'] = ['prior.json#coordination-sha256=' + hashlib.sha256(raw).hexdigest()]
    put_tasks(project, [active, task('B')]); ref, _ = envelope(project)
    result = registered(project, '--envelope', ref)
    assert result.returncode == 2 and 'Traceback' not in result.stderr
    assert 'prior resource reservation' in result.stderr
