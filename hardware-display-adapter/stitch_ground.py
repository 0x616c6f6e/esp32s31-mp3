from pathlib import Path
import pcbnew as p,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tmp/controls-ground-deps'))
import numpy as np,shapely
from shapely.geometry import Polygon,Point,LineString
from shapely.ops import unary_union
O=R/'hardware-display-adapter/am213-fpc-adapter';fn=O/'am213-fpc-adapter.kicad_pcb';b=p.LoadBoard(str(fn));xy=lambda a:(p.ToMM(a.x),p.ToMM(a.y))
def polygons(poly):
    result=[]
    for i in range(poly.OutlineCount()):
        line=poly.COutline(i);outer=[xy(line.CPoint(k)) for k in range(line.PointCount())];holes=[]
        for h in range(poly.HoleCount(i)):
            line=poly.CHole(i,h);holes.append([xy(line.CPoint(k)) for k in range(line.PointCount())])
        if len(outer)>2:result.append(Polygon(outer,holes).buffer(0))
    return result
gnd={};obstacles=[];existing=[]
for layer in [p.F_Cu,p.B_Cu]:
    gnd[layer]=[a for z in b.Zones() if z.GetLayer()==layer for a in polygons(z.GetFilledPolysList(layer))]
    for f in b.GetFootprints():
        for a in f.Pads():
            if a.GetNetname()!='/GND' and a.IsOnLayer(layer):obstacles+=polygons(a.GetEffectivePolygon(layer))
for t in b.GetTracks():
    if isinstance(t,p.PCB_VIA):
        if t.GetNetname()=='/GND':existing.append(Point(xy(t.GetPosition())))
        else:obstacles.append(Point(xy(t.GetPosition())).buffer(p.ToMM(t.GetWidth(p.F_Cu))/2))
    elif t.GetNetname()!='/GND':obstacles.append(LineString([xy(t.GetStart()),xy(t.GetEnd())]).buffer(p.ToMM(t.GetWidth())/2))
blocked=unary_union(obstacles).buffer(.31);added=[]
for f in gnd[p.F_Cu]:
    for z in gnd[p.B_Cu]:
        common=f.intersection(z)
        if common.area<.005 or any(common.buffer(.01).contains(x) for x in existing):continue
        free=common.difference(blocked)
        if free.is_empty:continue
        x0,y0,x1,y1=free.bounds
        xx,yy=np.meshgrid(np.arange(max(50.4,x0),min(66.6,x1)+.001,.05),np.arange(max(50.4,y0),min(71.6,y1)+.001,.05))
        valid=shapely.contains_xy(free,xx,yy)
        pts=[Point(x,y) for x,y in zip(xx[valid],yy[valid])]
        if not pts:continue
        point=max(pts,key=lambda q:q.distance(free.boundary));x,y=point.x,point.y
        t=p.PCB_VIA(b);t.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));t.SetWidth(p.FromMM(.4));t.SetDrill(p.FromMM(.2));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(b.FindNet('/GND'));b.Add(t);existing.append(point);added.append((x,y))
p.SaveBoard(str(fn),b);print('GND stitching vias:',added)
