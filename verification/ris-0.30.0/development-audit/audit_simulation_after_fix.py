"""Independent synthetic local CLI audit; no external calls or real input data."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

BASE = Path('/home/moontaehyung/plugins/moontaehyung')
CLI = BASE/'skills/ris/scripts/ris.py'
OUT = Path(__file__).parent
records = []
def run(name, argv, **kwargs):
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=75, **kwargs)
    entry = {'name': name, 'command': argv, 'returncode': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr}
    try:
        entry['parsed'] = json.loads(proc.stdout)
    except ValueError:
        pass
    records.append(entry)
    return entry

with tempfile.TemporaryDirectory(prefix='ris-independent-simulation-') as directory:
    root = Path(directory)/'project'
    root.mkdir()
    sibling = Path(directory)/'other-project'
    sibling.mkdir()
    sentinel = sibling/'synthetic-private.txt'
    sentinel.write_text('synthetic sentinel only')
    run('initialize_synthetic_project', [sys.executable, str(CLI), '--project', str(root), 'init'])
    model = root/'model.py'
    case = root/'case.json'
    case_value = {'question':'synthetic arithmetic', 'model':'y=2*x', 'method':'direct multiplication',
                  'assumptions':'exact integer input', 'boundary':'synthetic check only', 'limits':'not real scientific validation',
                  'inputs':{'x':3}, 'units':{'x':'dimensionless'}, 'seed':None}
    case.write_text(json.dumps(case_value))
    def simulate(name, source, timeout=3):
        model.write_text(source)
        before = {'model':hashlib.sha256(model.read_bytes()).hexdigest(), 'case':hashlib.sha256(case.read_bytes()).hexdigest()}
        item = run(name, [sys.executable, str(CLI), '--project', str(root), 'simulate', '--model', 'model.py', '--case', 'case.json', '--timeout', str(timeout)])
        item['input_hashes_before'] = before
        item['inputs_unchanged'] = all(hashlib.sha256((root/(k+'.py' if k=='model' else k+'.json')).read_bytes()).hexdigest()==v for k,v in before.items())
        return item
    simulate('positive_numerical_process', "import json,sys,os\nc=json.load(open(sys.argv[1])); print(json.dumps({'y':2*c['inputs']['x'],'pid':os.getpid()}))\n")
    simulate('protected_input_and_namespace', "import os,json,pathlib\np=pathlib.Path('/inputs/case.json')\ntry:\n p.write_text('mutated')\n protected=False\nexcept OSError:\n protected=True\nprint(json.dumps({'input_readonly':protected,'sibling_visible':pathlib.Path("+repr(str(sentinel))+").exists(),'host_home_visible':pathlib.Path('/home/moontaehyung').exists(),'host_env':os.environ.get('RIS_SYNTHETIC_SECRET'),'cwd':os.getcwd(),'python':__import__('sys').version.split()[0]}))\n")
    simulate('wall_budget_exhaustion', 'import time\ntime.sleep(10)\n', timeout=1)
    simulate('cpu_budget_exhaustion', 'while True: pass\n', timeout=1)
    simulate('output_budget_exhaustion', "import sys\nsys.stdout.write('x'*400000);sys.stdout.flush()\n")
    simulate('model_error', "raise RuntimeError('synthetic controlled failure')\n")
    simulate('invalid_output_json', "print('not JSON')\n")
    simulate('nonfinite_output', "print('{\"value\":NaN}')\n")
    simulate('empty_output_object', "print('{}')\n")
    case.write_text('{}')
    simulate('invalid_case_contract', "print('{\"y\":6}')\n")
    case.write_text(json.dumps(case_value))
    run('outside_project_input_rejected', [sys.executable, str(CLI), '--project', str(root), 'simulate', '--model', str(sentinel), '--case', 'case.json'])
    model.unlink()
    model.symlink_to(sentinel)
    run('outside_project_symlink_rejected', [sys.executable, str(CLI), '--project', str(root), 'simulate', '--model', 'model.py', '--case', 'case.json'])
    assert sentinel.read_text() == 'synthetic sentinel only'
(OUT/'simulation-results-after-output-fix.json').write_text(json.dumps(records, indent=2))
for item in records:
    result = item.get('parsed', {})
    print(item['name'], item['returncode'], result.get('execution'), result.get('result'), result.get('diagnostic', '')[:100])
