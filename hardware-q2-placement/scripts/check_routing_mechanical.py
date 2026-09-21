"""FreeCAD: check the current placement against the saved revision-F enclosure.

Optional MP3_LAYOUT_JSON, MP3_LAYOUT_STEP, MP3_LAYOUT_BOARD, MP3_LAYOUT_CHECK
environment variables select a candidate. Does not save the source enclosure.
Includes mated connector envelopes, battery, motor, both FPCs and wiring.
"""
import FreeCAD as App, Part, Import
from pathlib import Path
import os, json, math, hashlib
P=Path(__file__).resolve().parents[1];ROOT=P.parent
jpath=Path(os.environ.get('MP3_LAYOUT_JSON',str(P/'output/placement.json')))
step=Path(os.environ.get('MP3_LAYOUT_STEP',str(P/'output/placement-populated.step')))
pcb=Path(os.environ.get('MP3_LAYOUT_BOARD',str(P/'hardware.kicad_pcb')))
output=Path(os.environ.get('MP3_LAYOUT_CHECK',str(P/'output/mechanical-check.json')))
source=ROOT/'mechanical/enclosure-q2-f/ESP32S31_MP3_Q2_F.FCStd'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
data=json.loads(jpath.read_text(encoding='utf8'))
assert data['pcb_sha256']==sha(pcb),'Stale placement JSON'
source_hash=sha(source)
fps={f['reference']:f for f in data['footprints'] if not f['reference'].startswith('SCREW')}
doc=App.newDocument('PlacementSTEP');Import.insert(str(step),doc.Name)
assembly=max(doc.Objects,key=lambda o:len(o.OutList))
enclosure=App.openDocument(str(source))
names=['HousingWithControlPosts','RearCoverWithPCBPosts','BatteryReference','ControlBoard',
 'DisplayFPCRoute','ControlFPCRoute','MainControlFPCReserve','ControlFPCConnector',
 'LCDModule','ControlBoardFasteners','MotorHolderProposal',
 'MotorWire1','MotorWire2','BatteryWire1','BatteryWire2','BatteryWire3']
obstacles={n:enclosure.getObject(n).Shape for n in names}
obstacles['MotorMaximumEnvelope']=Part.makeCylinder(4.05,3.45,App.Vector(39,57,7.1))
parts={};unmatched=[]
for o in assembly.OutList:
 if not hasattr(o,'Shape') or o.Shape.isNull() or o.Shape.Volume<1e-8:continue
 base=o.Placement.Base
 ref=min(fps,key=lambda r:math.hypot(fps[r]['xy'][0]-base.x,fps[r]['xy'][1]+base.y))
 if math.hypot(fps[ref]['xy'][0]-base.x,fps[ref]['xy'][1]+base.y)>.005:
  unmatched.append(o);continue
 assert ref not in parts,ref
 shape=o.Shape.copy();shape.rotate(App.Vector(),App.Vector(0,0,1),180)
 mounting=5.2 if fps[ref]['side']=='F' else 4.2
 shape.translate(App.Vector(149,-49,mounting-base.z));parts[ref]=shape
assert set(parts)==set(fps),(len(parts),set(fps)-set(parts))
def overlap(a,b):
 aa=a.BoundBox;bb=b.BoundBox
 return aa.XMin<bb.XMax and aa.XMax>bb.XMin and aa.YMin<bb.YMax and aa.YMax>bb.YMin and aa.ZMin<bb.ZMax and aa.ZMax>bb.ZMin
conflicts=[];mutual=[];near=[]
for ref,shape in parts.items():
 for name,other in obstacles.items():
  if (ref=='FPC2' and name=='DisplayFPCRoute') or (ref=='H1' and name.startswith('MotorWire')) or (ref=='H2' and name.startswith('BatteryWire')):continue
  if overlap(shape,other):
   vol=shape.common(other).Volume
   if vol>1e-5:conflicts.append({'reference':ref,'against':name,'volume_mm3':round(vol,6)})
  if name in ['BatteryReference','MotorMaximumEnvelope','MotorHolderProposal','ControlFPCRoute','DisplayFPCRoute']:
   distance=shape.distToShape(other)[0]
   if distance<.5:near.append({'reference':ref,'against':name,'nominal_clearance_mm':round(distance,4)})
refs=list(parts)
for i,r in enumerate(refs):
 for q in refs[i+1:]:
  if overlap(parts[r],parts[q]):
   vol=parts[r].common(parts[q]).Volume
   if vol>1e-5:mutual.append({'references':[r,q],'volume_mm3':round(vol,6)})
assert sha(source)==source_hash,'Source enclosure changed during check'
report={'source_enclosure':str(source.relative_to(ROOT)).replace('\\','/'),
 'source_enclosure_sha256':source_hash,'pcb_sha256':sha(pcb),'populated_step_sha256':sha(step),
 'checked_component_instances':len(parts),'obstacles':list(obstacles),
 'nominal_mount_planes_case_z_mm':{'F':5.2,'B':4.2},
 'component_vs_enclosure_conflicts':conflicts,'component_vs_component_conflicts':mutual,
 'nominal_clearances_under_0_5mm':near,'pass':not conflicts and not mutual,
 'scope':'Nominal solids, including DNP footprint models conservatively. No enclosure source changes. Tolerances, cable bending and real selected battery require physical validation.'}
output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('MECHANICAL_RESULT',json.dumps(report,ensure_ascii=False))
if report['pass'] and os.environ.get('MP3_SAVE_FIT_ASSEMBLY')=='1':
 fit=App.newDocument('RoutingPlacementFitF')
 for name,shape in obstacles.items():
  o=fit.addObject('PartDesign::Feature',name);o.Shape=shape
  o.addProperty('App::PropertyString','SourceNote');o.SourceNote='Revision-F reference geometry; source enclosure unchanged.'
 for ref,shape in parts.items():
  o=fit.addObject('PartDesign::Feature','PCB_'+ref);o.Shape=shape
  o.addProperty('App::PropertyString','PCB_SHA256');o.PCB_SHA256=report['pcb_sha256']
 board=next(o for o in unmatched if o.Shape.BoundBox.XLength>40)
 shape=board.Shape.copy();shape.rotate(App.Vector(),App.Vector(0,0,1),180)
 shape.translate(App.Vector(149,-49,-shape.BoundBox.ZMin))
 matrix=App.Matrix();matrix.A33=1/shape.BoundBox.ZLength
 shape=shape.transformGeometry(matrix);shape.translate(App.Vector(0,0,4.2))
 o=fit.addObject('PartDesign::Feature','MainPCB');o.Shape=shape
 fit.recompute();fit.saveAs(str(P/'output/placement-F-fit.FCStd'))
