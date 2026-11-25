"""Re-run the public two-candidate thermal design fixture and retain actual CLI receipts."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('source',type=Path)
    parser.add_argument('destination',type=Path)
    args=parser.parse_args()
    project=args.destination.resolve()
    project.mkdir()
    spec=importlib.util.spec_from_file_location('model_fixture',args.source/'skills/ris/tests/test_simulation.py')
    fixture=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    # The original regression writes the exact model/cases and asserts the independent closed-form oracle.
    receipts=[]
    original=fixture.command
    def capture(path,*args):
        case=path/'case.json'
        before=case.read_text() if case.exists() else None
        code,value=original(path,*args)
        receipts.append(dict(argv=list(args),case=json.loads(before) if before else None,exit=code,result=value))
        if before:
            (project/('case-'+hashlib.sha256(before.encode()).hexdigest()[:16]+'.json')).write_text(before)
        return code,value
    fixture.command=capture
    fixture.test_design_sensitivity_revision_and_failure(project)
    (project/'receipts.json').write_text(json.dumps(receipts,indent=2))
    print(json.dumps([dict(exit=x['exit'],execution=x['result'].get('execution'),result=x['result'].get('result')) for x in receipts],indent=2))
if __name__=='__main__':main()
