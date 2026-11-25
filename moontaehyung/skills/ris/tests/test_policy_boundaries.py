import hashlib
import json
from pathlib import Path
import subprocess
import sys

RIS = Path(__file__).resolve().parents[1] / 'scripts' / 'ris.py'


def cli(project, *command):
    return subprocess.run([sys.executable, str(RIS), '--project', str(project), *map(str, command)],
                          capture_output=True, text=True)


def test_significant_default_and_legacy_consent(tmp_path):
    project = tmp_path/'local'
    project.mkdir()
    assert json.loads(cli(project, 'init', '--dry-run').stdout)['recording_policy'] == 'significant'
    assert not (project/'.ris').exists()
    assert cli(project,'init','--recording-policy','manual').returncode == 0
    config = project/'.ris/project.yaml'
    before = config.read_bytes()
    assert cli(project,'init','--recording-policy','significant').returncode != 0
    assert cli(project,'init').returncode == 0 and config.read_bytes() == before
    assert cli(project,'configure','--recording-policy','significant','--expected-hash','old').returncode != 0
    assert cli(project,'configure','--recording-policy','significant','--expected-hash',
               hashlib.sha256(before).hexdigest()).returncode == 0
    assert before in [path.read_bytes() for path in (project/'.ris/history').glob('*.yaml')]


def test_no_import_from_foreign_nested_or_external_sources(tmp_path):
    a = tmp_path/'A'
    b = tmp_path/'B'
    a.mkdir()
    b.mkdir()
    local_id = json.loads(cli(a,'init').stdout)['project_id']
    other_id = json.loads(cli(b,'init').stdout)['project_id']
    assert local_id != other_id
    (b/'body.txt').write_text('fixture-private-other-project')
    reject = cli(a,'record','--kind','finding','--title','no','--body-file',b/'body.txt')
    assert reject.returncode != 0 and 'fixture-private' not in reject.stdout
    nested = a/'other'
    nested.mkdir()
    assert cli(nested, 'init').returncode == 0
    (nested/'body.txt').write_text('fixture-private-nested-project')
    assert cli(a,'record','--kind','finding','--title','no','--body-file','other/body.txt').returncode != 0
    foreign = a/'imported.md'
    foreign.write_text(f'---\nproject_id: "{other_id}"\n---\n<!-- ris:deliver -->\nprivate-fixture\n<!-- /ris:deliver -->\n')
    reply = cli(a,'delivery','--source','imported.md')
    assert reply.returncode != 0 and 'private-fixture' not in reply.stdout
    assert not list((a/'.ris/research/findings').iterdir())
