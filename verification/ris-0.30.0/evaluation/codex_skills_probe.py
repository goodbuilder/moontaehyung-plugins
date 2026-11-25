"""Offline JSON-RPC initialize + local skills/list only. No thread or turn creation."""
import json,pathlib,subprocess,selectors,time
out=pathlib.Path(__file__).resolve().parent
record=json.loads((out/'host-compatibility.json').read_text())['codex']['argv']
work=out/'isolated-5o9_f8su/work'; (work/'.agents').mkdir(exist_ok=True)
# Actual local project discovery uses .agents/skills. Native plugin catalog remains unregistered.
argv=record[:-1]; idx=argv.index('--');argv[idx:idx]=['--ro-bind',str(out/'candidate-discovery-projection/skills'),'/work/.agents/skills']
argv+=['app-server','--stdio']
p=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
messages=[]; sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ)
def send(value):p.stdin.write(json.dumps(value)+'\n');p.stdin.flush()
def receive(wanted):
 deadline=time.monotonic()+12
 while time.monotonic()<deadline:
  for key,_ in sel.select(.2):
   line=key.fileobj.readline()
   if not line:raise RuntimeError('server closed')
   x=json.loads(line);messages.append(x)
   if x.get('id')==wanted:return x
 raise TimeoutError(wanted)
try:
 send({'id':1,'method':'initialize','params':{'clientInfo':{'name':'offline-evaluation-probe','version':'1'},'capabilities':{'experimentalApi':True}}});receive(1)
 send({'method':'initialized','params':{}})
 send({'id':2,'method':'skills/list','params':{'cwds':['/work'],'forceReload':True}});result=receive(2)
finally:
 p.terminate()
 try:p.wait(timeout=3)
 except subprocess.TimeoutExpired:p.kill();p.wait()
(out/'codex-skills-probe.json').write_text(json.dumps({'argv':argv,'messages':messages,'stderr':p.stderr.read()},indent=2))
print(json.dumps(result)[:1400])
