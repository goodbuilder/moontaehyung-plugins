"""Offline host metadata only. Requires explicit final archive digest; never starts a turn.
Fresh output directory per invocation; no auth, live configuration, installed-plugin or source writes.
"""
import argparse, hashlib, json, os, pathlib, selectors, subprocess, tarfile, tempfile, time, zipfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(archive, destination):
    def target(name):
        p = pathlib.PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or any(part in {'.aws', '.git'} for part in p.parts):
            raise ValueError('Unsafe archive member')
        return destination.joinpath(*p.parts)
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as z:
            for item in z.infolist():
                p = target(item.filename)
                if (item.external_attr >> 16) & 0o170000 == 0o120000: raise ValueError('Symlink refused')
                if item.is_dir(): p.mkdir(parents=True, exist_ok=True)
                else:
                    p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(z.read(item))
    else:
        with tarfile.open(archive) as t:
            for item in t:
                p = target(item.name)
                if item.isdir(): p.mkdir(parents=True, exist_ok=True)
                elif item.isfile():
                    p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(t.extractfile(item).read())
                else: raise ValueError('Only archive files/directories allowed')


def probe(argv):
    try:
        p = subprocess.run(argv, text=True, capture_output=True, timeout=25)
        return {'argv': argv, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    except subprocess.TimeoutExpired:
        return {'argv': argv, 'exit': 'timeout'}


def rpc_probe(argv):
    p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    seen = []; sel = selectors.DefaultSelector(); sel.register(p.stdout, selectors.EVENT_READ)
    def send(v): p.stdin.write(json.dumps(v)+'\n'); p.stdin.flush()
    def receive(id):
        end = time.monotonic()+15
        while time.monotonic() < end:
            for key, _ in sel.select(.2):
                line = key.fileobj.readline()
                if not line: raise RuntimeError('RPC closed')
                value = json.loads(line); seen.append(value)
                if value.get('id') == id: return value
        raise TimeoutError('offline read timed out')
    error = None
    try:
        send({'id': 1, 'method': 'initialize', 'params': {'clientInfo': {'name': 'final-offline-discovery', 'version': '1'}, 'capabilities': {'experimentalApi': True}}}); receive(1)
        send({'method': 'initialized', 'params': {}})
        send({'id': 2, 'method': 'skills/list', 'params': {'cwds': ['/work'], 'forceReload': True}}); receive(2)
        send({'id': 3, 'method': 'config/read', 'params': {'includeLayers': False, 'cwd': '/work'}}); receive(3)
    except Exception as exc:
        error = type(exc).__name__ + ': ' + str(exc)
    finally:
        p.terminate()
        try: p.wait(timeout=3)
        except subprocess.TimeoutExpired: p.kill(); p.wait()
    return {'argv': argv, 'messages': seen, 'error': error, 'stderr': p.stderr.read(),
            'model_requests': 0, 'allowed_methods': ['initialize', 'initialized', 'skills/list', 'config/read']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=pathlib.Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--manifest', type=pathlib.Path, required=True)
    args = parser.parse_args()
    archive = args.archive.resolve()
    if digest(archive) != args.sha256: raise SystemExit('Final archive SHA256 mismatch; no host started')
    packet = pathlib.Path(__file__).resolve().parent
    run = pathlib.Path(tempfile.mkdtemp(prefix='final-', dir=packet))
    extracted = run/'source'; extracted.mkdir(); extract(archive, extracted)
    roots = [p.parent.parent for p in extracted.rglob('.codex-plugin/plugin.json') if (p.parent.parent/'.claude-plugin/plugin.json').is_file()]
    if len(roots) != 1: raise SystemExit('Expected one dual-host product root')
    product = roots[0]
    tree = {str(p.relative_to(product)): digest(p) for p in sorted(product.rglob('*')) if p.is_file()}
    expected = json.loads(args.manifest.read_text())
    if not isinstance(expected, dict) or expected != tree:
        raise SystemExit('Source files do not exactly match supplied flat manifest; no host started')
    (run/'source-manifest.json').write_text(json.dumps(tree, indent=2))
    results = {'archive_sha256': args.sha256, 'source_tree_manifest_sha256': digest(run/'source-manifest.json'),
               'model_requests': 0, 'network': 'unshare-all; no network', 'live_home_mounted': False,
               'script_sha256': digest(pathlib.Path(__file__).resolve()),
               'supplied_source_manifest_sha256': digest(args.manifest), 'source_manifest_exact_match': True, 'hosts': {}}
    for host in ['codex', 'claude']:
        home=run/(host+'-home'); work=run/(host+'-work'); home.mkdir();work.mkdir()
        (work/'.agents').mkdir();(work/'.codex').mkdir()
        base=['bwrap','--die-with-parent','--unshare-all','--new-session','--clearenv','--ro-bind','/usr','/usr','--ro-bind','/bin','/bin','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--dir','/home','--bind',str(home),'/home/worker','--bind',str(work),'/work','--ro-bind',str(product),'/product','--ro-bind',str(product/'skills'),'/work/.agents/skills','--ro-bind',str(product/'agents'),'/work/.codex/agents','--chdir','/work','--setenv','HOME','/home/worker','--setenv','PATH','/usr/bin:/bin','--setenv','LANG','C.UTF-8','--setenv','PYTHONDONTWRITEBYTECODE','1']
        if host == 'claude':
            native = pathlib.Path('/home/moontaehyung/.local/bin/claude').resolve()
            command = base+['--ro-bind',str(native),'/opt/claude','--','/opt/claude']
            results['hosts'][host]={'version':probe(command+['--version']),
                'validation':probe(command+['plugin','validate','/product']),
                'agents_help':probe(command+['--plugin-dir','/product','agents','--help']),
                'agents_metadata':probe(command+['--plugin-dir','/product','agents','--json']),
                'local_details':probe(command+['--plugin-dir','/product','plugin','details','moontaehyung'])}
        else:
            package=pathlib.Path('/home/moontaehyung/.codex/npm-global')
            command=base+['--ro-bind',str(package),'/opt/codex','--','/usr/bin/node','/opt/codex/lib/node_modules/@openai/codex/bin/codex.js']
            role_args=[]
            for role in sorted((product/'agents').glob('*.toml')):
                role_args+=['-c','agents.'+role.stem+'.config_file='+json.dumps('/product/agents/'+role.name)]
            server=command+['--no-daemon','--disable','hooks','--disable','apps','-c','mcp_servers={}']+role_args+['app-server','--stdio']
            results['hosts'][host]={'version':probe(command+['--version']), 'local_rpc':rpc_probe(server)}
    after={str(p.relative_to(product)):digest(p) for p in sorted(product.rglob('*')) if p.is_file()}
    results['source_unchanged']=tree==after
    results['archive_still_matches']=digest(archive)==args.sha256
    results['limits']=['Native metadata/discovery only, not role execution.', 'Claude agents subcommand may list background sessions rather than product role definitions; inspect actual output.', 'No slash-command turn was sent, so runtime /skill dispatch is NOT_RUN.', 'Codex repo skills projection is not installed-plugin enrollment.', 'No auth/network/model/provider billing behavior tested.']
    (run/'host-results.json').write_text(json.dumps(results,indent=2))
    print(str(run/'host-results.json'))

if __name__=='__main__':main()
