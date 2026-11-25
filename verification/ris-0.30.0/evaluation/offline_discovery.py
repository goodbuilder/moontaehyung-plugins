"""Read-only installed CLI discovery in explicit mount allowlist. Never invokes a model."""
import hashlib,json,pathlib,shutil,subprocess
out=pathlib.Path(__file__).resolve().parent
src=pathlib.Path('/home/moontaehyung/plugins/moontaehyung'); projection=out/'candidate-discovery-projection'
if projection.exists():raise SystemExit('Refuse to overwrite discovery snapshot')
projection.mkdir()
for name in ['skills','agents','templates','references','.claude-plugin','.codex-plugin']:
 if (src/name).exists():shutil.copytree(src/name,projection/name,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
manifest={str(p.relative_to(projection)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(projection.rglob('*')) if p.is_file()}
(out/'candidate-discovery-manifest.json').write_text(json.dumps(manifest,indent=2))
base=json.loads((out/'host-compatibility.json').read_text())
results={}
for host, tail in [('claude',['plugin','validate','/product']),('codex',['--ignore-user-config','plugin','list'])]:
 argv=base[host]['argv']; cut=argv.index('--'); argv=argv[:cut]+['--ro-bind',str(projection),'/product']+argv[cut:]; argv[-1:]=tail
 p=subprocess.run(argv,capture_output=True,text=True,timeout=30)
 results[host]={'argv':argv,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
(out/'offline-discovery.json').write_text(json.dumps(results,indent=2)); print(json.dumps(results,indent=2))
