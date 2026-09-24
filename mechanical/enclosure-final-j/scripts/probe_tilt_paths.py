from pathlib import Path
import FreeCAD as A,Part,json
O=Path(__file__).resolve().parents[1];V=A.Vector
d=A.openDocument(str(O/'Q2_J_Glue_Insert_Assembly.FCStd'))
def hits(parts,targets,angle,pivot,offset):
 out=[]
 for a in parts:
  s=a.Shape.copy();s.rotate(V(*pivot),V(0,1,0),-angle);s.translate(V(*offset))
  for b in targets:
   if not s.BoundBox.intersect(b.Shape.BoundBox):continue
   v=sum(max(0,p.common(q).Volume) for p in s.Solids for q in b.Shape.Solids if p.BoundBox.intersect(q.BoundBox))
   if v>1e-5:out.append([a.Name,b.Name,round(v,5)])
 return out
res={}
for kind,pivot,base,parts,targets in [
 ('wheel',[42.35,59.3,12.35],[0,-3,-1.1],[d.WheelControlsA],[d.HousingControlsA]),
 ('controls',[47,59.3,11.1],[-1.3,-3.5,-.4],[d.ControlsBoard]+[o for o in d.Electronics.Group if o.Name.startswith('CTRL_')],[d.HousingControlsA,d.WheelControlsA,d.CenterButtonControlsA])]:
 poses=[(50,[base[0],base[1],z]) for z in [-20,-15,-10,-5,base[2]]]
 poses +=[(angle,base) for angle in [40,30,20,10,5,0]]
 poses +=[(0,[base[0],y,base[2]]) for y in [-2,-1,0]]
 poses +=[(0,[base[0],0,z]) for z in [base[2]/2,0]]
 poses +=[(0,[x,0,0]) for x in [-.9,-.6,-.3,0]] if kind=='controls' else []
 rows=[]
 for angle,offset in poses:
  h=hits(parts,targets,angle,pivot,offset)
  rows.append({'angle_y_degrees':-angle,'offset_mm':offset,'hits':h})
  print(kind,angle,offset,h,flush=True)
 res[kind]={'pivot_mm':pivot,'samples':rows}
(O/'preflight-tilt-probe.json').write_text(json.dumps(res,indent=2))
