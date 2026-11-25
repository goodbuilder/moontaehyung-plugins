"""Exercise delivery through the public CLI, including its read-only boundary."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import pytest

CLI = Path(__file__).resolve().parents[1] / 'scripts' / 'ris.py'
BLOCK = '<!-- ris:deliver -->\n실측은 3개뿐이다. 신뢰구간은 미확인이다.\n<!-- /ris:deliver -->\n'


def run(root, *args, stdin=None):
    return subprocess.run([sys.executable, str(CLI), '--project', str(root), 'delivery', *args],
                          input=stdin, text=True, capture_output=True)


def tree(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and not p.is_symlink()}


def test_public_read_markdown_and_retry(tmp_path):
    (tmp_path / 'finding.md').write_text(BLOCK)
    before = tree(tmp_path)
    first = run(tmp_path, '--source', 'finding.md')
    assert first.returncode == 0, first.stderr
    value = json.loads(first.stdout)
    assert value['passages'][0]['locator'] == 'finding.md:2-2'
    assert value['sources'][0]['sha256'] == hashlib.sha256(BLOCK.encode()).hexdigest()
    retry = run(tmp_path, '--source', 'finding.md', '--source', './finding.md')
    assert retry.stdout == first.stdout
    assert run(tmp_path, '--source', 'finding.md', '--format', 'markdown').stdout == BLOCK.splitlines()[1] + '\n'
    assert tree(tmp_path) == before


@pytest.mark.parametrize('version,directory', [(1, 'research'), (2, '.ris/research')])
def test_initialized_layouts_unchanged(tmp_path, version, directory):
    # Real supported project configuration, without requiring any write-capable
    # initialization command as part of delivery.
    (tmp_path / '.ris').mkdir()
    cfg = {'schema_version': version, 'template_version': 1, 'project_id': 'delivery-test',
           'recording_policy': 'manual', 'research_dir': directory}
    (tmp_path / '.ris/project.yaml').write_text(''.join(f'{k}: {json.dumps(v)}\n' for k, v in cfg.items()))
    source = tmp_path / directory / 'finding.md'
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(BLOCK)
    before = tree(tmp_path)
    assert run(tmp_path, '--source', f'{directory}/finding.md').returncode == 0
    assert tree(tmp_path) == before


def test_draft_omission_and_changed_numbers(tmp_path):
    (tmp_path / 'finding.md').write_text(BLOCK + '\n<!-- ris:deliver -->\nOnly a design budget; no measured latency.\n<!-- /ris:deliver -->\n')
    value = json.loads(run(tmp_path, '--source', 'finding.md').stdout)
    revision = value['revision']
    def verify(text):
        (tmp_path / 'draft.txt').write_text(text)
        return run(tmp_path, '--source', 'finding.md', '--draft-file', 'draft.txt', '--expected-revision', revision)
    missing = verify('실측은 3개뿐이다. 신뢰구간은 미확인이다.')
    assert missing.returncode == 1
    assert json.loads(missing.stdout)['missed'] == [value['passages'][1]]
    assert verify('실측은 30개뿐이다. 신뢰구간은 미확인이다.\nOnly a design budget; no measured latency.').returncode == 1
    assert verify('실측은 3개뿐이다.\n 신뢰구간은 미확인이다.\r\n\r\nOnly a design budget; no measured latency.').returncode == 0
    # Words alone or disconnected fragments do not preserve a passage.
    assert verify('실측은 3개뿐이다. OMIT 신뢰구간은 미확인이다.\nOnly a design budget; no measured latency.').returncode == 1
    (tmp_path / 'finding.md').write_text(BLOCK)
    stale = verify(BLOCK)
    assert stale.returncode == 2 and 'revision changed' in stale.stderr


def test_stdin_uninitialized_and_ambiguity(tmp_path):
    value = json.loads(run(tmp_path, '--source', '-', stdin=BLOCK).stdout)
    assert value['sources'][0]['path'] == 'stdin'
    assert list(tmp_path.iterdir()) == []
    for args in [('--source', '-', '--source', 'x.md'),
                 ('--source', '-', '--draft-file', '-', '--expected-revision', value['revision']),
                 ('--source', '-', '--expected-revision', value['revision'])]:
        assert run(tmp_path, *args, stdin=BLOCK).returncode == 2
    (tmp_path / 'source.md').write_text(BLOCK)
    rev = json.loads(run(tmp_path, '--source', 'source.md').stdout)['revision']
    assert run(tmp_path, '--source', 'source.md', '--draft-file', '-', '--expected-revision', rev, stdin=BLOCK).returncode == 0


@pytest.mark.parametrize('body', [
    '<!-- ris:deliver -->\n<!-- /ris:deliver -->',
    '<!-- ris:deliver -->\ntext', '<!-- /ris:deliver -->',
    '<!-- ris:deliver -->\nx\n<!-- ris:deliver -->\ny\n<!-- /ris:deliver -->',
    ' <!-- ris:deliver -->\nx\n<!-- /ris:deliver -->',
    '<!-- ris:deliver-->\nx\n<!-- /ris:deliver -->',
])
def test_malformed(tmp_path, body):
    assert run(tmp_path, '--source', '-', stdin=body).returncode == 2


def test_fence_examples_ignored(tmp_path):
    examples = '```markdown\n<!-- ris:deliver -->\nexample\n<!-- /ris:deliver -->\n```\n'
    examples += '~~~\n<!-- /ris:deliver -->\n~~~\n'
    value = json.loads(run(tmp_path, '--source', '-', stdin=examples + BLOCK).stdout)
    assert len(value['passages']) == 1 and '실측' in value['passages'][0]['text']
    assert run(tmp_path, '--source', '-', stdin=examples).returncode == 2


def test_unsafe_paths_and_no_writes(tmp_path):
    (tmp_path / 'source.md').write_text(BLOCK)
    (tmp_path / 'alias.md').symlink_to(tmp_path / 'source.md')
    (tmp_path / 'linked').symlink_to(tmp_path, target_is_directory=True)
    for name in ['../source.md', str(tmp_path / 'source.md'), 'alias.md', 'linked/source.md', 'missing.md']:
        assert run(tmp_path, '--source', name).returncode == 2
    revision = json.loads(run(tmp_path, '--source', 'source.md').stdout)['revision']
    before = tree(tmp_path)
    assert run(tmp_path, '--source', 'source.md', '--draft-file', 'alias.md', '--expected-revision', revision).returncode == 2
    assert tree(tmp_path) == before


def test_multiple_sources_and_no_cross_section_match(tmp_path):
    (tmp_path / 'one.md').write_text('<!-- ris:deliver -->\nFirst condition. Second limitation.\n<!-- /ris:deliver -->\n')
    (tmp_path / 'two.md').write_text(BLOCK)
    args = ('--source', 'one.md', '--source', 'two.md')
    selected = json.loads(run(tmp_path, *args).stdout)
    assert len(selected['sources']) == len(selected['passages']) == 2
    assert selected['passages'][1]['id'] == 'D0002'
    # A beginning and ending in unrelated sections cannot manufacture the
    # required contiguous passage, even if each sentence occurs somewhere.
    draft = 'First condition.\n\n## Other section\nUnrelated evidence.\nSecond limitation.\n' + BLOCK
    (tmp_path / 'draft.md').write_text(draft)
    failed = run(tmp_path, *args, '--draft-file', 'draft.md', '--expected-revision', selected['revision'], '--format', 'markdown')
    assert failed.returncode == 1
    assert json.loads(failed.stdout)['missed'] == [selected['passages'][0]]
    assert run(tmp_path, *args, '--draft-file', 'draft.md').returncode == 2


def test_numeric_suffix_and_paragraph_boundaries(tmp_path):
    (tmp_path / 'finding.md').write_text('<!-- ris:deliver -->\nMeasured value is 3\n<!-- /ris:deliver -->\n')
    args = ('--source', 'finding.md')
    revision = json.loads(run(tmp_path, *args).stdout)['revision']
    check = (*args, '--draft-file', '-', '--expected-revision', revision)
    for altered in ('Measured value is 3.5', 'Measured value is 3%', 'Not true: Measured value is 3',
                    'Measured value\n\nis 3'):
        assert run(tmp_path, *check, stdin=altered).returncode == 1
    assert run(tmp_path, *check, stdin='Summary\n\nMeasured value\nis 3\n\nNext action.').returncode == 0


def test_legacy_external_knowledge_is_not_delivery_input(tmp_path):
    (tmp_path/'.ris').mkdir()
    cfg={'schema_version':2,'template_version':1,'project_id':'local','recording_policy':'manual','research_dir':'.ris/research'}
    (tmp_path/'.ris/project.yaml').write_text(''.join(f'{k}: {json.dumps(v)}\n' for k,v in cfg.items()))
    path=tmp_path/'old.md'
    path.write_text('---\nknowledge_record: true\nproject_id: "local"\nsource_project_id: "other"\n---\n'+BLOCK)
    result=run(tmp_path,'--source','old.md')
    assert result.returncode!=0 and 'Cross-project' in result.stderr
