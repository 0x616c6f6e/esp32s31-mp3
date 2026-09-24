from pathlib import Path
import FreeCAD as A,Part,json,hashlib,sys
O=Path(__file__).resolve().parents[1];R=O.parents[1];J=O.parent/'enclosure-final-j';V=A.Vector
O.mkdir(exist_ok=True)
src=json.loads((J/'source.json').read_text())
for v in src.values():assert hashlib.sha256((R/v['path']).read_bytes()).hexdigest()==v['sha256']
(O/'source.json').write_text(json.dumps(src,indent=2))
d=A.openDocument(str(J/'Q2_J_Glue_Insert_Assembly.FCStd'));d.Label='Q2 K / assembly access, reinforced keys, LCD supports'
def box(x,y,z,w,l,h):return Part.makeBox(w,l,h,V(x,y,z))
def cyl(x,y,z,r,h):return Part.makeCylinder(r,h,V(x,y,z))
def ring(x,y,z,ro,ri,h):return cyl(x,y,z,ro,h).cut(cyl(x,y,z-.1,ri,h+.2))
def add(n,s,group='AssemblyReferences',label=None):
 o=d.getObject(n) or d.addObject('PartDesign::Feature',n);o.Shape=s.removeSplitter();d.getObject(group).addObject(o)
 if label:o.Label=label
 return o

s=d.HousingControlsA.Shape.copy()
# Raise only the front region. The original filleted outline and all apertures
# are carried upward; lower shell, boards, ports and switch contact planes stay.
top=s.common(box(-3,-4,11.9,56,90,5));top.translate(V(0,0,.9));s=s.fuse(top)
# Remove the integral motor support while preserving the outer side wall.
s=s.cut(d.MotorHolderGeometry.Shape.common(box(-2,-3,0,50.8,90,15)))
# Shorten the lower rear-fastener post; allow the keys/PCB to move over it.
s=s.cut(cyl(25,77,6.0,2.41,5.7))
# Rear-cover screw seats are raised internally; keep their external recesses.
rear=d.RearCoverWithPCBPosts.Shape.copy()
for y,n in [(3,'RearInsertTop'),(77,'RearInsertBottom')]:
 rear=rear.fuse(cyl(25,y,.65,2.2,1.0))
 rear=rear.cut(cyl(25,y,-.1,.95,2.0)).cut(cyl(25,y,-.1,1.9,.75))
 rear=rear.cut(cyl(25,y,1.7,2.85,1.5))
 s=s.cut(cyl(25,y,1.19,2.41,.66))
 s=s.fuse(cyl(25,y,1.85,2.6,(10.6 if y==3 else 6.0)-1.85))
 # Re-form the socket floor, then open the new glue-fit socket and passage.
 s=s.fuse(cyl(25,y,4.39,1.36,.81))
 s=s.cut(cyl(25,y,1.84,1.5,3.21)).cut(Part.makeCone(1.65,1.5,.15,V(25,y,1.85)))
 s=s.cut(cyl(25,y,1.84,.9,5.36))
 d.getObject(n).Shape=ring(25,y,2.05,1.25,.8,3)
d.RearCoverWithPCBPosts.Shape=rear.removeSplitter()
# Strengthen the three control pilots; add 0.5 mm of screw engagement.
fast=[]
for x,y in [(6,51),(44,51),(6,67),(44,67)]:
 s=s.fuse(cyl(x,y,11.9,.66,2.2))
 if (x,y)!=(44,51):
  s=s.cut(cyl(x,y,11.8,.65,1.7))
  fast.append(cyl(x,y,10.8,.8,2.5).fuse(cyl(x,y,10.3,1.65,.5)))
add('ControlBoardFasteners',Part.makeCompound(fast),label='3 x M1.6 x 2.5 UNDER HEAD + 0.3 washers')
# Thicken the edge-capture ledge downwards; retain its pad/support plane.
s=s.fuse(box(45.8,55.45,9.9,3.1,1.2,1.0))
# New keys: 1 mm retaining rims and >=0.85 mm faces. Contact tips stay Z12.65.
wheel=ring(25,59.3,13.6,16.5,6.15,.9).fuse(ring(25,59.3,12.35,17.35,15.3,1.0)).fuse(ring(25,59.3,12.35,16.5,15.3,1.35))
for x,y in [(25,46.3),(38,59.3),(12,59.3),(25,72.3)]:wheel=wheel.fuse(cyl(x,y,12.65,.85,1.0))
wheel=wheel.cut(cyl(25,59.3,12.1,7.55,1.55))
button=ring(25,59.3,12.35,7.15,3.2,1.0).fuse(ring(25,59.3,12.35,5.7,3.2,1.4)).fuse(cyl(25,59.3,13.5,5.7,.9)).fuse(cyl(25,59.3,12.65,1.2,1.0))
add('WheelControlsA',wheel,'PrintableParts','03 Wheel K / 1.0 mm rim / no carrier')
add('CenterButtonControlsA',button,'PrintableParts','04 Center key K / 1.0 mm rim / no carrier')
s=s.cut(ring(25,59.3,11.85,17.7,16.7,1.70))
# Raise the complete optical stack, leaving 0.3 mm air between LCD and cover.
for n in ['LCDModule','LCDActiveArea','CoverLens','LensBlackMask','LensAdhesive','ControlSymbols']:
 shape=d.getObject(n).Shape.copy();shape.translate(V(0,0,.95 if n=='ControlSymbols' else .9));d.getObject(n).Shape=shape
# Two solid rails and removable foam adhesive support the module's back face.
for y in [1.5,37.0]:s=s.fuse(box(14,y,11.5,22,2.5,1.04))
add('LCDMountTape',Part.makeCompound([box(15,2.4,12.54,20,1.1,.2),box(15,37.2,12.54,20,1.1,.2)]),label='LCD back mounting / 2 strips 20 x 1.1 x 0.2 mm adhesive foam')
# Raise the FPC channel to clear its new origin. PCB-side insertion is unchanged.
s=s.cut(box(.95,10.8,11.0,.4,19.2,2.4))
s=s.cut(box(1.0,11.1,12.05,2.6,18.6,1.25))
sys.path.insert(0,str(O/'scripts'));from display_route import build
flex,flex_report=build();ss=flex.Solids
add('DisplayFPCRoute',ss[0].multiFuse(ss[1:]))
(O/'display-route.json').write_text(json.dumps(flex_report,indent=2))
add('DisplayChannelLiner',box(.95,11.6,2.3,.05,17.6,10.2))
# A separate, later-installed motor carrier clears the controls' entry route.
holder=cyl(43,60,6.1,5.4,1.1).fuse(ring(43,60,7.15,5.4,4.35,1.2))
holder=holder.fuse(box(46.4,57.5,6.1,2.2,5,2.05))
holder=holder.cut(cyl(43,60,7.2,4.35,4)).cut(box(37.5,58.9,7.2,2.5,2.1,2))
holder.translate(V(0,.3,0))
holder=holder.cut(cyl(44.7,65.4995,5.8,2.1,1.3))
holder=holder.cut(box(37.4,63.3,5.8,3.65,3.3,3.0))
add('MotorCarrier',holder,'PrintableParts','05 Motor carrier / glue to right wall AFTER controls')
add('MotorCarrierAdhesive',box(48.6,57.8,6.1,.2,5,2.05),label='Motor carrier to wall / 0.2 mm epoxy design gap')
add('Motor_C08_005',cyl(43,60.3,7.3,4.05,3.45),label='C08-005 LRA / max OD8.1 x3.45')
add('MotorAdhesive',cyl(43,60.3,7.2,3.95,.1))
add('HousingControlsA',s,'PrintableParts','01 Housing K / higher front / open assembly path')
d.RearCoverWithPCBPosts.Label='02 Rear cover K / 1.0 mm screw bearing seat'
# The enlarged key heights meet the 2 mm upload dimension directly; no tabs.
d.InsertFitCoupon.Label='06 Optional insert coupon / notch end 2.65, 2.70, 2.75'
coupon=d.InsertFitCoupon.Shape.copy()
for x,diam in [(64,2.9),(72,3.0),(80,3.1)]:
 coupon=coupon.cut(cyl(x,4,1.8,diam/2,3.3)).cut(Part.makeCone(diam/2,diam/2+.15,.15,V(x,4,4.85)))
d.InsertFitCoupon.Shape=coupon.removeSplitter();d.InsertFitCoupon.Label='06 Optional insert coupon / notch end 2.90, 3.00, 3.10'
for o in d.PrintableParts.Group:
 assert o.Shape.isValid() and len(o.Shape.Solids)==1,(o.Name,len(o.Shape.Solids))
p=json.loads((J/'parameters.json').read_text())
p.update(revision='K',case_body_height_mm=14.4,case_height_including_lens_mm=15.1,
 controls_screws='3 x M1.6 x 2.5 UNDER HEAD, head <=D3.3 x0.5; each with ID1.7 OD4 thickness0.3 washer',
 controls_pilot_depth_mm=1.6,controls_pilot_roof_mm=.9,controls_nominal_screw_engagement_mm=1.4,
 wheel_retention_thickness_mm=1.0,center_retention_thickness_mm=1.0,
 rear_screw_bearing_thickness_mm=1.0,rear_insert_axial_span_mm=[2.05,5.05],
 rear_insert_bore_diameter_mm=3.0,rear_insert_radial_glue_gap_mm=.25,rear_insert_body_min_wall_mm=1.10,rear_insert_entry_min_wall_mm=.95,insert_coupon_holes_mm=[2.9,3.0,3.1],
 rear_insert_bore_start_z_mm=1.85,rear_lower_post_top_z_mm=6.0,
 lcd_origin_mm=[3.275,2.235,12.74],lcd_mount='Two integral rails + 0.20 mm back-face foam adhesive strips, installed from front before cover lens',
 motor_carrier='Separate printed part, glued after controls; rear PCB is installed last',motor_base_z_mm=7.3,motor_case_center_mm=[43,60.3],
 key_printing='Single parts without sacrificial carriers; wheel 2.15 mm, center 2.05 mm axial envelope',
 front_raise_mm=.9)
(O/'parameters.json').write_text(json.dumps(p,indent=2))
for i,(k,v) in enumerate(p.items(),1):d.DesignParameters.set('A'+str(i),k);d.DesignParameters.set('B'+str(i),str(v))
d.recompute();d.saveAs(str(O/'Q2_K_Assembly_Access.FCStd'))
print('K_BUILT',flush=True)
