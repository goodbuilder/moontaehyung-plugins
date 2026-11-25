#!/usr/bin/env python3
"""Run the bundled local RIS CLI in a fail-closed Linux filesystem namespace."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def python_namespace() -> list[str]:
    """Blank namespace and system Python mounts, without any project or scripts mount."""
    bwrap = shutil.which('bwrap')
    if not bwrap:
        raise RuntimeError('bubblewrap is required; isolation unavailable (no unsafe fallback)')
    # Only the selected project and trusted runtime code enter the namespace. Host home,
    # plugin state, instruction history, sibling projects, sockets and credentials do not.
    cmd = [bwrap, '--unshare-all', '--die-with-parent', '--new-session', '--clearenv',
           '--ro-bind', '/usr', '/usr', '--proc', '/proc', '--dev', '/dev',
           '--tmpfs', '/tmp', '--dir', '/home', '--dir', '/home/ris',
           '--setenv', 'HOME', '/home/ris', '--setenv', 'PATH', '/usr/bin:/bin',
           '--setenv', 'LANG', 'C.UTF-8', '--setenv', 'PYTHONDONTWRITEBYTECODE', '1']
    for directory in ('/lib', '/lib64', '/bin'):
        if Path(directory).exists():
            cmd.extend(['--ro-bind', directory, directory])
    return cmd


def command(project: Path, args: list[str]) -> list[str]:
    project = project.resolve(strict=True)
    if not project.is_dir():
        raise RuntimeError('Project must be an existing directory')
    cmd = python_namespace()
    cmd.extend(['--ro-bind', str(Path(__file__).resolve().parent), '/opt/ris-runtime',
                '--bind', str(project), '/project', '--chdir', '/project',
                '/usr/bin/python3', '/opt/ris-runtime/ris.py', '--project', '/project', *args])
    return cmd


def model_workspace_eligibility(project: Path) -> dict:
    """Conservative preflight only; success does not establish a clean model host."""
    spec = importlib.util.spec_from_file_location('ris_isolation_api', Path(__file__).with_name('ris.py'))
    ris = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ris)
    project = project.resolve(strict=True)
    cfg = ris.config(project)
    reasons = set()
    # Identified foreign records remain historical evidence, never silently deleted/rewritten.
    for directory, folders, files in os.walk(project, followlinks=False):
        current = Path(directory)
        if current != project and '.ris' in folders:
            reasons.add('nested_project')
            folders[:] = []
            continue
        kept = []
        for name in folders:
            if name == '.git':
                continue
            if (current / name).is_symlink():
                reasons.add('symlink_requires_curated_mount')
                continue
            if name in {'.aws', '.ssh', '.gnupg'}:
                reasons.add('private_directory_requires_curated_mount')
                continue
            kept.append(name)
        folders[:] = kept
        for name in files:
            path = current / name
            if path.is_symlink():
                reasons.add('symlink_requires_curated_mount')
                continue
            if path.suffix != '.md':
                continue
            try:
                metadata = ris.frontmatter(path.read_text(encoding='utf-8'))
            except (OSError, UnicodeError, ris.Error):
                reasons.add('uninspectable_markdown')
                continue
            if metadata.get('project_id') not in (None, cfg['project_id']):
                reasons.add('foreign_project_metadata')
            if (metadata.get('source_project_path') is not None
                    or metadata.get('source_project_id') not in (None, cfg['project_id'])):
                reasons.add('external_provenance')
    return {'model_execution_eligible': False,
            'known_contamination': sorted(reasons),
            'status': 'requires_curated_mount' if reasons else 'host_context_not_verified',
            'reason': 'Only local RIS CLI isolation is implemented; clean model-host context is not established.'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--check-model-eligibility', action='store_true')
    parser.add_argument('args', nargs=argparse.REMAINDER)
    values = parser.parse_args()
    args = values.args[1:] if values.args[:1] == ['--'] else values.args
    try:
        if values.check_model_eligibility:
            print(json.dumps(model_workspace_eligibility(values.project), sort_keys=True))
            return 0
        return subprocess.run(command(values.project, args), env={}).returncode
    except (OSError, RuntimeError) as exc:
        print(f'Isolation error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
