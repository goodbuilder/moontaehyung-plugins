#!/usr/bin/env python3
"""Matched development transport probe using installed RIS helper validators; no models."""
import importlib.util
import json
from pathlib import Path
import time

import os
SCRIPTS=Path(os.environ['RIS_AUDIT_SOURCE']).resolve()/'skills/ris/scripts'
def load(name):
 spec=importlib.util.spec_from_file_location(name,SCRIPTS/(name+'.py'))
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
RIS=load('ris'); FINDINGS=RIS.companion('ris_findings'); DELIVERY=RIS.companion('ris_delivery')
CANDIDATES={
 'A0':('existing roles + Skill + Helper',['existing-worker']),
 'A1':('add knowledge-only agent',['existing-worker','knowledge']),
 'A2':('add user-understanding agent',['existing-worker','understanding']),
 'A3':('combine knowledge and human',['existing-worker','knowledge-human']),
 'A4':('separate Knowledge Steward and Mentor',['existing-worker','steward','mentor']),
 'A5':('specialists including Strategist',['existing-worker','steward','mentor','strategist']),
 'A6':('specialists including Librarian',['existing-worker','steward','mentor','librarian']),
 'A7':('reallocate across existing agents',['researcher','engineer','planner']),
 'A8':('general worker with dynamic specialization',['dynamic-worker']),
 'A9':('hybrid agents/skills/helpers',['existing-worker','conditional-helper']),
}
FINDING={'id':'F1','statement':'The recorded observation is stale for this target.',
 'status':'CONFIRMED','conditions':{'source_revision':'2','current_revision':'3','source_temperature':'20 C','target_temperature':'25 C'},
 'axes':{'topic':'reuse'},'relations':[],
 'provenance':[{'source':'development:fixture','locator':'row 1','revision':'v1',
                'limitations':['Negative control was not performed.','One synthetic observation; no scientific transfer established.']}]}
REQUIRED=[FINDING['statement'],*FINDING['provenance'][0]['limitations'],
          'Source revision 2; current revision 3; source 20 C; target 25 C.']
QUALITY='Every required sentence survives publication, candidate validates, no model/network/cost, payload <= 100000 bytes.'

def encoded(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def check(draft):
 paragraphs=DELIVERY.paragraphs(draft)
 return [text for text in REQUIRED if not DELIVERY.contains(paragraphs,text)]
def run(candidate,control,mode):
 family,roles=CANDIDATES[candidate]
 FINDINGS.validate_finding(RIS.helper_api(),FINDING)
 # Every arm receives byte-identical common facts and has the same final publication boundary.
 payload={'finding':FINDING,'required_passages':REQUIRED,'authority':'local synthetic only'}
 envelopes=[{'to':roles[0],'payload':payload}]
 route=roles[1:]
 if mode=='conditional' and control=='clean':route=[]
 # Complete typed handoffs; no arm is assigned a deliberately lossy producer contract.
 for role in route:envelopes.append({'to':role,'payload':payload})
 draft='\n\n'.join(REQUIRED)
 if control=='defect':draft=draft.replace(REQUIRED[1],'')
 # Independent stewardship publication check applies in EVERY architecture, including A0.
 envelopes.append({'to':'independent-publication-steward','draft':draft,'required_passages':REQUIRED})
 missing=check(draft);repairs=0
 if missing:
  envelopes.append({'to':roles[0],'repair_missing':missing})
  draft='\n\n'.join(REQUIRED);repairs=1
  envelopes.append({'to':'independent-publication-steward','draft':draft,'required_passages':REQUIRED})
 remaining=check(draft);size=sum(map(lambda e:len(encoded(e)),envelopes))
 return {'injected_defects':0 if control=='clean' else 1,'detected_missing':len(missing),
         'remaining_missing':len(remaining),'repair_rounds':repairs,
         'coordinator_envelopes':len(envelopes),'coordinator_payload_bytes':size,
         'handoff_mode':mode,'quality_pass':not remaining and size<=100000,
         'synthetic_human_interventions':0,'actual_human_minutes':None,
         'model_quality':None,'provider_cost':None,'model_latency':None}

def main():
 results=[]
 for candidate in CANDIDATES:
  for mode in ('independent-stewardship','conditional'):
   for control in ('clean','defect'):
    cpu=time.process_time_ns();wall=time.perf_counter_ns()
    for _ in range(100):result=run(candidate,control,mode)
    result.update(candidate=candidate,control=control,iterations=100,
                  cpu_ns=time.process_time_ns()-cpu,wall_ns=time.perf_counter_ns()-wall)
    results.append(result)
 assert all(x['quality_pass'] for x in results)
 assert all(x['detected_missing']==x['injected_defects'] for x in results)
 output={'quality_condition':QUALITY,'resource_condition':'No providers/network/physical work; 100000 payload bytes per case; same helper check and repair rules.',
         'candidate_families':{k:v[0] for k,v in CANDIDATES.items()},'common_finding':FINDING,
         'common_required_passages':REQUIRED,'results':results,
         'assumptions':['Role routes are development proxies, not implemented model architectures.',
          'Every architecture has the same independent publication stewardship boundary.',
          'Conditional skips optional specialty handoffs on clean control; fixed stewardship always checks.',
          'A defect is injected after all producer handoffs at the common publication boundary.',
          'Repair is exact scripted restoration for all arms; no reasoning benefit inferred.',
          'CPU/wall measure local Python helper checks and JSON serialization only.',
          'Human intervention zero describes scripted cases, not real user time or development labor.',
          'Role labels do not establish real independent principal identity.']}
 Path(__file__).with_name('matched_boundary_results.json').write_text(json.dumps(output,indent=2)+'\n')
 print(json.dumps({'cases':len(results),'quality_pass':sum(x['quality_pass'] for x in results),
                   'detected_defects':sum(x['detected_missing'] for x in results)}))
if __name__=='__main__':main()
