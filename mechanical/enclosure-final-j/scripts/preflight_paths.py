"""Additional assembly-path and actuation checks; saved geometry is read-only."""
from pathlib import Path
import FreeCAD as A,Part,json,math
O=Path(__file__).resolve().parents[1];V=A.Vector
d=A.openDocument(str(O/'Q2_J_Glue_Insert_Assembly.FCStd'))
def vol(a,b):
 if not a.BoundBox.intersect(b.BoundBox):return 0
 return sum(max(0,x.common(y).Volume) for x in a.Solids for y in b.Solids if x.BoundBox.intersect(y.BoundBox))
def path(name,movers,targets,offsets):
 rows=[]
 for offset in offsets:
  hits=[]
  for a in movers:
   s=a.Shape.copy();s.translate(V(*offset))
   for b in targets:
    q=vol(s,b.Shape)
    if q>1e-5:hits.append([a.Name,b.Name,round(q,6)])
  rows.append({'offset_mm':offset,'hits':hits})
  print(name,offset,'hits',len(hits),json.dumps(hits[:5]),flush=True)
 return rows
res={}
main=[o for o in d.Electronics.Group if o.Name.startswith('PCB_') or o.Name=='MainPCB']+[d.RearCoverWithPCBPosts,d.MainBoardFasteners]
fixed=[d.HousingControlsA,d.ControlsBoard,d.WheelControlsA,d.CenterButtonControlsA,d.Motor_C08_005,d.LCDModule,d.RearInsertTop,d.RearInsertBottom,d.ControlBoardFasteners,d.ControlWashers,d.ControlEdgePad,d.BatteryPack]+[o for o in d.Electronics.Group if o.Name.startswith('CTRL_')]
res['rear_and_mainboard_axial_close']=path('REAR_CLOSE',main,fixed,[[0,0,z] for z in [-15,-10,-5,-2,-1,-.5,0]])
res['wheel_straight_insertion']=path('WHEEL_IN', [d.WheelControlsA],[d.HousingControlsA],[[0,0,z] for z in [-15,-10,-7,-5,-3,-1,0]])
res['center_straight_insertion']=path('CENTER_IN', [d.CenterButtonControlsA],[d.HousingControlsA,d.WheelControlsA],[[0,0,z] for z in [-15,-10,-7,-5,-3,-1,0]])
control=[d.ControlsBoard]+[o for o in d.Electronics.Group if o.Name.startswith('CTRL_')]
res['controls_axial_entry_at_left_offset']=path('CONTROLS_IN',control,[d.HousingControlsA,d.WheelControlsA,d.CenterButtonControlsA], [[-1.2,0,z] for z in [-15,-10,-7,-5,-3,-1,0]])
res['additional_reference_clearances']=[]
for a in [d.LensAdhesive]:
 for b in [d.HousingControlsA,d.LCDModule,d.CoverLens]:
  res['additional_reference_clearances'].append({'a':a.Name,'b':b.Name,'overlap_mm3':vol(a.Shape,b.Shape),'distance_mm':a.Shape.distToShape(b.Shape)[0]})
# Distinguish the moving contact of each switch from unintended package collisions.
res['key_travel_against_components']=[]
for name in ['WheelControlsA','CenterButtonControlsA']:
 for z in [0,-.1,-.2,-.33]:
  res['key_travel_against_components']+=path(name,[d.getObject(name)],[o for o in d.Electronics.Group if o.Name.startswith('CTRL_')],[[0,0,z]])
res['limitations']='Sampled rigid paths. Wires and flexes must be dressed during closing; no flex deformation, continuous sweep or tooling access simulation.'
(O/'preflight-path-check.json').write_text(json.dumps(res,indent=2))
