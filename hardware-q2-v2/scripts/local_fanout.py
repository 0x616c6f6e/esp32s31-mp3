"""Add short clearance-checked fanouts and GND stitching at remaining native airwires."""
from pathlib import Path
import pcbnew as p,json,sys,math,collections,heapq
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'tmp/v2-kicad-deps'))
from shapely.geometry import Polygon,Point,LineString
from shapely.ops import unary_union
from shapely import affinity
import shapely,numpy as np
b=p.LoadBoard(str(P/'q2-v2.kicad_pcb'));fn=P/'q2-v2.kicad_pro';pro=json.loads(fn.read_text(encoding='utf8'))
pro['board']['design_settings']['rules'].update(min_via_diameter=.35,min_through_hole_diameter=.15)
xy=lambda v:(p.ToMM(v.x),p.ToMM(v.y));V=lambda z:p.VECTOR2I(p.FromMM(float(z[0])),p.FromMM(float(z[1])));layers=[p.F_Cu,p.In2_Cu,p.In3_Cu,p.B_Cu]
polys=collections.defaultdict(lambda:collections.defaultdict(list));holes=[];pads={}
def polyset(ps):
 for i in range(ps.OutlineCount()):
  line=ps.COutline(i);poly=Polygon([xy(line.CPoint(k)) for k in range(line.PointCount())]);yield poly.buffer(0)
for f in b.GetFootprints():
 for a in f.Pads():
  pads[a.m_Uuid.AsString()]=(f,a)
  for l in layers:
   if a.IsOnLayer(l):polys[l][a.GetNetname()]+=list(polyset(a.GetEffectivePolygon(l)))
  if a.GetDrillSize().x:
   holes.append((a.GetNetname(),Point(xy(a.GetPosition())).buffer(max(xy(a.GetDrillSize()))/2+.3)))
for a in b.GetTracks():
 for l in layers:
  if not a.IsOnLayer(l):continue
  if isinstance(a,p.PCB_VIA):sh=Point(xy(a.GetPosition())).buffer(p.ToMM(a.GetWidth(l))/2)
  else:sh=LineString([xy(a.GetStart()),xy(a.GetEnd())]).buffer(p.ToMM(a.GetWidth())/2)
  polys[l][a.GetNetname()].append(sh)
outline=affinity.translate(Polygon(json.loads((P.parent/'hardware-q2-v2-plan/outline.json').read_text())[0]),128.868,67.647)
targets={}
if 'failed' in sys.argv:
 old=json.loads((P/'output/local-fanout.json').read_text())
 keys={(a['ref'],a['pin']) for a in old['failed']}
 targets={uid:(f,a) for uid,(f,a) in pads.items() if (f.GetReference(),a.GetNumber()) in keys}
elif 'all-core' in sys.argv:
 for uid,(f,a) in pads.items():
  if f.GetReference()=='U9' and a.GetNetname() and a.GetNetname()!='GND' and not a.GetNetname().startswith(('RF_','XTAL_','MCU_XTAL','MCU_USB_HS')):targets[uid]=(f,a)
else:
 drc=json.loads((P/'output/fullroute-drc.json').read_text(encoding='utf8'))
 for item in drc['unconnected_items']:
  for it in item['items']:
   if it['uuid'] in pads:
    f,a=pads[it['uuid']];targets[it['uuid']]=(f,a)
cache={};added=[];failed=[]
for uid,(f,a) in sorted(targets.items(),key=lambda q:(q[1][0].GetReference()!='U9',q[1][1].GetNetname()!='GND')):
 n=a.GetNetname();layer=f.GetLayer();start=xy(a.GetPosition());w=.1 if f.GetReference()=='U9' or n=='GND' else .15;diam=.35
 if n not in cache:
  obs={l:unary_union([z for net,ss in polys[l].items() if net!=n for z in ss]) for l in layers}
  hole=unary_union([s for net,s in holes if net!=n]);cache[n]=(obs,hole)
 obs,hole=cache[n]
 others=[e for e in added if e['net']!=n]
 viaob=unary_union([s for s in obs.values()]+[Point(e['xy']).buffer(diam/2) for e in others]+[LineString(e['path']).buffer(e['width']/2) for e in others]).buffer(diam/2+.105).union(hole.buffer(.075))
 # Drill clearance applies even to holes of the same electrical net.
 sameholes=[Point(xy(t.GetPosition())).buffer(p.ToMM(t.GetDrillValue())/2+.075+.201) for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname()==n]
 viaob=viaob.union(unary_union(sameholes))
 traceob=obs[layer].buffer(w/2+.105).union(hole.buffer(w/2))
 for e in others:
  traceob=traceob.union(Point(e['xy']).buffer(diam/2+w/2+.105))
  if e['layer']==layer:traceob=traceob.union(LineString(e['path']).buffer((e['width']+w)/2+.105))
 candidates=[]
 if f.GetReference()=='U9':
  cx,cy=xy(f.GetPosition());dx,dy=start[0]-cx,start[1]-cy
  outward=(math.copysign(1,dx),0) if abs(dx)>abs(dy) else (0,math.copysign(1,dy));tangent=(-outward[1],outward[0])
  for r in [.35,.45,.55,.7,.9,1.2,1.5,2,2.5,3,4]:
   for off in [0,.175,-.175,.35,-.35,.7,-.7,1.05,-1.05,1.4,-1.4]:
    if r<abs(off)+.25:continue
    z=(start[0]+outward[0]*r+tangent[0]*off,start[1]+outward[1]*r+tangent[1]*off)
    m=(start[0]+outward[0]*(r-abs(off)),start[1]+outward[1]*(r-abs(off)))
    candidates.append((r+abs(off),z,[start,m,z]))
 else:
  for r in [.4,.5,.65,.8,1,1.25,1.5,2,2.5]:
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
    z=(start[0]+dx*r,start[1]+dy*r);candidates.append((math.dist(start,z),z,[start,z]))
 valid=[]
 for _,z,path in sorted(candidates):
  if not outline.buffer(-.25-diam/2).contains(Point(z)) or viaob.intersects(Point(z)) or traceob.intersects(LineString(path)):continue
  valid.append((z,path));break
 if not valid and 'failed' in sys.argv:
  step=.025;N=160;vals=np.arange(-N,N+1)*step;xx,yy=np.meshgrid(vals+start[0],vals+start[1]);blocked=shapely.intersects_xy(traceob,xx,yy);goal=~shapely.intersects_xy(viaob,xx,yy);goal &= shapely.contains_xy(outline.buffer(-.25-diam/2),xx,yy)
  goal &= (xx-start[0])**2+(yy-start[1])**2 > .15**2
  heap=[(0,N,N)];dist={(N,N):0};prev={};end=None
  while heap:
   cost,x,y=heapq.heappop(heap)
   if cost>dist.get((x,y),1e9):continue
   if goal[y,x]:end=(x,y);break
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
    X,Y=x+dx,y+dy
    if not(0<=X<2*N+1 and 0<=Y<2*N+1) or blocked[Y,X]:continue
    if dx and dy and (blocked[y,X] or blocked[Y,x]):continue
    cc=cost+math.hypot(dx,dy)
    if cc<dist.get((X,Y),1e9):dist[X,Y]=cc;prev[X,Y]=(x,y);heapq.heappush(heap,(cc,X,Y))
  if end:
   nodes=[end]
   while nodes[-1]!=(N,N):nodes.append(prev[nodes[-1]])
   nodes.reverse();keep=[nodes[0]]
   for i in range(1,len(nodes)-1):
    aa,bb,cc=nodes[i-1:i+2]
    if (bb[0]-aa[0],bb[1]-aa[1])!=(cc[0]-bb[0],cc[1]-bb[1]):keep.append(bb)
   keep.append(nodes[-1]);path=[(start[0]+vals[x],start[1]+vals[y]) for x,y in keep];z=path[-1]
   if not traceob.intersects(LineString(path)):valid.append((z,path))
 for z,path in valid:
  for q,t in zip(path,path[1:]):
   if math.dist(q,t)<1e-6:continue
   track=p.PCB_TRACK(b);track.SetStart(V(q));track.SetEnd(V(t));track.SetWidth(p.FromMM(w));track.SetLayer(layer);track.SetNet(a.GetNet());b.Add(track)
  via=p.PCB_VIA(b);via.SetPosition(V(z));via.SetWidth(p.FromMM(diam));via.SetDrill(p.FromMM(.15));via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(a.GetNet());b.Add(via)
  added.append({'ref':f.GetReference(),'pin':a.GetNumber(),'net':n,'xy':z,'path':path,'layer':layer,'width':w});break
 if not valid:failed.append({'ref':f.GetReference(),'pin':a.GetNumber(),'net':n,'xy':start})
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(P/'q2-v2.kicad_pcb'),b);fn.write_text(json.dumps(pro,ensure_ascii=False,indent=2),encoding='utf8')
(P/'output/local-fanout.json').write_text(json.dumps({'added':added,'failed':failed},indent=2));print('ADDED',len(added),'FAILED',failed,flush=True)
