"""Read process registration through initialize control; never send user/turn messages."""
import argparse,json,pathlib,selectors,subprocess,time,hashlib
p=argparse.ArgumentParser();p.add_argument('--host-results',type=pathlib.Path,required=True);a=p.parse_args()
x=json.loads(a.host_results.read_text());r=a.host_results.resolve().parent
argv=x['hosts']['claude']['validation']['argv'][:-3]+['--plugin-dir','/product','-p','--input-format','stream-json','--output-format','stream-json','--verbose']
assert argv.count('--unshare-all')==1 and '--clearenv' in argv
request={'type':'control_request','request_id':'final-local-init-only','request':{'subtype':'initialize'}}
proc=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1);events=[];error=None
sel=selectors.DefaultSelector();sel.register(proc.stdout,selectors.EVENT_READ)
try:
 proc.stdin.write(json.dumps(request)+'\n');proc.stdin.flush();end=time.monotonic()+15
 while time.monotonic()<end:
  if not sel.select(.2):
   if proc.poll() is not None:break
   continue
  line=proc.stdout.readline()
  if not line:break
  event=json.loads(line)
  if event.get('type')=='control_response':
   response=event.get('response',{});payload=response.get('response',{})
   events.append({'type':'control_response','subtype':response.get('subtype'),'request_id':response.get('request_id'),'error':response.get('error'),'payload':{k:payload[k] for k in ['agents','commands','claude_code_version','output_style'] if k in payload},'payload_keys':sorted(payload)})
   break
  events.append({'type':event.get('type'),'subtype':event.get('subtype')})
except Exception as e:error=repr(e)
finally:
 proc.terminate()
 try:proc.wait(timeout=3)
 except subprocess.TimeoutExpired:proc.kill();proc.wait()
result={'argv':argv,'sent':[request],'events':events,'error':error,'stderr':proc.stderr.read(),'model_messages_sent':0,'auth_mounted':False,'network':'unshare-all disabled','archive_sha256':x['archive_sha256'],'source_manifest_sha256':x['supplied_source_manifest_sha256'],'script_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()}
output=r/'claude-initialize-registration.json'
if output.exists():raise SystemExit('Refuse to overwrite evidence')
output.write_text(json.dumps(result,indent=2));print(str(output))
