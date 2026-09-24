"""FreeCAD Python: simplified OK-23GF024-04 mechanical model and L fit study.

Outer dimensions follow OCN series drawing; internal plastic/contact details
are schematic. No electrical numbering or production land pattern is implied.
"""
from pathlib import Path
import hashlib, json
import FreeCAD as A
import Part

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'am213-fpc-adapter'/'models3d'
OUT.mkdir(exist_ok=True)
V = A.Vector
def box(x,y,z,w,l,h): return Part.makeBox(w,l,h,V(x,y,z))
def add(doc,name,shape,label=None):
    o=doc.addObject('PartDesign::Feature',name);o.Shape=shape
    if label:o.Label=label
    assert shape.isValid() and shape.Volume > 0,name
    return o
def prop(o,name,value):
    o.addProperty('App::PropertyString',name,'Model information');setattr(o,name,str(value))

d=A.newDocument('OK23GF024Mechanical')
d.Label='OK-23GF024-04 / mechanical approximation'
# Long axis Y; z=0 is the adapter top copper plane; symmetric about origin.
base=box(-1.27,-3.66,.06,2.54,7.32,.12)
rim=box(-1.27,-3.66,.18,2.54,7.32,.61).cut(box(-.97,-3.34,.18,1.94,6.68,.72))
tongue=box(-.18,-2.72,.18,.36,5.44,.53)
housing=add(d,'Housing',base.fuse(rim).fuse(tongue).removeSplitter())
prop(housing,'PartNumber','OK-23GF024-04')
prop(housing,'MeasuredDimensions','L 7.32 +/-0.20; housing W 2.54 +/-0.20; overall W 2.59 +/-0.20; H 0.79 +/-0.10 mm')
prop(housing,'Limitations','Outer envelope only dimensionally authoritative; cavity and contacts simplified; Numbering verified from OSPTEK AM213 adapter photograph; internal contacts still schematic')
contacts=[]
for side in [-1,1]:
    for i in range(12):
        y=-2.2+i*.4
        foot=box(.92 if side>0 else -1.295,y-.05,0,.375,.10,.10)
        inner=box(.24 if side>0 else -.89,y-.05,.19,.65,.10,.12)
        contacts.extend([foot,inner])
contact=add(d,'ContactsUnnumbered',Part.makeCompound(contacts),'24 contacts / schematic, not numbered')
clips=[]
for y in [-3.63,3.03]:
    for x in [-1.295,.995]:clips.append(box(x,y,0,.3,.60,.18))
clip=add(d,'HoldDowns',Part.makeCompound(clips),'Retention clips / simplified')
nom=Part.makeCompound([housing.Shape,contact.Shape,clip.Shape])
maxenv=add(d,'MaximumEnvelope',box(-1.395,-3.76,0,2.79,7.52,.89),'Maximum dimensional envelope / not physical solid')
prop(maxenv,'Scope','Connector tolerances only; excludes solder, FPC stack and enclosure tolerances')
d.recompute();d.saveAs(str(OUT/'OK-23GF024-04.FCStd'))
Part.export([housing,contact,clip],str(OUT/'OK-23GF024-04.step'))
loaded=Part.read(str(OUT/'OK-23GF024-04.step'))
assert loaded.isValid()
assert abs(loaded.BoundBox.XLength-2.59)<1e-6
assert abs(loaded.BoundBox.YLength-7.32)<1e-6
assert abs(loaded.BoundBox.ZLength-.79)<1e-6

source=ROOT.parent/'mechanical/enclosure-final-l/Q2_L_AM213_Adapter_Study.FCStd'
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
a=A.openDocument(str(source))
existing=list(a.Objects)
group=a.addObject('App::DocumentObjectGroup','BTBMechanicalReview')
for src in [housing,contact,clip,maxenv]:
    s=src.Shape.copy();s.translate(V(32,20,10.1))
    o=add(a,'BTB_'+src.Name,s,src.Label);group.addObject(o)
    prop(o,'Validation','J2 local center (3,12); long axis Y. Pin 1 upper-left in KiCad top view; insertion tolerances still require sample.')
reviewmax=a.BTB_MaximumEnvelope.Shape
results=[]
for o in existing:
    if not hasattr(o,'Shape') or o.Shape.isNull():continue
    # Only objects whose bounding boxes intersect can have volumetric collisions.
    bb=o.Shape.BoundBox
    if not bb.intersect(reviewmax.BoundBox):continue
    volume=reviewmax.common(o.Shape).Volume
    results.append({'name':o.Name,'label':o.Label,'intersection_mm3':round(volume,8),'distance_mm':round(reviewmax.distToShape(o.Shape)[0],6)})
exclude={'DisplayAdapterConnectors'} # Replaced reservation, intentional overlap.
collisions=[r for r in results if r['intersection_mm3']>1e-6 and r['name'] not in exclude]
assert not collisions,collisions
report={
 'part':'OK-23GF024-04','model':'simplified mechanical envelope; no production pads',
 'source_assembly':str(source.relative_to(ROOT.parent)), 'source_sha256':source_hash,
 'datasheet':'../reference/osptek-official/OK-23GF024-04.pdf',
 'nominal_model_bbox_mm':[2.59,7.32,.79],'maximum_envelope_mm':[2.79,7.52,.89],
 'contact_count':24,'pitch_mm':.4,
 'kicad_center_mm':[53,62],'board_local_center_mm':[3,12],
 'assembly_center_boardtop_mm':[32,20,10.1],'long_axis':'Y',
 'mating_family':'AM213 specified OK-23GM024-04 header / OK-23GF024-04 socket',
 'mating_height_nominal_mm':.8,'mating_height_note':'0.8H family designation; do not sum standalone header and socket heights; final mating tolerance not validated',
 'board_edge_clearance_nominal_mm':1.705,'board_edge_clearance_connector_max_only_mm':1.605,
 'screen_reserved_plane_z_mm':11.3,'nominal_gap_to_screen_reserve_mm':.41,'connector_max_gap_to_screen_reserve_mm':.31,
 'collisions_excluding_replaced_reservation':collisions,'intersecting_bounding_box_checks':results,
 'pin1_status':'OSPTEK AM213 adapter photograph: pin1 upper-left,12 lower-left,13 lower-right,24 upper-right (KiCad top view).',
 'limitations':['No proof of actual FPC reach/bend radius/contact side','No solder or assembly stack tolerances included','No electrical compatibility or production footprint validation']}
(OUT/'fit-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
a.Label='Q2 L / OK-23GF024-04 fit review / not production release'
a.recompute();a.saveAs(str(OUT/'Q2_L_BTB_Fit_Review.FCStd'))
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
print(json.dumps(report,ensure_ascii=False,indent=2))
