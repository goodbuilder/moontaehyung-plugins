"""Process-level registration probe: initialize control only; never sends user messages/turns."""
import hashlib,json,pathlib,selectors,shutil,subprocess,tempfile,time,tarfile
BASE=pathlib.Path(__file__).resolve().parent
RUN=pathlib.Path(tempfile.mkdtemp(prefix='claude-registration-',dir=BASE))
old=BASE/'final-qbed690o'
original=json.loads((old/'host-results.json').read_text())['hosts']['claude']['validation']['argv']
variants={'candidate':old/'source/moontaehyung'}
archive=RUN/'baseline-007ee7f.tar'
with archive.open('wb') as f:subprocess.run(['git','-C','/home/moontaehyung/plugins/moontaehyung','archive','007ee7ff2d727e813ba59584abc80e7b1c002e74'],stdout=f,check=True)
baseline=RUN/'baseline';baseline.mkdir()
with tarfile.open(archive) as t:
 for m in t:
  p=baseline/m.name
  if m.isdir():p.mkdir(parents=True,exist_ok=True)
  elif m.isfile():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.extractfile(m).read())
  else:raise RuntimeError('Nonregular baseline member')
variants['baseline-0.29']=baseline
for kind in ['default','explicit']:
 root=RUN/('control-'+kind);(root/'.claude-plugin').mkdir(parents=True);(root/'agents').mkdir()
 body={'name':'registration-control','version':'1.0.0','description':'No-model registration probe'}
 if kind=='explicit':body['agents']=['./agents/known-good.md']
 (root/'.claude-plugin/plugin.json').write_text(json.dumps(body))
 (root/'agents/known-good.md').write_text('---\nname: known-good\ndescription: Local discovery control, never execute.\nmodel: inherit\n---\nReturn no result; metadata only.\n')
 variants['control-'+kind]=root
results={}
for name,product in variants.items():
 home=RUN/(name+'-home');home.mkdir();work=RUN/(name+'-work');work.mkdir();(work/'.agents').mkdir();(work/'.codex').mkdir()
 argv=original.copy()
 # Rebuild explicit allowlist from known fixed mounts; no source root or host HOME mount.
 argv=['bwrap','--die-with-parent','--unshare-all','--new-session','--clearenv','--ro-bind','/usr','/usr','--ro-bind','/bin','/bin','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--dir','/home','--bind',str(home),'/home/worker','--bind',str(work),'/work','--ro-bind',str(product),'/product','--ro-bind','/home/moontaehyung/.local/share/claude/versions/2.1.331','/opt/claude','--chdir','/work','--setenv','HOME','/home/worker','--setenv','PATH','/usr/bin:/bin','--setenv','LANG','C.UTF-8','--','/opt/claude','--plugin-dir','/product','-p','--input-format','stream-json','--output-format','stream-json','--verbose']
 request={'type':'control_request','request_id':'local-init-only','request':{'subtype':'initialize'}}
 p=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
 events=[];error=None;sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ)
 try:
  p.stdin.write(json.dumps(request)+'\n');p.stdin.flush();end=time.monotonic()+15
  while time.monotonic()<end:
   ready=sel.select(.2)
   if not ready:
    if p.poll() is not None:break
    continue
   line=p.stdout.readline()
   if not line:break
   event=json.loads(line)
   # No account fields retained; namespace has no auth or account settings.
   if event.get('type')=='control_response':
    resp=event.get('response',{});payload=resp.get('response',{})
    events.append({'type':'control_response','subtype':resp.get('subtype'),'request_id':resp.get('request_id'),'error':resp.get('error'),'payload':{k:payload[k] for k in ['agents','commands','claude_code_version','output_style'] if k in payload},'payload_keys':sorted(payload)})
    break
   events.append({'type':event.get('type'),'subtype':event.get('subtype')})
 except Exception as exc:error=repr(exc)
 finally:
  p.terminate()
  try:p.wait(timeout=3)
  except subprocess.TimeoutExpired:p.kill();p.wait()
 results[name]={'argv':argv,'sent':[request],'events':events,'error':error,'stderr':p.stderr.read(),'model_messages_sent':0,'network':'disabled','auth_mounted':False}
 (RUN/'registration-results.json').write_text(json.dumps(results,indent=2))
 print(name,json.dumps(events)[:5000],error,flush=True)
print(str(RUN/'registration-results.json'))
