"""Nominal HC-FPC-05-10-12RLTAG body, per HCTL drawing in reference/.
Slot elevation is an assembly assumption, not a dimension on the drawing.
Local model axes: footprint X, negative footprint Y, Z above PCB.
"""
from pathlib import Path
import FreeCAD as A, Part, Import
P=Path(__file__).resolve().parents[1];V=A.Vector
doc=A.newDocument('HCTL12')
body=Part.makeBox(7.77,3.35,1,V(-3.885,-2.18,0))
slot=Part.makeBox(6.6,2.35,.32,V(-3.3,-2.181,.24))
body=body.cut(slot)
shapes=[('Housing',body,(.82,.8,.72))]
shapes.append(('Latch',Part.makeBox(7.4,.55,.22,V(-3.7,-2.18,.78)),(.12,.12,.13)))
for i in range(12):
 x=2.75-i*.5
 shapes.append(('Pin'+str(i+1),Part.makeBox(.3,.65,.08,V(x-.15,1.08,0)),(.75,.65,.3)))
for x in [-3.635,3.635]:shapes.append(('Mount',Part.makeBox(.3,1.15,.1,V(x-.15,-1.98,0)),(.7,.7,.7)))
objs=[]
for name,shape,color in shapes:
 shape.rotate(V(),V(0,0,1),180)
 o=doc.addObject('PartDesign::Feature',name);o.Shape=shape;objs.append(o)
 if o.ViewObject:o.ViewObject.ShapeColor=color
doc.recompute();Import.export(objs,str(P/'models3d/HCTL_FPC12.step'))
print('HCTL_MODEL_EXPORTED');A.closeDocument(doc.Name)
