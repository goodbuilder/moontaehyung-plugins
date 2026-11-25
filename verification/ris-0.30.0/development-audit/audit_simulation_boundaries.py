"""Bounded in-process boundary controls, synthetic temporary inputs only."""
import importlib.util
import json
from pathlib import Path
import tempfile

SCRIPTS = Path('/home/moontaehyung/plugins/moontaehyung/skills/ris/scripts')
def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
simulation = load('ris_simulation')
isolated = load('ris_isolated')
results = []
class API:
    class Error(Exception): pass
    def __init__(self, mutate=False): self.calls=0; self.mutate=mutate
    def inside(self, root, relative):
        self.calls += 1
        path = root/relative
        if self.mutate and self.calls==2:
            path.write_text('revision changed')
        return path
with tempfile.TemporaryDirectory(prefix='ris-independent-boundaries-') as name:
    root=Path(name)
    (root/'model.py').write_text('print(1)')
    original=simulation.read_input(API(),root,'model.py','.py')
    assert original==b'print(1)'
    results.append({'control':'positive_frozen_bytes','pass':True})
    try:
        simulation.read_input(API(mutate=True),root,'model.py','.py')
        raise AssertionError('changed input accepted')
    except API.Error as exc:
        assert 'changed' in str(exc)
        results.append({'control':'input_revision_change_rejected','pass':True,'diagnostic':str(exc)})
    (root/'oversize.py').write_bytes(b' '*(simulation.MAX_INPUT+1))
    try:
        simulation.read_input(API(),root,'oversize.py','.py')
        raise AssertionError('oversize input accepted')
    except API.Error as exc:
        results.append({'control':'oversize_input_rejected','pass':True,'diagnostic':str(exc)})
original_which = isolated.shutil.which
isolated.shutil.which=lambda _: None
try:
    isolated.python_namespace()
    raise AssertionError('unsafe isolation fallback')
except RuntimeError as exc:
    results.append({'control':'missing_namespace_fail_closed','pass':True,'diagnostic':str(exc)})
finally:
    isolated.shutil.which=original_which
Path(__file__).with_name('simulation-boundaries.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
