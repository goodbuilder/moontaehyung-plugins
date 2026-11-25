"""Independent canonical transport workflow; synthetic inputs only."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
CLI='/home/moontaehyung/plugins/moontaehyung/skills/ris/scripts/ris.py'
records=[]
with tempfile.TemporaryDirectory(prefix='ris-independent-findings-') as name:
    root=Path(name)
    initial=subprocess.run([sys.executable,CLI,'--project',name,'init','--recording-policy','manual'],capture_output=True,text=True)
    assert initial.returncode==0
    pid=next(json.loads(line.split(':',1)[1]) for line in (root/'.ris/project.yaml').read_text().splitlines() if line.startswith('project_id:'))
    revision=0
    serial=0
    def call(label,action,payload=None,success=True,authorize=True,rev=None,key=None):
        global revision,serial
        serial+=1
        argv=[sys.executable,CLI,'--project',name,'findings',action]
        if action!='inspect':
            (root/'payload.json').write_text(json.dumps(dict(project_id=pid,**(payload or {}))))
            argv+=['--input','payload.json','--expected-revision',str(revision if rev is None else rev),'--idempotency-key',key or 'audit-'+str(serial)]
            if authorize: argv+=['--authorize-record']
        proc=subprocess.run(argv,capture_output=True,text=True)
        item={'name':label,'command':argv,'returncode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr}
        try: item['parsed']=json.loads(proc.stdout)
        except ValueError: pass
        records.append(item)
        if success:
            assert proc.returncode==0,(label,proc.stderr)
            revision=item['parsed']['revision']
        else:
            assert proc.returncode!=0,(label,proc.stdout)
        return item.get('parsed',item)
    freeze={'obligation':{'id':'timing','specified_by':'independent-reviewer','question':'What interval was measured?', 'expected_scope':{'axis':'timing'}}}
    call('manual_authority_missing_rejected','obligate',freeze,success=False,authorize=False)
    call('freeze_question_before_any_record','obligate',freeze)
    call('missing_record_delivery_rejected','deliver',{'draft':'draft.md'},success=False)
    finding={'id':'timing-fact','statement':'Measured interval is unknown.','status':'UNKNOWN','conditions':{'interval':'unknown'},'axes':{'axis':'timing'},'relations':[], 'provenance':[{'source':'synthetic.csv','locator':'rows 1-3','revision':'synthetic-v1','limitations':['Timestamps were not recorded.']}]}
    call('propose','propose',{'finding':finding,'owner':'researcher'})
    call('stale_receipt_rejected','accept',{'id':'timing-fact','owner':'researcher','note':'synthetic reviewed'},success=False,rev=0)
    call('wrong_owner_receipt_rejected','accept',{'id':'timing-fact','owner':'different-owner','note':'synthetic reviewed'},success=False)
    call('accept','accept',{'id':'timing-fact','owner':'researcher','note':'synthetic owner receipt'})
    accepted=revision
    call('stale_owner_return_rejected','return',{'id':'timing-fact','owner':'researcher','note':'receipt','finding_revision':0,'transcript':'Measured interval is unknown.\n\nTimestamps were not recorded.'},success=False)
    call('owner_return_missing_fact_rejected','return',{'id':'timing-fact','owner':'researcher','note':'receipt','finding_revision':accepted,'transcript':'Timestamps were not recorded.'},success=False)
    call('owner_return_missing_limitation_rejected','return',{'id':'timing-fact','owner':'researcher','note':'receipt','finding_revision':accepted,'transcript':'Measured interval is unknown.'},success=False)
    call('complete_owner_return','return',{'id':'timing-fact','owner':'researcher','note':'receipt','finding_revision':accepted,'transcript':'Measured interval is unknown.\n\nTimestamps were not recorded.'})
    call('integrate','integrate',{'id':'timing-fact','owner':'researcher','note':'synthetic owner receipt'})
    call('self_review_resolution_rejected','resolve',{'id':'timing','specified_by':'researcher','finding_ids':['timing-fact'],'text':'Do not infer an interval.'},success=False)
    call('resolve_frozen_question','resolve',{'id':'timing','specified_by':'independent-reviewer','finding_ids':['timing-fact'],'text':'Do not infer an interval.'})
    call('missing_disposition_rejected','deliver',{'draft':'draft.md'},success=False)
    call('independent_disposition','disposition',{'id':'timing-fact','specified_by':'independent-reviewer','disposition':'USER_DELIVERY','decision_critical':True,'reason':'Material uncertainty','condition':'synthetic-v1'})
    draft=root/'draft.md'
    draft.write_text('Do not infer an interval.\n')
    call('missing_carried_fact_rejected','deliver',{'draft':'draft.md'},success=False)
    draft.write_text('Do not infer an interval.\n\nMeasured interval is unknown.\n')
    call('missing_limitation_rejected','deliver',{'draft':'draft.md'},success=False)
    draft.write_text(draft.read_text()+'\nTimestamps were not recorded.\n')
    result=call('complete_exact_delivery','deliver',{'draft':'draft.md'})
    assert result['delivery']['scope']=='Exact transport; no semantic/scientific validation'
    inspected=call('unchanged_receipt_current','inspect')
    assert inspected['delivery_current'] is True
    draft.write_text('Changed final answer.\n')
    inspected=call('edited_draft_receipt_stale','inspect')
    assert inspected['delivery_current'] is False
    ledger=root/'.ris/research/findings/knowledge.md'
    ledger.write_text(ledger.read_text()+'\nDirect user correction.\n')
    inspected=call('direct_edit_detected','inspect')
    assert inspected['direct_edit_pending']
    call('unreviewed_direct_edit_blocks_write','disposition',{'id':'timing-fact'},success=False)
    preimage=ledger.read_bytes()
    call('review_exact_direct_edit','review-edit',{'file_sha256':inspected['file_sha256'],'reason':'Review synthetic correction'})
    assert any(p.read_bytes()==preimage for p in (root/'.ris/history').glob('*.md'))
    inspected=call('review_invalidates_receipts','inspect')
    assert inspected['proposals'][0]['state']=='UNVERIFIED'
    assert inspected['obligations'][0]['state']=='INVALIDATED'
    assert inspected['delivery'] is None
    # A malformed JSON top level must remain untouched; inspect its error behavior.
    text=ledger.read_text(); begin='<!-- ris:findings -->\n```json\n'; end='\n```\n<!-- /ris:findings -->'
    ledger.write_text(text.split(begin)[0]+begin+'null'+end+text.split(end)[1])
    before=ledger.read_bytes()
    call('malformed_top_level_preserved','inspect',success=False)
    assert ledger.read_bytes()==before
    assert 'Traceback' not in records[-1]['stderr']
Path(__file__).with_name('findings-results-after-null-fix.json').write_text(json.dumps(records,indent=2))
for item in records:
    print(item['name'],item['returncode'], 'traceback' if 'Traceback' in item['stderr'] else '')
