from pathlib import Path
import json,math
P=Path(__file__).resolve().parents[1];g=json.loads((P/'output/geometry.json').read_text(encoding='utf8'));items=g['items'];d={o['id']:o for o in items}
c=json.loads((P/'output/connections.json').read_text(encoding='utf8'));requests=[]
def job(a,b,w):requests.append({'items':[{'uuid':a['id']},{'uuid':b['id']}],'width':w})
for net in ['BQ25895_I2C_CLK','VBUS_5V']:
    groups=c[net];done=[groups[0]]
    for group in groups[1:]:
        aa=[d[i] for cc in done for i in cc if d[i]['kind']=='via']
        bb=[d[i] for i in group if d[i]['kind']=='via'] or [d[i] for i in group if d[i]['kind']=='pad']
        a,b=min(((a,b) for a in aa for b in bb),key=lambda ab:math.dist(ab[0]['pos'],ab[1]['pos']))
        job(a,b,.127 if net=='BQ25895_I2C_CLK' else .4);done.append(group)
for ref,num,net,w in [('C14','1','GND',.127),('C10','1','GND',.127),('C10','2','VBAT',.4)]:
    a=next(o for o in items if o.get('ref')==ref and o.get('num')==num)
    cand=[o for o in items if o['kind']=='via' and o['net']==net]
    b=min(cand,key=lambda o:math.dist(a['pos'],o['pos']));job(a,b,w)
(P/'output/finish-requests.json').write_text(json.dumps({'unconnected_items':requests}),encoding='utf8')
print(requests)
