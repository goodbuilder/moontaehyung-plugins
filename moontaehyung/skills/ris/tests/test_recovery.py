import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
spec = importlib.util.spec_from_file_location('recovery_ris', SCRIPTS / 'ris.py')
ris = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ris)
r = ris.companion('ris_recovery')

@pytest.fixture
def project(tmp_path):
    ris.initialize(tmp_path, 'Recovery', 'Goal')
    return tmp_path

def save(root, body, **kw):
    return r.apply(ris, root, body, r.snapshot(ris, root)['hash'], True, **kw)

def create(root, known=True, id='N1'):
    return save(root, {'id': 'create-'+id, 'operation': 'create', 'history_complete': known, 'node': {'id': id, 'label': 'Question', 'scope': 'Scope', 'conditions': 'Conditions'}})

def request(i, kind='deepen', node='N1'):
    return {'id': 'event-'+str(i), 'operation': 'request', 'node_id': node, 'request_id': 'request-'+str(i), 'request_ref': 'conversation:'+str(i), 'kind': kind}

def test_progression_and_dedup(project):
    create(project)
    save(project, {'id': 'delivery', 'operation': 'delivered', 'node_id': 'N1', 'result_ref': 'conversation:result'})
    for i, action in enumerate(['assess_exhaustive', 'unused_frontier', 'exhaustive_now'], 1):
        event = request(i)
        assert save(project, event)['result']['action'] == action
        assert r.apply(ris, project, event, 'stale', True)['duplicate']
        event = event | {'id': 'retry-envelope-'+str(i)}
        assert r.apply(ris, project, event, 'stale', True)['duplicate']
        retry = event | {'id': 'delivery-retry-' + str(i), 'kind': 'retry', 'request_ref': 'resent'}
        assert r.apply(ris, project, retry, 'stale', True)['duplicate']
    save(project, {'id': 'exhaustive', 'operation': 'exhaustive-complete', 'node_id': 'N1', 'result_ref': 'conversation:exhaustive'})
    assert save(project, request(4))['result']['action'] == 'meta_recovery'

@pytest.mark.parametrize('kind', sorted(r.EXCLUDED | {'input'}))
def test_exclusions(project, kind):
    create(project)
    save(project, {'id': 'delivery', 'operation': 'delivered', 'node_id': 'N1', 'result_ref': 'conversation:result'})
    assert save(project, request(1, kind))['result']['count'] == 0

def test_unknown_independence_and_mixed(project):
    create(project, False)
    create(project, True, 'N2')
    for node in ['N1', 'N2']:
        save(project, {'id': 'delivery-'+node, 'operation': 'delivered', 'node_id': node, 'result_ref': 'conversation:result'})
    assert save(project, request(1))['result'] == {'action': 'assess_exhaustive', 'count': None, 'observed_count': 1, 'history_unknown': True, 'counted': True}
    event = request(2, 'input-and-deepen', 'N2') | {'input_ref': 'conversation:new-data'}
    assert save(project, event)['result']['count'] == 1
    assert r.snapshot(ris, project)['ledger']['nodes']['N1']['count'] is None

def test_semantic_history(project):
    create(project)
    save(project, {'id': 'rename', 'operation': 'rename', 'node_id': 'N1', 'label': 'Renamed', 'rationale': 'Same question'})
    body = {'label': 'Child', 'scope': 'Narrower', 'conditions': 'Same'}
    save(project, {'id': 'split', 'operation': 'split', 'parents': ['N1'], 'children': [body | {'id': 'N2'}, body | {'id': 'N3'}], 'rationale': 'Explicit subquestions'})
    save(project, {'id': 'merge', 'operation': 'merge', 'parents': ['N2', 'N3'], 'children': [body | {'id': 'N4'}], 'rationale': 'Unified question'})
    ledger = r.snapshot(ris, project)['ledger']
    assert ledger['nodes']['N1']['label'] == 'Renamed'
    assert ledger['nodes']['N4']['parents'] == ['N2', 'N3']
    assert len(ledger['events']) == 4

def test_guards_and_public_cli_legacy(project, tmp_path):
    cfg_path = project / '.ris/project.yaml'
    cfg_path.write_text(cfg_path.read_text().replace('recording_policy: "significant"', 'recording_policy: "manual"').replace('schema_version: 2', 'schema_version: 1').replace('research_dir: ".ris/research"', 'research_dir: "research"'))
    body = {'id': 'new', 'operation': 'create', 'node': {'id': 'N1', 'label': 'Question', 'scope': 'Scope', 'conditions': 'Condition'}}
    with pytest.raises(ris.Error, match='Manual'):
        r.apply(ris, project, body, 'missing')
    file = tmp_path / 'event.json'
    file.write_text(json.dumps(body))
    command = [sys.executable, str(SCRIPTS / 'ris.py'), '--project', str(project), 'recovery']
    result = subprocess.run(command + ['apply', '--body-file', str(file), '--expected-hash', 'missing', '--record-authorized'], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['result']['count'] is None
    result = subprocess.run(command + ['read'], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['ledger']['revision'] == 1
    with pytest.raises(ris.Error, match='CAS'):
        r.apply(ris, project, body | {'id': 'other'}, 'missing', True)
    target = project / '.ris/recovery.json'
    target.unlink()
    target.symlink_to(tmp_path / 'outside')
    with pytest.raises(ris.Error, match='Symlink'):
        r.snapshot(ris, project)

def test_concurrent_cli_cas(project, tmp_path):
    command = [sys.executable, str(SCRIPTS / 'ris.py'), '--project', str(project), 'recovery', 'apply', '--expected-hash', 'missing', '--record-authorized']
    jobs = []
    for i in range(2):
        body = {'id': 'create-'+str(i), 'operation': 'create', 'node': {'id': 'N'+str(i), 'label': 'Question', 'scope': 'Scope', 'conditions': 'Condition'}}
        file = tmp_path / ('event-'+str(i)+'.json')
        file.write_text(json.dumps(body))
        jobs.append(subprocess.Popen(command + ['--body-file', str(file)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
    outputs = [job.communicate() for job in jobs]
    assert sorted(job.returncode for job in jobs) == [0, 2], outputs
    assert len(r.snapshot(ris, project)['ledger']['nodes']) == 1


def test_history_reconciliation_and_no_partial_failure(project):
    create(project, False)
    save(project, {'id': 'history', 'operation': 'reconcile-history', 'node_id': 'N1', 'count': 2, 'evidence_ref': 'conversation:complete-history'})
    save(project, {'id': 'delivery', 'operation': 'delivered', 'node_id': 'N1', 'result_ref': 'conversation:result'})
    assert save(project, request(1))['result']['action'] == 'exhaustive_now'
    before = r.snapshot(ris, project)
    with pytest.raises(ris.Error):
        save(project, {'id': 'bad-split', 'operation': 'split', 'parents': ['N1'], 'children': [{'id': 'N2', 'label': 'Valid', 'scope': 'Scope', 'conditions': 'Condition'}, {'id': 'N3'}], 'rationale': 'Test atomic failure'})
    assert r.snapshot(ris, project) == before


def test_unknown_history_cannot_defer_escalation(project):
    create(project, False)
    save(project, {'id': 'delivery', 'operation': 'delivered', 'node_id': 'N1', 'result_ref': 'conversation:result'})
    for i, action in enumerate(['assess_exhaustive', 'unused_frontier', 'exhaustive_now'], 1):
        result = save(project, request(i))['result']
        assert result['action'] == action
        assert result['count'] is None
        assert result['observed_count'] == i

def test_changed_semantic_scope_does_not_invent_applicable_history(project):
    create(project)
    save(project, {'id': 'delivery', 'operation': 'delivered', 'node_id': 'N1', 'result_ref': 'conversation:answer'})
    save(project, request(1))
    child = {'label': 'Subquestion', 'scope': 'Different bounded scope', 'conditions': 'Explicit subset'}
    save(project, {'id': 'split', 'operation': 'split', 'parents': ['N1'], 'children': [child | {'id': 'N2'}, child | {'id': 'N3'}], 'rationale': 'Applicability not established'})
    ledger = r.snapshot(ris, project)['ledger']
    assert ledger['nodes']['N1']['count'] == 1
    assert ledger['nodes']['N2']['count'] is None
    assert ledger['nodes']['N2']['observed_count'] == 0


def test_proven_semantic_continuity_preserves_count_without_sum(project):
    create(project)
    save(project, {'id': 'delivery', 'operation': 'delivered', 'node_id': 'N1', 'result_ref': 'conversation:answer'})
    save(project, request(1))
    child = {'label': 'Same bounded question', 'scope': 'Scope', 'conditions': 'Conditions'}
    save(project, {'id': 'split', 'operation': 'split', 'parents': ['N1'], 'children': [child | {'id': 'N2'}, child | {'id': 'N3'}], 'history_applicability': 'preserve', 'rationale': 'Both branches retain applicability of the same prior request'})
    save(project, {'id': 'merge', 'operation': 'merge', 'parents': ['N2', 'N3'], 'children': [child | {'id': 'N4'}], 'history_applicability': 'preserve', 'rationale': 'Recombine duplicated common history, not independent requests'})
    node = r.snapshot(ris, project)['ledger']['nodes']['N4']
    assert node['count'] == 1
    assert node['observed_count'] == 1


def test_merge_counts_shared_and_distinct_requests(project):
    create(project)
    save(project, {'id': 'delivery', 'operation': 'delivered', 'node_id': 'N1',
                   'result_ref': 'conversation:answer'})
    save(project, request(1))
    branch = {'label': 'Applicable question', 'scope': 'Scope', 'conditions': 'Conditions'}
    save(project, {'id': 'split', 'operation': 'split', 'parents': ['N1'],
                   'children': [branch | {'id': name} for name in ['N2', 'N3']],
                   'history_applicability': 'preserve', 'rationale': 'Shared prior request'})
    save(project, request(2, node='N2'))
    save(project, request(3, node='N3'))
    merged = save(project, {'id': 'merge', 'operation': 'merge', 'parents': ['N2', 'N3'],
                            'children': [branch | {'id': 'N4'}], 'history_applicability': 'preserve',
                            'rationale': 'All three requests apply to the resulting scope'})
    assert merged['result']['count'] == 3


def test_stdin_and_metadata_boundary(project):
    command = [sys.executable, str(SCRIPTS / 'ris.py'), '--project', str(project),
               'recovery', 'apply', '--body-file', '-', '--expected-hash', 'missing',
               '--record-authorized']
    event = {'id': 'start', 'operation': 'create', 'history_complete': True,
             'node': {'id': 'Q', 'scope': 'Scope', 'conditions': 'Conditions', 'label': 'Question'}}
    rejected = subprocess.run(command, input=json.dumps(event | {'transcript': 'extra text'}),
                              capture_output=True, text=True)
    assert rejected.returncode == 2
    assert r.snapshot(ris, project)['hash'] == 'missing'
    accepted = subprocess.run(command, input=json.dumps(event), capture_output=True, text=True, check=True)
    assert json.loads(accepted.stdout)['result']['count'] == 0
    view = ris.context(project, question='Q')
    assert view['recovery']['count'] == 0
    assert view['recovery']['revision'] == 1
    assert 'recovery' not in ris.context(project, question='different')
