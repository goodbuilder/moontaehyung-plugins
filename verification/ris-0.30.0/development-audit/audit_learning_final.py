"""S16/S17 registered CLI evidence using disposable general profile only."""
import json,os,subprocess,sys,tempfile
from pathlib import Path
CLI='/home/moontaehyung/plugins/moontaehyung/skills/ris/scripts/ris.py'
records=[]
def run(label,*args,env=None):
 command=[sys.executable,CLI,'learning',*map(str,args)]
 p=subprocess.run(command,capture_output=True,text=True,env=env)
 assert p.returncode==0,p.stderr
 result=json.loads(p.stdout)
 records.append({'scenario':label,'command':command,'returncode':p.returncode,'result':result,'stderr':p.stderr})
 return result
confirmed={'level':'confirmed','evidence':'demonstration-confirmed-by-user','confirmed_at':'2026-01-01T00:00:00Z'}
for dimension in ('definition','calculation','application','limits','transfer'):
 dims={d:dict(confirmed) for d in ('definition','explanation','calculation','application','limits')}
 if dimension!='transfer':dims[dimension]={'level':'unknown','evidence':'none','confirmed_at':None}
 view=json.dumps({'schema':1,'consent':'general-concepts-only-v1','concepts':{'uncertainty':dims}})
 value=run('S16-'+dimension,'lesson','--mode','assist','--requested','--concept','uncertainty','--dimension-view',view)
 assert value['focus_dimension']==dimension
run('S16-delegated-no-teaching','lesson','--mode','delegated','--requested','--concept','uncertainty','--dimension-view',view)
with tempfile.TemporaryDirectory(prefix='ris-s17-profile-') as directory:
 root=Path(directory);root.chmod(0o700);path=root/'learning-profile.json'
 env=dict(os.environ,RIS_LEARNING_PROFILE_ROOT=directory)
 value=run('S17-consent','create','--profile',path,'--consent','general-concepts-only-v1',env=env)
 for concept,dimension in [('uncertainty','definition'),('uncertainty','limits'),('causality','application')]:
  value=run('S17-explicit-set','set','--profile',path,'--expected-hash',value['profile_hash'],'--concept',concept,'--dimension',dimension,'--level','learning','--evidence','self-report',env=env)
 value=run('S17-erase-one-dimension','erase','--profile',path,'--expected-hash',value['profile_hash'],'--concept','uncertainty','--dimension','definition',env=env)
 assert set(value['profile']['concepts']['uncertainty'])=={'limits'} and 'causality' in value['profile']['concepts']
 value=run('S17-erase-one-concept','erase','--profile',path,'--expected-hash',value['profile_hash'],'--concept','uncertainty',env=env)
 assert set(value['profile']['concepts'])=={'causality'}
 value=run('S17-inspect-retained','inspect','--profile',path,env=env)
 run('S17-delete-disposable','delete','--profile',path,'--expected-hash',value['profile_hash'],env=env)
Path(__file__).with_name('learning-S16-S17-final-results.json').write_text(json.dumps(records,indent=2))
print(len(records),'registered CLI controls passed')
