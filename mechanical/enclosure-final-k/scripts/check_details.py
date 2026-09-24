"""Nominal K fastening and adhesive contact checks; no strength certification."""
from pathlib import Path
import FreeCAD as A, Part, json
O=Path(__file__).resolve().parents[1]; V=A.Vector
d=A.openDocument(str(O/'Q2_K_Assembly_Access.FCStd'))
def volume(a,b):
 return sum(max(0,s.common(t).Volume) for s in a.Solids for t in b.Solids if s.BoundBox.intersect(t.BoundBox))
def span(n,x,y,z0,z1):
 q=Part.makeLine(V(x,y,z0),V(x,y,z1)).common(d.getObject(n).Shape)
 return sorted([[round(e.BoundBox.ZMin,6),round(e.BoundBox.ZMax,6)] for e in q.Edges])
def contact(n,target,delta):
 s=d.getObject(n).Shape.copy(); s.translate(V(*delta))
 return volume(s,d.getObject(target).Shape)/V(*delta).Length
tests={
 'wheel_flange':span('WheelControlsA',42,59.3,12,15),
 'center_flange':span('CenterButtonControlsA',31.8,59.3,12,15),
 'rear_bearing_top':span('RearCoverWithPCBPosts',26.3,3,0,3),
 'rear_bearing_bottom':span('RearCoverWithPCBPosts',26.3,77,0,3),
 'controls_roof_1':span('HousingControlsA',6,51,13.5,15),
 'controls_roof_2':span('HousingControlsA',6,67,13.5,15),
 'controls_roof_3':span('HousingControlsA',44,67,13.5,15),
 'lcd_rail_top':span('HousingControlsA',20,3,11.49,12.55),
 'lcd_rail_bottom':span('HousingControlsA',20,38,11.49,12.55)}
for n,v in tests.items():
 expected=.9 if 'roof' in n else 1.04 if 'rail' in n else 1.0
 assert abs(sum(b-a for a,b in v)-expected)<1e-5,(n,v,expected)
paths=[]
for n in ['RearInsertTop','RearInsertBottom']:
 for dz in [-10,-6,-3,-1,-.5,0]:
  s=d.getObject(n).Shape.copy();s.translate(V(0,0,dz));v=volume(s,d.HousingControlsA.Shape)
  paths.append({'part':n,'z_offset_mm':dz,'intersection_mm3':v});assert v<1e-5,(n,dz,v)
rear_screw_hit=volume(d.RearCoverFasteners.Shape,d.HousingControlsA.Shape)
assert rear_screw_hit<1e-5,rear_screw_hit
contacts={
 'lcd_tape_rail':contact('LCDMountTape','HousingControlsA',(0,0,-.001)),
 'lcd_tape_module':contact('LCDMountTape','LCDModule',(0,0,.001)),
 'carrier_glue_wall':contact('MotorCarrierAdhesive','HousingControlsA',(.001,0,0)),
 'carrier_glue_carrier':contact('MotorCarrierAdhesive','MotorCarrier',(-.001,0,0)),
 'motor_tape_base':contact('MotorAdhesive','MotorCarrier',(0,0,-.001)),
 'motor_tape_motor':contact('MotorAdhesive','Motor_C08_005',(0,0,.001))}
assert contacts['lcd_tape_rail']>43.9 and contacts['lcd_tape_module']>43.9,contacts
assert contacts['carrier_glue_wall']>10.2 and contacts['carrier_glue_carrier']>10.2,contacts
assert contacts['motor_tape_base']>45 and contacts['motor_tape_motor']>48,contacts
r={'material_z_spans_mm':tests,'adhesive_contact_estimate_mm2':contacts,
 'contact_method':'0.001 mm translation into mating body, intersection volume / displacement',
 'insert_rear_entry_samples':paths,'rear_screw_vs_resin_intersection_mm3':rear_screw_hit,
 'limitations':'Nominal geometry only. No torque, pull-out, drop, print-tolerance or adhesive strength qualification.'}
(O/'detail-check.json').write_text(json.dumps(r,indent=2));print('DETAIL_PASS',json.dumps(r),flush=True)
