#!/usr/bin/env python3
"""Independent synthetic local CLI review; not official E2E."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

SCRIPTS=Path('/home/moontaehyung/plugins/moontaehyung/skills/ris/scripts')
spec=importlib.util.spec_from_file_location('proposal_audit_ris',SCRIPTS/'ris.py')
api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
observations=[]
def cli(root,*args):
 p=subprocess.run([sys.executable,str(SCRIPTS/'ris.py'),'--project',str(root),*args],text=True,capture_output=True)
 try:value=json.loads(p.stdout or p.stderr)
 except ValueError:value={'unparsed':p.stdout or p.stderr}
 return p.returncode,value

def observe(name,passed,details):
 observations.append({'name':name,'status':'PASS' if passed else 'FAIL','details':details})

CASE={'question':'What is load?','model':'load=rate*hours','method':'multiply','assumptions':'fixed rate',
 'boundary':'two hours','limits':'No measured hardware validation','inputs':{'rate':3,'hours':2},
 'units':{'rate':'kW','hours':'h'},'output_units':{'load':'kWh'},'seed':None}
MODEL='import json,sys\np=json.load(open(sys.argv[1]))["inputs"]\nprint(json.dumps({"load":p["rate"]*p["hours"],"debug":"do not promote"}))\n'
with tempfile.TemporaryDirectory(prefix='ris-integrated-proposal-audit-') as tmp:
 base=Path(tmp)
 for schema in (1,2):
  for policy in ('manual','milestones','significant'):
   root=base/f'v{schema}-{policy}';root.mkdir()
   assert cli(root,'init','--recording-policy',policy)[0]==0
   if schema==1:
    cfg=api.config(root);(root/cfg['research_dir']).rename(root/'research')
    cfg.update(schema_version=1,research_dir='research');(root/'.ris/project.yaml').write_text(api.yaml_mapping(cfg))
   (root/'model.py').write_text(MODEL);(root/'case.json').write_text(json.dumps(CASE))
   args=['simulate','--model','model.py','--case','case.json','--record-result','load','integral','load','--expected-revision','0']
   code,result=cli(root,*args)
   allowed=policy=='significant'
   observe(f'v{schema}-{policy}-explicit-policy', (code==0 and result.get('recording')=='PROPOSED') if allowed else code!=0,
           {'code':code,'recording':result.get('recording'),'error':result.get('error')})
   if not allowed:
    code,result=cli(root,*args,'--authorize-record')
    assert code==0 and result['recording']=='PROPOSED',result
   _,context=cli(root,'context','--question','load')
   node=context['knowledge']['proposals'][0]
   expected_conditions={k:CASE[k] for k in ('model','boundary','assumptions')}
   observe(f'v{schema}-{policy}-proposal-conditions-provenance',node['finding']['conditions']==expected_conditions and
           node['finding']['statement']=='load = 6 kWh.' and len(node['finding']['provenance'])==2 and
           all(s['revision'].startswith('sha256:') for s in node['finding']['provenance']) and 'debug' not in json.dumps(node),node)
   _,cold=cli(root,'context','--question','load','--max-chars','1000')
   observe(f'v{schema}-{policy}-projection-budget','knowledge' not in cold and 'knowledge_ref' in cold and bool(cold['warnings']),cold)
   code,replay=cli(root,*args,*([] if allowed else ['--authorize-record']))
   observe(f'v{schema}-{policy}-cas-exact-retry',code==0 and replay.get('findings_revision')==1,{'code':code,'recording':replay.get('recording'),'revision':replay.get('findings_revision')})
   changed=dict(CASE,inputs={'rate':4,'hours':2});(root/'case.json').write_text(json.dumps(changed))
   code,conflict=cli(root,*args,*([] if allowed else ['--authorize-record']))
   observe(f'v{schema}-{policy}-cas-changed-input',code!=0 and conflict.get('recording')=='BLOCKED' and 'pending_proposal' in conflict,conflict)
   _,stale=cli(root,'findings','inspect','--question','load')
   observe(f'v{schema}-{policy}-source-stale',any(c['status']=='STALE' for c in stale['evidence_checks']['integral']),stale['evidence_checks'])
 root=base/'stale-during-run';root.mkdir();cli(root,'init','--recording-policy','significant')
 (root/'case.json').write_text(json.dumps(CASE));(root/'model.py').write_text('import time\ntime.sleep(1)\n'+MODEL)
 args=['simulate','--model','model.py','--case','case.json','--record-result','load','stale','load','--expected-revision','0']
 p=subprocess.Popen([sys.executable,str(SCRIPTS/'ris.py'),'--project',str(root),*args],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 time.sleep(.3);(root/'case.json').write_text(json.dumps(dict(CASE,inputs={'rate':9,'hours':2})))
 stdout,stderr=p.communicate();run=json.loads(stdout or stderr)
 observe('changed-during-execution',p.returncode!=0 and run.get('recording')=='BLOCKED' and 'changed during execution' in run.get('diagnostic',''),run)
 (root/'model.py').write_text('while True: pass\n')
 code,budget=cli(root,'simulate','--model','model.py','--case','case.json','--timeout','1','--record-result','budget','stopped','load','--expected-revision','0')
 observe('budget-stop-not-research-success',code!=0 and budget.get('execution')=='BUDGET_EXHAUSTED',budget)
 _,stopped=cli(root,'findings','inspect','--question','budget')
 nodes=stopped.get('proposals',[])
 observe('budget-proposal-preserves-blocked',len(nodes)==1 and nodes[0]['finding']['status']=='BLOCKED' and nodes[0]['state']=='PROPOSED',nodes)
 # Known legacy external history remains inert through actual read/search surfaces.
 cfg=api.config(root);legacy=root/cfg['research_dir']/'findings'/'knowledge-' + Path('unused') if False else root/cfg['research_dir']/'findings'/'legacy.md'
 legacy.write_text(api.note(cfg['project_id'],'finding','Legacy','CROSS_PROJECT_SENTINEL').replace('kind: "finding"','kind: "finding"\nknowledge_record: true\nsource_project_id: "foreign"\nsource_project_path: "/synthetic-other-project"'))
 for args in [('context','--include',str(legacy.relative_to(root))),('delivery','--source',str(legacy.relative_to(root))),('findings','search','--query','CROSS_PROJECT_SENTINEL')]:
  code,value=cli(root,*args)
  observe('legacy-entry-'+args[0], 'CROSS_PROJECT_SENTINEL' not in json.dumps(value) and '/synthetic-other-project' not in json.dumps(value),{'code':code,'value':value})
 report={'scope':'Independent developer synthetic CLI audit, not official E2E or semantic/scientific acceptance',
         'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in SCRIPTS.glob('ris*.py')},
         'observations':observations,'passed':sum(o['status']=='PASS' for o in observations),'total':len(observations)}
 Path(__file__).with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'passed':report['passed'],'total':report['total'],'failures':[o['name'] for o in observations if o['status']=='FAIL']}))
