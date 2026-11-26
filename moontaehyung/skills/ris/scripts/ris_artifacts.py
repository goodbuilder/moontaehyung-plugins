"""Cooperative role-scoped updates of separate and legacy combined RIS sources."""
import json
import re


PLAN_HEADINGS = {'research plan', 'execution plan', '연구 계획', '실행 계획'}
MAP_HEADINGS = {'research map', 'research map nodes', '연구 지도', '연구 지도 노드'}
FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})(.*)$')
WHITESPACE = re.compile(r'\s*')
KEY_SEPARATOR = re.compile(r'\s*:\s*')
FIELD_END = re.compile(r'\s*[,}]')
HEADING = re.compile(r'^ {0,3}(#{1,6})[ \t]+(.+)$')


def unique_object(pairs):
    result = dict(pairs)
    if len(result) != len(pairs):
        raise ValueError('Ambiguous duplicate key in the project-plan graph')
    return result


def graph_parts(raw):
    """Keep the literal JSON fields, including number types, within each owner's area."""
    decoder = json.JSONDecoder(object_pairs_hook=unique_object)
    graph = decoder.decode(raw)
    if not isinstance(graph, dict):
        raise ValueError('Expected a project-plan JSON object')
    pos = raw.index('{') + 1
    fields = {}
    for key in graph:
        pos = WHITESPACE.match(raw, pos).end()
        start = pos
        _, pos = decoder.raw_decode(raw, pos)
        pos = KEY_SEPARATOR.match(raw, pos).end()
        _, pos = decoder.raw_decode(raw, pos)
        fields[key] = raw[start:pos]
        pos = FIELD_END.match(raw, pos).end()
    execution = fields.pop('execution_plan', None)
    fields.pop('revision', None)  # The combined source has one revision counter.
    shared = bool({'research_map_root', 'map_semantics', 'first_level_research_questions'} & fields.keys())
    return tuple(fields.values()), execution, shared


def blocks(text):
    """Yield a line, or a complete fenced block with its contents and closing line."""
    lines = iter(text.splitlines(keepends=True))
    for line in lines:
        fence = FENCE.fullmatch(line.rstrip('\r\n'))
        if not fence or (fence[1][0] == '`' and '`' in fence[2]):
            yield line, None, None
            continue
        marker, _ = fence.groups()
        close = re.compile(r'^ {0,3}' + marker[0] + '{' + str(len(marker)) + r',}[ \t]*$')
        contents = []
        for closing in lines:
            if close.fullmatch(closing.rstrip('\r\n')):
                break
            contents.append(closing)
        else:
            raise ValueError('Unclosed Markdown fence in source')
        yield line, ''.join(contents), closing


def section(line):
    heading = HEADING.fullmatch(line.rstrip('\r\n'))
    if not heading:
        return 0, ''
    label = re.sub(r'[ \t]+#+[ \t]*$', '', heading[2]).strip().casefold()
    return len(heading[1]), label


def partitions(text):
    research, planning = [], []
    in_plan = False
    has_map = False
    for line, contents, closing in blocks(text):
        if contents is not None:
            if FENCE.fullmatch(line.rstrip('\r\n'))[2].strip() == 'project-plan':
                fields, execution, shared = graph_parts(contents)
                research.append((line, fields, closing))
                if execution is not None:
                    planning.append(('execution_plan', execution))
                has_map |= shared
            else:
                (planning if in_plan else research).append(line + contents + closing)
            continue
        level, label = section(line)
        if level in (1, 2):
            in_plan = level == 2 and label in PLAN_HEADINGS
            has_map |= label in MAP_HEADINGS
        (planning if in_plan else research).append(line)
    return research, planning, has_map


def compact_index(text, requested):
    """Project the canonical map table without sending research prose to the model."""
    active, header = False, False
    nodes = {}
    details = {}
    for line, contents, _ in blocks(text):
        if contents is not None:
            continue
        level, label = section(line)
        if level in (1, 2):
            active = level == 2 and label in {'research map nodes', '연구 지도 노드'}
            header = False
            continue
        row = line.strip()
        if not active or not row.startswith('|') or not row.endswith('|'):
            continue
        cells = [c.strip().replace(r'\|', '|') for c in re.split(r'(?<!\\)\|', row[1:-1])]
        if cells[0].casefold() == 'id':
            header = len(cells) >= 3 and cells[1].casefold() in {'parent', 'parent id', '상위 id'}
            continue
        if not header or re.fullmatch(r':?-+:?', cells[0]):
            continue
        if len(cells) < 3 or not cells[0] or cells[0] in nodes:
            raise ValueError('Invalid or duplicate map node ID: ' + cells[0])
        nid, parent, title = cells[:3]
        nodes[nid] = (nid, parent, title)
        if nid in requested:
            details[nid] = cells[3:]
    if not nodes:
        raise ValueError('No Research Map Nodes table with ID, Parent ID and title; inspect the existing map format directly')
    roots = {'', '-', '—'}
    checked = set()
    for nid in nodes:
        current, path = nid, set()
        while current not in roots and current not in checked:
            if current not in nodes:
                raise ValueError('Unknown map parent: ' + current)
            if current in path:
                raise ValueError('Cycle in map parentage at: ' + current)
            path.add(current)
            current = nodes[current][1]
        checked.update(path)
    missing = set(requested) - nodes.keys()
    if missing:
        raise ValueError('Unknown map IDs: ' + ', '.join(sorted(missing)))
    selected = [row for nid, row in nodes.items() if not requested or nid in requested]
    result = {'columns': ['id', 'parent', 'title'], 'nodes': selected, 'total_nodes': len(nodes)}
    if requested:
        result['details'] = details
    return result


def check_update(owner, kind, before, after, shared_source=False, dedicated=False):
    if owner not in ('researcher', 'planner') or kind not in ('plan', 'map'):
        raise ValueError('Select a Research Map or Research Plan for a role-scoped update')
    if kind == 'map' and owner != 'researcher':
        raise ValueError('The Researcher owns this Research Map')
    old_map, old_plan, shared = partitions(before)
    new_map, new_plan, proposed_shared = partitions(after)
    if kind == 'map':
        if new_plan != old_plan:
            raise ValueError('Researcher update changes execution-plan content')
        return
    # Older combined graphs can carry the plan under execution_plan without map metadata.
    if not dedicated:
        shared |= any(isinstance(part, tuple) for part in old_plan)
        proposed_shared |= any(isinstance(part, tuple) for part in new_plan)
    if shared_source or shared:
        if shared and not proposed_shared and not shared_source:
            raise ValueError('Preserve the combined map/plan source boundary')
        if owner == 'planner' and old_map != new_map:
            raise ValueError('Planner update changes protected Research Map content')
        if owner == 'researcher' and old_plan != new_plan:
            raise ValueError('Researcher update changes protected Research Plan content')
    elif owner != 'planner':
        raise ValueError('The Planner owns this Research Plan')
    elif proposed_shared:
        raise ValueError('Create a separate Research Map; this is a standalone Research Plan')
