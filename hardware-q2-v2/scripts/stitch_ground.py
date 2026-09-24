from pathlib import Path
import pcbnew as p,json,sys,math
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'tmp/v2-kicad-deps'))
import shapely,numpy as np
from shapely.geometry import Point,Polygon,LineString
from shapely.ops import unary_union
b=p.LoadBoard(str(P/'q2-v2.kicad_pcb'));pro=(P/'q2-v2.kicad_pro').read_bytes();xy=lambda v:(p.ToMM(v.x),p.ToMM(v.y));obs=[];holes=[];gpoints=[]
def polygon(ps,i):
 def pts(line):return [xy(line.CPoint(k)) for k in range(line.PointCount())]
 return Polygon(pts(ps.COutline(i)),[pts(ps.CHole(i,j)) for j in range(ps.HoleCount(i))]).buffer(0)
for f in b.GetFootprints():
 for a in f.Pads():
  if a.GetNetname()!='GND':
   ps=a.GetEffectivePolygon(a.GetLayer());obs += [polygon(ps,i) for i in range(ps.OutlineCount())]
   if a.GetDrillSize().x:holes.append(Point(xy(a.GetPosition())).buffer(max(xy(a.GetDrillSize()))/2+.3))
  elif a.GetDrillSize().x:gpoints.append(xy(a.GetPosition()))
 for z in f.Zones():
  if z.GetIsRuleArea() and z.GetDoNotAllowVias():
   ps=z.Outline();obs += [polygon(ps,i) for i in range(ps.OutlineCount())]
for t in b.GetTracks():
 if t.GetNetname()=='GND':
  if isinstance(t,p.PCB_VIA):gpoints.append(xy(t.GetPosition()))
  continue
 if isinstance(t,p.PCB_VIA):obs.append(Point(xy(t.GetPosition())).buffer(p.ToMM(t.GetWidth(p.F_Cu))/2))
 else:obs.append(LineString([xy(t.GetStart()),xy(t.GetEnd())]).buffer(p.ToMM(t.GetWidth())/2))
ob=unary_union(obs);hole=unary_union(holes);added=[];fail=[];zones=[z for z in b.Zones() if z.GetLayer() in [p.F_Cu,p.B_Cu] and z.GetNetname()=='GND']
for z in zones:
 ps=z.GetFilledPolysList(z.GetLayer())
 for i in range(ps.OutlineCount()):
  poly=polygon(ps,i)
  if poly.is_empty or any(poly.buffer(.005).contains(Point(q)) for q in gpoints):continue
  a,c,x,y=poly.bounds;xs=np.arange(a,x+.05,.05);ys=np.arange(c,y+.05,.05);xx,yy=np.meshgrid(xs,ys);inside=shapely.contains_xy(poly.buffer(-.02),xx,yy);found=False
  for diameter,drill in [(.45,.2),(.35,.15)]:
   blocked=ob.buffer(diameter/2+.105).union(hole.buffer(diameter/2));legal=inside & ~shapely.intersects_xy(blocked,xx,yy);pts=np.argwhere(legal)
   if not len(pts):continue
   # Prefer the interior of the island and an even distribution of ground returns.
   rep=poly.representative_point();ix=min(range(len(pts)),key=lambda k:(xs[pts[k,1]]-rep.x)**2+(ys[pts[k,0]]-rep.y)**2);iy,ix=pts[ix];pos=(float(xs[ix]),float(ys[iy]))
   via=p.PCB_VIA(b);via.SetPosition(p.VECTOR2I(p.FromMM(pos[0]),p.FromMM(pos[1])));via.SetWidth(p.FromMM(diameter));via.SetDrill(p.FromMM(drill));via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(b.FindNet('GND'));b.Add(via);gpoints.append(pos);added.append({'xy':pos,'diameter':diameter,'drill':drill,'layer':z.GetLayer()});found=True;break
  if not found:fail.append({'layer':z.GetLayer(),'area_mm2':poly.area,'bounds':poly.bounds})
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(P/'q2-v2.kicad_pcb'),b);(P/'q2-v2.kicad_pro').write_bytes(pro)
(P/'output/ground-stitching.json').write_text(json.dumps({'added':added,'failed':fail},indent=2));print('ADDED',len(added),'FAILED',len(fail),fail,flush=True)
