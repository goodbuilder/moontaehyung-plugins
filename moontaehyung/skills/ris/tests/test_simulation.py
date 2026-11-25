"""A controlled design calculation through the installed CLI interface."""
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

RIS = Path(__file__).resolve().parents[1] / 'scripts' / 'ris.py'
pytestmark = pytest.mark.skipif(not shutil.which('bwrap'), reason='Linux bubblewrap runtime required')

# Euler integration intentionally differs from the closed-form acceptance oracle.
MODEL = '''import json, sys
p = json.load(open(sys.argv[1]))["inputs"]
if min(p["capacitance"], p["duration"], *p["resistance"]) <= 0:
    sys.exit("nonpositive thermal parameters")
temperatures = []
for resistance in p["resistance"]:
    temperature = p["ambient"]
    dt = p["duration"] / 50000
    for _ in range(50000):
        temperature += dt * (p["power"] - (temperature-p["ambient"])/resistance) / p["capacitance"]
    temperatures.append(temperature)
print(json.dumps({"temperatures_C": temperatures}))
'''


def command(project, *args):
    run = subprocess.run([sys.executable, str(RIS), '--project', str(project), *args],
                         text=True, capture_output=True)
    return run.returncode, json.loads(run.stdout or run.stderr)


def test_design_sensitivity_revision_and_failure(tmp_path):
    assert command(tmp_path, 'init')[0] == 0
    (tmp_path / 'model.py').write_text(MODEL)
    spec = dict(question='Which insulation keeps the load below 50 C at 60 s?',
                model='C dT/dt = P - (T-Ta)/R', method='forward Euler, 50000 steps',
                assumptions='lumped thermal mass, constant parameters',
                boundary='T(0)=Ta, ambient fixed', limits='No measured hardware validation',
                inputs=dict(capacitance=10, power=20, duration=60, ambient=20,
                            resistance=[1, 2]),
                units=dict(capacitance='J/K', power='W', duration='s', ambient='degC',
                           resistance='K/W'), seed=None)
    def simulate():
        (tmp_path / 'case.json').write_text(json.dumps(spec))
        return command(tmp_path, 'simulate', '--model', 'model.py', '--case', 'case.json')
    code, first = simulate()
    assert code == 0 and first['execution'] == 'EXECUTED'
    exact = [20 + 20*r*(1-math.exp(-60/(10*r))) for r in [1, 2]]
    assert first['result']['temperatures_C'] == pytest.approx(exact, abs=.0003)
    assert [t < 50 for t in exact] == [True, False]
    assert simulate()[1]['output_sha256'] == first['output_sha256']
    spec['inputs']['power'] = 12
    _, changed = simulate()
    assert changed['case'] != first['case'] and changed['model'] == first['model']
    assert all(t < 50 for t in changed['result']['temperatures_C'])
    spec['inputs']['capacitance'] = 0
    code, stopped = simulate()
    assert code != 0 and stopped['execution'] == 'FAILED' and 'result' not in stopped


def test_result_record_and_cold_resume(tmp_path):
    command(tmp_path, 'init')
    model = tmp_path / 'load.py'
    model.write_text('import json,sys\np=json.load(open(sys.argv[1]))["inputs"]\n'
                     'print(json.dumps({"load":p["rate"]*p["hours"],"debug":"not a finding"}))\n')
    case = dict(question='What is total load?', model='load = rate × hours', method='multiply',
                assumptions='fixed rate', boundary='two hours', limits='constant-rate model',
                inputs={'hours':2, 'rate':3}, units={'hours':'h', 'rate':'kW'},
                output_units={'load':'kWh'}, seed=None)
    (tmp_path / 'load.json').write_text(json.dumps(case))
    args = ['simulate', '--model','load.py','--case','load.json','--record-result',
            'load','integral','load','--expected-revision','0']
    code, run = command(tmp_path,*args)
    assert code == 0 and run['recording'] == 'PROPOSED'
    code, resume = command(tmp_path, 'context','--question','load')
    node = resume['knowledge']['proposals'][0]
    assert node['state'] == 'PROPOSED'
    assert node['finding']['statement'] == 'load = 6 kWh.'
    assert node['finding']['axes']['result_sha256'] == run['output_sha256']
    assert 'debug' not in json.dumps(node)
    assert command(tmp_path,*args)[1]['findings_revision'] == 1
    case['inputs']['rate'] = 4
    (tmp_path / 'load.json').write_text(json.dumps(case))
    code, conflict = command(tmp_path,*args)
    assert code == 1 and conflict['recording'] == 'BLOCKED' and conflict['result']['load'] == 8
    _, inspect = command(tmp_path,'findings','inspect','--question','load')
    assert any(check['status']=='STALE' for check in inspect['evidence_checks']['integral'])
