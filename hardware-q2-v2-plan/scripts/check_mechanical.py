"""Nominal intersections of moved source models with the L assembly (not release approval)."""
from pathlib import Path
import FreeCAD as A,Part,json,hashlib,math
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'hardware-q2-v2-plan';V=A.Vector
j=json.loads((OUT/'placement.json').read_text(encoding='utf8'))
src=ROOT/'mechanical/enclosure-final-l/Q2_L_AM213_Adapter_Study.FCStd'
digest=hashlib.sha256(src.read_bytes()).hexdigest();d=A.openDocument(str(src))
existing={o.Name:o for o in d.Objects if hasattr(o,'Shape') and not hasattr(o,'Group') and not o.Shape.isNull()}
def common(a,b):
 if not a.BoundBox.intersect(b.BoundBox):return 0
 return a.common(b).Volume
parts={};changes=[]
for a in j['components']:
 r=a['ref'];old=a['before'];o=d.getObject('PCB_'+r)
 if r in ['CN2','CN3']:
  if o:d.removeObject(o.Name)
  continue
 if o is None:continue
 sh=o.Shape.copy()
 x,y=a['xy'];z=5.8 if a['side']=='F' else 4.2
 ox,oy=old['x'],old['y'];oz=5.8 if old['side']=='Top Layer' else 4.2
 center=V(48-ox,2+oy,oz)
 sh.translate(-center);sh.rotate(V(),V(0,0,1),-old['angle'])
 if (a['side']=='F')!=(old['side']=='Top Layer'):sh.rotate(V(),V(1,0,0),180)
 sh.rotate(V(),V(0,0,1),a['angle']);sh.translate(V(48-x,2+y,z));o.Shape=sh
 if r=='U10':
  sh.rotate(V(48-x,2+y,z),V(0,0,1),90);o.Shape=sh # Correct inherited nominal model's quarter-turn mismatch with land pattern.
 parts[r]=sh
 if math.hypot(x-ox,y-oy)>.001 or abs(a['angle']-old['angle'])>.01 or z!=oz:changes.append(r)
for r in j['removed']:
 o=d.getObject('PCB_'+r)
 if o:d.removeObject(o.Name)
for name in ['DisplayAdapterPCB','DisplayAdapterComponents','DisplayAdapterConnectors']:
 if d.getObject(name):d.removeObject(name)
sh=Part.read(str(ROOT/'hardware-display-adapter/am213-fpc-adapter/models3d/OK-23GF024-04.step'))
sh.rotate(V(),V(0,0,1),90);sh.translate(V(18,31.2,5.8));o=d.addObject('PartDesign::Feature','PCB_JDISP1');o.Shape=sh;parts['JDISP1']=sh;changes.append('JDISP1')
sh=Part.makeBox(8,8,.9,V(14,15,5.8));o=d.addObject('PartDesign::Feature','CoreBodyPlanningEnvelope');o.Shape=sh;o.Label='S31 QFN80 8x8 / height 0.9 / body only, no new support components';parts['CORE_BODY_PLAN']=sh;changes.append('CORE_BODY_PLAN')
names=['HousingControlsA','RearCoverWithPCBPosts','ControlFFC40mm','BatteryExpandedKeepout','BatteryWire1','BatteryWire2','BatteryWire3','MotorWire1','MotorWire2','MotorCarrier','Motor_C08_005','MainBoardFasteners','RearCoverFasteners','ControlsBoard','ScreenRearFPCEnvelope']
obstacles={n:existing[n].Shape for n in names}
hits=[];pairhits=[]
for r,sh in parts.items():
 for n,ob in obstacles.items():
  vol=common(sh,ob)
  if vol>1e-5:hits.append(dict(ref=r,obstacle=n,volume_mm3=round(vol,6),moved=r in changes))
for i,(r,a) in enumerate(parts.items()):
 for s,b in list(parts.items())[i+1:]:
  if r not in changes and s not in changes:continue
  vol=common(a,b)
  if vol>1e-5:pairhits.append(dict(a=r,b=s,volume_mm3=round(vol,6)))
report=dict(status='NOMINAL_EXISTING_MODELS_ONLY',moved_models=len(changes),assembly_collisions=hits,moved_component_collisions=pairhits,
 limitations=['Core body envelope only: 8x8mm and datasheet maximum 0.9mm height; new RF/clock/boot-Flash circuit and display native tail are not modelled','Existing nominal STEP geometry reused; manufacturing tolerances not included','CN2/CN3 use wires; tall original connector bodies intentionally absent','Unchanged assembly defects are reported separately by moved=false'])
(OUT/'mechanical-check.json').write_text(json.dumps(report,indent=2),encoding='utf8')
d.Label='Q2 V2 placement study / core circuit and display tail incomplete';d.recompute();d.saveAs(str(OUT/'Q2_V2_Placement_Study.FCStd'))
assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
print(json.dumps(report,indent=2))
