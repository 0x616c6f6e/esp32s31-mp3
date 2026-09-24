"""Package only reviewed exports, keeping electronics out of the print upload."""
from pathlib import Path
import hashlib,json,zipfile,shutil
O=Path(__file__).resolve().parents[1];R=O.parents[1];P=O/'print-package'
fit=json.loads((O/'fit-check.json').read_text())
assert not fit['static_conflicts'],fit['static_conflicts']
assert not fit['battery_expanded_conflicts'],fit['battery_expanded_conflicts']
assert not fit['invalid_shapes']
assert not any(v for row in fit['travel'] for k,v in row.items() if k in ['ControlsBoard','HousingControlsA','CenterButtonControlsA'])
insert=json.loads((O/'insert-check.json').read_text())
assert all(row[k]<1e-5 for row in insert['socket_checks'] for k in row if k.endswith('mm3'))
assert all(not row['collisions'] for row in json.loads((O/'insertion-check.json').read_text())['samples'])
src=json.loads((O/'source.json').read_text())
for v in src.values():assert hashlib.sha256((R/v['path']).read_bytes()).hexdigest()==v['sha256']
for f in ['README.md','fit-check.json','export-check.json','parameters.json','source.json','optimization.json','insertion-check.json','insert-check.json','insert-section.png','optimized-upper-shell.png']:
 shutil.copy2(O/f,P/('assembly-README.md' if f=='README.md' else f))
review_files=['PRINT-HOLD.md','PREFLIGHT-REVIEW.md','production-readiness.json','preflight-export-check.json','preflight-path-check.json','preflight-tilt-probe.json','preflight-detail-check.json','review-wheel-entry-collision.png','review-controls-entry-collision.png']
for f in review_files:
 shutil.copy2(O/f,P/f)
files=[p for p in P.iterdir() if p.is_file() and p.name!='manifest.json']
manifest={'units':'mm','purpose':'tough-resin assembly evaluation sample; see assembly-README.md for battery and wiring limits','files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}}
manifest['production_status']='HOLD: unresolved assembly paths, thin features and LCD retention; read PRINT-HOLD.md'
(P/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
out=O/'Q2-J-glue-insert-sample.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(P.iterdir()):
  if p.is_file():z.write(p,p.name)
with zipfile.ZipFile(out) as z:assert z.testzip() is None
print('PACKAGE_REVIEW_ONLY_HOLD',out,len(list(P.iterdir())),out.stat().st_size)
