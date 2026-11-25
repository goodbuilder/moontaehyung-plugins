"""Public CLI tests for knowledge governance; no providers or real experiments."""
import json
from pathlib import Path
import subprocess
import sys
import pytest

CLI=Path(__file__).resolve().parents[1]/'scripts/ris.py'

@pytest.fixture
def project(tmp_path):
    init=subprocess.run([sys.executable,str(CLI),'--project',str(tmp_path),'init','--name','test','--goal','test','--recording-policy','manual'],capture_output=True,text=True)
    assert init.returncode==0,init.stderr
    cfg={}
    for line in (tmp_path/'.ris/project.yaml').read_text().splitlines():
        k,_,v=line.partition(':'); cfg[k]=json.loads(v)
    return tmp_path,cfg['project_id']

class Flow:
    def __init__(self,project): self.root,self.project_id=project; self.revision=0; self.serial=0
    def run(self,action,payload=None,ok=True,authorize=True,revision=None,key=None,extra=()):
        args=[sys.executable,str(CLI),'--project',str(self.root),'findings',action,*extra]
        if action not in ('inspect','search'):
            self.serial+=1
            (self.root/'payload.json').write_text(json.dumps(dict(project_id=self.project_id,**payload)))
            args+=['--input','payload.json','--expected-revision',str(self.revision if revision is None else revision),'--idempotency-key',key or str(self.serial)]
            if authorize: args+=['--authorize-record']
        result=subprocess.run(args,text=True,capture_output=True)
        if ok:
            assert result.returncode==0,result.stderr
            value=json.loads(result.stdout); self.revision=value.get('revision',self.revision); return value
        assert result.returncode!=0,result.stdout
        return result.stderr
    def node(self,ident='f1',axis='timing',relations=None):
        return {'id':ident,'statement':'Actual sampling interval is unknown.' if ident=='f1' else 'A different finding '+ident+'.', 'status':'UNKNOWN','conditions':{'interval':'unknown'},'axes':{'topic':axis},'relations':relations or [], 'provenance':[{'source':'raw.csv','locator':'rows 1-3','revision':'sha256:abc','limitations':['No timestamps were recorded.']}]}
    def freeze(self,ident='o1',axis='timing'):
        return self.run('obligate',{'obligation':{'id':ident,'question':'What is measured timing?','expected_scope':{'topic':axis},'specified_by':'reviewer'}})
    def integrate(self,ident='f1'):
        for action in ('accept','return','integrate'):
            payload={'id':ident,'owner':'researcher','note':'Owner has reviewed this revision'}
            if action=='return':
                node=self.run('inspect',extra=('--node-id',ident))['proposals'][0]
                payload.update(finding_revision=node['accepted_revision'],transcript=node['finding']['statement']+'\n\nNo timestamps were recorded.\n\nConditions: interval=unknown.')
            self.run(action,payload)
    def disposition(self,ident='f1',kind='USER_DELIVERY',critical=True):
        return self.run('disposition',{'id':ident,'specified_by':'reviewer','disposition':kind,'decision_critical':critical,'reason':'Reviewed relevance','condition':'Current source revision','uncertainty_text':'The timing question remains unresolved.'})
    def resolve(self,ident='o1',finding='f1'):
        return self.run('resolve',{'id':ident,'specified_by':'reviewer','finding_ids':[finding],'text':'Timing remains unresolved; do not infer an interval.'})


def test_prefrozen_delivery_omissions_and_resume(project):
    flow=Flow(project); flow.freeze()
    flow.run('deliver',{'draft':'draft.md'},ok=False)
    flow.run('propose',{'owner':'researcher','finding':flow.node()})
    flow.run('accept',{'id':'f1','owner':'researcher','note':'recorded'})
    flow.run('deliver',{'draft':'draft.md'},ok=False)
    flow.run('return',{'id':'f1','owner':'researcher','note':'received','finding_revision':flow.revision,'transcript':'Actual sampling interval is unknown.\n\nNo timestamps were recorded.\n\nConditions: interval=unknown.'})
    flow.run('integrate',{'id':'f1','owner':'researcher','note':'integrated'})
    flow.resolve()
    assert 'disposition' in flow.run('deliver',{'draft':'draft.md'},ok=False)
    flow.disposition()
    draft=flow.root/'draft.md'; draft.write_text('Timing remains unresolved; do not infer an interval.\n\nActual sampling interval is unknown.\n')
    assert 'limitation' in flow.run('deliver',{'draft':'draft.md'},ok=False)
    draft.write_text(draft.read_text()+'\nNo timestamps were recorded.\n\nConditions: interval=unknown.\n')
    result=flow.run('deliver',{'draft':'draft.md'})
    assert result['delivery']['sha256']
    assert flow.run('inspect')['delivery']==result['delivery']
    context=subprocess.run([sys.executable,str(CLI),'--project',str(flow.root),'context','--include','.ris/research/findings/knowledge.md'],capture_output=True,text=True)
    assert context.returncode==0,context.stderr


def test_policy_cas_replay_search_and_relation(project):
    flow=Flow(project)
    assert 'policy' in flow.run('propose',{'owner':'researcher','finding':flow.node()},ok=False,authorize=False)
    flow.run('propose',{'owner':'researcher','finding':flow.node()},key='one')
    assert flow.run('propose',{'owner':'researcher','finding':flow.node()},key='one',revision=0)['replay']
    assert 'revision' in flow.run('accept',{'id':'f1','owner':'researcher','note':'x'},ok=False,revision=0)
    invalid=flow.node('f2',relations=[{'kind':'depends_on','target':'missing','conditions':{'scope':'test'},'evidence':['source:1']}])
    assert 'target' in flow.run('propose',{'owner':'researcher','finding':invalid},ok=False)
    for i in range(2,6): flow.run('propose',{'owner':'researcher','finding':flow.node('f'+str(i),'other')})
    result=flow.run('inspect',extra=('--query','different','--limit','2'))
    assert result['truncated'] and result['total_matching']==4 and len(result['proposals'])==2
    assert 'history' not in result and 'operations' not in result
    assert len(flow.run('inspect',extra=('--node-id','f1'))['proposals'])==1


def test_direct_edit_preserves_full_bytes_and_requires_new_receipts(project):
    flow=Flow(project); flow.freeze(); flow.run('propose',{'owner':'researcher','finding':flow.node()}); flow.integrate(); flow.resolve(); flow.disposition()
    path=flow.root/'.ris/research/findings/knowledge.md'
    original=path.read_text(); edited=original.replace('# Research knowledge','# User original wording')+'\nCorrection: irregular samples.\n'; path.write_text(edited)
    inspected=flow.run('inspect'); assert inspected['direct_edit_pending']
    assert 'Direct edit' in flow.run('disposition',{'id':'f1'},ok=False)
    flow.run('review-edit',{'file_sha256':inspected['file_sha256'],'reason':'Review user correction'})
    assert any(p.read_text()==edited for p in (flow.root/'.ris/history').glob('*.md'))
    result=flow.run('inspect'); assert result['proposals'][0]['state']=='UNVERIFIED'
    assert 'disposition' not in result['proposals'][0]
    assert result['obligations'][0]['state']=='INVALIDATED'
    flow.integrate(); flow.resolve(); flow.disposition()
    assert not flow.run('inspect')['direct_edit_pending']
    # Invalid edits are never overwritten even by review-edit.
    path.write_text(path.read_text().replace('<!-- ris:findings -->','<!-- broken -->'))
    preimage=path.read_bytes()
    flow.run('review-edit',{'file_sha256':'bad','reason':'x'},ok=False)
    assert path.read_bytes()==preimage


def test_independent_disposition_and_scoped_invalidation(project):
    flow=Flow(project); flow.freeze(); flow.run('propose',{'owner':'researcher','finding':flow.node()}); flow.integrate(); flow.resolve(); flow.disposition()
    flow.run('propose',{'owner':'researcher','finding':flow.node('f2','other')}); flow.integrate('f2')
    assert flow.run('inspect')['obligations'][0]['state']=='CURRENT'
    flow.disposition('f2','USED_INTERNAL',False)
    assert 'independent' in flow.run('disposition',{'id':'f1','specified_by':'researcher'},ok=False)
    assert 'Decision-critical' in flow.run('disposition',{'id':'f2','specified_by':'reviewer','disposition':'EXCLUDED','decision_critical':True},ok=False)
    # A reviewed deferral carries uncertainty into the answer instead of whole notes.
    flow.disposition('f2','DEFERRED',True)
    draft=flow.root/'draft.md'; draft.write_text('Timing remains unresolved; do not infer an interval.\n\nActual sampling interval is unknown.\n\nNo timestamps were recorded.\n\nConditions: interval=unknown.\n')
    assert 'uncertainty' in flow.run('deliver',{'draft':'draft.md'},ok=False)
    draft.write_text(draft.read_text()+'\nThe timing question remains unresolved.\n')
    flow.run('deliver',{'draft':'draft.md'})


def test_minimal_history_not_full_snapshots(project):
    flow=Flow(project)
    for i in range(20): flow.run('propose',{'owner':'researcher','finding':flow.node('f'+str(i))})
    raw=(flow.root/'.ris/research/findings/knowledge.md').read_text()
    assert '"snapshot"' not in raw and 'direct_edit_bytes_utf8' not in raw
    # One current node plus its creation delta, rather than all earlier nodes per revision.
    assert raw.count('"statement"')==40


def test_question_scope_and_owner_transcript(project):
    flow=Flow(project)
    # Scoped mutations bind both project and stable question identity.
    flow.run('obligate',{'question_id':'scopeA','obligation':{'id':'open','question':'Pending A only','expected_scope':{'topic':'A'},'specified_by':'reviewer'}},extra=('--question','scopeA'))
    flow.revision=0
    result=flow.run('inspect',extra=('--question','scopeB'))
    assert result['total_obligations']==0 and result['total_matching']==0
    flow.run('propose',{'question_id':'scopeB','owner':'researcher','finding':flow.node()},extra=('--question','scopeB'))
    result=flow.run('accept',{'question_id':'scopeB','id':'f1','owner':'researcher','note':'record'},extra=('--question','scopeB'))
    revision=result['proposals'][0]['accepted_revision']
    error=flow.run('return',{'question_id':'scopeB','id':'f1','owner':'researcher','note':'done','finding_revision':revision,'transcript':'Unrelated successful result.'},ok=False,extra=('--question','scopeB'))
    assert 'omits' in error
    error=flow.run('return',{'question_id':'scopeB','id':'f1','owner':'researcher','note':'done','finding_revision':revision,'transcript':'Actual sampling interval is unknown.'},ok=False,extra=('--question','scopeB'))
    assert 'limitations' in error
    flow.run('return',{'question_id':'scopeB','id':'f1','owner':'researcher','note':'corrected','finding_revision':revision,'transcript':'Actual sampling interval is unknown.\n\nNo timestamps were recorded.\n\nConditions: interval=unknown.'},extra=('--question','scopeB'))
    assert (flow.root/'.ris/research/findings/knowledge-scopeA.md').exists()
    assert (flow.root/'.ris/research/findings/knowledge-scopeB.md').exists()


def test_inspect_does_not_create_files(project):
    flow=Flow(project)
    before={str(p.relative_to(flow.root)):p.read_bytes() for p in flow.root.rglob('*') if p.is_file()}
    flow.run('inspect')
    after={str(p.relative_to(flow.root)):p.read_bytes() for p in flow.root.rglob('*') if p.is_file()}
    assert before==after


@pytest.mark.parametrize('malformation', ['null','bad-node','bad-ids','bad-delivery','missing-integrity'])
def test_malformed_ledgers_fail_without_traceback_or_mutation(project,malformation):
    flow=Flow(project); flow.freeze(); flow.run('propose',{'owner':'researcher','finding':flow.node()})
    path=flow.root/'.ris/research/findings/knowledge.md'; raw=path.read_text()
    begin='<!-- ris:findings -->\n```json\n'; end='\n```\n<!-- /ris:findings -->'
    value=json.loads(raw.split(begin)[1].split(end)[0])
    if malformation=='null': value=None
    elif malformation=='bad-node': value['proposals']=[None]
    elif malformation=='bad-ids': value['obligations'][0]['finding_ids']=[{}]
    elif malformation=='bad-delivery': value['delivery']=[]
    elif malformation=='missing-integrity': value.pop('narrative_sha256')
    path.write_text(raw.split(begin)[0]+begin+json.dumps(value)+end+raw.split(end)[1])
    before=path.read_bytes()
    assert 'Traceback' not in flow.run('inspect',ok=False)
    assert path.read_bytes()==before


def test_discovery_across_questions_and_scope_rejection(project):
    flow=Flow(project)
    flow.run('propose',{'question_id':'old','owner':'researcher','finding':flow.node()},extra=('--question','old'))
    flow.run('accept',{'question_id':'old','id':'f1','owner':'researcher','note':'recorded for discovery'},extra=('--question','old'))
    result=flow.run('search',extra=('--query','sampling','--question','new','--limit','1'))
    assert len(result['hits'])==1 and result['hits'][0]['question_id']=='old'
    assert result['scan_complete'] and not result['more']
    assert result['hits'][0]['reuse_status']=='UNKNOWN'
    # A different question's content is never silently injected into the new authority.
    flow.revision=0
    assert flow.run('inspect',extra=('--question','new'))['total_matching']==0
    flow.freeze('scope','other-topic'); flow.run('propose',{'owner':'researcher','finding':flow.node()}); flow.integrate()
    assert 'expected_scope' in flow.run('resolve',{'id':'scope','specified_by':'reviewer','finding_ids':['f1'],'text':'Unrelated answer.'},ok=False)
    # Dirty source notes are skipped, not presented as reusable findings.
    path=flow.root/'.ris/research/findings/knowledge-old.md'; path.write_text(path.read_text()+'\nUnreviewed correction\n')
    result=flow.run('search',extra=('--query','sampling','--limit','1'))
    assert all(hit['question_id']!='old' for hit in result['hits'])
    assert any(x['reason']=='pending-direct-edit' for x in result['skipped'])


def test_explicit_file_evidence_freshness_and_stale_draft(project):
    import hashlib
    flow=Flow(project); flow.freeze()
    data=flow.root/'raw.csv'; data.write_bytes(b'value\n1\n')
    node=flow.node(); node['provenance'][0].update(source='file:raw.csv',revision='sha256:'+hashlib.sha256(data.read_bytes()).hexdigest())
    flow.run('propose',{'owner':'researcher','finding':node}); flow.integrate(); flow.resolve(); flow.disposition()
    draft=flow.root/'draft.md'; draft.write_text('Timing remains unresolved; do not infer an interval.\n\nActual sampling interval is unknown.\n\nNo timestamps were recorded.\n\nConditions: interval=unknown.\n')
    flow.run('deliver',{'draft':'draft.md'}); assert flow.run('inspect')['delivery_current']
    draft.write_text('Changed draft')
    assert flow.run('inspect')['delivery_current'] is False
    data.write_bytes(b'value\n2\n')
    assert flow.run('inspect')['evidence_checks']['f1'][0]['status']=='STALE'
    assert not flow.run('search',extra=('--query','sampling'))['hits']


def test_condition_transport_and_duplicate_review(project):
    flow=Flow(project); flow.freeze(); node=flow.node(); node['conditions']={'source_temperature':'20 C','target_temperature':'80 C','material':'steel'}
    flow.run('propose',{'owner':'researcher','finding':node}); accepted=flow.run('accept',{'id':'f1','owner':'researcher','note':'record'})
    base='Actual sampling interval is unknown.\n\nNo timestamps were recorded.'
    returned={'id':'f1','owner':'researcher','note':'received','finding_revision':accepted['proposals'][0]['accepted_revision'],'transcript':base}
    assert 'omits' in flow.run('return',returned,ok=False)
    scope='Conditions: material=steel; source_temperature=20 C; target_temperature=80 C.'
    returned['transcript']=base+'\n\n'+scope; flow.run('return',returned)
    flow.run('integrate',{'id':'f1','owner':'researcher','note':'integrated'}); flow.resolve(); flow.disposition()
    draft=flow.root/'draft.md'; draft.write_text('Timing remains unresolved; do not infer an interval.\n\n'+base)
    assert 'conditions' in flow.run('deliver',{'draft':'draft.md'},ok=False)
    draft.write_text(draft.read_text()+'\n\n'+scope); flow.run('deliver',{'draft':'draft.md'})
    duplicate=dict(node,id='f2')
    assert 'duplicate' in flow.run('propose',{'owner':'researcher','finding':duplicate},ok=False)
    resolution={'action':'KEEP_SEPARATE','candidate_ids':['f1'],'reviewed_by':'reviewer','reason':'Different explicitly reviewed evidence source'}
    flow.run('propose',{'owner':'researcher','finding':duplicate,'duplicate_resolution':resolution})
    assert flow.run('inspect')['delivery'] is None
    conflict=dict(node,id='f3',conditions={'source_temperature':'20 C','target_temperature':'100 C','material':'steel'})
    result=flow.run('propose',{'owner':'researcher','finding':conflict})
    assert result['proposals'][-1]['duplicate_candidates'][0]['conditions_equal'] is False


def test_punctuated_question_and_unmanaged_note_compatibility(project):
    flow=Flow(project)
    flow.run('propose',{'question_id':'test.case:1','owner':'researcher','finding':flow.node()},extra=('--question','test.case:1'))
    assert (flow.root/'.ris/research/findings/knowledge-test.case%3A1.md').exists()
    path=flow.root/'.ris/research/findings/knowledge.md'; path.write_text('---\nris_id: "old-user-note"\nproject_id: '+json.dumps(flow.project_id)+'\nkind: "finding"\nstatus: "draft"\ncreated: "2026-11-25"\n---\n# Existing user note\n\nKeep this original user note.\n')
    result=subprocess.run([sys.executable,str(CLI),'--project',str(flow.root),'context','--include','.ris/research/findings/knowledge.md'],capture_output=True,text=True)
    assert result.returncode==0,result.stderr


def test_scope_token_boundaries_and_minimal_return_retention(project):
    flow=Flow(project); node=flow.node(); node['statement']='Measured interval=20.'; node['conditions']={'interval':'2'}
    flow.run('propose',{'owner':'researcher','finding':node}); result=flow.run('accept',{'id':'f1','owner':'researcher','note':'record'})
    payload={'id':'f1','owner':'researcher','note':'reviewed','finding_revision':result['proposals'][0]['accepted_revision'],'transcript':'Measured interval=20.\n\nNo timestamps were recorded.'}
    assert 'omits' in flow.run('return',payload,ok=False)
    payload['transcript']+='\n\nConditions: interval=2.\n\nIncidental private agent chatter.'
    result=flow.run('return',payload)
    assert 'return_transcript' not in result['proposals'][0]
    assert 'Incidental private agent chatter' not in (flow.root/'.ris/research/findings/knowledge.md').read_text()


def test_read_only_target_condition_comparison(project):
    flow=Flow(project); node=flow.node(); node['conditions']={'material':'steel','temperature':'20 C'}
    flow.run('propose',{'owner':'researcher','finding':node}); flow.run('accept',{'id':'f1','owner':'researcher','note':'record'})
    target=flow.root/'target.json'
    target.write_text(json.dumps({'project_id':flow.project_id,'conditions':{'material':'steel','temperature':'80 C'}}))
    result=flow.run('search',extra=('--query','sampling','--target-conditions','target.json'))
    assert result['hits'][0]['applicability']['status']=='CONFLICT'
    assert result['hits'][0]['conditions']==node['conditions'] and result['hits'][0]['axes']==node['axes']
    target.write_text(json.dumps({'project_id':flow.project_id,'conditions':node['conditions']}))
    assert flow.run('search',extra=('--query','sampling','--target-conditions','target.json'))['hits'][0]['applicability']['status']=='MATCH'


def make_scale_ledger(project, question, count, needle='bulkmatch'):
    """Synthetic canonical fixture; retrieval itself is exercised through CLI."""
    import importlib.util
    import hashlib
    spec=importlib.util.spec_from_file_location('pagination_fixture_findings',CLI.parent/'ris_findings.py')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    root,project_id=project
    proposals=[]
    for i in range(count):
        finding=Flow(project).node('n'+str(i))
        finding['statement']=needle+' '+str(i)
        proposals.append({'finding':finding,'owner':'researcher','state':'RECORDED','accepted_revision':1})
    value={'schema_version':1,'project_id':project_id,'question_id':question,'revision':1,'proposals':proposals,'obligations':[],'history':[],'operations':{},'narrative_sha256':hashlib.sha256(b'\n').hexdigest()}
    value['content_sha256']=module.digest(module.canonical(value).encode())
    path=root/'.ris/research/findings'/('knowledge-'+question+'.md'); path.parent.mkdir(exist_ok=True,parents=True)
    path.write_text(module.render(value,'\n'))


def test_cli_pagination_reaches_later_files_and_nodes(project):
    import time
    flow=Flow(project)
    for i in range(205): make_scale_ledger(project,'q'+str(i).zfill(3),1,'finalneedle' if i==204 else 'other')
    start=time.monotonic()
    first=flow.run('search',extra=('--query','finalneedle','--limit','1'))
    assert first['hits']==[] and first['more'] and first['next_cursor'] and first['scanned']==200
    second=flow.run('search',extra=('--query','finalneedle','--limit','1','--cursor',first['next_cursor']))
    assert second['hits'][0]['question_id']=='q204' and not second['more']
    file_seconds=time.monotonic()-start
    make_scale_ledger(project,'zlarge',125)
    start=time.monotonic()
    page=flow.run('search',extra=('--query','bulkmatch','--limit','100'))
    ids=[x['id'] for x in page['hits']]
    pages=1
    while page['next_cursor']:
        page=flow.run('search',extra=('--query','bulkmatch','--limit','100','--cursor',page['next_cursor']))
        ids.extend(x['id'] for x in page['hits']); pages+=1
    assert len(ids)==125 and len(set(ids))==125 and ids[-1]=='n124'
    print(json.dumps({'scale_files':206,'late_file_question':second['hits'][0]['question_id'],'file_pages':2,'file_seconds':round(file_seconds,3),'nodes':125,'last_node':ids[-1],'node_pages':pages,'node_seconds':round(time.monotonic()-start,3)}))


def test_cursor_rejects_changed_query_and_snapshot(project):
    flow=Flow(project); make_scale_ledger(project,'scale',3)
    page=flow.run('search',extra=('--query','bulkmatch','--limit','1'))
    assert 'cursor' in flow.run('search',ok=False,extra=('--query','different','--limit','1','--cursor',page['next_cursor']))
    path=flow.root/'.ris/research/findings/knowledge-scale.md'; path.write_text(path.read_text()+'\nHonest edit\n')
    assert 'snapshot changed' in flow.run('search',ok=False,extra=('--query','bulkmatch','--limit','1','--cursor',page['next_cursor']))


def test_post_dispatch_honest_edit_is_not_returned(project,monkeypatch):
    import importlib.util
    from types import SimpleNamespace
    spec=importlib.util.spec_from_file_location('pagination_api',CLI)
    api=importlib.util.module_from_spec(spec); spec.loader.exec_module(api)
    module=api.companion('ris_findings'); make_scale_ledger(project,'scale',1)
    root,_=project; path=root/'.ris/research/findings/knowledge-scale.md'
    original=module.dispatch
    def changed_dispatch(api,root,args,**kwargs):
        value=original(api,root,args,**kwargs)
        if args.action=='inspect': path.write_text(path.read_text()+'\nHonest post-inspection edit\n')
        return value
    monkeypatch.setattr(module,'dispatch',changed_dispatch)
    with pytest.raises(api.Error,match='snapshot changed'):
        module.search(api,root,SimpleNamespace(query='bulkmatch',limit=1,target_conditions=None,cursor=None))
    assert path.read_text().endswith('Honest post-inspection edit\n')


def test_skipped_invalid_records_remain_distinct_across_pages(project):
    flow=Flow(project)
    for i in range(3): make_scale_ledger(project,'q00'+str(i),1)
    path=flow.root/'.ris/research/findings/knowledge-q000.md'; path.write_text(path.read_text()+'\nUnreviewed correction\n')
    first=flow.run('search',extra=('--query','bulkmatch','--limit','1'))
    assert first['more'] and first['skipped_total']==1
    last=flow.run('search',extra=('--query','bulkmatch','--limit','1','--cursor',first['next_cursor']))
    assert last['traversal_complete'] and not last['more'] and not last['scan_complete']
    assert last['skipped']==[] and last['skipped_total']==1 and last['skipped_previous_pages']==1
