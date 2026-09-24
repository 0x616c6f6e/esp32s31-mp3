from pathlib import Path
import FreeCAD as A,Part
O=Path('mechanical/enclosure-final-h');d=A.openDocument(str(O/'Q2_H_Reinforced_Assembly.FCStd'))
for n in ['ControlFFC40mm','DisplayFPCRoute','ControlBoardFasteners','MotorWire1']:
 s=d.getObject(n).Shape;print(n,'volumes',[round(q.Volume,5) for q in s.Solids])
 if n=='ControlFFC40mm':
  for i,q in enumerate(s.Solids):
   for j,b in enumerate(d.ControlBoardFasteners.Shape.Solids):
    c=q.common(b)
    if c.Volume>1e-5:print('hit',i,j,c.Volume,c.BoundBox,'part',q.BoundBox)
  u=s.Solids[0].multiFuse(s.Solids[1:]).removeSplitter();print('united',u.Volume,u.isValid(),len(u.Solids),'fastener',u.common(d.ControlBoardFasteners.Shape).Volume)
