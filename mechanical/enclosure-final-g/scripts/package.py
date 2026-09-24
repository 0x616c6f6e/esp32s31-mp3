"""Package only reviewed exports, keeping electronics out of the print upload."""
from pathlib import Path
import hashlib,json,zipfile,shutil
O=Path(__file__).resolve().parents[1];R=O.parents[1];P=O/'print-package'
fit=json.loads((O/'fit-check.json').read_text())
assert not fit['static_conflicts'],fit['static_conflicts']
assert not fit['battery_expanded_conflicts'],fit['battery_expanded_conflicts']
assert not fit['invalid_shapes']
src=json.loads((O/'source.json').read_text())
for v in src.values():assert hashlib.sha256((R/v['path']).read_bytes()).hexdigest()==v['sha256']
for f in ['README.md','fit-check.json','export-check.json','parameters.json','source.json']:
 shutil.copy2(O/f,P/('assembly-README.md' if f=='README.md' else f))
files=[p for p in P.iterdir() if p.is_file() and p.name!='manifest.json']
manifest={'units':'mm','purpose':'tough-resin assembly evaluation sample; see assembly-README.md for battery and wiring limits','files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}}
(P/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
out=O/'Q2-G-resin-sample.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(P.iterdir()):
  if p.is_file():z.write(p,p.name)
with zipfile.ZipFile(out) as z:assert z.testzip() is None
print('PACKAGE_READY',out,len(list(P.iterdir())),out.stat().st_size)
