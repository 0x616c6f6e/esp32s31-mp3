import FreeCAD as A,Part
from pathlib import Path
p=Path('mechanical/enclosure-final-g/Q2_G_Thin_Assembly.FCStd');d=A.openDocument(str(p));s=d.HousingControlsA.Shape
for x,y in [(6,51),(44,51),(6,67),(44,67)]:
 print('mount',x,y)
 for z in [11.85,11.95,12.2,12.6,12.9,13.1,13.3,13.45]:
  print(z,[s.isInside(A.Vector(x+dx,y,z),1e-6,True) for dx in [0,.7,1,1.8,2.2,2.8]])
