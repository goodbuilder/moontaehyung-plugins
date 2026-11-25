"""Compare named public historical records, source objects and seven review chapters."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

def sha(data):
    return hashlib.sha256(data).hexdigest()

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('originals',type=Path,help='Directory containing the three historical evaluation roots')
args=parser.parse_args()
root=args.originals
git=Path(__file__).resolve().parents[2]
commit='007ee7ff2d727e813ba59584abc80e7b1c002e74'
origins=dict(A=root/'2026-11-25-self-critical',B=root/'2026-11-25-confirmation-0.28.1',C=root/'2026-11-25-self-critical-0.29.0')
name='RIS-0.29.0-007ee7f-architecture-review.zip'
prefix='RIS-0.29.0-review/'
allow={'A/REPORT.md','A/TRACEABILITY.md','B/decision.json','B/new-score-table.md','B/omission-rca.md',
       'B/resources.json','C/REPORT.md','C/TRACEABILITY.md','C/cutoff-status.json','C/owner-manifest.json',
       'C/delivery-replay/defect-check.md','C/development-replay/defect-check.md'}
rows=[]
with zipfile.ZipFile(Path(__file__).resolve().parent/'historical'/name) as z:
    sums=dict(line.split('  ',1)[::-1] for line in z.read(prefix+'CHECKSUMS.sha256').decode().splitlines())
    for rel,h in sums.items():
        if rel[:2] in ('01','02','03','04','05','06','07') and '/' not in rel:
            rows.append(dict(member=rel,match=sha(z.read(prefix+rel))==h))
    for rec in csv.DictReader(io.StringIO(z.read(prefix+'ORIGINS.tsv').decode()),delimiter='\t'):
        locator=rec['original_locator']
        if locator not in allow: continue
        area,rel=locator.split('/',1)
        raw=(origins[area]/rel).read_bytes()
        rows.append(dict(locator=locator,member=rec['member'],original_matches=sha(raw)==rec['original_sha256'],
                         match=sha(z.read(prefix+rec['member']))==rec['member_sha256']))
manifest=json.loads((origins['C']/'owner-manifest.json').read_bytes())
mismatch=[rel for rel,h in manifest.items() if sha(subprocess.check_output(['git','-C',git,'show',commit+':moontaehyung/'+rel]))!=h]
print(json.dumps(dict(review_documents=rows,baseline_files=len(manifest),baseline_mismatch=mismatch,
                      missing_named_rows=sorted(allow-{r.get('locator') for r in rows}),archive_sha256=sha((Path(__file__).resolve().parent/'historical'/name).read_bytes())),indent=2))
assert len([r for r in rows if 'locator' not in r])==7 and not mismatch and all(r['match'] and r.get('original_matches',True) for r in rows)
