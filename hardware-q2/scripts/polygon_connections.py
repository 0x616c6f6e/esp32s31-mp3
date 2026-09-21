"""Use pads as copper-island anchors; avoid free-via net reassignment on import."""
from pathlib import Path
import json,math,collections
P=Path(__file__).resolve().parents[1]
polys=json.loads((P/'output/zone-samples.json').read_text(encoding='utf8'))
g=json.loads((P/'output/geometry.json').read_text(encoding='utf8'));items=g['items']
requests=[]
for p in polys:
    if p['existing_vias'] or not p['pads']:continue
    a=p['pads'][0]
    candidates=[o for o in items if o['net']==p['net'] and o['kind']=='via' and not (p['bounds'][0]<=o['pos'][0]<=p['bounds'][2] and p['bounds'][1]<=o['pos'][1]<=p['bounds'][3])]
    if p['net']!='GND':
        candidates += [o for o in items if o['net']==p['net'] and o['kind']=='pad' and o['id'] not in [k['id'] for k in p['pads']] and not (p['bounds'][0]<=o['pos'][0]<=p['bounds'][2] and p['bounds'][1]<=o['pos'][1]<=p['bounds'][3])]
    if not candidates:continue
    b=min(candidates,key=lambda o:math.dist(a['pos'],o['pos']))
    requests.append({'items':[{'uuid':a['id']},{'uuid':b['id']}],'width':.25 if p['net'] in ['VBUS_5V','Net-(D2-A)','VCC_LCD_BG'] else .18})
old=json.loads((P/'output/remaining-drc.json').read_text(encoding='utf8'))
byid={o['id']:o for o in items}
for v in old['unconnected_items']:
    if all(i['uuid'] in byid for i in v['items']):
        a=byid[v['items'][0]['uuid']]
        if a['net']=='VBAT':v['width']=.18 # R2 high-impedance battery-voltage sense branch only.
        requests.append(v)
(P/'output/polygon-requests.json').write_text(json.dumps({'unconnected_items':requests}),encoding='utf8')
print('PAD_ANCHOR_REQUESTS',len(requests))
