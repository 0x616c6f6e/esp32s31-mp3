"""Read-only extraction using KiCad's bundled Python; never saves the board."""
from pathlib import Path
import pcbnew, json, hashlib
HERE=Path(__file__).resolve().parent
boardpath=HERE.parents[1]/'hardware/hardware.kicad_pcb'
b=pcbnew.LoadBoard(str(boardpath))
f=next(f for f in b.GetFootprints() if f.GetReference()=='FPC2')
mm=lambda v: round(pcbnew.ToMM(v),6)
pads=[]
for p in f.Pads():
    xy=[mm(p.GetPosition().x),mm(p.GetPosition().y)]
    pads.append({'pin':p.GetNumber(),'net':p.GetNetname(),'pcb_xy':xy,'case_xy':[round(149-xy[0],6),round(xy[1]-49,6)]})
data={'file':str(boardpath),'sha256':hashlib.sha256(boardpath.read_bytes()).hexdigest(),'ref':f.GetReference(),'footprint':str(f.GetFPID().GetLibItemName()),'layer':b.GetLayerName(f.GetLayer()),'angle_deg':f.GetOrientationDegrees(),'pcb_xy':[mm(f.GetPosition().x),mm(f.GetPosition().y)],'pads':pads}
(HERE/'reference/current-fpc2.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(data,ensure_ascii=True,indent=2))
