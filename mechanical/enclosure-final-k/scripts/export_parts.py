"""Export independent K parts in millimetres, with no sacrificial frames."""
from pathlib import Path
import FreeCAD as A, Part, MeshPart, Import, json
O=Path(__file__).resolve().parents[1]; V=A.Vector
d=A.openDocument(str(O/'Q2_K_Assembly_Access.FCStd'))
P=O/'print-package'; P.mkdir(exist_ok=True)
entries={'01-housing':'HousingControlsA','02-rear-cover':'RearCoverWithPCBPosts',
 '03-wheel':'WheelControlsA','04-center-button':'CenterButtonControlsA',
 '05-motor-carrier':'MotorCarrier','06-insert-fit-coupon-optional':'InsertFitCoupon'}
report=[]
for name,obj in entries.items():
 shape=d.getObject(obj).Shape
 assert shape.isValid() and len(shape.Solids)==1,(name,len(shape.Solids))
 mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.025,AngularDeflection=.15,Relative=False)
 b=mesh.BoundBox; shift=V(-b.XMin,-b.YMin,-b.ZMin)
 s=shape.copy(); s.translate(shift); mesh.translate(*shift)
 s.exportStep(str(P/(name+'.step'))); mesh.write(str(P/(name+'.stl')))
 assert mesh.isSolid(),name
 report.append({'part':name,'object':obj,'dimensions_mm':[b.XLength,b.YLength,b.ZLength],
 'solid_count':len(s.Solids),'mesh_closed':mesh.isSolid(),'mesh_facets':mesh.CountFacets,
 'translation_from_assembly_mm':list(shift)})
objects={o.Name:o for o in d.PrintableParts.Group+d.Electronics.Group+d.AssemblyReferences.Group
 if hasattr(o,'Shape') and not o.Shape.isNull() and o.Name not in ['InsertFitCoupon','LCDActiveArea','LensBlackMask','WheelCopper','ControlSymbols']}
Import.export(list(objects.values()),str(O/'Q2_K_Assembly_Access.step'))
(O/'export-check.json').write_text(json.dumps(report,indent=2))
print('EXPORT_COMPLETE',json.dumps(report),flush=True)
