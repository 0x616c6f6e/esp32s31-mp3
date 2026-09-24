"""FreeCAD: fit controls, key travel and stock FFC to the user's new mainboard.

The revision-F enclosure and mainboard remain read-only. Re-run after exporting
controls-populated.step from the final PCB. Dimensions in mm, case coordinates.
"""
from pathlib import Path
import FreeCAD as A,Part,Import,MeshPart
import json,math,hashlib
P=Path(__file__).resolve().parents[1];ROOT=P.parent;OUT=P/'mechanical';OUT.mkdir(exist_ok=True)
V=A.Vector
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
source=ROOT/'mechanical/enclosure-q2-f/ESP32S31_MP3_Q2_F.FCStd'
plan=json.loads((OUT/'interconnect-plan.json').read_text())
main=ROOT/plan['mainboard']
hashes={'enclosure':sha(source),'mainboard':sha(main)}
assert sha(main)==plan['mainboard_sha256'],'Mainboard changed; refresh interconnect plan'
old=A.openDocument(str(source))
doc=A.newDocument('Q2_Controls_B');doc.Label='Q2 / I2C wheel and four keys + independent POWER / B'
parts={};colors={}
groups={n:doc.addObject('App::DocumentObjectGroup',n) for n in ['Enclosure','ControlsPCB','References','Construction']}
def add(name,shape,group='References',color=(.55,.58,.62),label=None):
 o=doc.addObject('PartDesign::Feature',name);o.Shape=shape;groups[group].addObject(o);o.Label=label or name;parts[name]=o;colors[name]=color
 if o.ViewObject:o.ViewObject.ShapeColor=color
 return o
def cylinder(name,r,h,x,y,z):
 o=doc.addObject('Part::Cylinder',name);o.Radius=r;o.Height=h;o.Placement.Base=V(x,y,z);groups['Construction'].addObject(o);return o
def ring(name,ro,ri,z,h):
 outer=cylinder(name+'Outer',ro,h,25,59.3,z);inner=cylinder(name+'Inner',ri,h+.2,25,59.3,z-.1)
 o=doc.addObject('Part::Cut',name);o.Base=outer;o.Tool=inner;groups['Construction'].addObject(o);return o
def finish(name,objects,color):
 o=doc.addObject('Part::MultiFuse',name);o.Shapes=objects;o.Refine=True;groups['Enclosure'].addObject(o);parts[name]=o;colors[name]=color;return o
for n in ['RearCoverWithPCBPosts','LCDModule','LCDActiveArea','CoverLens','LensBlackMask','LensAdhesive','ControlSymbols','BatteryReference','DisplayFPCRoute','ControlBoardFasteners','Motor_C08_005','MotorHolderProposal','MotorAdhesive']:
 o=old.getObject(n);sh=o.Shape.copy()
 if n.startswith('Motor'):sh.translate(V(0,5,0))
 if n=='RearCoverWithPCBPosts':
  raw=add('RearCoverSourceF',sh,'Construction')
  relief=doc.addObject('Part::Box','FFCRearLipRelief');relief.Length=1.17;relief.Width=7.1;relief.Height=1.175;relief.Placement.Base=V(47.55,48.161,1.325);groups['Construction'].addObject(relief)
  rear=doc.addObject('Part::Cut',n);rear.Base=raw;rear.Tool=relief;rear.Refine=True;rear.Label='Rear cover / local FFC inner-lip relief';groups['Enclosure'].addObject(rear);parts[n]=rear;colors[n]=(.55,.58,.62)
 else:add(n,sh,'References',label=o.Label)
# Register the new mainboard by its 46 x 76 outline. The old mounting posts
# remain visible as a reference; their redesign is not claimed by this check.
md=json.loads((OUT/'mainboard-reference.json').read_text())
mf={c['ref']:c for c in md['footprints'] if c['model']}
native_main=A.newDocument('MainLayoutImport');Import.insert(str(OUT/'mainboard-layout-reference.step'),native_main.Name)
ma=max(native_main.Objects,key=lambda o:len(o.OutList))
main_models={}
for item in ma.OutList:
 if item.TypeId=='App::Origin':continue
 sh=Part.getShape(item)
 if sh.isNull() or sh.Volume<1e-8:continue
 base=item.Placement.Base
 ref=min(mf,key=lambda r:math.hypot(mf[r]['xy'][0]-base.x,mf[r]['xy'][1]+base.y))
 sh=sh.copy();sh.rotate(V(),V(0,0,1),180)
 if math.hypot(mf[ref]['xy'][0]-base.x,mf[ref]['xy'][1]+base.y)>.005:
  sh.translate(V(176.868,-65.647,-sh.BoundBox.ZMin));mat=A.Matrix();mat.A33=1.6/sh.BoundBox.ZLength
  sh=sh.transformGeometry(mat);sh.translate(V(0,0,4.2));add('MainPCB',sh,color=(.1,.4,.26));continue
 assert ref not in main_models,ref
 sh.translate(V(176.868,-65.647,(5.8 if mf[ref]['side']=='F' else 4.2)-base.z))
 main_models[ref]=add('PCB_'+ref,sh,label=ref+' / '+mf[ref]['footprint'])
assert set(main_models)==set(mf),(set(mf)-set(main_models))
A.closeDocument(native_main.Name);A.setActiveDocument(doc.Name)
housing=add('HousingSourceF',old.getObject('HousingWithControlPosts').Shape.copy(),'Construction')
# A hidden underside recess accepts the raised wheel-retention flange. External
# wheel aperture and all exterior surfaces are preserved.
recess=ring('RetentionRecess',17.45,16.7,11.7,.95)
h=doc.addObject('Part::Cut','HousingControlsA');h.Base=housing;h.Tool=recess;h.Refine=True;groups['Enclosure'].addObject(h);parts[h.Name]=h;colors[h.Name]=(.74,.77,.80)
wheelparts=[ring('WheelFace',16.5,6.15,12.95,.6),ring('WheelCollar',16.5,15.8,12.35,.61),ring('WheelFlange',17.2,15.8,12.35,.2)]
for i,(x,y) in enumerate([(25,46.3),(38,59.3),(12,59.3),(25,72.3)]):wheelparts.append(cylinder('WheelPlunger'+str(i),.85,.31,x,y,12.65))
wheel=finish('WheelControlsA',wheelparts,(.045,.05,.057))
button=finish('CenterButtonControlsA',[cylinder('CenterFace',5.7,.8,25,59.3,12.7),cylinder('CenterPlunger',1.2,.2,25,59.3,12.65),ring('CenterRetainer',6.9,3.2,12.35,.2),ring('CenterSleeve',5.3,3.2,12.35,.6)],(.77,.79,.82))
doc.recompute()
data=json.loads((P/'output/design.json').read_text(encoding='utf8'))
fps={c['ref']:c for c in data['components'] if c['kind'] not in ['Wheel','TestPoint','MountingHole']}
native=A.newDocument('ControlsImport');Import.insert(str(P/'output/controls-populated.step'),native.Name)
assembly=next(o for o in native.Objects if o.Label=='controls-populated 1');models={};board=None
for item in assembly.OutList:
 if item.TypeId=='App::Origin':continue
 shape=Part.getShape(item)
 if shape.isNull() or shape.Volume<1e-8:continue
 base=item.Placement.Base
 ref=min(fps,key=lambda r:math.hypot(44-fps[r]['pcb'][0]-base.x,fps[r]['pcb'][1]+base.y))
 sh=shape.copy();sh.rotate(V(),V(0,0,1),180)
 if math.hypot(44-fps[ref]['pcb'][0]-base.x,fps[ref]['pcb'][1]+base.y)>.005:
  # KiCad exports the dielectric alone (0.71 mm for a 0.8 mm finished PCB).
  # Fit checking uses the full nominal finished-board envelope including copper.
  sh.translate(V(47,42.3,-sh.BoundBox.ZMin));mat=A.Matrix();mat.A33=.8/sh.BoundBox.ZLength
  sh=sh.transformGeometry(mat);sh.translate(V(0,0,11.1));board=add('ControlsBoard',sh,'ControlsPCB',(.06,.36,.22));continue
 assert ref not in models,ref
 sh.translate(V(47,42.3,(11.9 if fps[ref]['pcb'][2]=='F' else 11.1)-base.z))
 models[ref]=add('CTRL_'+ref,sh,'ControlsPCB',(.13,.14,.17),ref+' / '+fps[ref]['value'])
assert set(models)==set(fps),(set(fps)-set(models))
assert board is not None,'PCB solid missing'
assert abs(board.Shape.BoundBox.ZLength-.8)<.01,('PCB thickness',board.Shape.BoundBox.ZLength)
A.closeDocument(native.Name);A.setActiveDocument(doc.Name)
# Actual copper outlines (not the old illustrative twelve-sector guide).
electrodes=json.loads((P/'output/electrodes.json').read_text());copper=[]
for ch in electrodes['channels']:
 polys=[]
 for poly in ch['polygons']:
  points=[V(3+x,42.3+y,11.9) for x,y in poly['points']]
  face=Part.Face(Part.makePolygon(points+[points[0]]));polys.append(face)
 copper.append(max(polys,key=lambda f:f.Area).extrude(V(0,0,.012)))
add('WheelCopper',Part.makeCompound(copper),'ControlsPCB',(.78,.58,.25))
obstacles={n:o.Shape for n,o in parts.items() if n not in ['HousingSourceF','RearCoverSourceF'] and not n.startswith('CTRL_') and n not in ['ControlsBoard','WheelCopper']}
obstacles['MotorMaximumEnvelope']=Part.makeCylinder(4.05,3.45,V(39,62,7.1))
def volume(a,b):
 aa=a.BoundBox;bb=b.BoundBox
 if aa.XMax<=bb.XMin or bb.XMax<=aa.XMin or aa.YMax<=bb.YMin or bb.YMax<=aa.YMin or aa.ZMax<=bb.ZMin or bb.ZMax<=aa.ZMin:return 0.
 return a.common(b).Volume
conflicts=[];clearances=[]
for ref,obj in list(models.items())+[('ControlsBoard',board)]:
 for n,sh in obstacles.items():
  vol=volume(obj.Shape,sh)
  if vol>1e-5:conflicts.append({'part':ref,'obstacle':n,'volume_mm3':round(vol,6)})
  if n in ['BatteryReference','MotorMaximumEnvelope','MotorHolderProposal','HousingControlsA']:
   clearances.append({'part':ref,'obstacle':n,'distance_mm':round(obj.Shape.distToShape(sh)[0],4)})
for i,(ref,obj) in enumerate(models.items()):
 for ref2,obj2 in list(models.items())[i+1:]:
  vol=volume(obj.Shape,obj2.Shape)
  if vol>1e-5:conflicts.append({'part':ref,'obstacle':ref2,'volume_mm3':round(vol,6)})
stroke=[]
for n,o in [('Wheel',wheel),('Center',button)]:
 sh=o.Shape.copy();sh.translate(V(0,0,-.33))
 stroke.append({'part':n,'axial_displacement_mm':.33,'board_collision_mm3':volume(sh,board.Shape),'housing_collision_mm3':volume(sh,h.Shape),'note':'Rigid axial clearance envelope only; rocking tilt and feel need prototype validation.'})
report={'source_sha256':hashes,'controls_pcb_sha256':sha(P/'controls.kicad_pcb'),'models':len(models),'board_mm':[44,34,.8],'nominal_component_conflicts':conflicts,'clearances':clearances,'axial_travel_check':stroke,'switch':'SKSWCEE010: nominal height 0.6 +/-0.05, stroke 0.13','plunger_gap_mm':[.1,.2],'nominal_travel_to_trigger_mm':.28,'worst_height_travel_to_trigger_mm':.33,'board_to_battery_nominal_gap_mm':.3,'touch_cover_air_gap_mm':1.05,'mainboard_connected':False,'status':'Nominal geometry only; battery selection, tolerances, rocking mechanics and touch calibration require prototype validation.'}
report['pass']=not conflicts and all(r['board_collision_mm3']<1e-5 and r['housing_collision_mm3']<1e-5 for r in stroke)
rocking=[]
# A single-key pose: 0.165 mm translation plus +/-asin(0.165/13) tilt.
# This gives the selected plunger ~0.33 mm travel and the perpendicular
# plungers ~0.165 mm. It verifies a feasible envelope, not force equilibrium.
angle=math.degrees(math.asin(.165/13))
for axis,sgn in [(V(1,0,0),1),(V(1,0,0),-1),(V(0,1,0),1),(V(0,1,0),-1)]:
 sh=wheel.Shape.copy();sh.rotate(V(25,59.3,12.65),axis,sgn*angle);sh.translate(V(0,0,-.165))
 rocking.append({'axis':list(axis),'angle_deg':sgn*angle,'translation_z_mm':-.165,'board_collision_mm3':volume(sh,board.Shape),'housing_collision_mm3':volume(sh,h.Shape),'center_button_collision_mm3':volume(sh,button.Shape)})
report['four_way_pose_check']=rocking
report['pass']=report['pass'] and all(max(r[k] for k in ['board_collision_mm3','housing_collision_mm3','center_button_collision_mm3'])<1e-5 for r in rocking)
import sys
sys.path.insert(0,str(P/'scripts'))
from ffc_route import build as build_ffc
report['interconnect']=build_ffc(add,parts,models,obstacles,volume)
report['pass']=report['pass'] and report['interconnect']['nominal_route_pass']
report['mainboard_source']=plan['mainboard']
report['mainboard_thickness_mm']=1.6
report['mainboard_models_missing']=md['missing_component_models']
report['mainboard_mounting_posts_match_new_hole_pattern']=False
report['motor_case_center_mm']=[39,62]
report['motor_and_battery_wires_not_rerouted_in_this_assembly']=True
report['mainboard_connected']=False
report['scope_note']='Nominal control-board and FFC fit to new mainboard registered by board outline. Original housing exterior preserved; new mainboard mounting posts and harnesses still require redesign. Cable dimensions not dimensioned by connector drawing are assumptions.'
(OUT/'fit-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(OUT/'colors.json').write_text(json.dumps(colors,indent=2)+'\n')
for o in [h,wheel,button,rear]:
 assert o.Shape.isValid() and len(o.Shape.Solids)==1,(o.Name,len(o.Shape.Solids))
 Import.export([o],str(OUT/(o.Name+'.step')))
 mesh=MeshPart.meshFromShape(Shape=o.Shape,LinearDeflection=.05,AngularDeflection=.2,Relative=False);mesh.write(str(OUT/(o.Name+'.stl')))
doc.recompute();doc.saveAs(str(OUT/'Q2_Controls_Assembly.FCStd'))
assert hashes=={'enclosure':sha(source),'mainboard':sha(main)}
print('CONTROLS_FIT',json.dumps({k:report[k] for k in ['pass','models','nominal_component_conflicts','axial_travel_check']},ensure_ascii=False))
A.closeDocument(old.Name)
