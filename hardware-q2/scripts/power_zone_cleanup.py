from pathlib import Path
import pcbnew as p,json,sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'tmp'));from sexpr import *
b=p.LoadBoard(str(P/'hardware.kicad_pcb'));nets={'Net-(D2-A)','Net-(U4-SW)'}
zz=[z for z in b.Zones() if z.GetNetname() in nets];remove=set();polys=[]
for z in zz:
    c=z.Outline().COutline(0);polys.append({'net':z.GetNetname(),'points':[[c.CPoint(i).x/1e6,c.CPoint(i).y/1e6] for i in range(c.PointCount())]})
    for t in b.GetTracks():
        if not isinstance(t,p.PCB_VIA) and t.GetLayer()==p.F_Cu and t.GetNetname() in ['BQ25895_I2C_CLK','BQ25895_I2C_SDA']:
            if any(z.Outline().Contains(pt) for pt in [t.GetStart(),t.GetEnd(),p.VECTOR2I(int((t.GetStart().x+t.GetEnd().x)/2),int((t.GetStart().y+t.GetEnd().y)/2))]):remove.add(t.m_Uuid.AsString())
t=parse((P/'hardware.kicad_pcb').read_text(encoding='utf8'));t[:]=[n for n in t if not(isinstance(n,list) and n[0] in ['segment','arc','via'] and (get(n,'uuid')[1] in remove or get(n,'net',['net',''])[1] in nets))]
(P/'hardware.kicad_pcb').write_text(dump(t)+'\n',encoding='utf8');(P/'output/power-keepouts.json').write_text(json.dumps(polys),encoding='utf8');print('POWER_SIGNAL_RIPUP',len(remove))
