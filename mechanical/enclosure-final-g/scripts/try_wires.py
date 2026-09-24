import FreeCAD as A,Part
from pathlib import Path
O=Path('mechanical/enclosure-final-g');d=A.openDocument(str(O/'Q2_G_Thin_Assembly.FCStd'));V=A.Vector
for y in [55.8,56.4,56.0,56.6,59.9,60.5]:
 s=Part.makeCylinder(.225,32.09,V(1.61,y,7.1),V(1,0,0));bad=[]
 for o in d.Electronics.Group:
  b=o.Shape.BoundBox
  if b.YMin<y+.225 and b.YMax>y-.225 and b.ZMax>6.875 and b.ZMin<7.325:
   v=s.common(o.Shape).Volume
   if v>1e-5:bad.append((o.Name,v))
 print(y,bad,flush=True)
