"""Read public client quota status without exposing balance amounts, identity, tokens, or credentials."""
import hashlib,json,subprocess,sys,selectors,time,tempfile,os
from pathlib import Path
root=Path(__file__).resolve().parent
def read_quota():
    target=Path(tempfile.mkdtemp(prefix='quota-read-',dir=root))
    env={k:os.environ[k] for k in ('HOME','PATH','LANG','USER') if k in os.environ}
    env['CODEX_SQLITE_HOME']=str(target/'db')
    (target/'db').mkdir(exist_ok=True)
    binpath=next((Path.home()/'.codex/npm-global').glob('**/vendor/*/bin/codex'))
    cmd=[str(binpath),'--no-daemon','--disable','hooks','--disable','apps','--disable','plugins','-c','mcp_servers={}','-c','sqlite_home='+json.dumps(str(target/'db')),'-c','log_dir='+json.dumps(str(target/'log')),'app-server','--stdio']
    isolated_config=target/'config.toml'
    if not isolated_config.exists():isolated_config.write_text('')
    prefix=['bwrap','--die-with-parent','--bind','/','/','--dev','/dev','--tmpfs','/tmp','--bind',str(target),str(target)]
    for n in ('sessions','skills','plugins','rules','memories'):
        loc=Path.home()/'.codex'/n
        if loc.is_dir():prefix+=['--tmpfs',str(loc)]
    prefix+=['--ro-bind',str(isolated_config),str(Path.home()/'.codex/config.toml'),'--chdir',str(target),'--']
    with subprocess.Popen(prefix+cmd,cwd=target,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=(target/'probe.stderr').open('w'),text=True,bufsize=1) as p:
        try:
            def send(j):p.stdin.write(json.dumps(j)+'\n');p.stdin.flush()
            def recv(i):
                sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ)
                t=time.monotonic()+45
                while time.monotonic()<t and sel.select(max(.01,t-time.monotonic())):
                    a=p.stdout.readline()
                    if not a:break
                    v=json.loads(a)
                    if v.get('id')==i:return v
                raise RuntimeError('no quota response')
            send({'id':1,'method':'initialize','params':{'clientInfo':{'name':'ris_observe','version':'1'},'capabilities':{}}})
            recv(1);send({'method':'initialized','params':{}})
            send({'id':2,'method':'account/rateLimits/read','params':{}})
            result=recv(2)
            if 'error' in result:raise RuntimeError('quota unavailable: '+str(result['error'].get('code')))
            rates=result['result'].get('rateLimits') or result['result'].get('rate_limits')
            c=rates.get('credits') or {};windows=[w for w in [rates.get('primary'),rates.get('secondary')] if w]
            raw=result['result']
            return {'at':time.time(),'windows':windows,'ordinaryUsageAllowed':raw.get('ordinaryUsageAllowed'),'hasCredits':c.get('hasCredits'),'unlimitedCredits':c.get('unlimited'),'balanceObservable':c.get('balance') is not None,'creditBalancePositive':(float(c['balance'])>0) if c.get('balance') is not None else None,'spendControlReached':rates.get('spendControlReached'),'rateLimitReachedType':rates.get('rateLimitReachedType'),'responseFieldNames':sorted(raw),'creditFieldNames':sorted(c)}
        finally:p.terminate()
if __name__=='__main__':print(json.dumps(read_quota()))
