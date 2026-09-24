from pathlib import Path
import FreeCAD as A,Part,json
O=Path(__file__).resolve().parents[1];V=A.Vector
d=A.openDocument(str(O/'Q2_K_Assembly_Access.FCStd'))
def common(a,b):
 return sum(max(0,x.common(y).Volume) for x in a.Solids for y in b.Solids if x.BoundBox.intersect(y.BoundBox))
def zsegments(n,x,y):
 return [[e.BoundBox.ZMin,e.BoundBox.ZMax] for e in d.getObject(n).Shape.common(Part.makeLine(V(x,y,-1),V(x,y,16))).Edges]
res={'local_thickness_probes':[],'mounts':[],'ports':[],'switch_body_collision':[]}
for name,n,x,y in [('wheel_retention','WheelControlsA',42,59.3),('center_retention','CenterButtonControlsA',31.5,59.3),('control_pilot_roof','HousingControlsA',6,51),('rear_head_seat','RearCoverWithPCBPosts',26.2,3),('rear_main_screw_pilot_floor','RearCoverWithPCBPosts',37.428,35.361)]:
 res['local_thickness_probes'].append({'feature':name,'xy_mm':[x,y],'solid_z_intervals_mm':zsegments(n,x,y)})
src=json.loads((O/'source.json').read_text())
for row in src['main']['footprints']:
 if not row['ref'].startswith('SCREW'):continue
 x,y=176.868-row['xy'][0],row['xy'][1]-65.647
 hole=Part.makeCylinder(row['holes'][0][1]/2-.001,1.6,V(x,y,4.2))
 probe=Part.makeCylinder(.799,2.99,V(x,y,1.21))
 seat=Part.makeCylinder(1.89,.01,V(x,y,4.19)).cut(Part.makeCylinder(.801,.03,V(x,y,4.18)))
 res['mounts'].append({'ref':row['ref'],'xy_mm':[x,y],'pcb_hole_obstruction_mm3':common(hole,d.MainPCB.Shape),'pilot_obstruction_mm3':common(probe,d.RearCoverWithPCBPosts.Shape),'support_material_missing_mm3':seat.cut(d.RearCoverWithPCBPosts.Shape).Volume})
# Small conservative mating-envelope probes, based on modeled connector axes.
# These are not any specific purchased cable's molded overbody.
usb=Part.makeBox(8.5,8,2.5,V(9.302,77.4,6.2))
jack=Part.makeCylinder(1.75,8,V(36.435,77.5,7.9),V(0,1,0))
card=Part.makeBox(9,11,1,V(46.5,11.5,6.0))
for name,s in [('USB_metal_tip_only',usb),('3.5mm_jack_shaft_only',jack),('microSD_card_only',card)]:
 res['ports'].append({'probe':name,'housing_overlap_mm3':common(s,d.HousingControlsA.Shape),'rear_overlap_mm3':common(s,d.RearCoverWithPCBPosts.Shape)})
for name in ['WheelControlsA','CenterButtonControlsA']:
 s=d.getObject(name).Shape.copy();s.translate(V(0,0,-.33))
 for o in d.Electronics.Group:
  if not o.Name.startswith('CTRL_SW'):continue
  # The round top solid represents the moving cap; the rectangular main body is fixed.
  body=o.Shape.Solids[0]
  res['switch_body_collision'].append({'key':name,'switch':o.Name,'travel_mm':.33,'fixed_body_overlap_mm3':common(s,body)})
res['lens_adhesive']={'to_housing_mm':d.LensAdhesive.Shape.distToShape(d.HousingControlsA.Shape)[0],'to_lens_mm':d.LensAdhesive.Shape.distToShape(d.CoverLens.Shape)[0]}
res['lcd_module_to_housing_mm']=d.LCDModule.Shape.distToShape(d.HousingControlsA.Shape)[0]
res['lcd_module_to_lens_mm']=d.LCDModule.Shape.distToShape(d.CoverLens.Shape)[0]
res['limitations']='Local probes, not global wall-thickness analysis; ports checked using stated bare mating envelopes, not cable overmolds. No material strength or tolerance simulation.'
(O/'preflight-detail-check.json').write_text(json.dumps(res,indent=2))
print('DETAILS',json.dumps(res),flush=True)
