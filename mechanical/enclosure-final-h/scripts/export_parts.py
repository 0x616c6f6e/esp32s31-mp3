"""Millimetre sample exports; sacrificial handling frames are not assembly parts."""
from pathlib import Path
import FreeCAD as A,Part,MeshPart,json,hashlib
O=Path(__file__).resolve().parents[1];V=A.Vector
d=A.openDocument(str(O/'Q2_H_Reinforced_Assembly.FCStd'))
P=O/'print-package';P.mkdir(exist_ok=True)
C=O/'clean-parts';C.mkdir(exist_ok=True)
def box(x,y,z,w,l,h):return Part.makeBox(w,l,h,V(x,y,z))
def frame(part,size,edge_x):
 x,y=25-size/2,59.3-size/2
 f=box(x,y,11.5,size,size,2.6).cut(box(x+2,y+2,11.4,size-4,size-4,2.8))
 # Two detachable tabs meet the flange, away from the four switch plungers.
 for sign in [-1,1]:
  start,end=sorted([25+sign*edge_x,25+sign*(size/2-1.8)])
  f=f.fuse(box(start,58.9,12.4,end-start,.8,.3))
 return part.fuse(f).removeSplitter()
entries=[('01-housing',d.HousingControlsA.Shape),('02-rear-cover',d.RearCoverWithPCBPosts.Shape),('03-wheel-with-carrier',frame(d.WheelControlsA.Shape,42,16.9)),('04-center-with-carrier',frame(d.CenterButtonControlsA.Shape,20,6.6))]
report=[]
for name,shape in entries:
 assert shape.isValid() and len(shape.Solids)==1,(name,len(shape.Solids))
 # Mesh extrema avoid conservative B-spline bounding boxes.
 mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.025,AngularDeflection=.15,Relative=False)
 b=mesh.BoundBox;shift=V(-b.XMin,-b.YMin,-b.ZMin)
 s=shape.copy();s.translate(shift);mesh.translate(*shift)
 s.exportStep(str(P/(name+'.step')));mesh.write(str(P/(name+'.stl')))
 assert mesh.isSolid(),name
 report.append({'part':name,'dimensions_mm':[b.XLength,b.YLength,b.ZLength],'solid_count':len(s.Solids),'mesh_closed':mesh.isSolid(),'mesh_facets':mesh.CountFacets,'translation_from_assembly_mm':list(shift)})
for n,o in [('03-wheel',d.WheelControlsA),('04-center-button',d.CenterButtonControlsA)]:o.Shape.exportStep(str(C/(n+'.step')))
physical=list(d.PrintableParts.Group)+list(d.Electronics.Group)+list(d.AssemblyReferences.Group)
ImportObjects=[o for o in physical if hasattr(o,'Shape') and not o.Shape.isNull()]
import Import
Import.export(ImportObjects,str(O/'Q2_H_Reinforced_Assembly.step'))
(O/'export-check.json').write_text(json.dumps(report,indent=2))
print('EXPORT_COMPLETE',json.dumps(report),flush=True)
