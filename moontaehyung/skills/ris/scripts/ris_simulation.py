"""Run a reviewed, project-owned numerical model with frozen inputs and bounded output."""
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import stat
import subprocess
import tempfile

MAX_INPUT = 8 * 1024 * 1024
MAX_OUTPUT = 256 * 1024


def add_parser(sub):
    cmd = sub.add_parser('simulate', help='Execute a reviewed Python model on an isolated JSON case')
    cmd.add_argument('--model', required=True, help='Project-relative Python source')
    cmd.add_argument('--case', required=True, help='Project-relative JSON case')
    cmd.add_argument('--record-result', nargs=3, metavar=('QUESTION','FINDING','OUTPUT_FIELD'),
                     help='Propose one decision-relevant output from this run to its canonical question')
    cmd.add_argument('--expected-revision', type=int, help='Inspected findings revision for a proposal')
    cmd.add_argument('--authorize-record', action='store_true', help='Explicit bounded recording under restricted policy')
    cmd.add_argument('--timeout', type=int, default=10, choices=range(1, 61), metavar='1..60')


def read_input(api, root, relative, suffix):
    path = api.inside(root, relative)
    if path.suffix != suffix:
        raise api.Error('Expected a ' + suffix + ' input')
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as stream:
        pre = os.fstat(stream.fileno())
        if not stat.S_ISREG(pre.st_mode) or pre.st_size > MAX_INPUT:
            raise api.Error('Model inputs must be bounded regular project files')
        data = stream.read(MAX_INPUT + 1)
        post = api.inside(root, relative).stat()
    if (pre.st_dev, pre.st_ino, pre.st_mtime_ns, pre.st_ctime_ns, pre.st_size) != (post.st_dev, post.st_ino, post.st_mtime_ns, post.st_ctime_ns, len(data)):
        raise api.Error('Input changed during selection; read the new revision')
    return data


def receipt(relative, data):
    return {'path': relative, 'sha256': hashlib.sha256(data).hexdigest()}


def finite_json(raw):
    value = json.loads(raw)
    # Reject both literal NaN and an exponent which overflowed the platform float.
    json.dumps(value, allow_nan=False)
    return value


def run_model(api, args, model, case, spec, info):
    try:
        ns = api.companion('ris_isolated').python_namespace()
        with tempfile.TemporaryDirectory(prefix='ris-model-') as temp:
            folder = Path(temp)
            (folder/'model.py').write_bytes(model)
            (folder/'case.json').write_bytes(case)
            cmd = ns + ['--ro-bind', temp, '/inputs', '--chdir', '/inputs', '--',
                        '/usr/bin/prlimit', '--cpu=' + str(args.timeout), '--as=536870912',
                        '--fsize=' + str(MAX_OUTPUT), '--nproc=1', '--core=0', '--',
                        '/usr/bin/python3', '-ISB', '/inputs/model.py', '/inputs/case.json']
            # Only reviewed model and case enter /inputs. stdout/stderr are anonymous bounded files.
            with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
                run = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                     env={}, timeout=args.timeout)
                out.seek(0)
                raw = out.read(MAX_OUTPUT + 1)
                err.seek(0)
                diagnostic = err.read(4096).decode(errors='replace')
                stderr_size = os.fstat(err.fileno()).st_size
        if len(raw) >= MAX_OUTPUT or stderr_size >= MAX_OUTPUT:
            return dict(info, execution='BUDGET_EXHAUSTED', diagnostic='Model output limit reached')
        if run.returncode:
            return dict(info, execution='FAILED', returncode=run.returncode, diagnostic=diagnostic)
        result = finite_json(raw)
        if not isinstance(result, dict) or not result:
            raise ValueError('Expected one nonempty bounded JSON result object')
        info['environment']['python'] = subprocess.check_output(['/usr/bin/python3', '-V'], text=True).strip()
        return dict(info, ok=True, execution='EXECUTED', output_sha256=hashlib.sha256(raw).hexdigest(),
                    result=result, validation='REQUIRES_SEPARATE_CHECK', limits=spec['limits'])
    except subprocess.TimeoutExpired:
        return dict(info, execution='BUDGET_EXHAUSTED', diagnostic='Wall time limit reached')
    except (OSError, RuntimeError, ValueError, RecursionError) as exc:
        return dict(info, execution='BLOCKED' if isinstance(exc, (OSError, RuntimeError)) else 'FAILED',
                    diagnostic=str(exc))


def dispatch(api, root, args):
    if bool(args.record_result) != (args.expected_revision is not None):
        raise api.Error('Use --record-result and --expected-revision together')
    cfg = api.config(root)
    model = read_input(api, root, args.model, '.py')
    case = read_input(api, root, args.case, '.json')
    spec = finite_json(case)
    texts = ('question', 'model', 'method', 'assumptions', 'boundary', 'limits')
    if not isinstance(spec, dict) or any(not isinstance(spec.get(k), str) or not spec[k].strip() for k in texts):
        raise api.Error('Case must describe question, model, method, assumptions, boundary and limits')
    if (not isinstance(spec.get('inputs'), dict) or not isinstance(spec.get('units'), dict)
            or not spec['inputs'] or spec['inputs'].keys() != spec['units'].keys()
            or any(not isinstance(unit, str) or not unit.strip() for unit in spec['units'].values())
            or 'seed' not in spec or spec['seed'] is not None and type(spec['seed']) is not int):
        raise api.Error('Provide named inputs with matching units and integer seed or null for deterministic models')
    info = {'project_id': cfg['project_id'], 'model': receipt(args.model, model),
            'case': receipt(args.case, case), 'seed': spec['seed'], 'timeout_s': args.timeout,
            'observed_at': api.timestamp(), 'execution': 'NOT_RUN', 'ok': False,
            'environment': {'kernel': platform.release(), 'machine': platform.machine()}}
    if args.record_result:
        question, finding_id, field = args.record_result
        findings = api.companion('ris_findings')
        findings.location(api, cfg, question)
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', finding_id):
            raise api.Error('Expected a stable finding ID of 1..64 letters, digits, hyphens or underscores')
        if cfg['recording_policy'] != 'significant' and not args.authorize_record:
            raise api.Error('Selected result recording requires explicit authority under this project policy')
        units = spec.get('output_units')
        if not isinstance(units, dict) or not isinstance(units.get(field), str) or not units[field].strip():
            raise api.Error('Pin the selected result field and its unit in case.output_units')
    result = run_model(api, args, model, case, spec, info)
    if not args.record_result:
        return result
    if result['ok']:
        selected = result['result'].get(field)
        numbers = selected if isinstance(selected, list) else [selected]
        if not 1 <= len(numbers) <= 64 or any(type(value) not in (int,float) for value in numbers):
            return dict(result, ok=False, recording='BLOCKED',
                        diagnostic='Selected field must contain one to 64 numeric results')
        statement = f"{field} = {json.dumps(selected, allow_nan=False)} {units[field]}."
        status = 'CONFIRMED'
    else:
        statement = f"The simulation ended with {result['execution']}. {field} has no accepted value."
        status = 'BLOCKED'
    sources = [{'source': 'file:'+record['path'], 'locator': locator,
                'revision': 'sha256:'+record['sha256'], 'limitations': [spec['limits']]}
               for record, locator in ((info['model'], 'executed model source'),
                                       (info['case'], 'inputs, units, boundaries and seed'))]
    finding = {'id': finding_id, 'statement': statement, 'status': status,
               'conditions': {'model': spec['model'], 'boundary': spec['boundary'],
                              'assumptions': spec['assumptions']},
               'axes': {'generation': 'simulation', 'execution': result['execution'],
                        'verification': 'requires separate check', 'audit': 'pending'},
               'relations': [], 'provenance': sources}
    if result['ok']:
        finding['axes'].update(result_sha256=result['output_sha256'], python=result['environment']['python'])
    try:
        inputs_current = all(api.study_evidence_hash(root, record['path']) == record
                             for record in (info['model'], info['case']))
    except (api.Error, OSError):
        inputs_current = False
    if not inputs_current:
        return dict(result, ok=False, recording='BLOCKED', pending_proposal=finding,
                    diagnostic='A selected input changed during execution; review its revision')
    try:
        saved = findings.propose_generated(api, root, question, args.expected_revision,
                                           'simulation-'+finding_id, 'engineer', finding,
                                           authorized=args.authorize_record)
    except api.Error as exc:
        return dict(result, ok=False, recording='BLOCKED', diagnostic=str(exc),
                    pending_proposal=finding)
    return dict(result, recording='PROPOSED', question=question, finding_id=finding_id,
                findings_revision=saved['revision'])
