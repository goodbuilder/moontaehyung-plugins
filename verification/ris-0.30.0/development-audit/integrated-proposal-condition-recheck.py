import importlib.util,json,subprocess,sys,tempfile
from pathlib import Path
HERE=Path(__file__).parent
original=HERE.parent/'architecture/findings_scope_audit.py'
run=subprocess.run([sys.executable,str(original)],capture_output=True,text=True)
spec=importlib.util.spec_from_file_location('audit_findings_flow',Path('/home/moontaehyung/plugins/moontaehyung/skills/ris/tests/test_findings.py'))
tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
spec=importlib.util.spec_from_file_location('audit_findings_ris',tests.CLI)
ris=importlib.util.module_from_spec(spec);spec.loader.exec_module(ris)
with tempfile.TemporaryDirectory(prefix='ris-condition-recheck-') as td:
 root=Path(td);ris.initialize(root,recording_policy='manual');flow=tests.Flow((root,ris.config(root)['project_id']))
 flow.freeze();finding=flow.node();finding['conditions']={'material':'Birch','source_temperature':'20 C','target_temperature':'25 C'}
 flow.run('propose',{'owner':'researcher','finding':finding})
 flow.run('accept',{'id':'f1','owner':'researcher','note':'recorded'})
 _,_=None,None
 snapshot=flow.run('inspect',extra=('--node-id','f1'))['proposals'][0]
 scope=ris.companion('ris_findings').condition_passage(finding)
 flow.run('return',{'id':'f1','owner':'researcher','note':'received','finding_revision':snapshot['accepted_revision'],
                    'transcript':finding['statement']+'\n\nNo timestamps were recorded.\n\n'+scope})
 flow.run('integrate',{'id':'f1','owner':'researcher','note':'integrated'});flow.resolve();flow.disposition()
 (root/'draft.md').write_text('Timing remains unresolved; do not infer an interval.\n\n'+finding['statement']+'\n\nNo timestamps were recorded.')
 error=flow.run('deliver',{'draft':'draft.md'},ok=False)
 result={'original_probe':{'exit_code':run.returncode,'stderr':run.stderr,'rejected_at_owner_return':'Owner return omits' in run.stderr},
         'after_correct_owner_return':{'delivery_omitting_conditions_rejected':'conditions' in error,'error':error},
         'status':'PASS' if run.returncode!=0 and 'Owner return omits' in run.stderr and 'conditions' in error else 'FAIL',
         'scope':'Developer synthetic negative regression, not official E2E'}
 (HERE/'integrated-proposal-condition-recheck.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
