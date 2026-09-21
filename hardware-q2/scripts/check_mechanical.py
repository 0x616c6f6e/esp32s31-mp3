"""Inspect new board and envelopes against revision D, before final integration."""
import FreeCAD as App,Part,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'hardware-q2';V=App.Vector
d=App.openDocument(str(ROOT/'mechanical/enclosure-q2-d/ESP32S31_MP3_Q2_D.FCStd'))
g=json.loads((P/'output/geometry.json').read_text(encoding='utf8'))
pcb=Part.Shape();pcb.read(str(P/'output/board-only.step'));pcb.rotate(V(),V(0,0,1),180);pcb.translate(V(149,-49,4.245))
assert pcb.isValid()
housing=d.HousingWithControlPosts.Shape
out={'board_mm':[pcb.BoundBox.XLength,pcb.BoundBox.YLength,pcb.BoundBox.ZLength],'pcb_housing_mm3':pcb.common(housing).Volume,'components':[]}
new_components=[]
for f in g['footprints']:
    ref=f['reference']
    if ref.startswith('SCREW'):continue
    (x0,y0),(x1,y1)=f['bounds_mm'];h=.7 if ref.startswith('R') else 1 if ref.startswith('C') else 1.3
    if ref.startswith('L'):h=2.5
    h={'U9':3.2,'CARD2':1.8,'USB1':3.2,'CN1':5.5,'H1':5.5,'H2':5.5,'FPC2':1}.get(ref,h)
    if ref=='USB1':x0,x1,y0,y1=130.949,140.021,121.349,126.921
    if ref=='CN1':x0,x1,y0,y1=109.365,115.845,113.17,127.31
    z=5.2 if f['side']=='top' else 4.2-h
    sh=Part.makeBox(x1-x0,y1-y0,h,V(149-x1,y0-49,z));new_components.append((ref,sh))
    for name,other in [('housing',housing),('screen',d.LCDModule.Shape),('control',d.ControlBoard.Shape),('FPC',d.DisplayFPCRoute.Shape)]:
        if ref=='FPC2' and name=='FPC':continue
        vol=sh.common(other).Volume
        if vol>1e-5:out['components'].append({'ref':ref,'against':name,'mm3':round(vol,6)})
battery=d.BatteryReference.Shape.copy();battery.translate(V(-1.8,1.5,0))
for ref,sh in new_components:
    v=sh.common(battery).Volume
    if v>1e-5:out['components'].append({'ref':ref,'against':'battery shifted+1.5Y','mm3':round(v,6)})
out['pcb_FPC_mm3']=pcb.common(d.DisplayFPCRoute.Shape).Volume
(P/'output/mechanical-preflight.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print('MECHANICAL_PREFLIGHT',json.dumps(out))
