"""Remove only DRC-involved routing, keep all pads/nets and design rules intact."""
from pathlib import Path
import sys,json,collections
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'hardware-q2'
sys.path.insert(0,str(ROOT/'tmp'));from sexpr import *
report=Path(sys.argv[1]) if len(sys.argv)>1 else P/'output/placement-drc.json'
d=json.loads(report.read_text(encoding='utf8'));tree=parse((P/'hardware.kicad_pcb').read_text(encoding='utf8'))
types={'shorting_items','clearance','solder_mask_bridge','tracks_crossing','hole_clearance','hole_to_hole','copper_edge_clearance','via_dangling','track_dangling','copper_sliver'}
remove={i['uuid'] for v in d['violations'] if v['type'] in types for i in v['items']}
counter=collections.Counter()
for n in list(tree):
    if isinstance(n,list) and n[0] in ['segment','arc','via'] and get(n,'uuid')[1] in remove:
        counter[get(n,'net',['net',''])[1]]+=1;tree.remove(n)
for z in children(tree,'zone'):
    z[:]=[n for n in z if not(isinstance(n,list) and n[0]=='filled_polygon')]
(P/'hardware.kicad_pcb').write_text(dump(tree)+'\n',encoding='utf8')
print('REMOVED',sum(counter.values()),dict(counter))
