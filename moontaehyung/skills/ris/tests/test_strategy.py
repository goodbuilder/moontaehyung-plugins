import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
spec = importlib.util.spec_from_file_location('strategy_ris', SCRIPTS / 'ris.py')
ris = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ris)


def cli(root, *args, body=None, success=True):
    result = subprocess.run([sys.executable,str(SCRIPTS/'ris.py'),'--project',str(root),*args],
                            input=json.dumps(body) if body else None,text=True,capture_output=True)
    if success:
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)
    assert result.returncode != 0
    return result.stderr


def test_actual_cli_strategy_and_strict_recovery(tmp_path):
    root = tmp_path/'project'
    root.mkdir()
    ris.initialize(root)
    cfg = ris.config(root)
    relative = ris.research_path(cfg,'research/findings/origin.md')
    note = ris.inside(root,relative)
    note.write_text(ris.note(cfg['project_id'],'finding','Origin','Observed strategy history'))
    capture = root/'work.json'
    capture.write_text('{"command":"local-fixture","result":"negative control failed as predicted"}')
    work = {'path':'work.json','sha256':hashlib.sha256(capture.read_bytes()).hexdigest(),
            'action':'inspect fixture','outcome':'negative control failed as predicted'}
    body = {'id':'lesson-1','origin_note':relative,'origin_question':'Q1','input_revision':'2',
            'conditions':{'material':'Birch'},'method':'verify input revision first',
            'observed_outcome':'stale source caught','failure_cases':['different measurement regime'],
            'competing_explanation':'manual inspection','confidence_limits':'one synthetic fixture',
            'reopening_trigger':'input revision changes','work_evidence':[work]}
    cli(root,'recovery','strategy-record','--body-file','-', '--expected-hash',
        hashlib.sha256(note.read_bytes()).hexdigest(),body=body)
    found = cli(root,'recovery','strategy-search','stale','--conditions','{"material":"Birch"}')
    assert found['results'][0]['applicability'] == 'review_required'
    assert found['results'][0]['transfer_verdict'] == 'unverified'
    different = cli(root,'recovery','strategy-search','stale','--conditions','{"material":"Steel"}')
    assert different['results'][0]['applicability'] == 'not_applicable_without_recheck'
    application = {'origin_note':relative,'strategy_id':'lesson-1','target_question':'Q2',
                   'target_revision':'1','target_conditions':{'material':'Steel'},
                   'baseline_next_action':'inspect input','retrieval_changed_action':'none; mismatch',
                   'actual_action':'retain baseline','observed_result':'no transfer claimed',
                   'negative_control':'wrong material capture','verdict':'not applied',
                   'rationale':'material mismatch','work_evidence':[work]}
    cli(root,'recovery','strategy-apply','--body-file','-','--expected-hash',
        hashlib.sha256(note.read_bytes()).hexdigest(),body=application)
    assert '<!-- ris:strategy-application -->' in note.read_text()
    history = cli(root,'recovery','strategy-search','stale','--conditions','{"material":"Birch"}')
    assert history['results'][0]['application_history'][0]['verdict'] == 'not applied'
    capture.write_text('changed')
    stale = cli(root,'recovery','strategy-search','stale','--conditions','{"material":"Birch"}')
    assert stale['results'][0]['evidence_freshness'] == 'changed_or_unavailable'
    capture.write_text('{"command":"local-fixture","result":"negative control failed as predicted"}')
    def event(body, success=True):
        current = cli(root,'recovery','read')
        return cli(root,'recovery','apply','--body-file','-','--expected-hash',current['hash'],body=body,success=success)
    event({'id':'create','operation':'create','evidence_policy':'verified-local','history_complete':True,
           'node':{'id':'Q1','label':'Question','scope':'same project','conditions':'Birch'}})
    incomplete = {'id':'exhaust','operation':'exhaustive-complete','node_id':'Q1','result_ref':relative}
    assert 'coverage' in event(incomplete,False)
    exhaustive = dict(incomplete,coverage=['local fixture'],remaining_frontier='Unmeasured domain transfer',work_evidence=[work])
    result = event(exhaustive)
    assert result['result']['scientific_completeness'] == 'not_certified'
    assert result['result']['work_evidence'][0]['action_execution'] == 'asserted_not_independently_observed'
    result = event({'id':'meta','operation':'meta-complete','node_id':'Q1','result_ref':relative,
                    'failed_assumption':'revision remained current','changed_method':'re-read pinned input',
                    'negative_control':'wrong revision fixture', 'work_evidence':[work]})
    assert result['result']['action'] == 'meta_recorded'
    assert result['result']['count'] == 0


def test_malformed_strategy_records_are_clean_errors(tmp_path):
    root=tmp_path/'project'
    root.mkdir()
    ris.initialize(root)
    cfg=ris.config(root)
    path=ris.inside(root,ris.research_path(cfg,'research/findings/bad.md'))
    for value in (None, [], {'id':'bad'}, {'id':'bad','project_id':cfg['project_id'],
                   'conditions':{'x':None},'work_evidence':[]}):
        path.write_text(ris.note(cfg['project_id'],'finding','Bad','')+
                        '\n<!-- ris:strategy -->\n```json\n'+json.dumps(value)+
                        '\n```\n<!-- /ris:strategy -->')
        error=cli(root,'recovery','strategy-search','bad','--conditions','{}',success=False)
        assert 'Malformed originating strategy' in error
        assert 'Traceback' not in error


def test_foreign_frontmatter_cannot_impersonate_local_strategy(tmp_path):
    root=tmp_path/'project'
    root.mkdir()
    ris.initialize(root)
    cfg=ris.config(root)
    path=ris.inside(root,ris.research_path(cfg,'research/findings/foreign.md'))
    value={'id':'local-claim','project_id':cfg['project_id'],'conditions':{'x':'y'},
           'work_evidence':[{'path':'missing','sha256':'abc','action':'x','outcome':'y'}]}
    path.write_text(ris.note('foreign-project','finding','Foreign','')+
                    '\n<!-- ris:strategy -->\n```json\n'+json.dumps(value)+
                    '\n```\n<!-- /ris:strategy -->')
    strategy=ris.companion('ris_strategy')
    assert strategy.retrieve(ris.helper_api(),root,'local-claim',{'x':'y'})['results'] == []
