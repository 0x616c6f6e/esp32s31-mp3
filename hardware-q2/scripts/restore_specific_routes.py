from pathlib import Path
import json,sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'tmp'));from sexpr import *
board=P/'hardware.kicad_pcb';t=parse(board.read_text(encoding='utf8'));old=parse((P/'output/before-simplification.kicad_pcb').read_text(encoding='utf8'))
nets={'ESP_BOOT1','CH343P_UART_TX','Net-(U2-HPOUTB)'}
select=lambda n:isinstance(n,list) and n[0] in ['segment','arc','via'] and get(n,'net',['net',''])[1] in nets
t[:]=[n for n in t if not select(n)];t.extend(n for n in old if select(n));board.write_text(dump(t)+'\n',encoding='utf8')
r=json.loads((P/'output/route-simplification.json').read_text(encoding='utf8'));r['restored_nets']=sorted(nets);r['groups']=[s for s in r['groups'] if s['net'] not in nets];r['length_saved_mm']=sum(s['before_mm']-s['after_mm'] for s in r['groups']);r['removed_segments_before_selective_restore']=r.pop('removed_segments');r['added_segments_before_selective_restore']=r.pop('added_segments');(P/'output/route-simplification.json').write_text(json.dumps(r,indent=2),encoding='utf8')
print('RESTORED_REVIEWED_PATHS',nets)
