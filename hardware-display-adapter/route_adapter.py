from pathlib import Path
import pcbnew as p,sys
R=Path(__file__).resolve().parent;O=R/'am213-fpc-adapter';OUT=O/'output'
sys.path.insert(0,str(R.parent/'tmp'));from sexpr import parse,get,children,dump,S
b=p.LoadBoard(str(O/'am213-fpc-adapter.kicad_pcb'))
if len(sys.argv)>1 and sys.argv[1]=='import':
    # Native SES import can renumber nets. Import by explicit net NAME and
    # preserve the real tail/footprints instead of the virtual routing terminals.
    sess=parse((OUT/'adapter.ses').read_text());routes=get(sess,'routes')
    scale=1000/float(get(routes,'resolution')[2])
    vec=lambda x,y:p.VECTOR2I(round(float(x)*scale),round(-float(y)*scale))
    for n in children(get(routes,'network_out'),'net'):
        ni=b.FindNet(str(n[1]));assert ni, n[1]
        for w in children(n,'wire'):
            path=get(w,'path');coords=path[3:]
            for i in range(0,len(coords)-2,2):
                t=p.PCB_TRACK(b);t.SetStart(vec(*coords[i:i+2]));t.SetEnd(vec(*coords[i+2:i+4]));t.SetWidth(round(float(path[2])*scale));t.SetLayer(p.F_Cu if path[1]=='F.Cu' else p.B_Cu);t.SetNet(ni);b.Add(t)
        for w in children(n,'via'):
            t=p.PCB_VIA(b);t.SetPosition(vec(w[2],w[3]));t.SetWidth(p.FromMM(.4));t.SetDrill(p.FromMM(.2));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(ni);b.Add(t)
    p.SaveBoard(str(O/'am213-fpc-adapter.kicad_pcb'),b)
    print('Imported tracks/vias:',len(b.GetTracks()));sys.exit()
assert p.ExportSpecctraDSN(b,str(OUT/'adapter-native.dsn'))
t=parse((OUT/'adapter-native.dsn').read_text().replace('(string_quote ")','(string_quote QUOTE)'))
s=get(t,'structure');net=get(t,'network')
get(s,'boundary')[:]=['boundary',['rect','pcb','50000','-72000','67000','-50000']]
for item in [s]+children(net,'class'):
    for r in list(children(item,'rule')):item.remove(r)
    item.append(['rule',['width','120'],['clearance','110'],['clearance','100',['type','smd_smd']]])
# Tail is already routed. Prevent the router placing vias or detours in it.
# Substitute routing terminals at the island edge. They are NOT added to PCB.
for comp in children(get(t,'placement'),'component'):
    for pos in children(comp,'place'):
        if pos[1]=='J1':pos[2]='50400'
lib=get(t,'library')
for im in children(lib,'image'):
    if im[1]=='Adapter:FPC21_Fingers':
        for a in list(children(im,'outline')):im.remove(a)
        for pin in children(im,'pin'):
            pin[1]=S('TAIL_ROUTE_POINT');pin[3]='550' if int(pin[2])%2 else '0'
            pin[4]=str(-4000+(int(pin[2])-1)*400)
lib.append(['padstack',S('TAIL_ROUTE_POINT'),['shape',['circle',S('F.Cu'),'400','0','0']],['shape',['circle',S('B.Cu'),'400','0','0']],['attach','off']])
get(t,'wiring')[:]=['wiring']
for w in get(t,'wiring')[1:]:
    if isinstance(w,list) and w[0] in ['wire','via']:
        for typ in list(children(w,'type')):w.remove(typ)
        w.append(['type','protect'])
(OUT/'adapter.dsn').write_text(dump(t).replace('(string_quote QUOTE)','(string_quote ")'))
print('Routing prepared')
