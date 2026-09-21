"""Give fragmented copper polygons real via anchors, then connect power anchors."""
from pathlib import Path
import json,sys,math,uuid,collections
HERE=Path(__file__).resolve().parent
s=HERE/'route_repair.py'
exec(compile(s.read_text(encoding='utf8').split('results=[];new=[]')[0],str(s),'exec'))
polys=json.loads((P/'output/zone-samples.json').read_text(encoding='utf8'))
new=[];anchors=collections.defaultdict(list);report=[]
for net in sorted(set(a['net'] for a in polys)):
    _,vm=masks(net,.127)
    for poly in [a for a in polys if a['net']==net]:
        if poly['existing_vias']:
            anchor=poly['existing_vias'][0]
            if net!='GND':anchors[net].append(anchor)
            continue
        x0,y0,x1,y1=poly['bounds'];points=sorted(poly['points'],key=lambda pt:(pt[0]-(x0+x1)/2)**2+(pt[1]-(y0+y1)/2)**2)
        pt=next((pt for pt in points if 0<=pix(pt)[0]<W and 0<=pix(pt)[1]<H and not vm[pix(pt)[1],pix(pt)[0]]),None)
        if pt is None:
            report.append({'net':net,'bounds':poly['bounds'],'status':'no safe via site'});continue
        uid=str(uuid.uuid4());ob={'id':uid,'kind':'via','net':net,'pos':pt,'width':.5,'hole':.25,'layers':G['layers']}
        new.append(ob);items.append(ob);anchor={'id':uid,'pos':pt}
        if net!='GND':anchors[net].append(anchor)
        # Do not place several superimposed new holes for adjacent polygon samples.
        px,py=pix(pt);vm[max(0,py-11):py+12,max(0,px-11):px+12]=True
        report.append({'net':net,'bounds':poly['bounds'],'via':pt})
tree=parse((P/'hardware.kicad_pcb').read_text(encoding='utf8'))
for o in new:tree.append(['via',['at',*map(str,o['pos'])],['size','.5'],['drill','.25'],['layers',S('F.Cu'),S('B.Cu')],['net',S(o['net'])],['uuid',S(o['id'])]])
(P/'hardware.kicad_pcb').write_text(dump(tree)+'\n',encoding='utf8')
connections=[]
for net,aa in anchors.items():
    aa=list({a['id']:a for a in aa}.values())
    if len(aa)<2:continue
    done=[aa.pop(0)]
    while aa:
        a,b=min(((a,b) for a in done for b in aa),key=lambda ab:math.dist(ab[0]['pos'],ab[1]['pos']))
        connections.append({'items':[{'uuid':a['id']},{'uuid':b['id']}]});done.append(b);aa.remove(b)
(P/'output/zone-route-requests.json').write_text(json.dumps({'unconnected_items':connections}),encoding='utf8')
(P/'output/zone-stitch-report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('ZONE_STITCHES',len(new),'POWER_LINK_REQUESTS',len(connections),json.dumps(report))
