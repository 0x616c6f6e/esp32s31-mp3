"""Finish the single reset airwire with clearance-aware two-layer grid search."""
from pathlib import Path
import pcbnew as p,sys,heapq,math,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tmp/controls-ground-deps'))
import numpy as np,shapely
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union
O=R/'hardware-display-adapter/am213-fpc-adapter';fn=O/'am213-fpc-adapter.kicad_pcb';
b=p.LoadBoard(str(fn));net=b.FindNet('/GND')
xy=lambda v:(p.ToMM(v.x),p.ToMM(v.y))
step=.01;xs=np.arange(50.4,66.6+step/2,step);ys=np.arange(50.4,71.6+step/2,step);xx,yy=np.meshgrid(xs,ys)
obs=[];blocked=[];viablocked=[]
for layer in [p.F_Cu,p.B_Cu]:
    polys=[]
    for f in b.GetFootprints():
        for a in f.Pads():
            if not a.IsOnLayer(layer) or a.GetNetname()=='/GND':continue
            poly=a.GetEffectivePolygon(layer)
            for i in range(poly.OutlineCount()):
                pts=poly.COutline(i);polys.append(Polygon([xy(pts.CPoint(k)) for k in range(pts.PointCount())]))
    for t in b.GetTracks():
        if t.GetNetname()=='/GND' or not t.IsOnLayer(layer):continue
        if isinstance(t,p.PCB_VIA):polys.append(Point(xy(t.GetPosition())).buffer(p.ToMM(t.GetWidth(layer))/2))
        else:polys.append(LineString([xy(t.GetStart()),xy(t.GetEnd())]).buffer(p.ToMM(t.GetWidth())/2))
    g=unary_union(polys);obs.append(g)
    blocked.append(shapely.contains_xy(g.buffer(.151),xx,yy))
    viablocked.append(shapely.contains_xy(g.buffer(.255),xx,yy))
(O/'output/routing-obstacles.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1700" height="1400" viewBox="48 55 18 14"><rect x="48" y="55" width="18" height="14" fill="white"/>'+obs[0].svg(scale_factor=.04,fill_color='#da3434')+obs[1].svg(scale_factor=.04,fill_color='#3445da',opacity=.35)+'<circle cx="50.95" cy="65.6" r=".15" fill="lime"/><circle cx="51.8" cy="59.8" r=".15" fill="lime"/></svg>')
idx=lambda pos:(round((pos[0]-xs[0])/step),round((pos[1]-ys[0])/step))
start=(0,*idx(tuple(map(float,sys.argv[1:3]))));end=(1,*idx((56,56)))
components=json.loads((O/'output/ground-components.json').read_text());target=next(g for g in components if any(x['layer']==p.B_Cu for x in g['polygons']))
goal=[]
for layer in [p.F_Cu,p.B_Cu]:
    g=unary_union([shapely.from_wkt(x['wkt']) for x in target['polygons'] if x['layer']==layer]);goal.append(shapely.contains_xy(g,xx,yy))
def heuristic(n):return 0
print('blocked endpoints',blocked[start[0]][start[2],start[1]],blocked[end[0]][end[2],end[1]])
heap=[(heuristic(start),0,start)];cost={start:0};prev={};closed=set()
while heap:
    _,c,n=heapq.heappop(heap)
    if n in closed:continue
    closed.add(n)
    if goal[n[0]][n[2],n[1]]:end=n;break
    l,x,y=n;nexts=[]
    for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
        X,Y=x+dx,y+dy
        if 0<=X<len(xs) and 0<=Y<len(ys) and not blocked[l][Y,X]:nexts.append(((l,X,Y),math.hypot(dx,dy)))
    if not viablocked[0][y,x] and not viablocked[1][y,x]:nexts.append(((1-l,x,y),20))
    for nn,dc in nexts:
        cc=c+dc
        if cc<cost.get(nn,float('inf')):cost[nn]=cc;prev[nn]=n;heapq.heappush(heap,(cc+heuristic(nn),cc,nn))
else:
    print('reachable',len(closed),'nearest',min(heuristic(n) for n in closed),'end B reachable',(1,end[1],end[2]) in closed)
    raise RuntimeError('No reset route found')
path=[end]
while path[-1]!=start:path.append(prev[path[-1]])
path.reverse();out=[path[0]]
for i in range(1,len(path)-1):
    a,z,q=path[i-1:i+2]
    if tuple(z[k]-a[k] for k in range(3))!=tuple(q[k]-z[k] for k in range(3)):out.append(z)
out.append(path[-1]);v=lambda n:p.VECTOR2I(p.FromMM(float(xs[n[1]])),p.FromMM(float(ys[n[2]])))
for a,z in zip(out,out[1:]):
    if a[0]!=z[0]:
        t=p.PCB_VIA(b);t.SetPosition(v(a));t.SetWidth(p.FromMM(.3));t.SetDrill(p.FromMM(.15));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu)
    else:
        t=p.PCB_TRACK(b);t.SetStart(v(a));t.SetEnd(v(z));t.SetWidth(p.FromMM(.1));t.SetLayer(p.F_Cu if a[0]==0 else p.B_Cu)
    t.SetNet(net);b.Add(t)
p.SaveBoard(str(fn),b)
(O/('output/ground-route-'+sys.argv[1]+'.json')).write_text(json.dumps([[n[0],float(xs[n[1]]),float(ys[n[2]])] for n in out],indent=2))
print('Reset routed:',len(out),'vertices;',len(closed),'searched nodes')
