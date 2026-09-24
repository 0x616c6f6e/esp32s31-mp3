"""Appearance-only SLA sample. Preserve visible surfaces; respect 2 mm size gate."""
from pathlib import Path
import FreeCAD as A,Part,Import,MeshPart,json,hashlib,itertools,zipfile
ROOT=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
SOURCE=ROOT/'mechanical/appearance-prototype-v1/Q2_Appearance_Prototype_V1.FCStd'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(SOURCE);old=A.openDocument(str(SOURCE));d=A.newDocument('Q2AppearanceV2')
d.Label='Q2 appearance sample V2 / SLA / 2.2 mm small parts'
V=A.Vector
for sub in ['print-parts','reference']:(O/sub).mkdir(exist_ok=True)
def rounded(w,h,r,z,t,x,y):
 shapes=[Part.makeBox(w-2*r,h,t,V(x+r,y,z)),Part.makeBox(w,h-2*r,t,V(x,y+r,z))]
 shapes += [Part.makeCylinder(r,t,V(a,b,z)) for a,b in [(x+r,y+r),(x+w-r,y+r),(x+w-r,y+h-r),(x+r,y+h-r)]]
 return shapes[0].multiFuse(shapes[1:]).removeSplitter()
body_original=old.getObject('HousingControlsA').Shape.copy()
# Lower only the hidden cover-lens support by .22 mm. Front face stays z=13.5.
seat=rounded(46.3,40.3,10.65,13.20,1.2,1.85,.35)
body=body_original.cut(seat).removeSplitter()
rear=old.getObject('RearCoverWithPCBPosts').Shape.copy()
# Solid appearance controls; no 0.20 mm retention flange or switch plungers.
wheel=Part.makeCylinder(16.5,2.2,V(25,59.3,11.35)).cut(Part.makeCylinder(6.15,2.4,V(25,59.3,11.25))).removeSplitter()
center=Part.makeCylinder(5.7,2.2,V(25,59.3,11.30))
# .9 mm visible cap, lower core inside the existing LCD opening. Top stays14.2.
screen=rounded(46,40,10.5,13.30,.90,2,.5).fuse(rounded(43.45,36.33,10,12.0,1.31,3.275,2.235)).removeSplitter()
spec=[('01-body','HousingControlsA','机身',body,(.74,.77,.80)),
      ('02-rear-cover','RearCoverWithPCBPosts','后盖',rear,(.67,.70,.73)),
      ('03-wheel','WheelAppearance','圆环外观样件',wheel,(.045,.05,.057)),
      ('04-center-button','CenterAppearance','中心键外观样件',center,(.77,.79,.82)),
      ('05-screen-dummy','ScreenAppearance','屏幕外观占位片',screen,(.025,.032,.042))]
records=[];objects=[]
for filename,name,label,shape,color in spec:
 assert shape.isValid() and len(shape.Solids)==1,name
 o=d.addObject('PartDesign::Feature',name);o.Label=label;o.Shape=shape;objects.append(o)
 o.addProperty('App::PropertyString','Purpose','Manufacturing').Purpose='Appearance sample only; tape fixation, not a functional switch mechanism.'
 if o.ViewObject:o.ViewObject.ShapeColor=color
 bb=shape.BoundBox;local=shape.copy();local.translate(V(-bb.XMin,-bb.YMin,-bb.ZMin))
 mesh=MeshPart.meshFromShape(Shape=local,LinearDeflection=.03,AngularDeflection=.15,Relative=False)
 assert mesh.isSolid(),name
 dims=[round(mesh.BoundBox.XLength,5),round(mesh.BoundBox.YLength,5),round(mesh.BoundBox.ZLength,5)]
 s=sorted(dims);passes=all(v>=5 for v in s) or (s[0]>=2 and s[1]>=2 and s[2]>=10)
 assert passes,(name,dims)
 mesh.write(str(O/'print-parts'/(filename+'.stl')));local.exportStep(str(O/'reference'/(filename+'.step')))
 records.append({'file':filename+'.stl','label':label,'source_object':name,'dimensions_mm':dims,'closed_mesh':True,'valid_single_solid':True,'passes_material_minimum_size':passes,'color':color,'triangles':mesh.CountFacets})
fit=[]
for a,b in itertools.combinations(objects,2):
 volume=a.Shape.common(b.Shape).Volume
 fit.append({'a':a.Name,'b':b.Name,'overlap_mm3':volume})
 # Body/rear joint is inherited; require all other pairs to be collision free.
 if {a.Name,b.Name}!={'HousingControlsA','RearCoverWithPCBPosts'}:assert volume<1e-6,(a.Name,b.Name,volume)
removed=body_original.cut(body)
assert removed.cut(seat).Volume<1e-7
assert body.cut(body_original).Volume<1e-7
assert abs(wheel.BoundBox.ZMax-13.55)<1e-7
assert abs(center.BoundBox.ZMax-13.5)<1e-7
assert abs(screen.BoundBox.ZMax-14.2)<1e-7
# Verify SCREW3 revision survives in the rear-cover B-rep.
assert any(isinstance(f.Surface,Part.Cylinder) and abs(f.Surface.Radius-.8)<1e-7 and abs(f.Surface.Center.x-4.)<1e-7 and abs(f.Surface.Center.y-43.5)<1e-7 for f in rear.Faces)
d.recompute();d.saveAs(str(O/'Q2_Appearance_Prototype_V2.FCStd'))
Import.export(objects,str(O/'reference/assembled-appearance.step'))
manifest={'purpose':'appearance-only SLA sample; not functional electronics assembly','units':'mm','scale':'1:1','source':str(SOURCE.relative_to(ROOT)),'source_sha256':before,'parts':records,'pairwise_fit':fit,'SCREW3_case_center_mm':[4.,43.5],'changes':{'wheel_thickness_mm':2.2,'center_thickness_mm':2.2,'screen_total_thickness_mm':2.2,'screen_cap_thickness_mm':.9,'lens_seat_z_mm':13.2,'original_lens_seat_z_mm':13.42,'visible_top_z_mm':{'wheel':13.55,'center':13.5,'screen':14.2}},'limitations':['Minimum overall size passed locally; not factory DFM approval.','Body and rear retain prior local thin features; no global minimum-wall certification.','Temporary tape/adhesive assembly only; switch travel and populated PCB fit are not retained.']}
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert sha(SOURCE)==before
A.closeDocument(d.Name);A.closeDocument(old.Name)
print('APPEARANCE_V2_READY',json.dumps(records,ensure_ascii=False));print('PAIRWISE_FIT',json.dumps(fit))
