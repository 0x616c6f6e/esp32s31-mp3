from pathlib import Path
import FreeCAD as A,Part,Import,json,hashlib
O=Path(__file__).resolve().parents[1];V=A.Vector
d=A.openDocument(str(O/'Q2_L_AM213_Adapter_Study.FCStd'))
k=A.openDocument(str(O.parent/'enclosure-final-k/Q2_K_Assembly_Access.FCStd'))
def vol(a,b):return sum(max(0,s.common(t).Volume) for s in a.Solids for t in b.Solids if s.BoundBox.intersect(t.BoundBox))
def touch(delta,target):
 s=d.LensAdhesive.Shape.copy();s.translate(V(*delta));return vol(s,d.getObject(target).Shape)/V(*delta).Length
adh_area=d.LensAdhesive.Shape.Volume/.2
contacts={'ledge_mm2':touch((0,0,-.001),'HousingControlsA'),'glass_mm2':touch((0,0,.001),'CoverLens'),'adhesive_plan_area_mm2':adh_area}
assert min(contacts['ledge_mm2'],contacts['glass_mm2'])>.99*adh_area,contacts
same={}
for n in ['RearCoverWithPCBPosts','WheelControlsA','CenterButtonControlsA','MotorCarrier','MainPCB','ControlsBoard']:
 a=d.getObject(n).Shape;b=k.getObject(n).Shape;v=a.cut(b).Volume+b.cut(a).Volume;same[n]=v;assert v<1e-5,(n,v)
worst=d.ScreenRearFPCEnvelope.Shape.copy();worst.translate(V(0,0,-.2))
worst_hits={n:vol(worst,d.getObject(n).Shape) for n in ['HousingControlsA','MainPCB','PCB_U9','DisplayAdapterPCB','DisplayAdapterComponents','DisplayAdapterConnectors']}
assert all(v<1e-5 for v in worst_hits.values()),worst_hits
clear={}
for a,b in [('DisplayAdapterComponents','PCB_U9'),('DisplayAdapterConnectors','ScreenRearFPCEnvelope'),('LCDModule','HousingControlsA')]:
 clear[a+'/'+b]=d.getObject(a).Shape.distToShape(d.getObject(b).Shape)[0]
pts=json.loads((O/'screen-contours.json').read_text())['cover']
origin=json.loads((O/'parameters.json').read_text())['display_cover_xy_mm']
errors=[d.CoverLens.Shape.distToShape(Part.Vertex(V(origin[0]+x,origin[1]+y,14.0)))[0] for x,y in pts]
# Source drawing radii are not dimensioned. Bound the analytic approximation.
assert max(errors)<.1,max(errors)
parts=[d.CoverLens,d.LCDModule,d.OLEDOpticalBond]
Import.export(parts,str(O/'AM213Q410502LK-screen-stack.step'))
s=Part.read(str(O/'AM213Q410502LK-screen-stack.step'));b=s.BoundBox
dims=[b.XLength,b.YLength,b.ZLength]
assert all(abs(a-b)<1e-5 for a,b in zip(dims,[46.3,37.5,2.28])),dims
r={'nominal_screen_stack_mm':dims,'glass_adhesive_contacts':contacts,'unchanged_parts_symmetric_difference_mm3':same,
 'screen_stack_extra_0p2mm_backwards_conflicts':worst_hits,'nominal_clearances_mm':clear,
 'cover_analytic_vs_pdf_max_outside_deviation_mm':max(errors),
 'screen_free_tail_is_not_routed':True,'adapter_is_only_reserved_volume':True,'full_assembly_release':False}
(O/'screen-check.json').write_text(json.dumps(r,indent=2));print('SCREEN_CHECK',json.dumps(r),flush=True)
