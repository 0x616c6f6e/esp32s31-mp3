from pathlib import Path
import FreeCAD as A,Part,json
O=Path(__file__).resolve().parents[1];d=A.openDocument(str(O/'Q2_I_Serviceable_Assembly.FCStd'))
targets=[d.HousingControlsA,d.WheelControlsA,d.CenterButtonControlsA,d.ControlEdgePad]
parts=[d.ControlsBoard]+[o for o in d.Electronics.Group if o.Name.startswith('CTRL_')]
results=[]
for x in [-1.2,-.9,-.6,-.3,0]:
 hits=[]
 for o in parts:
  s=o.Shape.copy();s.translate(A.Vector(x,0,0))
  for t in targets:
   if not s.BoundBox.intersect(t.Shape.BoundBox):continue
   v=sum(max(0,a.common(b).Volume) for a in s.Solids for b in t.Shape.Solids if a.BoundBox.intersect(b.BoundBox))
   if v>1e-5:hits.append([o.Name,t.Name,round(v,6)])
 results.append({'pcb_x_offset_mm':x,'collisions':hits})
 print('INSERTION',x,hits,flush=True)
(O/'insertion-check.json').write_text(json.dumps({'method':'sampled lateral insertion without mainboard, wires, screws or FFC; no continuous swept-volume or compliance simulation','samples':results},indent=2))
