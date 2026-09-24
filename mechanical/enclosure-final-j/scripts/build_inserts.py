"""Convert only the two rear-cover fastenings to cold-glued M1.6 inserts.

All dimensions in mm. Insert geometry is an envelope, not a thread/knurl model.
The 2.70 mm bore is a glue-fit design, NOT the vendor's heat-set pilot size.
"""
from pathlib import Path
import FreeCAD as A, Part, json, hashlib

O = Path(__file__).resolve().parents[1]
R = O.parents[1]
I = O.parent / 'enclosure-final-i'
V = A.Vector
for v in json.loads((O/'source.json').read_text()).values():
    assert hashlib.sha256((R/v['path']).read_bytes()).hexdigest() == v['sha256']
d = A.openDocument(str(I/'Q2_I_Serviceable_Assembly.FCStd'))
d.Label = 'Q2 J / rear-cover glue-in M1.6 inserts'
s = d.HousingControlsA.Shape.copy()

def cyl(x, y, z, r, h):
    return Part.makeCylinder(r, h, V(x,y,z))

inserts = []
for y in (3.0, 77.0):
    # Boss rear end is Z=1.2. 3.2-deep socket, 0.15 entry chamfer.
    s = s.cut(cyl(25,y,1.19,1.35,3.21))
    s = s.cut(Part.makeCone(1.50,1.35,.15,V(25,y,1.2)))
    # Screw tip must pass beyond the insert without biting the old resin pilot.
    s = s.cut(cyl(25,y,1.19,.9,6.01))
    # Flush-to-shoulder placement; end recessed 0.2 from the boss rear face.
    n = d.addObject('PartDesign::Feature', 'RearInsertTop' if y==3 else 'RearInsertBottom')
    n.Label = 'M1.6 x 3 / OD2.5 / glue-in / ' + ('top' if y==3 else 'bottom')
    n.Shape = cyl(25,y,1.4,1.25,3).cut(cyl(25,y,1.3,.8,3.2))
    n.addProperty('App::PropertyString','Specification').Specification = 'M1.6x0.35; OD 2.5; length 3.0; headless knurled brass; envelope only'
    d.AssemblyReferences.addObject(n)
    inserts.append(n)
d.HousingControlsA.Shape = s.removeSplitter()
assert s.isValid() and len(s.Solids)==1

# Separate, optional glue-fit coupon. A corner notch identifies the small-hole end.
g=d.addObject('App::DocumentObjectGroup','ManufacturingAids')
c=d.addObject('PartDesign::Feature','InsertFitCoupon')
c.Label='Optional fit coupon / notch end 2.65, middle 2.70, far end 2.75'
q=Part.makeBox(24,8,5,V(60,0,0)).cut(Part.makeBox(1,1,6,V(60,0,-.5)))
for x,diam in [(64,2.65),(72,2.70),(80,2.75)]:
    q=q.cut(cyl(x,4,1.8,diam/2,3.3))
    q=q.cut(cyl(x,4,.8,.9,4.3))
    q=q.cut(Part.makeCone(diam/2,diam/2+.15,.15,V(x,4,4.85)))
c.Shape=q.removeSplitter();g.addObject(c)
assert c.Shape.isValid() and len(c.Shape.Solids)==1

p=json.loads((I/'parameters.json').read_text())
p.update(revision='J',rear_cover_inserts='2 x M1.6x0.35, OD2.5 x L3.0 mm, headless knurled brass, cold glued',
    rear_insert_example='In-saiL MT-M1.6x3.0-OD2.5; verify actual widest OD and length before gluing',
    rear_insert_centers_mm=[[25,3],[25,77]],rear_insert_bore_diameter_mm=2.70,
    rear_insert_bore_depth_mm=3.20,rear_insert_radial_glue_gap_mm=.10,
    rear_insert_recess_mm=.20,rear_insert_bore_entry_chamfer_mm=.15,
    rear_insert_body_min_wall_mm=1.05,rear_insert_entry_min_wall_mm=.90,
    rear_insert_axial_span_mm=[1.4,4.4],rear_screw_clearance_diameter_mm=1.8,
    rear_screw_clearance_end_z_mm=7.2,rear_screw_tip_z_mm=6.65,
    rear_screw_tip_clearance_mm=.55,rear_insert_thread_overlap_envelope_mm=3.0,
    rear_insert_installation='Cold glue after full resin post-cure; seat to shoulder without force; no heat-setting. Fit and glue strength require physical tests.',
    insert_coupon_holes_mm=[2.65,2.70,2.75])
(O/'parameters.json').write_text(json.dumps(p,indent=2),encoding='utf-8')
for i,(k,v) in enumerate(p.items(),1):
    d.DesignParameters.set('A'+str(i),k);d.DesignParameters.set('B'+str(i),str(v))
d.recompute();d.saveAs(str(O/'Q2_J_Glue_Insert_Assembly.FCStd'))
(O/'optimization.json').write_text(json.dumps({
    'source':'../enclosure-final-i/Q2_I_Serviceable_Assembly.FCStd',
    'modified_printed_parts':['HousingControlsA'],
    'new_hardware':[n.Name for n in inserts],
    'unchanged_parts':['RearCoverWithPCBPosts','WheelControlsA','CenterButtonControlsA'],
    'optional_manufacturing_aid':'InsertFitCoupon',
    'method':'Material removed for cold-glue sockets; case envelope, PCB positions and other hardware retained',
    'glue_joint_strength_tested':False,
    'references':['https://www.ppmcn.com/mini-tech-inserts/','https://formlabs.com/blog/adding-screw-threads-3d-printed-parts/']
},indent=2),encoding='utf-8')
print('J_SAVED',flush=True)
