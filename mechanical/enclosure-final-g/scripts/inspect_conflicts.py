import FreeCAD as A,Part
from pathlib import Path
O=Path('mechanical/enclosure-final-g');d=A.openDocument(str(O/'Q2_G_Thin_Assembly.FCStd'))
for n in ['PCB_L2','ControlBoardFasteners','ControlFFC40mm','MotorWire1','HousingControlsA']:
 s=d.getObject(n).Shape;print(n,s.BoundBox,'solids',len(s.Solids),'volume',s.Volume)
for a,b in [('PCB_L2','MotorWire1'),('HousingControlsA','MotorWire1'),('ControlFFC40mm','ControlBoardFasteners')]:
 s=d.getObject(a).Shape.common(d.getObject(b).Shape);print('COMMON',a,b,s.Volume,s.BoundBox)
 if a=='ControlFFC40mm':
  for i,c in enumerate(d.getObject(b).Shape.Solids):
   print('screw',i,c.BoundBox,c.Volume,'common',c.common(d.getObject(a).Shape).Volume)
