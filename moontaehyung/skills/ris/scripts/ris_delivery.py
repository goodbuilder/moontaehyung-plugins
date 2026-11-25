"""Read-only, revision-pinned transport of owner-selected final passages."""
import hashlib
import json
import os
import re
import stat
import sys

START = '<!-- ris:deliver -->'
END = '<!-- /ris:deliver -->'


def add_parser(sub):
    parser = sub.add_parser('delivery', help='Read or check selected final passages without recording')
    parser.add_argument('--source', action='append', required=True, help='Project-relative Markdown path; repeatable, or sole - for stdin')
    parser.add_argument('--format', choices=('json', 'markdown'), default='json')
    parser.add_argument('--draft-file', help='Project-relative outgoing draft path, or - for stdin')
    parser.add_argument('--expected-revision', help='Composite revision returned when selecting passages')


def read_file(api, root, relative, markdown=False):
    path = api.inside(root, relative)
    if markdown and path.suffix.lower() != '.md':
        raise api.Error('Delivery source must be a Markdown file: ' + relative)
    # No-follow protects the final component between validation and open. Recheck
    # the path and inode after reading to detect replacement during the read.
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise api.Error('Expected a regular delivery file: ' + relative)
        data = stream.read()
        after = os.fstat(stream.fileno())
    current = api.inside(root, relative).stat()
    signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if signature(before) != signature(after) or signature(after) != signature(current):
        raise api.Error('Delivery file changed while reading: ' + relative)
    return path.relative_to(root).as_posix(), data


def passages(api, label, text):
    result, opening, fence = [], None, None
    lines = text.splitlines()
    for number, line in enumerate(lines, 1):
        token = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            if token and token[1][0] == fence[0] and len(token[1]) >= len(fence) and not token[2].strip():
                fence = None
            continue
        if token:
            fence = token[1]
            continue
        if line == START:
            if opening is not None:
                raise api.Error(f'Nested delivery block: {label}:{number}')
            opening = number
        elif line == END:
            if opening is None:
                raise api.Error(f'Unmatched delivery end: {label}:{number}')
            body = '\n'.join(lines[opening:number-1]).strip('\n')
            if not body.strip():
                raise api.Error(f'Empty delivery block: {label}:{opening}')
            result.append({'locator': f'{label}:{opening+1}-{number-1}', 'text': body})
            opening = None
        elif START in line or END in line or re.search(r'<!--\s*/?ris:deliver\b', line, re.I):
            raise api.Error(f'Delivery markers must be exact standalone lines: {label}:{number}')
    if opening is not None:
        raise api.Error(f'Unclosed delivery block: {label}:{opening}')
    if not result:
        raise api.Error('No delivery passages selected: ' + label)
    return result


def paragraphs(text):
    """Compare whole publication-ready paragraphs while allowing ordinary line wrapping."""
    lines = ['' if line in (START, END) else line for line in text.splitlines()]
    return [' '.join(part.split()) for part in re.split(r'\n\s*\n', '\n'.join(lines)) if part.strip()]


def contains(draft, passage):
    required = paragraphs(passage)
    return any(draft[i:i + len(required)] == required for i in range(len(draft) - len(required) + 1))


def dispatch(api, root, args):
    if '-' in args.source and (len(args.source) != 1 or args.draft_file == '-'):
        raise api.Error('Stdin must be the sole source and cannot also supply the draft')
    if bool(args.draft_file) != bool(args.expected_revision):
        raise api.Error('--draft-file and --expected-revision are required together')
    sources, selected, seen = [], [], set()
    for source in args.source:
        label, data = ('stdin', sys.stdin.buffer.read()) if source == '-' else read_file(api, root, source, markdown=True)
        if label in seen:
            continue  # Repeated selection/retry does not multiply obligations.
        seen.add(label)
        sources.append({'path': label, 'sha256': hashlib.sha256(data).hexdigest()})
        selected.extend(passages(api, label, data.decode('utf-8')))
    revision = hashlib.sha256(json.dumps(sources, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    for number, passage in enumerate(selected, 1):
        passage['id'] = f'D{number:04d}'
    value = {'revision': revision, 'sources': sources, 'passages': selected,
             'scope': 'Selected-text transport only; not scientific or semantic validation.'}
    if args.draft_file:
        if args.expected_revision != revision:
            raise api.Error('Delivery revision changed; reload selected passages before checking the draft')
        _, data = ('stdin', sys.stdin.buffer.read()) if args.draft_file == '-' else read_file(api, root, args.draft_file)
        draft = paragraphs(data.decode('utf-8'))
        value['missed'] = [p for p in selected if not contains(draft, p['text'])]
        value['ok'] = not value['missed']
    return value


def render(value):
    return '\n\n'.join(p['text'] for p in value['passages'])
