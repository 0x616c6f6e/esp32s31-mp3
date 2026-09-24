"""Export an appearance-only sample from the reviewed assembly, unchanged geometry."""
from pathlib import Path
import FreeCAD as A,Part,Import,MeshPart,json,hashlib
O=Path(__file__).resolve().parent;ROOT=O.parents[1]
src=ROOT/'mechanical/final-board-review/Q2_Final_Mainboard_Assembly.FCStd'
before=hashlib.sha256(src.read_bytes()).hexdigest()
old=A.openDocument(str(src));d=A.newDocument('Q2AppearanceV1');d.Label='Q2 appearance sample V1'
for sub in ['print-parts','reference']:(O/sub).mkdir(exist_ok=True)
spec=[('01-body','HousingControlsA','机身',(.74,.77,.80)),
 ('02-rear-cover','RearCoverWithPCBPosts','后盖',(.67,.70,.73)),
 ('03-wheel','WheelControlsA','圆环',(.045,.05,.057)),
 ('04-center-button','CenterButtonControlsA','中心键',(.77,.79,.82)),
 ('05-screen-dummy','CoverLens','屏幕外观占位片',(.025,.032,.042))]
records=[];objects=[]
for name,source,label,color in spec:
 sh=old.getObject(source).Shape.copy();assert sh.isValid() and len(sh.Solids)==1,source
 o=d.addObject('PartDesign::Feature',source);o.Label=label;o.Shape=sh;objects.append(o)
 if o.ViewObject:o.ViewObject.ShapeColor=color
 bb=sh.BoundBox;local=sh.copy();local.translate(A.Vector(-bb.XMin,-bb.YMin,-bb.ZMin))
 mesh=MeshPart.meshFromShape(Shape=local,LinearDeflection=.03,AngularDeflection=.15,Relative=False)
 assert mesh.isSolid(),name
 mesh.write(str(O/'print-parts'/(name+'.stl')))
 local.exportStep(str(O/'reference'/(name+'.step')))
 records.append({'file':name+'.stl','label':label,'quantity':1,'shape_conservative_bbox_mm':[round(bb.XLength,4),round(bb.YLength,4),round(bb.ZLength,4)],'mesh_dimensions_mm':[round(mesh.BoundBox.XLength,4),round(mesh.BoundBox.YLength,4),round(mesh.BoundBox.ZLength,4)],'source_object':source,'original_min_xyz_mm':[bb.XMin,bb.YMin,bb.ZMin],'closed_mesh':True,'shape_valid':True,'color':color,'triangles':mesh.CountFacets})
d.recompute();d.saveAs(str(O/'Q2_Appearance_Prototype_V1.FCStd'))
Import.export(objects,str(O/'reference/assembled-appearance.step'))
assert hashlib.sha256(src.read_bytes()).hexdigest()==before
(O/'manifest.json').write_text(json.dumps({'purpose':'appearance sample only','units':'mm','scale':'1:1','source':str(src.relative_to(ROOT)),'source_sha256':before,'parts':records},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('APPEARANCE_SAMPLE_READY',json.dumps(records,ensure_ascii=False))
