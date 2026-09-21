"""Run after final PCB export. Freeze exact new PCB and current component envelopes."""
import FreeCAD as App,Part,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'hardware-q2';DEST=ROOT/'mechanical/enclosure-q2-e/reference';DEST.mkdir(exist_ok=True)
g=json.loads((P/'output/geometry.json').read_text(encoding='utf8'))
layout={'footprints':g['footprints'],'outline_size_mm':[46,76],'outline_mm':[101,51,147,127],'corner_radius_mm':10}
(P/'output/layout-data.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2),encoding='utf8')
V=App.Vector;s=Part.Shape();s.read(str(P/'output/board-only.step'));s.rotate(V(),V(1,0,0),180);s.translate(V(-99,-49,8.055));s.exportBrep(str(DEST/'source-PCB.brep'))
shapes=[]
for f in g['footprints']:
    ref=f['reference']
    if ref.startswith('SCREW'):continue
    (x0,y0),(x1,y1)=f['bounds_mm'];h=.7 if ref.startswith('R') else 1 if ref.startswith('C') else 1.3
    if ref.startswith('L'):h=2.5
    h={'U9':3.2,'CARD2':1.8,'USB1':3.2,'CN1':5.5,'H1':5.5,'H2':5.5,'FPC2':1}.get(ref,h)
    if ref=='USB1':x0,x1,y0,y1=130.949,140.021,121.349,126.921
    if ref=='CN1':x0,x1,y0,y1=109.365,115.845,113.17,127.31
    if ref=='FPC2':x0,x1,y0,y1=138.148,141.348,65.450,73.350
    z=7.1-h if f['side']=='top' else 8.1
    shapes.append(Part.makeBox(x1-x0,y1-y0,h,V(x0-99,y0-49,z)))
Part.makeCompound(shapes).exportBrep(str(DEST/'source-ComponentEnvelopes.brep'))
data={'pcb_source_sha256':hashlib.sha256((P/'hardware.kicad_pcb').read_bytes()).hexdigest(),'layout_data_sha256':hashlib.sha256((P/'output/layout-data.json').read_bytes()).hexdigest(),'note':'Actual new PCB46x76R10 with screw-boss notches. Most component heights assumed; FPC2 height1.0 verified by JUSHUO drawing.'}
(DEST/'source-manifest.json').write_text(json.dumps(data,indent=2),encoding='utf8')
print('NEW_MECHANICAL_SOURCE_FROZEN')
