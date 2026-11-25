"""Evaluation prototype: trusted controller launches credential-free isolated commands.
No model transport implemented. Product/runtime state comes only from local RIS CLI.
"""
import json,pathlib,subprocess,sys
PACKET=pathlib.Path(__file__).resolve().parent
PROJECT=PACKET/'prototype-project'
PRODUCT=PACKET/'candidate-discovery-projection'
def worker(argv,timeout=15):
 PROJECT.mkdir(exist_ok=True)
 base=['bwrap','--die-with-parent','--unshare-all','--new-session','--clearenv','--ro-bind','/usr','/usr','--ro-bind','/bin','/bin','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--dir','/home','--dir','/home/worker','--setenv','HOME','/home/worker','--setenv','PATH','/usr/bin:/bin','--setenv','PYTHONDONTWRITEBYTECODE','1','--ro-bind',str(PRODUCT),'/product','--bind',str(PROJECT),'/project','--chdir','/project','--']
 p=subprocess.run(base+argv,text=True,capture_output=True,timeout=timeout)
 return {'argv':argv,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
def model_admission(quota,approved_budget,included_only_enforced):
 # Only a broker with an enforced no-paid-spend mechanism may change this prototype.
 return {'allowed':False,'reason':'model transport intentionally absent; budget approval and provider-side included-only enforcement require independent confirmation','quota_observed':quota is not None,'budget_supplied':approved_budget is not None,'control_claimed':bool(included_only_enforced)}
if __name__=='__main__':
 if sys.argv[1:]!=['--probe']:raise SystemExit('Only --probe is implemented; model calls forbidden')
 report=[]
 report.append(worker(['/usr/bin/python3','/product/skills/ris/scripts/ris.py','--project','/project','init','--name','Fresh evaluation prototype','--goal','Controlled two-stage development case']))
 report.append(worker(['/usr/bin/python3','/product/skills/ris/scripts/ris.py','--project','/project','status']))
 sentinel=PACKET/'custodian-only-sentinel';sentinel.write_text('not research data')
 link=PROJECT/'outside-link'
 if not link.exists():link.symlink_to(sentinel)
 code="""import os,json,socket
checks={}
for name,path in [('real_home','/home/moontaehyung'),('credentials','/home/moontaehyung/.codex/auth.json'),('sealed','/home/moontaehyung/ris-verification/sealed-evaluations'),('custodian_symlink','/project/outside-link')]:
 try:open(path).read(1);checks[name]='VISIBLE'
 except OSError:checks[name]='blocked'
try:open('/product/injected','w').write('x');checks['product_write']='ALLOWED'
except OSError:checks['product_write']='blocked'
s=socket.socket();s.settimeout(.2)
try:s.connect(('1.1.1.1',443));checks['network']='ALLOWED'
except OSError:checks['network']='blocked'
print(json.dumps(checks))
assert all(v=='blocked' for v in checks.values())
"""
 report.append(worker(['/usr/bin/python3','-c',code]))
 report.append(model_admission(json.loads((PACKET.parent/'quota.json').read_text()),None,False))
 (PACKET/'worker-controller-probe.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
