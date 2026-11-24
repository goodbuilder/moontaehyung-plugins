"""Guards the one-source-two-tools plugin layout against silent drift (see references/maintenance.md)."""
import json
from pathlib import Path
import re

import pytest

PLUGIN=Path(__file__).resolve().parents[3]
ROLES=['auditor','designer','engineer','planner','researcher']

def manifest(name):
    return json.loads((PLUGIN/name/'plugin.json').read_text(encoding='utf-8'))

def codex_agent(role):
    # Python 3.10 has no tomllib and the helper is standard-library only, so read the three known fields.
    text=(PLUGIN/'agents'/f'{role}.toml').read_text(encoding='utf-8')
    name=re.search(r'^name = "(.*)"$',text,re.M)
    description=re.search(r'^description = "(.*)"$',text,re.M)
    body=re.search(r'^developer_instructions = """\n?(.*?)"""',text,re.M|re.S)
    assert name and description and body,f'{role}.toml is missing a required field'
    return {'name':name[1],'description':description[1],'developer_instructions':body[1]}

def claude_agent(role):
    text=(PLUGIN/'agents/claude'/f'{role}.md').read_text(encoding='utf-8')
    m=re.match(r'\A---\n(.*?)\n---\n(.*)\Z',text,re.S)
    assert m,f'{role}.md has no frontmatter'
    meta=dict(re.findall(r'^(\w+):\s*"?(.*?)"?\s*$',m[1],re.M))
    return meta,m[2].strip()

def test_manifest_versions_match():
    assert manifest('.codex-plugin')['version']==manifest('.claude-plugin')['version']

def test_every_role_exists_in_both_formats_and_is_listed_by_claude_manifest():
    listed=set(manifest('.claude-plugin')['agents'])
    for role in ROLES:
        assert (PLUGIN/'agents'/f'{role}.toml').is_file(),role
        assert (PLUGIN/'agents/claude'/f'{role}.md').is_file(),role
        assert f'./agents/claude/{role}.md' in listed,role
    assert {Path(p).stem for p in listed}==set(ROLES)

KNOWN_DRIFT={}  # role -> {'description','instructions'}; add only with an owner decision, strict xfail

def params(check):
    return [pytest.param(r,marks=pytest.mark.xfail(strict=True,reason='codex/claude role text diverges'))
            if check in KNOWN_DRIFT.get(r,()) else r for r in ROLES]

@pytest.mark.parametrize('role',ROLES)
def test_role_name_matches_across_formats(role):
    assert codex_agent(role)['name']==claude_agent(role)[0]['name']==role

@pytest.mark.parametrize('role',params('description'))
def test_role_description_matches_across_formats(role):
    assert codex_agent(role)['description']==claude_agent(role)[0]['description']

@pytest.mark.parametrize('role',params('instructions'))
def test_role_shared_instructions_match_across_formats(role):
    shared=codex_agent(role)['developer_instructions'].strip();_,body=claude_agent(role)
    # The Claude file may append tool-specific guidance after the shared instructions, never alter them.
    assert body.startswith(shared)

def test_no_symlinks_in_plugin_tree():
    links=[str(p.relative_to(PLUGIN)) for p in PLUGIN.rglob('*') if p.is_symlink()]
    assert not links,links
