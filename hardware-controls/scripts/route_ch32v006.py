"""Prepare local freerouting DSN, or import its result. KiCad DRC is authoritative."""
from pathlib import Path
import sys,json,shutil
import pcbnew as p
R=Path(__file__).resolve().parents[2];P=R/'hardware-controls';O=P/'output/ch32v006-review';C=O/'candidate'
sys.path.insert(0,str(R/'tmp'));from sexpr import parse,get,children,dump,S
mode=sys.argv[1] if len(sys.argv)>1 else 'export'
pro=(C/'controls.kicad_pro').read_bytes()
b=p.LoadBoard(str(C/'controls.kicad_pcb'))
if mode=='import':
    assert p.ImportSpecctraSES(b,str(O/'controls-ch32.ses'))
    p.SaveBoard(str(C/'controls.kicad_pcb'),b);(C/'controls.kicad_pro').write_bytes(pro)
    print('Imported',len(b.GetTracks()),'tracks/vias');sys.exit()
p.ExportSpecctraDSN(b,str(O/'native.dsn'))
tree=parse((O/'native.dsn').read_text().replace('(string_quote ")','(string_quote QUOTE)'))
structure=get(tree,'structure');placement=get(tree,'placement');network=get(tree,'network')
for c in list(children(placement,'component')):
    for a in list(children(c,'place')):
        if a[1]=='E1':c.remove(a)
    if not children(c,'place'):placement.remove(c)
for n in children(network,'net'):
    pins=get(n,'pins')
    if pins:pins[:]=[pins[0]]+[x for x in pins[1:] if not str(x).startswith('E1-')]
rule=['rule',['width','150'],['clearance','170'],['clearance','150',['type','smd_smd']]]
for item in [structure]+children(network,'class'):
    for r in list(children(item,'rule')):item.remove(r)
    item.append(rule)
for k in children(structure,'keepout'):
    c=get(k,'circle')
    if c:c[2]='4100'
for a in b.FindFootprintByReference('E1').Pads():
    ps=a.GetEffectivePolygon(p.F_Cu)
    for i in range(ps.OutlineCount()):
        line=ps.COutline(i);points=[]
        for k in range(line.PointCount()):
            v=line.CPoint(k);points.extend([str(round(v.x/1000,3)),str(round(-v.y/1000,3))])
        structure.append(['keepout',S('TOUCH_'+a.GetNumber()),['polygon','F.Cu','0']+points])
for item in get(tree,'wiring')[1:]:
    if isinstance(item,list) and item[0] in ['wire','via']:
        for typ in list(children(item,'type')):item.remove(typ)
        item.append(['type','protect'])
(O/'controls-ch32.dsn').write_text(dump(tree).replace('(string_quote QUOTE)','(string_quote ")'))
shutil.copy2(C/'controls.kicad_pcb',O/'controls-preroute.kicad_pcb')
print('Routing input ready')
