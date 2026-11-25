"""No model calls, credentials or network; replay recorded deterministic CLI version probes."""
import json, pathlib, subprocess
packet = pathlib.Path(__file__).resolve().parent
record = json.loads((packet / 'host-compatibility.json').read_text())
for host in ['codex', 'claude']:
    argv = record[host]['argv']
    assert argv[-1] == '--version'
    assert '--unshare-all' in argv and '--clearenv' in argv
    p = subprocess.run(argv, capture_output=True, text=True, timeout=20)
    print(json.dumps({'host': host, 'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}))
    if p.returncode: raise SystemExit(p.returncode)
