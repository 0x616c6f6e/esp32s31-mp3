exec(open(__file__.replace('analyze_ground.py','stitch_ground.py')).read().split('blocked=')[0])
from shapely.ops import nearest_points
bylayer={}
for layer in [p.F_Cu,p.B_Cu]:
    geoms=list(gnd[layer])
    for f in b.GetFootprints():
        for pad in f.Pads():
            if pad.GetNetname()=='/GND' and pad.IsOnLayer(layer):geoms+=polygons(pad.GetEffectivePolygon(layer))
    for t in b.GetTracks():
        if t.GetNetname()!='/GND' or not t.IsOnLayer(layer):continue
        geoms.append(Point(xy(t.GetPosition())).buffer(.2) if isinstance(t,p.PCB_VIA) else LineString([xy(t.GetStart()),xy(t.GetEnd())]).buffer(p.ToMM(t.GetWidth())/2))
    union=unary_union(geoms).buffer(.00001)
    bylayer[layer]=list(union.geoms) if hasattr(union,'geoms') else [union]
nodes=[(layer,i,geom) for layer in bylayer for i,geom in enumerate(bylayer[layer])];parent=list(range(len(nodes)))
def root(i):
    while parent[i]!=i:i=parent[i]
    return i
for via in existing:
    ids=[i for i,(_,_,g) in enumerate(nodes) if g.contains(via)]
    for i in ids[1:]:parent[root(i)]=root(ids[0])
groups={}
for i,n in enumerate(nodes):groups.setdefault(root(i),[]).append(i)
print('Ground components',len(groups))
for k,ids in groups.items():print(k,[(nodes[i][0],nodes[i][2].area,nodes[i][2].bounds) for i in ids])
import json
out=[]
for k,ids in groups.items():
    out.append({'component':k,'polygons':[{'layer':nodes[i][0],'wkt':nodes[i][2].wkt} for i in ids]})
(O/'output/ground-components.json').write_text(json.dumps(out))
for k,ids in groups.items():
    for kk,jds in groups.items():
        if kk<=k:continue
        best=min([(nodes[i][2].distance(nodes[j][2]),nodes[i][0],nearest_points(nodes[i][2],nodes[j][2])) for i in ids for j in jds if nodes[i][0]==nodes[j][0]],default=None,key=lambda a:a[0])
        if best:print('Between',k,kk,'distance',best[0],'layer',best[1],'points',[q.wkt for q in best[2]])
