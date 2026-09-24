"""Position study only; retain the produced PCB and L enclosure unchanged."""
from pathlib import Path
import FreeCAD as A,Part,json,hashlib
O=Path(__file__).resolve().parent;R=O.parents[1];V=A.Vector
source=R/'mechanical/enclosure-final-l/Q2_L_AM213_Adapter_Study.FCStd'
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
d=A.openDocument(str(source));existing=[o for o in d.Objects if hasattr(o,'Shape') and not hasattr(o,'Group') and not o.Shape.isNull()]
group=d.addObject('App::DocumentObjectGroup','V2BTBPlacementStudy')
def add(n,sh,label):
    assert sh.isValid();o=d.addObject('PartDesign::Feature',n);o.Shape=sh;o.Label=label;group.addObject(o);return o
shape=Part.read(str(R/'hardware-display-adapter/am213-fpc-adapter/models3d/OK-23GF024-04.step'))
shape.rotate(V(),V(0,0,1),90);shape.translate(V(18,31.2,5.8))
socket=add('V2DisplayBTB',shape,'V2 candidate / OK-23GF024-04 / mainboard FRONT / NOT frozen')
envelope=add('V2BTBMaxEnvelope',Part.makeBox(7.52,2.79,.89,V(14.24,29.805,5.8)),'Socket maximum dimensions / excludes solder and mated screen tail')
access=add('V2BTBAccessReservation',Part.makeBox(11,6,1.7,V(12.5,28.2,5.8)),'11x6 placement & access reservation / engineering allowance')
old=Part.makeBox(2.79,7.52,.89,V(32-1.395,20-3.76,5.8))
def collisions(sh,exclude):
    a=[]
    for o in existing:
        if o.Name in exclude or not sh.BoundBox.intersect(o.Shape.BoundBox):continue
        v=sh.common(o.Shape).Volume
        if v>1e-6:a.append({'object':o.Name,'label':o.Label,'intersection_mm3':round(v,6)})
    return a
old_hits=collisions(old,set())
candidate_all=collisions(envelope.Shape,set())
candidate_hits=collisions(envelope.Shape,{'PCB_U9'})
access_hits=collisions(access.Shape,{'PCB_U9'})
assert not candidate_hits,candidate_hits
assert not access_hits,access_hits
report={
 'status':'CANDIDATE XY; NOT FINAL SCREEN-FPC MATING APPROVAL',
 'source_assembly':str(source.relative_to(R)),'source_sha256':source_hash,
 'pcb_datum':'KiCad Edge.Cuts centerline bounding-box upper-left (128.868,67.647); outline 46x76 mm',
 'pcb_side':'F.Cu / screen-facing side; case solder plane Z=5.8',
 'candidate_board_local_xy_mm':[30,29.2],'candidate_kicad_xy_mm':[158.868,96.847],
 'candidate_case_xyz_mm':[18,31.2,5.8],'connector_long_axis':'X',
 'candidate_footprint_angle_deg':90,'angle_status':'90 vs 270 deg must be selected by actual folded screen tail and contact numbering',
 'reference_angle90_pin1_board_local_mm':[27.8,30.4],
 'case_transform':{'x':'176.868 - pcb_x','y':'pcb_y - 65.647'},
 'screen_orientation_assumption':'Factory free tail exits toward case left, close to lower edge of landscape screen',
 'tail_centerline_y_estimate_mm':31.2,
 'tail_y_estimate_basis':'Drawing p5 rear folded view: 5.15+-0.5 edge gap and 4.00 tail width; chosen landscape orientation gives .85+37.5-(5.15+4/2). This is NOT a fully dimensioned connector placement.',
 'candidate_x_basis':'Engineering choice in area vacated by U9, clear of right-side TF socket; not a supplier-defined X datum',
 'prior_adapter_z_mm':10.1,'main_front_z_mm':5.8,'solder_plane_drop_mm':4.3,
 'candidate_max_height_mm':.89,'nominal_mated_height_mm':.8,
 'old_adapter_xy_projected_to_main_front_collisions':old_hits,
 'candidate_collisions_before_module_removal':candidate_all,
 'candidate_collisions_after_module_removal':candidate_hits,
 'access_reservation_collisions_after_module_removal':access_hits,
 'limits':['No native screen tail solid or measured free length; folding/reach and 90/270 orientation remain unverified','Old module U9 removed only for this collision assessment; bare-chip RF, crystal, power, decoupling and antenna layout not designed','Access box is an allowance, not a swept tool or latch simulation','No PCB, schematic, net or enclosure changes applied to production projects']}
(O/'position-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
d.Label='Q2 V2 / direct front BTB candidate / screen tail confirmation required'
d.recompute();d.saveAs(str(O/'Q2_V2_BTB_Position_Study.FCStd'))
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
print(json.dumps(report,ensure_ascii=False,indent=2))
