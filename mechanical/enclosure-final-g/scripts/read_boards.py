from pathlib import Path
import pcbnew as p,json,hashlib
R=Path(__file__).resolve().parents[3];O=R/'mechanical/enclosure-final-g'
res={}
for name,path in [('main',R/'hardware-q2/ProPrj_esp32s31-mp4_2026-09-22.kicad_pcb'),('controls',R/'hardware-controls/controls.kicad_pcb')]:
 b=p.LoadBoard(str(path));res[name]={'path':str(path.relative_to(R)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'thickness':p.ToMM(b.GetDesignSettings().GetBoardThickness()),'footprints':[]}
 for f in b.GetFootprints():
  res[name]['footprints'].append({'ref':f.GetReference(),'fp':str(f.GetFPID().GetLibItemName()),'xy':[p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y)],'side':'B' if f.IsFlipped() else 'F','angle':f.GetOrientationDegrees(),'model':[m.m_Filename for m in f.Models()],'holes':[[a.GetNumber(),p.ToMM(a.GetDrillSize().x)] for a in f.Pads() if a.GetDrillSize().x]})
(O/'source.json').write_text(json.dumps(res,indent=2),encoding='utf8')
print('Main matches previous',res['main']['sha256']==json.loads((R/'mechanical/final-board-review/mainboard-reference.json').read_text())['sha256'])
print('Drilled footprints',[(x['ref'],x['holes']) for x in res['main']['footprints'] if x['ref'].startswith(('SCREW','CN'))])
