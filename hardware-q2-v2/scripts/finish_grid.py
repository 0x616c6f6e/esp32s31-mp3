"""Clearance-aware local completion router; native KiCad DRC remains authoritative."""
from pathlib import Path
import sys,json,math,heapq,time,collections
import pcbnew as p
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'tmp/v2-kicad-deps'))
import numpy as np,shapely
from shapely.geometry import Point,LineString,Polygon,box
from shapely.ops import unary_union,nearest_points
from shapely import affinity
fn=P/'q2-v2.kicad_pcb';b=p.LoadBoard(str(fn));pro=(P/'q2-v2.kicad_pro').read_bytes()
xy=lambda v:(p.ToMM(v.x),p.ToMM(v.y))
V=lambda z:p.VECTOR2I(p.FromMM(float(z[0])),p.FromMM(float(z[1])))
layers=[p.F_Cu,p.In2_Cu,p.In3_Cu,p.B_Cu]
outline=affinity.translate(Polygon(json.loads((P.parent/'hardware-q2-v2-plan/outline.json').read_text())[0]),128.868,67.647)
def psgeom(ps):
 polys=[]
 for i in range(ps.OutlineCount()):
  def points(c):return [xy(c.CPoint(j)) for j in range(c.PointCount())]
  polys.append(Polygon(points(ps.COutline(i)),[points(ps.CHole(i,j)) for j in range(ps.HoleCount(i))]).buffer(0))
 return unary_union(polys)
def geometry(a,l):
 if isinstance(a,p.PAD):return psgeom(a.GetEffectivePolygon(l))
 if isinstance(a,p.PCB_VIA):return Point(xy(a.GetPosition())).buffer(p.ToMM(a.GetWidth(l))/2)
 return LineString([xy(a.GetStart()),xy(a.GetEnd())]).buffer(p.ToMM(a.GetWidth())/2)
def database():
 items={};cu={l:collections.defaultdict(list) for l in layers};holes=[];keepouts=[]
 for f in b.GetFootprints():
  for z in f.Zones():
   if z.GetIsRuleArea() and z.GetDoNotAllowVias():keepouts.append(psgeom(z.Outline()))
  for a in f.Pads():
   items[a.m_Uuid.AsString()]=a
   if a.GetDrillSize().x:holes.append((a.GetNetname(),Point(xy(a.GetPosition())).buffer(max(xy(a.GetDrillSize()))/2),.25 if a.GetAttribute()==p.PAD_ATTRIB_NPTH else .3))
 for a in b.GetTracks():
  items[a.m_Uuid.AsString()]=a
  if isinstance(a,p.PCB_VIA):holes.append((a.GetNetname(),Point(xy(a.GetPosition())).buffer(p.ToMM(a.GetDrillValue())/2),.2))
 shapes={}
 for uid,a in items.items():
  shapes[uid]={l:geometry(a,l) for l in layers if a.IsOnLayer(l)}
  for l,s in shapes[uid].items():cu[l][a.GetNetname()].append(s)
 return items,cu,holes,keepouts,shapes
def group(seed,items,shapes):
 net=items[seed].GetNetname();todo=[seed];seen={seed};candidates=[u for u,a in items.items() if a.GetNetname()==net]
 while todo:
  u=todo.pop()
  for v in candidates:
   if v in seen:continue
   if any(shapes[u][l].distance(shapes[v][l])<.00015 for l in shapes[u].keys() & shapes[v].keys()):seen.add(v);todo.append(v)
 return {l:unary_union([shapes[u][l] for u in seen if l in shapes[u]]) for l in layers},seen
def route(uid1,uid2=None,ground=False):
 items,cu,holes,keepouts,shapes=database();a=items[uid1];net=a.GetNetname();start,seen=group(uid1,items,shapes)
 if ground:
  goal={l:unary_union([shapes[u][l] for u,v in items.items() if u not in seen and v.GetNetname()==net and isinstance(v,p.PCB_VIA) and l in shapes[u]]) for l in layers}
 else:
  if uid2 in seen:print('Already connected',net,flush=True);return True
  goal,_=group(uid2,items,shapes)
 width=.1;diam=.35;drill=.15;step=.05
 both=unary_union(list(start.values())+list(goal.values()));x0,y0,x1,y1=both.bounds
 # Full board width is available for long detours, but no routing outside the outline.
 x0=max(129.118,x0-5);y0=max(67.897,y0-5);x1=min(174.618,x1+5);y1=min(143.397,y1+5)
 nx=int(math.ceil((x1-x0)/step))+1;ny=int(math.ceil((y1-y0)/step))+1
 xs=x0+np.arange(nx)*step;ys=y0+np.arange(ny)*step;xx,yy=np.meshgrid(xs,ys);size=nx*ny
 inside=shapely.contains_xy(outline.buffer(-.25-width/2-.001),xx,yy)
 obs={l:unary_union([s for n,ss in cu[l].items() if n!=net for s in ss]) for l in layers}
 foreignholes=unary_union([s.buffer(c+width/2+.001) for n,s,c in holes if n!=net])
 traceobs={l:obs[l].buffer(.102+width/2).union(foreignholes) for l in layers}
 blocked=np.array([shapely.intersects_xy(traceobs[l],xx,yy)|~inside for l in layers])
 viaob=unary_union(list(obs.values())).buffer(.102+diam/2)
 viaob=viaob.union(unary_union([s.buffer(.201+drill/2) for n,s,c in holes]+keepouts))
 viafree=~shapely.intersects_xy(viaob,xx,yy)&shapely.contains_xy(outline.buffer(-.25-diam/2-.001),xx,yy)
 ownvias=[v for v in items.values() if isinstance(v,p.PCB_VIA) and v.GetNetname()==net]
 reuse=unary_union([Point(xy(v.GetPosition())).buffer(.09) for v in ownvias])
 viafree|=shapely.contains_xy(reuse,xx,yy)
 smask=np.array([shapely.contains_xy(start[l].buffer(-.01),xx,yy)&~blocked[i] for i,l in enumerate(layers)])
 gmask=np.array([shapely.contains_xy(goal[l].buffer(-.01),xx,yy)&~blocked[i] for i,l in enumerate(layers)])
 if not smask.any() or not gmask.any():print('No grid terminals',net,smask.sum(),gmask.sum(),flush=True);return False
 # Euclidean distance to the target bounding box is an admissible heuristic.
 gy,gx=np.where(gmask.any(axis=0));gx0,gx1=gx.min(),gx.max();gy0,gy1=gy.min(),gy.max()
 hx=np.maximum(np.maximum(gx0-np.arange(nx),np.arange(nx)-gx1),0);hy=np.maximum(np.maximum(gy0-np.arange(ny),np.arange(ny)-gy1),0)
 heuristic=np.sqrt(hx[None,:]**2+hy[:,None]**2).ravel()
 costs=np.full(4*size,np.inf);prev=np.full(4*size,-1,dtype=np.int64);heap=[];bf=blocked.reshape(4,size);gf=gmask.ravel();vf=viafree.ravel()
 for node in np.flatnonzero(smask):costs[node]=0;heapq.heappush(heap,(float(heuristic[node%size]),0,int(node)))
 moves=[(1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,math.sqrt(2)),(-1,1,math.sqrt(2)),(1,-1,math.sqrt(2)),(-1,-1,math.sqrt(2))]
 end=None;visited=0;beg=time.time();print('Routing',net,'grid',nx,ny,'starts',smask.sum(),'goals',gmask.sum(),flush=True)
 while heap:
  _,cost,node=heapq.heappop(heap)
  if cost>costs[node]+1e-8:continue
  if gf[node]:end=node;break
  visited+=1
  if visited%200000==0:
   print(net,'visited',visited,'seconds',round(time.time()-beg),flush=True)
   if time.time()-beg>240:break
  l,q=divmod(node,size);y,x=divmod(q,nx)
  for dx,dy,d in moves:
   X,Y=x+dx,y+dy
   if not(0<=X<nx and 0<=Y<ny):continue
   Q=Y*nx+X
   if bf[l,Q] or (dx and dy and (bf[l,y*nx+X] or bf[l,Y*nx+x])):continue
   nn=l*size+Q;nc=cost+d
   if nc+1e-8<costs[nn]:costs[nn]=nc;prev[nn]=node;heapq.heappush(heap,(nc+heuristic[Q],nc,nn))
  if vf[q]:
   for L in range(4):
    if L==l or bf[L,q]:continue
    nn=L*size+q;nc=cost+30
    if nc+1e-8<costs[nn]:costs[nn]=nc;prev[nn]=node;heapq.heappush(heap,(nc+heuristic[q],nc,nn))
 if end is None:print('FAILED',net,visited,flush=True);return False
 nodes=[end]
 while prev[nodes[-1]]>=0:nodes.append(int(prev[nodes[-1]]))
 nodes.reverse()
 def point(n):L,q=divmod(n,size);Y,X=divmod(q,nx);return L,(float(xs[X]),float(ys[Y]))
 paths=[];vias=[];current=[];lastlayer=None
 for node in nodes:
  L,z=point(node)
  if L!=lastlayer:
   if current:paths.append((lastlayer,current));vias.append(z)
   current=[z];lastlayer=L
  else:current.append(z)
 if current:paths.append((lastlayer,current))
 # Replace grid transitions within an existing via by its exact centre.
 for i,z in enumerate(vias):
  old=next((v for v in ownvias if math.dist(xy(v.GetPosition()),z)<.091),None)
  if old:
   pos=xy(old.GetPosition());paths[i][1].append(pos);paths[i+1][1].insert(0,pos);vias[i]=None
 # Exact segment collision check before modifying the board.
 for L,path in paths:
  if len(path)>1 and traceobs[layers[L]].intersects(LineString(path)):print('Exact check failed',net,flush=True);return False
 count=0
 for L,path in paths:
  keep=[path[0]]
  for i in range(1,len(path)-1):
   ax,ay=path[i][0]-path[i-1][0],path[i][1]-path[i-1][1];cx,cy=path[i+1][0]-path[i][0],path[i+1][1]-path[i][1]
   if abs(ax*cy-ay*cx)>1e-8 or ax*cx+ay*cy<0:keep.append(path[i])
  keep.append(path[-1])
  for q,z in zip(keep,keep[1:]):
   if math.dist(q,z)<1e-6:continue
   t=p.PCB_TRACK(b);t.SetStart(V(q));t.SetEnd(V(z));t.SetWidth(p.FromMM(width));t.SetLayer(layers[L]);t.SetNet(a.GetNet());b.Add(t);count+=1
 for z in vias:
  if z is None:continue
  v=p.PCB_VIA(b);v.SetPosition(V(z));v.SetWidth(p.FromMM(diam));v.SetDrill(p.FromMM(drill));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(a.GetNet());b.Add(v)
 p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(fn),b);(P/'q2-v2.kicad_pro').write_bytes(pro)
 print('CONNECTED',net,count,'segments',len([v for v in vias if v]),'vias',round(time.time()-beg,1),'seconds',flush=True);return True

if __name__=='__main__':
 drc=json.loads((P/'output/fullroute-drc.json').read_text(encoding='utf8'));results=[]
 for e in drc['unconnected_items']:
  uu=[a['uuid'] for a in e['items']]
  items={a.m_Uuid.AsString():a for f in b.GetFootprints() for a in f.Pads()};items.update({a.m_Uuid.AsString():a for a in b.GetTracks()})
  if uu[0] not in items:continue
  net=items[uu[0]].GetNetname()
  if len(sys.argv)>1 and sys.argv[1]!=net:continue
  if net=='GND':results.append([net,route(uu[0],ground=True)])
  elif uu[1] in items:results.append([net,route(*uu)])
 (P/'output/grid-completion.json').write_text(json.dumps(results,indent=2));print(results,flush=True)
