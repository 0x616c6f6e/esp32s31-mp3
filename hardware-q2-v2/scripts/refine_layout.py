"""Resolve new-part placement clashes while preserving V1 mechanical anchors."""
from pathlib import Path
import pcbnew as p,json,sys,math,re
P=Path(__file__).resolve().parents[1];ROOT=P.parent
sys.path.insert(0,str(ROOT/'tmp/v2-kicad-deps'))
from shapely.geometry import box,Polygon
from shapely import affinity
fn=P/'q2-v2.kicad_pcb';pro=(P/'q2-v2.kicad_pro').read_bytes();b=p.LoadBoard(str(fn));origin=(128.868,67.647)
fs={f.GetReference():f for f in b.GetFootprints()}
outline=Polygon(json.loads((ROOT/'hardware-q2-v2-plan/outline.json').read_text())[0]).buffer(-.35)
def rect(f):
 q=f.GetBoundingBox(False,False);return box(p.ToMM(q.GetX())-origin[0],p.ToMM(q.GetY())-origin[1],p.ToMM(q.GetRight())-origin[0],p.ToMM(q.GetBottom())-origin[1])
def xy(f):return (p.ToMM(f.GetPosition().x)-origin[0],p.ToMM(f.GetPosition().y)-origin[1])
def move(f,x,y):f.SetPosition(p.VECTOR2I(p.FromMM(origin[0]+x),p.FromMM(origin[1]+y)))
# Imported fab/silk may extend far; place against physical pads and courtyard.
def physical(f):
 pts=[]
 for pad in f.Pads():
  if not pad.GetNumber():continue
  bb=pad.GetBoundingBox();pts.append(box(p.ToMM(bb.GetX())-origin[0],p.ToMM(bb.GetY())-origin[1],p.ToMM(bb.GetRight())-origin[0],p.ToMM(bb.GetBottom())-origin[1]))
 from shapely.ops import unary_union
 shape=unary_union(pts).convex_hull if pts else rect(f)
 f.BuildCourtyardCaches()
 courtyard=f.GetCourtyard(f.GetLayer())
 if courtyard and courtyard.OutlineCount():
  line=courtyard.COutline(0);poly=Polygon([(p.ToMM(line.CPoint(i).x)-origin[0],p.ToMM(line.CPoint(i).y)-origin[1]) for i in range(line.PointCount())]);shape=shape.union(poly)
 return shape.buffer(.12)
newrefs={r for r in fs if re.match(r'^[RCQLY]|^TP',r) and re.search(r'\d+',r) and int(re.search(r'\d+',r)[0])>=100}|{'U20','U21','JRF1'}
# Core passives retain manufacturer local arrangement unless a new connector overlaps.
core={r for r in newrefs if r.startswith(('C10','C11','C12','L10','R10','R110','Y101')) and not r.startswith('R12')}
core.discard('C130');core.discard('C131')
movable=newrefs-core
occupied={r:(physical(f),f.GetLayer()) for r,f in fs.items() if r not in movable}
changes=[]
for ref in sorted(movable,key=lambda r:-physical(fs[r]).area):
 f=fs[ref];shape=physical(f);ox,oy=xy(f);side=f.GetLayer();obstacles=[v[0] for r,v in occupied.items() if v[1]==side]
 if side==p.B_Cu:obstacles+=[box(0,46,18,53.5)]
 def valid(poly):return outline.contains(poly) and all(not poly.intersects(o) for o in obstacles)
 if valid(shape):occupied[ref]=(shape,side);continue
 candidates=[]
 for dx in range(-30,31):
  for dy in range(-30,31):
   distance=dx*dx+dy*dy
   if distance:candidates.append((distance,dx*.5,dy*.5))
 for dist,dx,dy in sorted(candidates):
  cand=affinity.translate(shape,dx,dy)
  # New support parts stay above audio/USB/motor region where practicable.
  if valid(cand):
   move(f,ox+dx,oy+dy);occupied[ref]=(cand,side);changes.append({'ref':ref,'before':[ox,oy],'after':[ox+dx,oy+dy]});break
 else:raise RuntimeError('No collision-free position '+ref)
# Imported mounting holes have zero annulus and are mechanical NPTH.
for ref in ['SCREW1','SCREW2','SCREW3','SCREW5']:
 for a in fs[ref].Pads():a.SetAttribute(p.PAD_ATTRIB_NPTH);a.SetNetCode(0)
# Imported decorative outlines are assembly marks. Generate production silk later.
for f in fs.values():
 for g in f.GraphicalItems():
  if g.GetLayer() in [p.F_SilkS,p.B_SilkS]:g.SetLayer(p.B_Fab if f.IsFlipped() else p.F_Fab)
p.SaveBoard(str(fn),b);(P/'q2-v2.kicad_pro').write_bytes(pro)
(P/'output/placement-refinements.json').write_text(json.dumps(changes,indent=2))
print('Resolved positions:',len(changes))

