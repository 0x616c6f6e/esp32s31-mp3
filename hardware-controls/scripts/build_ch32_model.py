"""Nominal QFN20 model; package dimensions from WCH CH32V006 datasheet."""
from pathlib import Path
import FreeCAD as A, Part
P=Path(__file__).resolve().parents[1]
out=P/'output/ch32v006-review/candidate/models3d/CH32V006_QFN20.step'
V=A.Vector
box=lambda x,y,z,w,h,d:Part.makeBox(w,h,d,V(x,y,z))
shapes=[box(-1.5,-1.5,.025,3,3,.725),box(-.95,-.95,0,1.9,1.9,.025)]
for i in range(5):
    a=-.8+.4*i
    shapes.extend([box(-1.5,a-.1,0,.25,.2,.05),box(1.25,a-.1,0,.25,.2,.05),box(a-.1,-1.5,0,.2,.25,.05),box(a-.1,1.25,0,.2,.25,.05)])
shape=Part.makeCompound(shapes)
assert shape.isValid()
shape.exportStep(str(out))
print('Nominal QFN20: 3 x 3 x 0.75 mm;',out)
