"""End-to-end checks for the explicit schema-1 storage migration."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'ris.py'
MIGRATION = SCRIPT.with_name('ris_layout_migration.py')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ris = load('ris_migration_test_helper', SCRIPT)
migration = load('ris_layout_migration_test_helper', MIGRATION)


def cli(project, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), '--project', str(project), *args],
        text=True, capture_output=True)


def cli_json(project, *args):
    result = cli(project, *args)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def snapshot(root):
    entries = {}
    stack = [root]
    while stack:
        parent = stack.pop()
        for entry in sorted(os.scandir(parent), key=lambda item: item.name):
            path = Path(entry.path)
            rel = path.relative_to(root).as_posix()
            info = entry.stat(follow_symlinks=False)
            mode = info.st_mode
            if path.is_symlink():
                entries[rel] = ('symlink', os.readlink(path), info.st_mtime_ns)
            elif os.path.isdir(path):
                entries[rel] = ('directory', info.st_mode, info.st_mtime_ns)
                stack.append(path)
            elif os.path.isfile(path):
                entries[rel] = ('file', path.read_bytes(), info.st_mode, info.st_mtime_ns)
            else:
                entries[rel] = ('special', mode)
    return entries


def make_v1(project, *, handoff='mixed'):
    """Create a synthetic schema-1 project with valid state and a proposal."""
    (project / 'data').mkdir()
    source = project / 'data' / 'source.csv'
    source.write_text('id,value\n1,synthetic\n', encoding='utf-8')
    (project / 'README.md').write_text(
        'This user-owned link is outside the migration scan: [context](research/CONTEXT.md).\n',
        encoding='utf-8')
    (project / 'unrelated.txt').write_text('Keep this byte-for-byte.\n', encoding='utf-8')

    ris.initialize(project, 'Synthetic migration project', 'Move only known RIS state.')
    config_path = project / '.ris' / 'project.yaml'
    cfg = ris.config(project)
    (project / cfg['research_dir']).rename(project / 'research')
    cfg['schema_version'] = 1
    cfg['research_dir'] = 'research'
    config_path.write_text(ris.yaml_mapping(cfg), encoding='utf-8')

    plan = ris.add_record(
        project, 'plan', 'Synthetic active plan',
        'Plan source: [dataset](../../data/source.csv).\n',
    )
    context_path = 'research/CONTEXT.md'
    config_hash = hashlib.sha256(config_path.read_bytes()).hexdigest()
    ris.configure(project, config_hash, active_plan=plan['path'])

    active_ref = plan['path'] + '#D-001'
    ris.initialize_state(project, run_id='RISRUN-SYNTHETIC-MIGRATION', active_plan_ref=active_ref)
    state_snapshot = ris.read_state_snapshot(project)
    state = state_snapshot['state']
    state.update({
        'status': 'RESEARCHING',
        'tasks': [{
            'id': 'T-001', 'type': 'research', 'owner': 'researcher', 'status': 'PASS',
            'depends_on': [], 'artifact_refs': [context_path, plan['path']],
            'audit_status': 'NOT_RUN', 'attempt': 1, 'invalidated_by': [],
            'question_ref': context_path,
        }],
        'quality_gates': {'evidence': 'NOT_RUN'},
        'pending_user_decisions': [context_path],
        'blocked_items': [{'ref': plan['path'], 'reason': 'Synthetic pending source review'}],
    })
    ris.update_state(project, state_snapshot['sha256'], json.dumps(state, ensure_ascii=False))

    proposal_source = project / context_path
    proposal_base = hashlib.sha256(proposal_source.read_bytes()).hexdigest()
    proposal = ris.propose(project, context_path, proposal_base, 'Synthetic proposed context update.')

    if handoff == 'mixed':
        (project / 'HANDOFF.md').write_text(
            '# Human handoff\n\n'
            'Keep this unrelated link: [project README](README.md).\n'
            'Resume from the [research context](research/CONTEXT.md).\n',
            encoding='utf-8')
    elif handoff == 'plain':
        (project / 'HANDOFF.md').write_text(
            '# Research handoff\n\nResume from [current context](research/CONTEXT.md).\n',
            encoding='utf-8')
    elif handoff != 'none':
        raise ValueError(handoff)

    assert ris.check(project)['ok']
    return {
        'project_id': cfg['project_id'], 'plan': plan, 'active_ref': active_ref,
        'context_path': context_path, 'proposal': proposal['proposal'],
        'proposal_base': proposal_base,
    }


def test_cli_preview_is_read_only_then_migrates_identity_state_proposals_and_links(tmp_path):
    project = tmp_path / 'legacy'
    project.mkdir()
    before = make_v1(project, handoff='plain')
    original = snapshot(project)

    preview = cli_json(project, 'migrate-layout', '--include-handoff')
    assert preview['status'] == 'preview'
    assert preview['from'] == {'schema_version': 1, 'research_dir': 'research'}
    assert preview['to'] == {'schema_version': 2, 'research_dir': '.ris/research'}
    assert any(change.get('move') == 'HANDOFF.md' for change in preview['changes'])
    assert snapshot(project) == original

    applied = cli_json(project, 'migrate-layout', '--apply', '--include-handoff')
    assert applied['status'] == 'migrated'
    cfg = ris.config(project)
    assert cfg['schema_version'] == 2 and cfg['research_dir'] == '.ris/research'
    assert cfg['project_id'] == before['project_id']
    assert cfg['active_plan'] == before['plan']['path'].replace('research/', '.ris/research/', 1)
    assert not (project / 'research').exists()
    assert not (project / '.ris' / 'layout-migration.json').exists()

    plan_rel = before['plan']['path'].replace('research/', '.ris/research/', 1)
    plan = project / plan_rel
    plan_meta = ris.frontmatter(plan.read_text(encoding='utf-8'))
    assert plan_meta['project_id'] == before['project_id']
    assert plan_meta['ris_id'] == before['plan']['ris_id']
    assert '[dataset](../../../data/source.csv)' in plan.read_text(encoding='utf-8')
    assert (project / 'data/source.csv').read_text(encoding='utf-8') == 'id,value\n1,synthetic\n'

    state = ris.read_state(project)
    expected_context = '.ris/research/CONTEXT.md'
    expected_plan = plan_rel
    assert state['project_id'] == before['project_id']
    assert state['run_id'] == 'RISRUN-SYNTHETIC-MIGRATION'
    assert state['goal_ref'] == expected_context
    assert state['active_plan_ref'] == expected_plan + '#D-001'
    assert state['pending_user_decisions'] == [expected_context]
    assert state['blocked_items'] == [{'ref': expected_plan, 'reason': 'Synthetic pending source review'}]
    task = state['tasks'][0]
    assert task['question_ref'] == expected_context
    assert task['artifact_refs'] == [expected_context, expected_plan]

    proposal_path = project / before['proposal']
    proposal = json.loads(proposal_path.read_text(encoding='utf-8'))
    assert proposal['project_id'] == before['project_id']
    assert proposal['target'] == expected_context
    assert proposal['base_sha256'] == before['proposal_base']
    assert ris.check(project)['ok']

    handoff = project / '.ris/HANDOFF.md'
    assert handoff.is_file() and not (project / 'HANDOFF.md').exists()
    assert '[current context](research/CONTEXT.md)' in handoff.read_text(encoding='utf-8')
    assert (handoff.parent / 'research/CONTEXT.md').is_file()
    assert (project / 'README.md').read_bytes() == original['README.md'][1]
    assert (project / 'unrelated.txt').read_bytes() == original['unrelated.txt'][1]


def test_unowned_mixed_handoff_stays_root_and_only_ris_link_is_rebased(tmp_path):
    project = tmp_path / 'legacy'
    project.mkdir()
    make_v1(project, handoff='mixed')
    original = (project / 'HANDOFF.md').read_text(encoding='utf-8')

    preview = cli_json(project, 'migrate-layout')
    handoff_changes = [change for change in preview['changes'] if change.get('update') == 'HANDOFF.md']
    assert len(handoff_changes) == 1
    assert handoff_changes[0]['scope'] == 'relative RIS research links only'
    assert handoff_changes[0]['links_rebased'] == 1
    assert not any(change.get('move') == 'HANDOFF.md' for change in preview['changes'])
    assert (project / 'HANDOFF.md').read_text(encoding='utf-8') == original

    applied = cli_json(project, 'migrate-layout', '--apply')
    assert applied['status'] == 'migrated'
    handoff = (project / 'HANDOFF.md').read_text(encoding='utf-8')
    assert 'Keep this unrelated link: [project README](README.md).' in handoff
    assert '[research context](.ris/research/CONTEXT.md)' in handoff
    assert not (project / '.ris/HANDOFF.md').exists()
    assert (project / 'README.md').read_text(encoding='utf-8') == (
        'This user-owned link is outside the migration scan: [context](research/CONTEXT.md).\n')


def test_unowned_handoff_without_research_links_is_byte_identical(tmp_path):
    project = tmp_path / 'legacy'
    project.mkdir()
    make_v1(project, handoff='none')
    handoff = project / 'HANDOFF.md'
    original = b'# Unrelated handoff\r\n\r\n[Project README](README.md)\r\n'
    handoff.write_bytes(original)

    preview = cli_json(project, 'migrate-layout')
    assert any(change.get('preserve') == 'HANDOFF.md' for change in preview['changes'])
    assert not any(change.get('update') == 'HANDOFF.md' for change in preview['changes'])
    applied = cli_json(project, 'migrate-layout', '--apply')
    assert applied['status'] == 'migrated'
    assert handoff.read_bytes() == original
    assert not (project / '.ris/HANDOFF.md').exists()


@pytest.mark.parametrize('collision', ['destination', 'destination_symlink', 'source_symlink'])
def test_preview_refuses_destination_or_research_symlink_without_writes(tmp_path, collision):
    project = tmp_path / collision
    project.mkdir()
    make_v1(project, handoff='none')
    outside = tmp_path / f'{collision}-outside'
    outside.mkdir()
    sentinel = outside / 'sentinel.txt'
    sentinel.write_text('outside stays untouched', encoding='utf-8')
    if collision == 'destination':
        (project / '.ris/research').mkdir()
    elif collision == 'destination_symlink':
        (project / '.ris/research').symlink_to(outside, target_is_directory=True)
    else:
        (project / 'research/plans/unsafe').symlink_to(outside, target_is_directory=True)
    before = snapshot(project)

    result = cli(project, 'migrate-layout')
    assert result.returncode != 0
    assert snapshot(project) == before
    assert sentinel.read_text(encoding='utf-8') == 'outside stays untouched'
    assert not (project / '.ris/layout-migration.json').exists()


def test_apply_failure_rolls_back_from_marker_and_retry_succeeds(tmp_path, monkeypatch):
    project = tmp_path / 'legacy'
    project.mkdir()
    before = make_v1(project, handoff='plain')
    config_before = (project / '.ris/project.yaml').read_bytes()
    state_before = (project / '.ris/state.json').read_bytes()
    context_before = (project / 'research/CONTEXT.md').read_bytes()

    def interrupt_after_tree_move(root, plan):
        os.rename(root / 'research', root / '.ris/research')
        raise OSError('simulated interruption after moving the research tree')

    monkeypatch.setattr(migration, '_apply', interrupt_after_tree_move)
    with pytest.raises(OSError, match='simulated interruption'):
        migration.migrate_layout(project, apply=True, include_handoff=True)
    assert not (project / '.ris/layout-migration.json').exists()
    assert (project / '.ris/project.yaml').read_bytes() == config_before
    assert (project / '.ris/state.json').read_bytes() == state_before
    assert (project / 'research/CONTEXT.md').read_bytes() == context_before
    assert not (project / '.ris/research').exists()
    assert (project / 'HANDOFF.md').is_file()

    retry = cli_json(project, 'migrate-layout', '--apply', '--include-handoff')
    assert retry['status'] == 'migrated'
    assert ris.config(project)['project_id'] == before['project_id']
    assert ris.check(project)['ok']


def test_schema2_project_is_already_current_and_ignores_unrelated_root_research(tmp_path):
    project = tmp_path / 'current'
    project.mkdir()
    ris.initialize(project, 'Already current')
    root_research = project / 'research'
    root_research.mkdir()
    keep = root_research / 'unrelated.txt'
    keep.write_text('root user data', encoding='utf-8')
    handoff = project / 'HANDOFF.md'
    handoff.write_text('unrelated root handoff', encoding='utf-8')
    before = snapshot(project)

    preview = cli_json(project, 'migrate-layout')
    assert preview['status'] == 'already_current' and preview['changes'] == []
    applied = cli_json(project, 'migrate-layout', '--apply')
    assert applied['status'] == 'already_current' and applied['changes'] == []
    assert snapshot(project) == before
