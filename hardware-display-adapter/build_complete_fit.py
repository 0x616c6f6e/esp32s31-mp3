"""Assembly-review copy with routed adapter component envelopes and folded flex."""
from pathlib import Path
import FreeCAD as A,Part,json,hashlib
from folded_route import build
R=Path(__file__).resolve().parent;O=R/'am213-fpc-adapter';OUT=O/'output';V=A.Vector
source=R.parent/'mechanical/enclosure-final-l/Q2_L_AM213_Adapter_Study.FCStd';sha=hashlib.sha256(source.read_bytes()).hexdigest()
d=A.openDocument(str(source));original=[o for o in d.Objects if hasattr(o,'Shape') and not hasattr(o,'Group') and not o.Shape.isNull()]
group=d.addObject('App::DocumentObjectGroup','CompletedDisplayAdapter')
def add(name,shape,label):
    assert shape.isValid() and shape.Volume>0,name
    o=d.addObject('PartDesign::Feature',name);o.Shape=shape;o.Label=label;group.addObject(o);return o
island=add('AdapterSubstrate',Part.makeBox(17,22,.12,V(29,8,9.98)),'Adapter / 17x22 mm flex component island')
stiff=add('AdapterStiffener',Part.makeBox(17,22,.48,V(29,8,9.5)),'FR4 stiffener + adhesive budget / 0.48 mm')
tail,meta=build()
pts=[V(27,17.1005,9.98),V(29,16.1005,9.98),V(29,24.7005,9.98),V(27,23.7005,9.98)]
flare=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,.12))
tail=tail.fuse(flare)
flex=add('AdapterFoldedFlex',tail,'70 mm folded flex / R0.8 candidate / do not crease')
# Keep the entire 3.5 mm reinforcement on the straight final approach.
tip_stiff=add('AdapterTipStiffener',Part.makeBox(3.5,6.6,.08,V(8.352,17.1005,3.56)),'Insertion stiffener + adhesive / finished 0.20 mm tip')
meta['tip_stiffener_straight_length_mm']=12.2-8.352
meta['tip_required_stiffener_length_mm']=3.5
assert meta['tip_stiffener_straight_length_mm']>=3.5
components=[]
data=json.loads((OUT/'design.json').read_text(encoding='utf8'))
for c in data['components']:
    if c['ref'] in ['J1','TP1'] or c['dnp']:continue
    model='OK-23GF024-04' if c['ref']=='J2' else c['footprint']
    sh=Part.read(str(O/'models3d'/(model+'.step')))
    sh.rotate(V(0,0,0),V(0,0,1),-c['pcb'][2]);sh.translate(V(c['pcb'][0]-21,c['pcb'][1]-42,10.1))
    obj=add('Adapter_'+c['ref'],sh,c['ref']+' / '+c['value']);components.append(obj)
maxbtb=add('AdapterBTBMax',Part.makeBox(2.79,7.52,.89,V(32-1.395,20-3.76,10.1)),'J2 maximum dimensions / verification envelope')
reserved={'DisplayAdapterPCB','DisplayAdapterConnectors'}
checks=[]
for a in [island,stiff,flex,tip_stiff]+components+[maxbtb]:
    for o in original:
        if o.Name in reserved or not a.Shape.BoundBox.intersect(o.Shape.BoundBox):continue
        volume=a.Shape.common(o.Shape).Volume
        if volume>1e-6:checks.append({'adapter_part':a.Name,'existing_part':o.Name,'volume_mm3':round(volume,6),'interpretation':'intentional connector insertion into simplified solid envelope' if o.Name=='PCB_FPC2' and a in [flex,tip_stiff] else 'REVIEW'})
meta['intersections']=checks;meta['source_sha256']=sha;meta['btb_center_boardlocal_mm']=[3,12];meta['btb_center_case_mm']=[32,20,10.1]
meta['component_heights_mm']={o.Name:round(o.Shape.BoundBox.ZLength,4) for o in components}
meta['limits']=['R0.8 bend and 0.12mm stack require flex fabricator approval','Socket cavity/contact geometry not exact; insertion face/thickness and latch clearance require physical sample','Screen-side flexible tail and mated BTB stack are not tolerance-verified','Reserve 0.48mm for island stiffener+adhesive, not a measured supplied stack']
(OUT/'folded-tail-check.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
Part.export([flex],str(OUT/'folded-tail.step'))
d.Label='Q2 L / completed AM213 adapter fit candidate'
d.recompute();d.saveAs(str(O/'models3d/Q2_L_AM213_Completed_Adapter.FCStd'))
assert hashlib.sha256(source.read_bytes()).hexdigest()==sha
print(json.dumps(meta,ensure_ascii=False,indent=2))
