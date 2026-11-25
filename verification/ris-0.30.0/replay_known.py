"""Development regression only. Replays disclosed sources and missing information through real CLI."""
import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def describe(case, raw):
    if case == 'R01':
        rows = list(csv.DictReader(line for line in raw.decode().splitlines() if not line.startswith('#')))
        last = rows[-1]
        may = next(x for x in rows if x['year'] == last['year'] and x['month'] == '5')
        differences = {k: str(Decimal(last[k])-Decimal(may[k])) for k in ('average','deseasonalized')}
        assert differences == {'average':'-5.65','deseasonalized':'0.94'}
        assert all(int(x['ndays']) > 0 and Decimal(x['unc']) > 0 for x in (may,last))
        assert 'Missing months have been interpolated' in raw.decode() and 'no information for SIO data' in raw.decode()
        return (f"The October 2026 monthly mean was {last['average']}, down 5.65 from May. "
                f"The deseasonalized series rose by 0.94 over those months. The raw decrease does not establish a declining trend.",
                "NOAA flags interpolated months with negative standard deviation and uncertainty. "
                "For the early Scripps series the negative fields mark unavailable quality statistics. "
                "The May and October rows compared here have positive day counts and uncertainty.",
                "Header lines 25–34 and May/October 2026 rows",differences)
    packet = json.loads(raw)
    times = [item['properties']['time'] for item in packet['features']]
    def iso(value):
        return datetime.fromtimestamp(value/1000,timezone.utc).isoformat(timespec='milliseconds')
    span = [iso(min(times)),iso(max(times))]
    assert span == ['2026-11-24T01:32:42.417+00:00','2026-11-24T23:29:55.097+00:00']
    return (f"The {len(times)} event origins in the frozen packet run from {span[0]} to {span[1]}.",
            f"The feed was generated at {iso(packet['metadata']['generated'])}. "
            "Event-origin endpoints describe observed events in this packet and do not measure catalogue completeness.",
            "features[*].properties.time and metadata.generated",dict(count=len(times),endpoints=span))


def replay(cli, source, out, case):
    project = out/case
    project.mkdir()
    report=[]
    def invoke(args, okay=True):
        proc=subprocess.run([sys.executable,str(cli),'--project',str(project),*args],capture_output=True,text=True)
        value=json.loads(proc.stdout or proc.stderr)
        report.append(dict(args=args,exit=proc.returncode,response=value if 'proposals' not in value else {
            k:value[k] for k in ('revision','delivery','direct_edit_pending','file_sha256') if k in value}))
        (project/'commands.json').write_text(json.dumps(report,indent=2))
        if (proc.returncode == 0) != okay:
            raise RuntimeError(str((args,proc.returncode,value)))
        return value
    prev=source/'2026-11-25-self-critical-0.29.0/development-replay'/case
    if (source/'historical'/case/'source.json').is_file():
        meta=json.loads((source/'historical'/case/'source.json').read_text())
        frozen=source/'final-source/known'/case
        raw=(frozen/meta['source_file']).read_bytes()
        answer=frozen/'historical-answer.txt'
    else:
        meta=json.loads((prev/'packet/source.json').read_text())
        raw=(source/'2026-11-25-self-critical/evaluation/real/sources'/meta['source_file']).read_bytes()
        answer=prev/'first/answer.txt'
    assert sha(raw)==meta['source_sha256']
    (project/meta['source_file']).write_bytes(raw)
    identity=invoke(['init','--goal',meta['objective']])['project_id']
    revision=0
    idx=0
    def change(action,payload,okay=True):
        nonlocal idx,revision
        idx+=1
        path=f'input-{idx:02}.json'
        (project/path).write_text(json.dumps(dict(payload,project_id=identity,question_id=case),ensure_ascii=False))
        result=invoke(['findings',action,'--question',case,'--input',path,'--expected-revision',str(revision),'--idempotency-key',f'op-{idx}'],okay)
        if okay: revision=result['revision']
        return result
    q='What are the method qualifications on these data?' if case=='R01' else 'What is the observed event-origin interval?'
    change('obligate',dict(obligation=dict(id='scope',specified_by='regression-oracle',question=q,expected_scope={'topic':case})))
    stmt,lim,loc,values=describe(case,raw)
    item=dict(id='F1',statement=stmt,status='CONFIRMED',conditions=dict(dataset='frozen source only'),
              axes=dict(topic=case,origin='calculation',validation='development arithmetic check',audit='not independently audited'),
              relations=[],provenance=[dict(source='file:'+meta['source_file'],locator=loc,revision='sha256:'+sha(raw),limitations=[lim])])
    change('propose',dict(finding=item,owner='development-producer'))
    node=dict(id='F1',owner='development-producer',note='Development fixture, scoped to the frozen source.')
    accepted=change('accept',node)['revision']
    old=answer.read_bytes()
    (project/'historical-answer.txt').write_bytes(old)
    change('return',dict(node,finding_revision=accepted,transcript=stmt),False)
    passage='\n\n'.join([stmt,lim,'Conditions: dataset=frozen source only.'])
    change('return',dict(node,finding_revision=accepted,transcript=passage))
    change('integrate',node)
    change('resolve',dict(id='scope',specified_by='regression-oracle',finding_ids=['F1'],text=stmt))
    change('disposition',dict(id='F1',specified_by='regression-oracle',disposition='USER_DELIVERY',
                              decision_critical=True,reason='Changes interpretation for the user',condition='Frozen record'))
    negative=change('deliver',dict(draft='historical-answer.txt'),False)
    (project/'corrected-passage.md').write_text(passage+'\n')
    good=change('deliver',dict(draft='corrected-passage.md'))
    fresh=invoke(['findings','inspect','--question',case,'--node-id','F1'])
    assert fresh['delivery_current'] and fresh['delivery']==good['delivery']
    return dict(values=values,historical_answer_sha256=sha(old),source_sha256=sha(raw),negative=negative,
                accepted_revision=revision,corrected_passage=passage,receipt=good['delivery'],
                scope='Scripted developer fixtures, historical-answer bytes; no autonomous role, user delivery or independent semantic score.')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('cli',type=Path)
    parser.add_argument('sources',type=Path)
    parser.add_argument('new_output',type=Path)
    args=parser.parse_args()
    args.new_output.mkdir()
    results={case:replay(args.cli.resolve(),args.sources,args.new_output,case) for case in ('R01','R02')}
    (args.new_output/'results.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(results,indent=2))
