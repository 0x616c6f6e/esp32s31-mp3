"""Apply the reproducible SCREW3 support adjustment and refresh its exports."""
from pathlib import Path
import sys,json,hashlib,math
import FreeCAD as A,Part,Import,MeshPart
ROOT=Path(__file__).resolve().parents[3];O=ROOT/'mechanical/final-board-review'
sys.path.insert(0,str(O/'scripts'))
from mounting_adjustment import apply
source=ROOT/'mechanical/enclosure-q2-f/ESP32S31_MP3_Q2_F.FCStd'
pcb=ROOT/'hardware-q2/ProPrj_esp32s31-mp4_2026-09-22.kicad_pcb'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in [source,pcb,ROOT/'esp32s31-mp3_gerber.zip']}
s=A.openDocument(str(source));adjustment=apply(s)
d=A.openDocument(str(O/'Q2_Final_Mainboard_Assembly.FCStd'))
rear=d.getObject('RearCoverWithPCBPosts');old=rear.Shape.copy()
d.getObject('RearCoverSourceF').Shape=s.getObject('RearCoverWithPCBPosts').Shape.copy()
rear.Label='Rear cover / SCREW3 support moved 0.5 mm inward'
if 'SCREW3CaseX' not in rear.PropertiesList:rear.addProperty('App::PropertyLength','SCREW3CaseX','Mounting')
rear.SCREW3CaseX=4.0
if 'SCREW3Change' not in rear.PropertiesList:rear.addProperty('App::PropertyString','SCREW3Change','Mounting')
rear.SCREW3Change='Support and pilot shifted +0.5 mm case X = -0.5 mm KiCad X; PCB unchanged.'
d.recompute();shape=rear.Shape
assert shape.isValid() and len(shape.Solids)==1
changed=old.cut(shape).fuse(shape.cut(old))
local=Part.makeBox(5.4,4.4,4.5,A.Vector(1.2,41.3,0))
assert changed.cut(local).Volume<1e-7,'Unexpected change outside SCREW3 region'
# Verify the pilot cylinder's actual B-rep axis, not only the parameter.
axes=[]
for face in shape.Faces:
 surface=face.Surface
 if isinstance(surface,Part.Cylinder) and abs(surface.Radius-.8)<1e-7:
  c=surface.Center
  if abs(c.y-43.5)<.002:axes.append([c.x,c.y])
assert axes and all(abs(a[0]-4.0)<1e-7 for a in axes),axes
mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.03,AngularDeflection=.15,Relative=False)
assert mesh.isSolid()
Import.export([rear],str(O/'RearCoverWithPCBPosts.step'));mesh.write(str(O/'RearCoverWithPCBPosts.stl'))
d.recompute();d.save()
report=json.loads((O/'fit-check.json').read_text())
report['mounting_adjustment']=adjustment
posts=report['mounting_review']['existing_posts']
for p in posts:
 if p['name']=='MainPCBPostOuter2':p['center_case_mm']=[4.,43.5]
for h in report['mounting_review']['actual_mainboard_holes']:
 p=min(posts,key=lambda p:math.dist(h['case_xy_mm'],p['center_case_mm']))
 h['nearest_old_post']=p['name'];h['center_offset_mm']=round(math.dist(h['case_xy_mm'],p['center_case_mm']),4)
report['mounting_review']['all_aligned']=False;report['mainboard_mounting_posts_match_new_hole_pattern']=False
report['review_conclusion']='FAIL: SCREW3 support moved +0.5 mm in case X, PCB hole unchanged. Previously recorded motor/jack and C13/display-flex conflicts remain.'
report['scope_note']='Mechanical-only SCREW3 revision. Other geometry unchanged; prior full review retained, not rerun.'
report['pass']=False
(O/'fit-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
adjustment.update(shape_valid=True,solid_count=len(shape.Solids),mesh_closed=mesh.isSolid(),verified_pilot_axes=axes,localized_change_check=True)
(O/'screw3-shift-check.json').write_text(json.dumps(adjustment,indent=2)+'\n')
A.closeDocument(d.Name);A.closeDocument(s.Name)
assert before=={p:sha(Path(p)) for p in before}
print('SCREW3_SHIFT_OK',json.dumps(adjustment))
