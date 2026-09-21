"""Identify separate copper islands without merging disjoint polygons in one zone."""
import pcbnew as p,json,collections,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(P/'hardware.kicad_pcb'));c=b.GetConnectivity()
objects=[a for f in b.GetFootprints() for a in f.Pads()]+list(b.GetTracks());out={};requests=[]
for net in ['GND','Net-(U4-SW)']:
    oo={a.m_Uuid.AsString():a for a in objects if a.GetNetname()==net};parent={k:k for k in oo}
    def root(k):
        while parent[k]!=k:parent[k]=parent[parent[k]];k=parent[k]
        return k
    def union(a,b):parent[root(a)]=root(b)
    for k,a in oo.items():
        for v in list(c.GetConnectedTracks(a))+list(c.GetConnectedPads(a)):
            q=v.m_Uuid.AsString()
            if q in oo:union(k,q)
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetname()!=net:continue
        for l in z.GetLayerSet().CuStack():
            polys=z.GetFilledPolysList(l)
            for i in range(polys.OutlineCount()):
                key=z.m_Uuid.AsString()+':'+str(l)+':'+str(i);parent[key]=key
                for k,a in oo.items():
                    if not a.IsOnLayer(l):continue
                    pts=[a.GetPosition()] if isinstance(a,p.PAD) else [a.GetStart(),a.GetEnd()]
                    if any(polys.Contains(pt,i) for pt in pts):union(k,key)
    groups=collections.defaultdict(list)
    for k in oo:groups[root(k)].append(k)
    groups=sorted(groups.values(),key=len,reverse=True);out[net]=groups
    anchor=lambda grp:[oo[k] for k in grp if isinstance(oo[k],p.PCB_VIA)] or [oo[k] for k in grp if isinstance(oo[k],p.PAD)]
    done=anchor(groups[0])
    for grp in groups[1:]:
        aa=anchor(grp)
        if not aa:continue
        a,z=min(((a,z) for a in aa for z in done),key=lambda az:(az[0].GetPosition()-az[1].GetPosition()).SquaredEuclideanNorm())
        requests.append({'items':[{'uuid':a.m_Uuid.AsString()},{'uuid':z.m_Uuid.AsString()}],'width':.127 if net=='GND' else .4})
        done+=aa
(P/'output/copper-clusters.json').write_text(json.dumps(out),encoding='utf8')
(P/'output/cluster-requests.json').write_text(json.dumps({'unconnected_items':requests}),encoding='utf8')
print({k:[len(g) for g in v] for k,v in out.items()});print(requests)
