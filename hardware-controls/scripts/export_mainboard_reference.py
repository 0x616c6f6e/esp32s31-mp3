"""Make a read-only source-board reference with locally available nominal models.
The user's hardware-q2-layout files are never saved or changed.
"""
from pathlib import Path
import json,hashlib
import pcbnew as p
P=Path(__file__).resolve().parents[1];ROOT=P.parent
plan=json.loads((P/'mechanical/interconnect-plan.json').read_text())
source=ROOT/plan['mainboard'];assert hashlib.sha256(source.read_bytes()).hexdigest()==plan['mainboard_sha256']
b=p.LoadBoard(str(source))
manifest=json.loads((ROOT/'hardware-q2-placement/models3d/model-manifest.json').read_text())
known={m['footprint']:m for m in manifest['models']};records=[]
for f in b.GetFootprints():
 ref=f.GetReference();fp=str(f.GetFPID().GetLibItemName())
 model=ROOT/'hardware-q2-placement/models3d'/known[fp]['file'] if fp in known else P/'models3d/HCTL_FPC12.step' if ref=='FPC1' else None
 f.Models().clear()
 if model:
  assert model.exists(),model
  m=p.FP_3DMODEL();m.m_Filename=str(model);m.m_Scale.x=m.m_Scale.y=m.m_Scale.z=1;f.Add3DModel(m)
 records.append({'ref':ref,'footprint':fp,'xy':[f.GetPosition().x/1e6,f.GetPosition().y/1e6],'angle':f.GetOrientationDegrees(),'side':'B' if f.IsFlipped() else 'F','model':str(model.relative_to(ROOT)).replace('\\','/') if model else None,'pads':{a.GetNumber():{'net':a.GetNetname(),'xy':[a.GetPosition().x/1e6,a.GetPosition().y/1e6]} for a in f.Pads() if a.GetNumber()}})
out=ROOT/'tmp/main-layout-reference.kicad_pcb';p.SaveBoard(str(out),b)
(P/'mechanical/mainboard-reference.json').write_text(json.dumps({'source':plan['mainboard'],'sha256':plan['mainboard_sha256'],'thickness_mm':1.6,'models_are_nominal_reused_by_matching_footprint_name':True,'missing_component_models':[r['ref'] for r in records if not r['model']],'footprints':records},indent=2)+'\n')
print('REFERENCE_BOARD_READY',out)
