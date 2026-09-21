import pcbnew as p,json,collections
from pathlib import Path
P=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(P/'hardware.kicad_pcb'));c=b.GetConnectivity()
objects=[a for f in b.GetFootprints() for a in f.Pads()]+list(b.GetTracks())
out={}
for net in ['BQ25895_I2C_CLK','VBAT','VBUS_5V','GND']:
    oo={a.m_Uuid.AsString():a for a in objects if a.GetNetname()==net};groups=[]
    while oo:
        key,a=oo.popitem();stack=[a];group=[key]
        while stack:
            a=stack.pop()
            for v in list(c.GetConnectedTracks(a))+list(c.GetConnectedPads(a)):
                k=v.m_Uuid.AsString()
                if k in oo:stack.append(oo.pop(k));group.append(k)
        groups.append(group)
    out[net]=groups
(P/'output/connections.json').write_text(json.dumps(out),encoding='utf8')
print({k:[len(x) for x in v] for k,v in out.items()})
