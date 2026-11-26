"""Exercise the user-facing record/update path, including an existing combined source."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest


CLI = Path(__file__).resolve().parents[1] / 'scripts' / 'ris.py'
MAP = '''## 연구 지도 노드
| ID | 상위 ID | 표시 이름 |
| --- | --- | --- |
| goal | — | 측정 |
| image | goal | 영상 측정 |
| timing | goal | 시간 |
| hdmi | image | HDMI |
| rtsp | timing | RTSP |
| exposure | timing | 노출 시차 |
'''
UPDATED_MAP = MAP.replace('| hdmi | image', '| reception | image | 영상 수신 |\n| hdmi | reception').replace(
    '| rtsp | timing', '| rtsp | reception') + '\n관련 질문: reception → exposure\n'
PLAN = '## 연구 계획\n\nMeasure timing separately.\n'
GRAPH = {'revision': 1, 'research_map_root': 'goal', 'nodes': [{'id': 'goal', 'status': 'confirmed'}],
         'execution_plan': [{'id': 'capture', 'map_ids': ['rtsp'], 'action': 'Capture'}]}


@pytest.fixture
def project(tmp_path):
    call(tmp_path, 'init', '--name', 'Review')
    return tmp_path


def call(root, *args, ok=True):
    result = subprocess.run([sys.executable, str(CLI), '--project', str(root), *args],
                            capture_output=True, text=True)
    assert result.returncode == (0 if ok else 2), (result.stdout, result.stderr)
    return json.loads(result.stdout if ok else result.stderr)


def create(root, kind, body, owner=None):
    (root / 'body.md').write_text(body)
    record = call(root, 'record', '--kind', kind, '--title', kind, '--body-file', 'body.md',
                  *(['--owner', owner] if owner else []))
    return root / record['path']


def update(root, path, owner, data, *, expected=None, ok=True, shared=False):
    before = path.read_bytes()
    revision = expected or hashlib.sha256(before).hexdigest()
    (root / 'edit.md').write_bytes(data)
    result = call(root, 'update', str(path.relative_to(root)), '--owner', owner, '--expected-hash',
                  revision, '--body-file', 'edit.md', *(['--shared-source'] if shared else []), ok=ok)
    if not ok:
        assert path.read_bytes() == before
    return result


def test_separate_artifacts_have_distinct_writers(project):
    research = create(project, 'map', MAP, 'researcher')
    plan = create(project, 'plan', PLAN, 'planner')
    assert research != plan
    update(project, research, 'researcher', research.read_bytes().replace(MAP.strip().encode(), UPDATED_MAP.strip().encode()))
    before = research.read_bytes()
    update(project, plan, 'planner', plan.read_bytes().replace(b'Measure', b'Check'))
    update(project, research, 'planner', before.replace(b'rtsp', b'missing'), ok=False)
    update(project, plan, 'researcher', plan.read_bytes(), ok=False)
    update(project, plan, 'researcher', plan.read_bytes().replace(b'Check', b'Wrong'), ok=False, shared=True)
    update(project, plan, 'planner', plan.read_bytes().replace(b'artifact_owner: "planner"', b'artifact_owner: "researcher"'), ok=False)
    assert research.read_bytes() == before
    assert call(project, 'check')['ok']


@pytest.mark.parametrize('explicit', [False, True])
def test_shared_source_reparent_survives_plan_retries(project, explicit):
    heading = '## Measurements' if explicit else '## 연구 지도 노드'
    graph = dict(GRAPH)
    if explicit:
        del graph['research_map_root']
    raw_graph = json.dumps(graph, ensure_ascii=False, indent=2)
    body = (MAP.replace('## 연구 지도 노드', heading) + '\n' + PLAN
            + '\n## Data\n\n```project-plan\n' + raw_graph + '\n```')
    path = create(project, 'plan', body)
    initial = path.read_bytes()
    first_hash = hashlib.sha256(initial).hexdigest()
    desired_map = UPDATED_MAP.replace('## 연구 지도 노드', heading)
    revised = initial.replace(MAP.replace('## 연구 지도 노드', heading).encode(), desired_map.encode())
    update(project, path, 'researcher', revised, shared=explicit)
    assert path.read_bytes() == revised
    stale_plan = initial.replace(b'Measure timing', b'Record timing')
    assert 'changed' in update(project, path, 'planner', stale_plan, expected=first_hash, ok=False, shared=explicit)['error']
    # Even with the current hash a stale full-body candidate must not revert the map.
    update(project, path, 'planner', stale_plan, ok=False, shared=explicit)
    planned = revised.replace(b'Measure timing', b'Record timing').replace(b'"Capture"', b'"Capture and check"')
    update(project, path, 'planner', planned, shared=explicit)
    assert desired_map.encode() in path.read_bytes()
    update(project, path, 'researcher', revised, ok=False, shared=explicit)
    for changed in (planned.replace(b'"confirmed"', b'"rejected"'), planned.replace(b'| rtsp | reception', b'| rtsp | timing')):
        update(project, path, 'planner', changed, ok=False, shared=explicit)
    assert (project / '.ris' / 'history' / (first_hash + '.md')).read_bytes() == initial


def test_fenced_example_is_not_a_planner_owned_section(project):
    example = '\n````md\n## Research Plan\nresearch example\n```\n````\n'
    path = create(project, 'plan', MAP + example + PLAN)
    update(project, path, 'planner', path.read_bytes().replace(b'research example', b'changed'), ok=False)
    data = path.read_bytes().replace(b'\n', b'\r\n')
    path.write_bytes(data)
    changed = data.replace(b'Measure timing', b'Check timing')
    update(project, path, 'planner', changed)
    assert path.read_bytes() == changed


def test_map_index_covers_other_branches_and_limits_details(project):
    appendix = '\n## Evidence\n\n```md\n## 연구 지도 노드\n| ID | parent | Title |\n| fake | goal | example |\n```'
    path = create(project, 'map', MAP.replace('RTSP |', 'RTSP | stored evidence |') + appendix, 'researcher')
    result = call(project, 'map-index', str(path.relative_to(project)))
    assert ['rtsp', 'timing', 'RTSP'] in result['nodes']
    assert ['hdmi', 'image', 'HDMI'] in result['nodes']
    assert 'details' not in result and 'stored evidence' not in str(result) and 'fake' not in str(result)
    focused = call(project, 'map-index', str(path.relative_to(project)), '--node', 'rtsp')
    assert focused['nodes'] == [['rtsp', 'timing', 'RTSP']] and focused['total_nodes'] == len(result['nodes'])
    assert focused['details'] == {'rtsp': ['stored evidence']}
    assert focused['sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_standalone_plan_cannot_be_created_with_map_content_by_planner(project):
    (project / 'candidate.md').write_text(MAP)
    result = call(project, 'record', '--kind', 'plan', '--owner', 'planner', '--title', 'Plan',
                  '--body-file', 'candidate.md', ok=False)
    assert 'separate Research Map' in result['error']


@pytest.mark.parametrize('parent,message', [('rtsp', 'Cycle'), ('missing', 'Unknown map parent')])
def test_map_index_detects_invalid_parentage(project, parent, message):
    body = MAP.replace('| rtsp | timing |', f'| rtsp | {parent} |')
    path = create(project, 'map', body, 'researcher')
    assert message in call(project, 'map-index', str(path.relative_to(project)), ok=False)['error']
