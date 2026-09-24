from pathlib import Path
import FreeCAD as A,Part,json,hashlib,math
O=Path(__file__).resolve().parents[1];R=O.parents[1];V=A.Vector
for v in json.loads((O/'source.json').read_text()).values():assert hashlib.sha256((R/v['path']).read_bytes()).hexdigest()==v['sha256']
d=A.openDocument(str(O.parent/'enclosure-final-h/Q2_H_Reinforced_Assembly.FCStd'));d.Label='Q2 I / cable protection and serviceable controls mounts'
def box(x,y,z,w,l,h):return Part.makeBox(w,l,h,V(x,y,z))
def cyl(x,y,z,r,h):return Part.makeCylinder(r,h,V(x,y,z))
def ring(x,y,z,ro,ri,h):return cyl(x,y,z,ro,h).cut(cyl(x,y,z-.1,ri,h+.2))
def add(n,s,group='AssemblyReferences'):
 o=d.getObject(n) or d.addObject('PartDesign::Feature',n);o.Shape=s;d.getObject(group).addObject(o);return o
s=d.HousingControlsA.Shape.copy();fast=[];wash=[]
for x,y in [(6,51),(44,51),(6,67),(44,67)]:
 # Recover the front skin instead of extending the blind hole towards the face.
 s=s.fuse(cyl(x,y,13.0,.66,.3))
 if (x,y)==(44,51):
  s=s.fuse(cyl(x,y,11.9,.66,1.3));continue
 s=s.cut(cyl(x,y,11.8,.65,1.2))
 wash.append(ring(x,y,10.8,2,.85,.3))
 fast.append(cyl(x,y,10.8,.8,2).fuse(cyl(x,y,10.3,1.65,.5)))
add('ControlBoardFasteners',Part.makeCompound(fast));add('ControlWashers',Part.makeCompound(wash))
# Capture the right PCB edge below the FFC span, without a fastener crossing the cable.
# Slide the unfastened board towards +X by 1.2 mm, then tighten its three screws.
clip=box(45.8,55.45,10.3,3.1,1.2,.6)
s=s.fuse(clip)
add('ControlEdgePad',box(45.85,55.55,10.9,1.1,1.0,.2))
# Broader retention rims: preserve key faces and plunger elevations.
wheel=d.WheelControlsA.Shape.fuse(ring(25,59.3,12.35,17.35,15.8,.50))
button=d.CenterButtonControlsA.Shape.fuse(ring(25,59.3,12.35,7.15,3.2,.40)).fuse(ring(25,59.3,12.4,5.7,3.2,.5))
# Small fillets at the retention rim roots; identify circular seam edges by geometry.
def round_seam(shape,z,radius,fillet):
 es=[]
 for e in shape.Edges:
  c=e.Curve
  if hasattr(c,'Radius') and abs(c.Radius-radius)<1e-5 and abs(e.BoundBox.ZMin-z)<1e-5 and abs(e.BoundBox.ZMax-z)<1e-5:es.append(e)
 if not es:return shape,False
 try:
  out=shape.makeFillet(fillet,es)
  if out.isValid():return out,True
 except Exception:pass
 return shape,False
wheel,wf=round_seam(wheel.removeSplitter(),12.85,16.5,.12)
button,bf=round_seam(button.removeSplitter(),12.75,5.7,.15)
d.WheelControlsA.Shape=wheel.removeSplitter();d.CenterButtonControlsA.Shape=button.removeSplitter()
s=s.cut(ring(25,59.3,11.85,17.7,16.7,1.15))
# Widen the center release only inside the wheel; exterior opening stays fixed.
d.WheelControlsA.Shape=d.WheelControlsA.Shape.cut(cyl(25,59.3,12.65,7.5,.40)).removeSplitter()
# Round the ends of the cable reliefs rather than adding narrow printed hooks.
def channel(x,y,z,w,l,h):
 q=box(x,y,z,w,l,h)
 es=[e for e in q.Edges if abs(e.BoundBox.XLength-w)<1e-6 and e.BoundBox.YLength<1e-6 and e.BoundBox.ZLength<1e-6]
 return q.makeFillet(.6,es)
s=s.cut(channel(.95,10.8,1.5,.4,19.2,10.9)).cut(channel(48.7,47.9,1.3,.3,7.6,9.95))
add('DisplayChannelLiner',box(.95,11.6,2.3,.05,17.6,9.3))
add('ControlChannelLiner',box(48.95,48.7,2.6,.05,6.0,7.2))
add('WireEdgeInsulation',box(1.95,48,4.0,.05,14,2.0))
# Relieve sharp rear-lip corners at the two cable pass-through regions.
rear=d.RearCoverWithPCBPosts.Shape.copy()
rear=rear.cut(box(1.2,10.6,1.55,1.8,19.6,1.05)).cut(box(47.35,47.85,1.2,1.5,7.7,1.4))
d.RearCoverWithPCBPosts.Shape=rear.removeSplitter()
# Rebuild two motor conductors: clear the rounded lower corner and separate
# their diagonal approaches to the motor in both X and Z.
def conductor(pts,r=.225):
 pieces=[]
 for a,b in zip(pts,pts[1:]):
  a,b=V(*a),V(*b);v=b-a
  pieces.append(Part.makeCylinder(r,v.Length,a,v))
 for p in pts[1:-1]:pieces.append(Part.makeSphere(r,V(*p)))
 return pieces[0].multiFuse(pieces[1:]).removeSplitter()
d.MotorWire1.Shape=conductor([(4.22,70.106,3.25),(2.2,70.106,3.25),(1.61,68.5,3.25),(1.61,68.5,10.6),(1.61,55.8,10.6),(6,55.8,10.6),(6,55.8,7.1),(33.7,55.8,7.1),(35,59.6,8),(38.9,59.6,8)])
d.MotorWire2.Shape=conductor([(4.22,67.606,3.25),(1.61,67.606,3.25),(1.61,67.606,10),(1.61,56.4,10),(8,56.4,10),(8,56.4,7.1),(32.7,56.4,7.1),(32.7,56.4,9),(36,60.4,9),(38.9,60.4,9)])
# All intersecting segments must be united before collision testing or STEP export.
normalized=[]
for o in d.Objects:
 if o.Name in ['DisplayFPCRoute','ControlFFC40mm'] or (o.Name.startswith(('BatteryWire','MotorWire')) and 'Relief' not in o.Name):
  ss=o.Shape.Solids
  if len(ss)>1:o.Shape=ss[0].multiFuse(ss[1:]).removeSplitter();normalized.append(o.Name)
s=s.removeSplitter();d.HousingControlsA.Shape=s
for o in d.PrintableParts.Group:assert o.Shape.isValid() and len(o.Shape.Solids)==1,(o.Name,len(o.Shape.Solids))
params=json.loads((O/'parameters.json').read_text());params.update(controls_screws='3 x M1.6 x 2 UNDER HEAD, each with DIN125A 1.7 ID x4 OD x0.3 mm washer; right upper screw OMITTED',controls_pilot_depth_mm=1.1,controls_pilot_roof_mm=.5,controls_nominal_screw_engagement_mm=.9,controls_screw_tip_to_pilot_end_mm=.2,controls_edge_capture='Right PCB edge at case Y55.45..56.65, with 0.2 mm insulating pad; no screw across FFC',wheel_retention_thickness_mm=.5,center_retention_thickness_mm=.4)
(O/'parameters.json').write_text(json.dumps(params,indent=2))
for i,(k,v) in enumerate(params.items(),1):d.DesignParameters.set('A'+str(i),k);d.DesignParameters.set('B'+str(i),str(v))
d.recompute();d.saveAs(str(O/'Q2_I_Serviceable_Assembly.FCStd'))
(O/'optimization.json').write_text(json.dumps({'source':'../enclosure-final-h/Q2_H_Reinforced_Assembly.FCStd','normalized_cable_and_wire_shapes':normalized,'wheel_root_fillet_applied':wf,'center_root_fillet_applied':bf,'previous_compound_overlap_false_negative_corrected':True},indent=2))
print('I_SAVED',wf,bf,flush=True)
