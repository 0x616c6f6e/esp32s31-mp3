from pathlib import Path
import sys,json
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'tmp'));from sexpr import *
ids={'244894fc-5308-40fe-9356-a39d7a7d0764','31519886-55dc-46fd-9501-b968fe37ac0b','5878b604-6ed2-42e0-9d62-1d97f79f2dc8','994bf9cf-c207-4c38-9ec4-e5e3641704dd','32984585-c21e-49b1-895f-44ae6690c288','8ec40b77-84f9-4678-bb95-acf5c98e913b'}
t=parse((P/'hardware.kicad_pcb').read_text(encoding='utf8'));t[:]=[n for n in t if not(isinstance(n,list) and n[0]=='segment' and get(n,'uuid')[1] in ids)]
(P/'hardware.kicad_pcb').write_text(dump(t)+'\n',encoding='utf8')
print('OPENED_GROUND_ESCAPE',len(ids))
