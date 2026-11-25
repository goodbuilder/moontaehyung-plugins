"""Local synthetic execution only; namespace availability is an explicit requirement."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
spec = importlib.util.spec_from_file_location('ris_isolated', SCRIPTS / 'ris_isolated.py')
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


def test_namespace_isolates_sibling_and_host_context(tmp_path):
    project = tmp_path / 'project'
    project.mkdir()
    sibling = tmp_path / 'other-project'
    sibling.mkdir()
    (sibling / 'private.txt').write_text('synthetic cross-project sentinel')
    (project / 'escape').symlink_to(sibling)
    cmd = launcher.command(project, ['init'])
    initialized = subprocess.run(cmd, text=True, capture_output=True)
    assert initialized.returncode == 0, initialized.stderr
    # Run a synthetic probe in the exact same namespace and clean process environment.
    index = cmd.index('/usr/bin/python3')
    probe = '''import os,json,pathlib
print(json.dumps({'sibling':pathlib.Path(%r).exists(),
 'escape':pathlib.Path('/project/escape/private.txt').exists(),
 'host_home':pathlib.Path(%r).exists(), 'home':os.environ['HOME'],
 'secret_env':os.environ.get('RIS_SYNTHETIC_SECRET'),
 'project':pathlib.Path('/project/.ris').is_dir()}))''' % (str(sibling), str(Path.home()))
    result = subprocess.run(cmd[:index] + ['/usr/bin/python3', '-c', probe],
                            env={'RIS_SYNTHETIC_SECRET': 'synthetic'}, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    values = json.loads(result.stdout)
    assert values == {'sibling': False, 'escape': False, 'host_home': False,
                      'home': '/home/ris', 'secret_env': None, 'project': True}
    context = subprocess.run([sys.executable, str(SCRIPTS / 'ris_isolated.py'),
                              '--project', str(project), '--', 'context'],
                             text=True, capture_output=True)
    assert context.returncode == 0, context.stderr


def test_model_preflight_never_claims_clean_host_and_detects_legacy(tmp_path):
    project = tmp_path / 'project'
    project.mkdir()
    initialized = subprocess.run(launcher.command(project, ['init']), capture_output=True, text=True)
    assert initialized.returncode == 0, initialized.stderr
    clean = launcher.model_workspace_eligibility(project)
    assert clean['model_execution_eligible'] is False
    assert clean['status'] == 'host_context_not_verified'
    legacy = project / 'legacy.md'
    legacy.write_text('---\nproject_id: "foreign"\nsource_project_id: "other"\n---\nHistorical body')
    before = legacy.read_bytes()
    nested = project / 'nested'
    (nested / '.ris').mkdir(parents=True)
    result = launcher.model_workspace_eligibility(project)
    assert result['status'] == 'requires_curated_mount'
    assert set(result['known_contamination']) >= {'external_provenance', 'foreign_project_metadata', 'nested_project'}
    assert legacy.read_bytes() == before
