"""Apply final mechanical clearance changes to the currently routed draft."""
from pathlib import Path
import pcbnew as p,json,sys,math,uuid
ROOT=Path(__file__).resolve().parents[2];DST=ROOT/'hardware-q2'
sys.path.insert(0,str(ROOT/'tmp'));from sexpr import *
b=p.LoadBoard(str(DST/'hardware.kicad_pcb'));old=[]
for f in b.GetFootprints():
    if f.GetReference() not in ['R2','C43']:continue
    pads=[(a,(a.GetPosition().x,a.GetPosition().y)) for a in f.Pads()]
    x,y={'R2':(146.2,88.672),'C43':(142.6,90.628)}[f.GetReference()]
    f.SetPosition(p.VECTOR2I(round(x*1e6),round(y*1e6)))
    if f.GetReference()=='R2' and not f.IsFlipped():f.Flip(f.GetPosition(),False)
    for a,pos in pads:old.append((pos,(a.GetPosition().x-pos[0],a.GetPosition().y-pos[1]),a.GetNetname()))
for t in b.GetTracks():
    if isinstance(t,p.PCB_VIA):continue
    for getter,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
        q=getter()
        for (x,y),(dx,dy),net in old:
            if t.GetNetname()==net and math.hypot(q.x-x,q.y-y)<15000:setter(p.VECTOR2I(q.x+dx,q.y+dy));break
p.SaveBoard(str(DST/'hardware.kicad_pcb'),b)
tree=parse((DST/'hardware.kicad_pcb').read_text(encoding='utf8'))
s=(DST/'scripts/revise_layout.py').read_text(encoding='utf8')
exec(s[s.index("tree[:]=[g for g in tree"):s.index('# Existing antenna rule area')])
# Motor copper pours remain at their old connector location: replace with routed conductors.
tree[:]=[n for n in tree if not(isinstance(n,list) and n[0]=='zone' and get(n,'net',['net',''])[1] in ['MOTOR_OUT_N','MOTOR_OUT_P'])]
(DST/'hardware.kicad_pcb').write_text(dump(tree)+'\n',encoding='utf8')
print('FINAL_PLACEMENT_REFINED')
