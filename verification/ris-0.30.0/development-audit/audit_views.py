"""Registered Designer navigation CLI controls on disposable synthetic notes."""
import hashlib,importlib.util,json,subprocess,sys,tempfile
from pathlib import Path
S=Path('/home/moontaehyung/plugins/moontaehyung/skills/ris/scripts')
spec=importlib.util.spec_from_file_location('view_audit_ris',S/'ris.py');ris=importlib.util.module_from_spec(spec);spec.loader.exec_module(ris)
results=[]
with tempfile.TemporaryDirectory(prefix='ris-audit-views-') as name:
 root=Path(name);ris.initialize(root,recording_policy='manual');cfg=ris.config(root)
 plan='.ris/research/plans/stable-plan.md';(root/plan).write_text(ris.note(cfg['project_id'],'plan','Synthetic existing plan','[Existing map](../maps/stable-map.html#stable-node)'))
 foreign='.ris/research/plans/foreign.md';(root/foreign).write_text('---\nproject_id: "foreign"\nris_id: "secret-id"\nkind: "plan"\n---\n# Secret title\nSecret prose\n')
 def snapshot():return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
 before=snapshot()
 selections=[(kind,[]) for kind in ('research','knowledge','decision','evidence','plan','learning','strategy')]+[('plan',['--include',plan]),('plan',['--include',foreign])]
 for kind,extra in selections:
  cmd=[sys.executable,str(S/'ris.py'),'--project',name,'view',kind,*extra]
  p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
  value=json.loads(p.stdout);assert 'Secret' not in p.stdout and 'secret-id' not in p.stdout
  results.append({'command':cmd,'returncode':p.returncode,'result':value,'stderr':p.stderr})
 assert snapshot()==before
 assert results[-2]['result']['records'][0]['links'][0]['href']=='../maps/stable-map.html#stable-node'
Path(__file__).with_name('views-cli-results.json').write_text(json.dumps({'controls':results,'project_files_unchanged':True},indent=2))
print(len(results),'CLI controls passed; all project file paths and bytes unchanged')
