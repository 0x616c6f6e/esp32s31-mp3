from pathlib import Path
import pcbnew as p,json,sys
P=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(P/'q2-v2.kicad_pcb'));pro=(P/'q2-v2.kicad_pro').read_bytes();d=json.loads((P/'output/fullroute-drc.json').read_text(encoding='utf8'));held=[]
ids={t.m_Uuid.AsString():t for t in b.GetTracks()};removed=[]
for e in d['violations']:
 if e['type'] not in ['via_dangling','track_dangling']:continue
 if e['type']=='track_dangling' and 'tracks' not in sys.argv:continue
 t=ids.get(e['items'][0]['uuid'])
 if t is None or t.GetNetname()=='DAC_I2S_DOUT' and 'all' not in sys.argv:continue
 removed.append([t.GetNetname(),e['type'],e['items'][0]['uuid']]);held.append(t);b.Remove(t)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(P/'q2-v2.kicad_pcb'),b);(P/'q2-v2.kicad_pro').write_bytes(pro)
print('Pruned',removed)
