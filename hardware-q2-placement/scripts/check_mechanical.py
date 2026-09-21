"""Check new native STEP components against saved revision-E enclosure geometry.

Uses nominal front/back mounting planes independently: the KiCad STEP exporter
surface offsets include copper thickness, whereas enclosure stack is nominal1mm.
This is nominal interference checking; some model dimensions remain assumptions.
"""
import FreeCAD as App,Part,Import,json,math,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parent
data=json.loads((P/'output/placement.json').read_text(encoding='utf8'));fps={f['reference']:f for f in data['footprints'] if not f['reference'].startswith('SCREW')}
doc=App.newDocument('NewPlacementSTEP');Import.insert(str(P/'output/placement-populated.step'),doc.Name)
assembly=next(o for o in doc.Objects if o.Label=='placement-populated 1')
enclosure_path=ROOT/'mechanical/enclosure-q2-e/ESP32S31_MP3_Q2_E.FCStd'
enclosure_hash_before=hashlib.sha256(enclosure_path.read_bytes()).hexdigest()
enclosure=App.openDocument(str(enclosure_path))
names=['HousingWithControlPosts','RearCoverWithPCBPosts','BatteryReference','ControlBoard','DisplayFPCRoute','ControlFPCRoute','MainControlFPCReserve','ControlFPCConnector']
obstacles={n:enclosure.getObject(n).Shape for n in names}
obstacles.update({o.Name:o.Shape for o in enclosure.Objects if o.Name in ['LCDModule','LCD','DisplayModule','ControlBoardFasteners']})
parts={};unmatched=[]
for o in assembly.OutList:
    if not hasattr(o,'Shape') or o.Shape.isNull() or o.Shape.Volume<1e-8:continue
    base=o.Placement.Base
    ref=min(fps,key=lambda r:math.hypot(fps[r]['xy'][0]-base.x,fps[r]['xy'][1]+base.y))
    if math.hypot(fps[ref]['xy'][0]-base.x,fps[ref]['xy'][1]+base.y)>.005:
        unmatched.append(o.Label);continue # Board body only.
    assert ref not in parts,ref
    shape=o.Shape.copy();shape.rotate(App.Vector(),App.Vector(0,0,1),180)
    mounting_z=5.2 if fps[ref]['side']=='F' else 4.2
    shape.translate(App.Vector(149,-49,mounting_z-base.z));parts[ref]=shape
assert set(parts)==set(fps),(set(fps)-set(parts),len(parts))
def bb_overlap(a,b):
    aa=a.BoundBox;bb=b.BoundBox
    return aa.XMin<bb.XMax and aa.XMax>bb.XMin and aa.YMin<bb.YMax and aa.YMax>bb.YMin and aa.ZMin<bb.ZMax and aa.ZMax>bb.ZMin
conflicts=[]
for ref,shape in parts.items():
    for name,other in obstacles.items():
        if ref=='FPC2' and name=='DisplayFPCRoute':continue
        if not bb_overlap(shape,other):continue
        vol=shape.common(other).Volume
        if vol>1e-5:conflicts.append({'reference':ref,'against':name,'volume_mm3':round(vol,6)})
mutual=[];refs=list(parts)
for i,r in enumerate(refs):
    for q in refs[i+1:]:
        if not bb_overlap(parts[r],parts[q]):continue
        vol=parts[r].common(parts[q]).Volume
        if vol>1e-5:mutual.append({'references':[r,q],'volume_mm3':round(vol,6)})
report={'source_enclosure':'mechanical/enclosure-q2-e/ESP32S31_MP3_Q2_E.FCStd','source_enclosure_sha256':hashlib.sha256((ROOT/'mechanical/enclosure-q2-e/ESP32S31_MP3_Q2_E.FCStd').read_bytes()).hexdigest(),'pcb_sha256':hashlib.sha256((P/'hardware.kicad_pcb').read_bytes()).hexdigest(),'checked_component_instances':len(parts),'obstacles':list(obstacles),'nominal_mount_planes_case_z_mm':{'F':5.2,'B':4.2},'component_vs_enclosure_conflicts':conflicts,'component_vs_component_conflicts':mutual,'pass':not conflicts and not mutual,'scope':'Nominal geometric intersections only. Model assumptions, solder/cable/battery tolerances and screen FPC insertion are unverified. Existing enclosure file not changed.'}
report['populated_step_sha256']=hashlib.sha256((P/'output/placement-populated.step').read_bytes()).hexdigest()
assert report['source_enclosure_sha256']==enclosure_hash_before, 'Enclosure saved during checking; rerun against a stable saved version.'
report['model_manifest_sha256']=hashlib.sha256((P/'models3d/model-manifest.json').read_bytes()).hexdigest()
(P/'output/mechanical-check.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('MECHANICAL_CHECK',json.dumps(report))
