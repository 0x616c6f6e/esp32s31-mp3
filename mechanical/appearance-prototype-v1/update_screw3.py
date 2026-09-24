"""Refresh the appearance sample and deliverable package after SCREW3 adjustment."""
from pathlib import Path
import json,hashlib,shutil,zipfile
import FreeCAD as A,Part,Import,MeshPart
O=Path(__file__).resolve().parent;ROOT=O.parents[1]
src=ROOT/'mechanical/final-board-review/Q2_Final_Mainboard_Assembly.FCStd'
old=A.openDocument(str(src));d=A.openDocument(str(O/'Q2_Appearance_Prototype_V1.FCStd'))
rear=d.getObject('RearCoverWithPCBPosts');rear.Shape=old.getObject('RearCoverWithPCBPosts').Shape.copy()
rear.Label='后盖 / SCREW3 固定柱向板内移 0.5 mm'
d.recompute();assert rear.Shape.isValid() and len(rear.Shape.Solids)==1
bb=rear.Shape.BoundBox;local=rear.Shape.copy();local.translate(A.Vector(-bb.XMin,-bb.YMin,-bb.ZMin))
mesh=MeshPart.meshFromShape(Shape=local,LinearDeflection=.03,AngularDeflection=.15,Relative=False)
assert mesh.isSolid();mesh.write(str(O/'print-parts/02-rear-cover.stl'))
local.exportStep(str(O/'reference/02-rear-cover.step'))
m=json.loads((O/'manifest.json').read_text(encoding='utf8'))
for r in m['parts']:
 if r['source_object']=='RearCoverWithPCBPosts':
  r.update(triangles=mesh.CountFacets,closed_mesh=True,shape_valid=True,
           mesh_dimensions_mm=[round(mesh.BoundBox.XLength,4),round(mesh.BoundBox.YLength,4),round(mesh.BoundBox.ZLength,4)])
Import.export([d.getObject(r['source_object']) for r in m['parts']],str(O/'reference/assembled-appearance.step'))
d.save();A.closeDocument(d.Name);A.closeDocument(old.Name)
m['source_sha256']=hashlib.sha256(src.read_bytes()).hexdigest()
m['revision_note']='2026-09-22: SCREW3 support and pilot moved 0.5 mm inward (-X in KiCad, +X in case). PCB unchanged.'
(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
note=O/'加工说明.txt';text=note.read_text(encoding='utf8')
text=text.replace('本次保持当前造型，不调整内部结构。','保持当前外观造型；SCREW3 对应固定柱和孔已向板内移 0.5 mm。')
note.write_text(text,encoding='utf8')
package=ROOT/'mechanical/Q2-appearance-prototype-v1'
files=['Q2_Appearance_Prototype_V1.FCStd','manifest.json','加工说明.txt']
files += [str(p.relative_to(O)) for sub in ['print-parts','reference'] for p in (O/sub).iterdir() if p.is_file()]
for f in files:
 dest=package/f;dest.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(O/f,dest)
with zipfile.ZipFile(ROOT/'mechanical/Q2-appearance-prototype-v1.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in files:z.write(package/f,str(Path(f)).replace('\\','/'))
with zipfile.ZipFile(ROOT/'mechanical/Q2-appearance-prototype-v1.zip') as z:
 assert z.testzip() is None
 assert z.read('print-parts/02-rear-cover.stl')==(O/'print-parts/02-rear-cover.stl').read_bytes()
print('APPEARANCE_SCREW3_REFRESH_OK',len(files),'files; closed rear mesh',mesh.CountFacets)
