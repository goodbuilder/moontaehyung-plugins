#!/usr/bin/env python3
"""Development fixture, deterministic transport/validation probe; no model calls."""
import json
from pathlib import Path
import time

FACTS = {
 'source_revision':2,'current_source_revision':3,'target_revision':1,
 'source_conditions':{'material':'Birch','temperature':'20 C'},
 'target_conditions':{'material':'Birch','temperature':'25 C'},
 'evidence_bytes_match':True,
 'strategy':{'method':'reuse a matched observation after checking conditions',
             'failure_cases':['temperature-dependent delamination'],
             'negative_control':'not performed','confidence_limits':'one synthetic observation'},
 'hard_limits':['same-project only','no model or physical runs'],
}
REQUIRED = tuple(FACTS)


def encode(value):
 return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def validate(payload):
 return [key for key in REQUIRED if key not in payload]


def decide(payload):
 return {'reuse':'recheck' if payload['source_revision'] != payload['current_source_revision'] or payload['source_conditions'] != payload['target_conditions'] else 'review_required',
         'strategy_transfer':'unverified' if payload['strategy']['negative_control'] == 'not performed' else 'review_required'}


def execute(architecture):
 messages=[]; rework=0; detected=[]
 if architecture == 'integrated':
  # One worker directly owns the common complete input; no inter-worker transport.
  payload=dict(FACTS)
  coordinator=[{'to':'integrated','facts':FACTS}]
 elif architecture == 'split_producer':
  # Legacy lossy summary contract, intentionally omits freshness and boundary facts.
  producer={k:v for k,v in FACTS.items() if k not in {'current_source_revision','hard_limits','strategy'}}
  messages.append({'producer_to_planner':producer})
  payload=dict(producer); detected=validate(payload)
  if detected:
   messages.append({'planner_to_producer':{'missing':detected}})
   repair={key:FACTS[key] for key in detected}; messages.append({'producer_to_planner_repair':repair})
   payload.update(repair);rework=1
  coordinator=[{'to':'producer','facts':FACTS},{'to':'planner','handoff':producer}]
 else:
  # Typed conditional handoff: boundary-critical facts required before delegation.
  producer=dict(FACTS)
  messages.append({'producer_to_planner':producer})
  payload=dict(producer)
  coordinator=[{'to':'producer','facts':FACTS},{'to':'planner','handoff_ref':'local:producer-output','required':REQUIRED}]
 output=decide(payload)
 coordinator.append({'result':output})
 return {'detected_missing_fields':detected,'missing_after_repair':validate(payload),
         'rework_rounds':rework,'inter_role_messages':len(messages),
         'inter_role_payload_bytes':sum(len(encode(m)) for m in messages),
         'coordinator_payload_bytes':sum(len(encode(m)) for m in coordinator),
         'output':output}


def main():
 results={}
 for architecture in ('integrated','split_producer','conditional_handoff'):
  start=time.perf_counter_ns()
  for _ in range(1000):
   result=execute(architecture)
  elapsed=time.perf_counter_ns()-start
  results[architecture]=dict(result,iterations=1000,total_local_python_ns=elapsed)
 report={'fixture':'common development knowledge/strategy fixture; not evaluation custodian data',
         'facts':FACTS,'architectures':results,
         'limitations':['No models, semantic generation, retrieval or researcher quality measured.',
          'Missing facts are injected by the split summary projection; detection is required-key validation.',
          'The same validator and exact final decision rule are used in all three paths.',
          'Transport topology/contract differences are bundled; this is not an architecture quality ranking.',
          'Local Python timings are noisy microbenchmarks and exclude provider/network/runtime setup.',
          'Coordinator bytes count JSON envelopes only; not tokens, context occupancy, cost or model latency.']}
 Path(__file__).with_name('offline_handoff_results.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(results,indent=2))

if __name__=='__main__':main()
