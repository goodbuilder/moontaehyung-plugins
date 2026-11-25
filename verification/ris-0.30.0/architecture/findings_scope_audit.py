#!/usr/bin/env python3
"""Synthetic public CLI peer audit; no evaluation fixture access."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path('/home/moontaehyung/plugins/moontaehyung/skills/ris')
spec=importlib.util.spec_from_file_location('development_findings_tests',ROOT/'tests/test_findings.py')
tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
with tempfile.TemporaryDirectory(prefix='ris-scope-audit-') as td:
 root=Path(td)
 result=subprocess.run([sys.executable,str(tests.CLI),'--project',str(root),'init','--recording-policy','manual'],capture_output=True,text=True)
 assert result.returncode==0,result.stderr
 # Public init result exposes identity; no private configuration access is required.
 project_id=json.loads(result.stdout)['project_id']
 flow=tests.Flow((root,project_id));flow.freeze()
 finding=flow.node();finding['conditions']={'material':'Birch','source_temperature':'20 C','target_temperature':'25 C'}
 flow.run('propose',{'owner':'researcher','finding':finding})
 flow.integrate();flow.resolve();flow.disposition()
 draft='Timing remains unresolved; do not infer an interval.\n\nActual sampling interval is unknown.\n\nNo timestamps were recorded.\n'
 (root/'draft.md').write_text(draft)
 output=flow.run('deliver',{'draft':'draft.md'})
 report={'finding':'Delivery succeeds while omitting all recorded applicability conditions',
         'conditions':finding['conditions'],'draft':draft,'delivery_accepted':bool(output['delivery']),
         'all_condition_values_omitted':all(v not in draft for v in finding['conditions'].values()),
         'scope':'Exact CLI reproduction on fresh synthetic project; helper only checks statement, provenance limitations, and reviewer text.',
         'identity_limit':'Owner/reviewer independence compares caller-provided names, not authenticated distinct principals; this is declared workflow governance, not an isolation proof.'}
 Path(__file__).with_name('findings_scope_audit_results.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
