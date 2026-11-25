#!/usr/bin/env python3
"""Bounded host interface for opt-in general learning preferences.

Profile access is host-isolated; explicit project contributions update only canonical CONTEXT.
"""
from __future__ import annotations
import argparse
import hashlib
import fcntl
import json
import os
from pathlib import Path
import tempfile
from datetime import datetime, timezone

CONCEPTS = ('uncertainty', 'causality', 'evidence-quality', 'experimental-design', 'tradeoffs', 'reproducibility')
LEVELS = ('unknown', 'learning', 'practiced', 'confirmed')
EVIDENCE = ('none', 'self-report', 'inferred', 'demonstration-confirmed-by-user')
DIMENSIONS = ('definition', 'explanation', 'calculation', 'application', 'limits')
MODES = ('delegated', 'assist', 'collaborate')
CONSENT = 'general-concepts-only-v1'


def validate(value):
    if not isinstance(value, dict) or set(value) != {'schema', 'consent', 'concepts'}:
        raise ValueError('Profile accepts only schema, consent and bounded general concepts')
    if type(value['schema']) is not int or value['schema'] != 1 or value['consent'] != CONSENT or not isinstance(value['concepts'], dict):
        raise ValueError('Invalid profile schema or explicit consent')
    for concept, dimensions in value['concepts'].items():
        if concept not in CONCEPTS or not isinstance(dimensions, dict):
            raise ValueError('Unknown general concept')
        for dimension, entry in dimensions.items():
            if dimension not in DIMENSIONS or not isinstance(entry, dict) or set(entry) != {'level', 'evidence', 'confirmed_at'}:
                raise ValueError('Unknown dimension or extra project data')
            level, evidence = entry['level'], entry['evidence']
            allowed = {'unknown': ('none',), 'learning': ('self-report', 'inferred'),
                       'practiced': ('self-report',), 'confirmed': ('demonstration-confirmed-by-user',)}
            if level not in allowed or evidence not in allowed[level]:
                raise ValueError('Incoherent level and evidence')
            stamp = entry['confirmed_at']
            if level == 'confirmed':
                if not isinstance(stamp, str):
                    raise ValueError('Confirmation time is required')
                parsed = datetime.strptime(stamp, '%Y-%m-%dT%H:%M:%SZ')
                if parsed.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
                    raise ValueError('Confirmation time cannot be in the future')
            elif stamp is not None:
                raise ValueError('Only confirmed demonstrations have a confirmation time')
    return value


def read_profile(path):
    path = Path(path)
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError('Profile symlinks are forbidden')
    if path.stat().st_size > 8192:
        raise ValueError('Profile exceeds bounded size')
    raw = path.read_bytes()
    return validate(json.loads(raw)), hashlib.sha256(raw).hexdigest()


def _write(path, value):
    path = Path(path)
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError('Profile symlinks are forbidden')
    raw = (json.dumps(validate(value), sort_keys=True, indent=2) + '\n').encode()
    fd, temporary = tempfile.mkstemp(prefix='.learning-', dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {'profile_hash': hashlib.sha256(raw).hexdigest(), 'profile': value}


def session_contract(mode, intent, contribution, view='researcher'):
    if mode not in MODES or view not in ('researcher', 'designer', 'teach-me'):
        raise ValueError('Unsupported mode or view')
    for text in (intent, contribution):
        if not isinstance(text, str) or not text.strip() or len(text) > 4096:
            raise ValueError('Provide bounded project-local intent and contribution')
    return {'mode': mode, 'view': view, 'project_local': {'intent': intent, 'contribution': contribution},
            'persisted': False, 'profile_access': False,
            'responsibility': {'delegated': 'agent proposes and verifies; user retains goal and authority',
                               'assist': 'user leads; agent answers and checks selected work',
                               'collaborate': 'user and agent compare contributions before synthesis'}[mode],
            'integration': 'Preserve user contribution attribution; check conflicts against evidence and HARD constraints; ask only on consequential ambiguity',
            'view_contract': {'researcher': 'Show evidence, uncertainty and next decision',
                              'designer': 'Show alternatives, dependencies, tradeoffs and verification criteria',
                              'teach-me': 'Explain a general concept, invite a concrete demonstration, distinguish inference from user-confirmed ability'}[view],
            'switching': 'Mode may change each turn on explicit request; no persistent ability inference or authority expansion'}



def _contribution_locked(ris, root, args):
    """Append attributed input to the existing authority, never a parallel goal store."""
    ris_delivery = ris.companion('ris_delivery')
    cfg = ris.config(root)
    if cfg['recording_policy'] != 'significant' and not args.authorize_record:
        raise ris.Error('Recording policy requires explicit --authorize-record')
    _, raw = ris_delivery.read_file(ris, root, args.input)
    if len(raw) > 65536:
        raise ris.Error('Contribution input exceeds 64 KiB')
    payload = json.loads(raw)
    required = {'project_id', 'attributed_to', 'contributor', 'intent', 'purpose', 'constraints', 'hypotheses', 'observations', 'decision', 'goal_change'}
    if not isinstance(payload, dict) or set(payload) != required:
        raise ris.Error('Contribution requires the documented exact attributed fields')
    if payload['project_id'] != cfg['project_id']:
        raise ris.Error('Contribution project_id must match this exact project')
    for key in ('attributed_to', 'intent'):
        if not isinstance(payload[key], str) or not payload[key].strip() or len(payload[key]) > 4096:
            raise ris.Error('Bounded attribution and intent are required')
    if payload['contributor'] not in ('user', 'agent'):
        raise ris.Error('contributor must be user or agent')
    purpose = payload['purpose']
    if not isinstance(purpose, dict) or set(purpose) != {'status', 'text'} or purpose['status'] not in ('INFERRED', 'PROPOSED', 'USER_STATED') or not isinstance(purpose['text'], str) or not purpose['text'].strip() or len(purpose['text']) > 4096:
        raise ris.Error('Purpose requires an explicit INFERRED, PROPOSED or USER_STATED label and text')
    if purpose['status'] == 'USER_STATED' and payload['contributor'] != 'user':
        raise ris.Error('Agent purpose cannot become user-stated')
    for key in ('constraints', 'hypotheses', 'observations'):
        if not isinstance(payload[key], list) or len(payload[key]) > 32 or any(not isinstance(x,str) or not x.strip() or len(x)>4096 for x in payload[key]):
            raise ris.Error('Contributions require bounded explicit string lists')
    decision = payload['decision']
    if not isinstance(decision, dict) or set(decision) != {'kind', 'reason'} or decision['kind'] not in ('NO_DECISION', 'USER_ACCEPTS', 'USER_REJECTS', 'USER_DEFERS') or not isinstance(decision['reason'],str) or not decision['reason'].strip() or len(decision['reason']) > 4096:
        raise ris.Error('Explicit user decision or NO_DECISION and reason required')
    if decision['kind'] != 'NO_DECISION' and payload['contributor'] != 'user':
        raise ris.Error('Agent cannot assert a user decision')
    goal = payload['goal_change']
    if goal is not None and (not isinstance(goal,str) or not goal.strip() or len(goal)>4096):
        raise ris.Error('goal_change must be null or bounded text')
    if goal is not None and (not args.user_approved_goal_change or payload['contributor'] != 'user' or decision['kind'] != 'USER_ACCEPTS'):
        raise ris.Error('Changed goal requires explicit user approval and USER_ACCEPTS decision')
    if args.user_approved_goal_change and goal is None:
        raise ris.Error('Approval must bind an exact proposed goal change')
    relative = ris.research_path(cfg, 'research/CONTEXT.md')
    _, current = ris_delivery.read_file(ris, root, relative)
    if hashlib.sha256(current).hexdigest() != args.expected_hash:
        raise ris.Error('Context changed; inspect exact current revision first')
    text = current.decode('utf-8')
    metadata = ris.frontmatter(text)
    if metadata.get('project_id') != cfg['project_id'] or metadata.get('kind') != 'context' or not metadata.get('ris_id'):
        raise ris.Error('Canonical CONTEXT identity mismatch')
    if goal is not None:
        heading = '## 지금 해결할 질문\n'
        if text.count(heading) != 1:
            raise ris.Error('Canonical question heading changed; review CONTEXT before goal integration')
        prefix, rest = text.split(heading, 1)
        if '\n## ' not in rest:
            raise ris.Error('Canonical question boundary missing')
        _, remainder = rest.split('\n## ', 1)
        text = prefix + heading + goal.strip() + '\n\n## ' + remainder
    stamp = {'at': ris.timestamp(), 'context_preimage_sha256': args.expected_hash,
             'observation_status': 'ATTRIBUTED_NOT_INDEPENDENTLY_VERIFIED',
             'goal_changed_by_explicit_user_decision': goal is not None,
             'profile_access': False}
    # Attribution is historical input. Only the canonical question section above is a current goal.
    record = {'contribution': payload, 'stamp': stamp,
              'authority': 'Attributed input in canonical CONTEXT; inferred/proposed purpose is not adopted goal; constraints require existing goal/HARD-constraint decision process'}
    rendered = text + '\n\n### Attributed research contribution\n```json\n' + json.dumps(record, ensure_ascii=False, indent=2) + '\n```\n'
    # Hold one project lock across policy read, CAS and commit; safe_update would relock.
    latest_cfg = ris.config(root)
    if latest_cfg['project_id'] != cfg['project_id'] or (latest_cfg['recording_policy'] != 'significant' and not args.authorize_record):
        raise ris.Error('Project identity or recording policy changed; review authority again')
    history = ris.inside(root, '.ris/history')
    history.mkdir(exist_ok=True)
    backup = history / (args.expected_hash + '.md')
    if backup.exists():
        if backup.read_bytes() != current:
            raise ris.Error('Context history preimage mismatch')
    else:
        ris.atomic_note_write(backup, current)
    ris.atomic_note_write(ris.inside(root, relative), rendered.encode('utf-8'), expected=current)
    result = {'status':'updated', 'path':relative, 'sha256':hashlib.sha256(rendered.encode()).hexdigest(),
              'backup':backup.relative_to(root).as_posix()}
    return dict(result, contribution_stamp=stamp, project_local=True, profile_access=False)


def contribution(ris, root, args):
    with ris.project_lock(root):
        return _contribution_locked(ris, root, args)


def lesson(mode, requested, concept, supplied_view):
    # Deliberately takes values only: no profile path or project/history lookup.
    view = json.loads(supplied_view)
    validate(view)
    if mode == 'delegated' or not requested:
        return {'teaching': False, 'reason': 'Delegated work or no explicit lesson request',
                'profile_access': False, 'profile_updated': False}
    dimensions = view['concepts'].get(concept, {})
    rank = {'unknown':0, 'learning':1, 'practiced':2, 'confirmed':3}
    focus = min(DIMENSIONS, key=lambda d: rank[dimensions.get(d, {'level':'unknown'})['level']])
    examples = {
        'uncertainty': ('Estimate 10 ± 2 units.', 'Lower=10-2=8; upper=10+2=12. This interval is an assumption, not a confidence guarantee.', 'For 20 ± 3, calculate both bounds.', '17 and 23'),
        'causality': ('Synthetic treatment change=5; control change=2.', 'Adjusted change=5-2=3 units. This requires comparable trends; arithmetic alone does not prove causation.', 'Treatment change 8, control 3: calculate adjusted change.', '5 units'),
        'evidence-quality': ('Independent fixture reports 8 successes in 10 trials.', 'Observed fraction=8/10=0.8. A small sample and source independence limit generalization.', 'For 9 successes in 12 trials, compute the fraction.', '0.75'),
        'experimental-design': ('Two synthetic groups each contain 4 items.', 'Total=4+4=8; allocation fraction=4/8=0.5. Random allocation and measurement control remain separate requirements.', 'For 6 items per group, compute total and fraction.', '12 and 0.5'),
        'tradeoffs': ('Option A costs 4 with benefit 8; B costs 3 with benefit 5.', 'A benefit/cost=8/4=2; B=5/3≈1.67. This ranking assumes linear comparable benefits and ignores hard constraints.', 'Option C costs 5 with benefit 10: compute ratio.', '2'),
        'reproducibility': ('Two deterministic fixture runs return 6 and 6.', 'Absolute difference=|6-6|=0. Identical outputs support repeatability for these inputs, not external validity.', 'Runs return 6 and 7: compute difference.', '1')}
    scene, calculation, exercise, answer = examples[concept]
    fully_confirmed = all(dimensions.get(d, {}).get('level') == 'confirmed' for d in DIMENSIONS)
    if fully_confirmed:
        return {'teaching':True, 'concept':concept, 'focus_dimension':'transfer', 'basics_skipped':True,
                'transfer_task':{'synthetic':True, 'scene':scene,
                                 'question':'Apply this concept to a changed assumption, state which conclusion no longer follows, and propose a verification check. No prerequisite lesson is assigned.'},
                'ability_assessment':'NOT_ASSESSED: historical confirmed dimensions do not prove transfer or cognitive improvement',
                'profile_access':False, 'profile_updated':False}
    definitions = {'uncertainty':'Uncertainty describes what remains unknown about a value or conclusion; a bound and a confidence interval are different claims.',
                   'causality':'Causality concerns what would change under an intervention, beyond observed association.',
                   'evidence-quality':'Evidence quality concerns how well a source and method support a specified claim.',
                   'experimental-design':'Experimental design specifies comparisons, allocation and measurement before observing results.',
                   'tradeoffs':'A tradeoff exchanges one valued outcome for another under explicit constraints.',
                   'reproducibility':'Reproducibility asks whether specified methods and inputs permit another run to recover the reported result.'}
    content = {'synthetic':True, 'scene':scene}
    if focus == 'definition':
        content.update(prerequisite=definitions[concept], explanation='Identify the claim, its inputs and the kind of conclusion before using the arithmetic.')
        exercise, answer = 'Restate the definition and name one conclusion the definition alone does not establish.', 'A definition does not establish the truth of this case or its scientific validity.'
    elif focus == 'explanation':
        content.update(reasoning='Explain why the comparison or operation addresses the stated claim, then identify its assumption.', calculation=calculation)
        exercise, answer = 'Explain each input and why the operation fits the question, without computing a new result.', 'Explain the input meaning, the operation and the assumption; arithmetic alone is insufficient.'
    elif focus == 'calculation':
        content['calculation'] = calculation
    elif focus == 'application':
        content.update(application='Choose whether this model applies to a new case where an input is missing. Preserve the missing input as unknown before selecting the computation.', worked_decision='Do not substitute zero for the missing input; obtain evidence or report an unresolved result.')
        exercise, answer = 'One required input is unavailable: choose compute, infer zero, or hold and explain.', 'Hold the affected calculation; request the missing evidence or report unknown.'
    elif focus == 'limits':
        content.update(limitation_review=calculation, counterexample='The arithmetic can remain identical while an assumption fails; the scientific conclusion may then be unsupported.')
        exercise, answer = 'Name an assumption whose failure would invalidate transfer and specify a falsifying check.', 'Check measurement, comparison or boundary assumptions using independent evidence before transferring the result.'
    return {'teaching':True, 'concept':concept, 'focus_dimension':focus,
            'adaptation':'Start with the least established supplied dimension; confirmed dimensions still have transfer limits',
            'basics_skipped':False, 'worked_application':content,
            'practice':{'question':exercise,'answer':answer},
            'ability_assessment':'NOT_ASSESSED: an example or inferred profile level is not actual confirmed ability; obtain a user-confirmed demonstration before explicit host profile set',
            'profile_access':False, 'profile_updated':False, 'project_transfer':'No project text or output is accepted into the supplied general view'}

def add_parser(sub):
    command = sub.add_parser('learning', help='Explicit opt-in bounded general learning profile')
    actions = command.add_subparsers(dest='learning_action', required=True)
    for action in ('create', 'inspect', 'set', 'erase', 'delete'):
        parser = actions.add_parser(action)
        parser.add_argument('--profile', type=Path, required=True, help='Explicit host-selected file; never discovered')
        if action == 'create':
            parser.add_argument('--consent', choices=[CONSENT], required=True)
        if action in ('set', 'erase', 'delete'):
            parser.add_argument('--expected-hash', required=True)
        if action in ('set', 'erase'):
            parser.add_argument('--concept', choices=CONCEPTS, required=True)
            parser.add_argument('--dimension', choices=DIMENSIONS, required=action=='set', help='Omit for erase to remove the whole selected concept')
        if action == 'set':
            parser.add_argument('--level', choices=LEVELS, required=True)
            parser.add_argument('--evidence', choices=EVIDENCE, required=True)
            parser.add_argument('--user-confirmed', action='store_true')
    integrate = actions.add_parser('contribute', help='CAS-bound attributed contribution to canonical project CONTEXT')
    integrate.add_argument('--input', required=True, help='Project-relative typed JSON contribution')
    integrate.add_argument('--expected-hash', required=True)
    integrate.add_argument('--authorize-record', action='store_true')
    integrate.add_argument('--user-approved-goal-change', action='store_true')
    teach = actions.add_parser('lesson', help='Optional worked application from a supplied bounded general dimension view')
    teach.add_argument('--mode', choices=MODES, required=True)
    teach.add_argument('--requested', action='store_true')
    teach.add_argument('--concept', choices=CONCEPTS, required=True)
    teach.add_argument('--dimension-view', required=True, help='Typed general profile payload only; no file lookup')
    session = actions.add_parser('session')
    session.add_argument('--mode', choices=MODES, required=True)
    session.add_argument('--view', choices=['researcher', 'designer', 'teach-me'], default='researcher')
    session.add_argument('--intent', required=True)
    session.add_argument('--contribution', required=True)


def _dispatch(ris, root, args):
    try:
        action = args.learning_action
        if action == 'contribute':
            return contribution(ris, root, args)
        if action == 'lesson':
            return lesson(args.mode, args.requested, args.concept, args.dimension_view)
        if action == 'session':
            return session_contract(args.mode, args.intent, args.contribution, args.view)
        path = args.profile
        if action == 'create':
            # Exclusive create prevents overwriting an existing profile.
            value = {'schema': 1, 'consent': args.consent, 'concepts': {}}
            validate(value)
            if path.is_symlink() or any(p.is_symlink() for p in path.parents):
                raise ValueError('Profile symlinks are forbidden')
            raw = (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(raw)
            return {'profile': value, 'profile_hash': hashlib.sha256(raw).hexdigest()}
        value, digest = read_profile(path)
        if action == 'inspect':
            return {'profile': value, 'profile_hash': digest}
        if digest != args.expected_hash:
            raise ValueError('Profile changed; inspect before editing or deleting')
        if action == 'erase':
            if args.dimension is None:
                value['concepts'].pop(args.concept, None)
            else:
                dimensions = value['concepts'].get(args.concept, {})
                dimensions.pop(args.dimension, None)
                if not dimensions:
                    value['concepts'].pop(args.concept, None)
            return _write(path, value)
        if action == 'delete':
            path.unlink()
            return {'deleted': True, 'consent_revoked': True}
        if action == 'set':
            if args.evidence == 'demonstration-confirmed-by-user' and not args.user_confirmed:
                raise ValueError('Explicit --user-confirmed is required for demonstrated ability')
            value['concepts'].setdefault(args.concept, {})[args.dimension] = {
                'level': args.level, 'evidence': args.evidence,
                'confirmed_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') if args.level == 'confirmed' else None}
            return _write(path, value)
        raise ValueError('Unknown learning action')
    except (ValueError, OSError, TypeError) as exc:
        raise ris.Error(str(exc)) from exc


def dispatch(ris, root, args):
    """Serialize cooperative host calls without leaving a profile sidecar."""
    if args.learning_action in ('session', 'contribute', 'lesson'):
        return _dispatch(ris, root, args)
    try:
        configured = os.environ.get('RIS_LEARNING_PROFILE_ROOT')
        if not configured:
            raise ValueError('Trusted host must provision RIS_LEARNING_PROFILE_ROOT outside projects')
        parent = Path(configured)
        if not parent.is_absolute() or not parent.is_dir():
            raise ValueError('Host profile root must be an existing absolute directory')
        if args.profile != parent / 'learning-profile.json':
            raise ValueError('Only the host-provisioned learning-profile.json is accessible')
        if root is not None and parent.resolve().is_relative_to(Path(root).resolve()):
            raise ValueError('Profile root must be outside the selected project')
        if parent.stat().st_uid != os.getuid() or parent.stat().st_mode & 0o077:
            raise ValueError('Host profile root must be user-owned with mode 0700')
        if parent.is_symlink() or any(p.is_symlink() for p in parent.parents):
            raise ValueError('Profile symlinks are forbidden')
        fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            return _dispatch(ris, root, args)
        finally:
            os.close(fd)
    except (OSError, ValueError) as exc:
        raise ris.Error(str(exc)) from exc
