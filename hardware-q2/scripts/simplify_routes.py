"""Shorten degree-two routing chains with clearance-checked 45-degree shortcuts.

Original arcs and USB routes remain outside this pass. Native DRC gates the result.
"""
from pathlib import Path
HERE=Path(__file__).resolve().parent;s=HERE/'route_repair.py'
exec(compile(s.read_text(encoding='utf8').split('results=[];new=[]')[0],str(s),'exec'))
original=parse((ROOT/'hardware/hardware.kicad_pcb').read_text(encoding='utf8'))
oldids={get(n,'uuid')[1] for n in original if isinstance(n,list) and n[0] in ['segment','arc']}
groups=collections.defaultdict(list)
for o in items:
    if o['kind']=='track' and o['id'] not in oldids and 'USB_D' not in o['net']:groups[(o['net'],o['layers'][0],o['width'])].append(o)
removed=set();added=[];stats=[]
for (net,layer,width),tracks in groups.items():
    mask,_=masks(net,width);mi=mask[LS.index(layer)];adj=collections.defaultdict(list)
    for o in tracks:
        for pt in [o['pos'],o['end']]:adj[tuple(pt)].append(o)
    pins=[o for o in items if o['net']==net and o['kind'] in ['via','pad'] and layer in o['layers']]
    # Preserve trace endpoints used by other widths/layers/original routing.
    special={tuple(pt) for o in items if o['net']==net and o not in tracks for pt in ([o['pos'],o['end']] if o['kind'] in ['track','arc'] else [o['pos']])}
    for pt in adj:
        if any(math.dist(pt,o['pos'])<max(o.get('width',0),max(o.get('size',[0])))/2+.03 for o in pins):special.add(pt)
    seen=set();chains=[]
    def walk(start,first):
        pts=[list(start)];ids=[];pt=start;o=first
        while o['id'] not in seen:
            seen.add(o['id']);ids.append(o['id']);pt=tuple(o['end'] if tuple(o['pos'])==pt else o['pos']);pts.append(list(pt))
            if pt in special or len(adj[pt])!=2:break
            nxt=[t for t in adj[pt] if t['id'] not in seen]
            if not nxt:break
            o=nxt[0]
        return pts,ids
    for pt,edges in adj.items():
        if len(edges)!=2 or pt in special:
            for o in edges:
                if o['id'] not in seen:chains.append(walk(pt,o))
    def clear(a,b):
        pa,pb=pix(a),pix(b);n=max(abs(pb[0]-pa[0]),abs(pb[1]-pa[1]))*2+1
        xx=np.rint(np.linspace(pa[0],pb[0],n)).astype(int);yy=np.rint(np.linspace(pa[1],pb[1],n)).astype(int)
        return bool(np.all((xx>=0)&(xx<W)&(yy>=0)&(yy<H))) and not mi[yy,xx].any()
    def alternatives(a,b):
        dx,dy=b[0]-a[0],b[1]-a[1];sx=1 if dx>=0 else -1;sy=1 if dy>=0 else -1;v=min(abs(dx),abs(dy))
        if min(abs(dx),abs(dy))<1e-6 or abs(abs(dx)-abs(dy))<1e-6:return [[a,b]]
        return [[a,[round(a[0]+sx*v,6),round(a[1]+sy*v,6)],b],[a,[round(b[0]-sx*v,6),round(b[1]-sy*v,6)],b]]
    before=after=0;count=0
    for pts,ids in chains:
        if len(ids)<3:continue
        path=[pts[0]];i=0
        while i<len(pts)-1:
            chosen=None
            for j in range(len(pts)-1,i+1,-1):
                for pp in alternatives(pts[i],pts[j]):
                    if all(clear(a,b) for a,b in zip(pp,pp[1:])):chosen=(j,pp);break
                if chosen:break
            if chosen:j,pp=chosen;path+=pp[1:];i=j
            else:i+=1;path.append(pts[i])
        bl=sum(math.dist(a,b) for a,b in zip(pts,pts[1:]));al=sum(math.dist(a,b) for a,b in zip(path,path[1:]))
        if len(path)>=len(pts) or al>bl+1e-5:continue
        removed.update(ids);before+=bl;after+=al;count+=1
        for a,b in zip(path,path[1:]):
            if a!=b:added.append({'id':str(uuid.uuid4()),'net':net,'pos':a,'end':b,'width':width,'layer':layer})
    if count:stats.append({'net':net,'layer':layer,'chains':count,'before_mm':before,'after_mm':after})
tree=parse((P/'hardware.kicad_pcb').read_text(encoding='utf8'));tree[:]=[n for n in tree if not(isinstance(n,list) and n[0]=='segment' and get(n,'uuid')[1] in removed)]
names={0:'F.Cu',6:'In2.Cu',8:'In3.Cu',2:'B.Cu'}
for o in added:tree.append(['segment',['start',*map(str,o['pos'])],['end',*map(str,o['end'])],['width',str(o['width'])],['layer',S(names[o['layer']])],['net',S(o['net'])],['uuid',S(o['id'])]])
(P/'hardware.kicad_pcb').write_text(dump(tree)+'\n',encoding='utf8')
report={'removed_segments':len(removed),'added_segments':len(added),'length_saved_mm':sum(s['before_mm']-s['after_mm'] for s in stats),'groups':stats}
(P/'output/route-simplification.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('SIMPLIFIED',len(removed),len(added),report['length_saved_mm'],flush=True)
