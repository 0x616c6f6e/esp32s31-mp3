from pathlib import Path
import FreeCAD as A, Part, json
O=Path(__file__).resolve().parents[1];V=A.Vector
d=A.openDocument(str(O/'Q2_J_Glue_Insert_Assembly.FCStd'))
i=A.openDocument(str(O.parent/'enclosure-final-i/Q2_I_Serviceable_Assembly.FCStd'))
s=d.HousingControlsA.Shape
def cyl(x,y,z,r,h):return Part.makeCylinder(r,h,V(x,y,z))
checks=[]
for y in [3.,77.]:
    # Continuous axial insertion of the maximum OD envelope, before electronics.
    sweep=cyl(25,y,-3,1.25,7.4)
    passage=cyl(25,y,1.2,.8,5.45)
    wall=cyl(25,y,1.35,2.4,3.05).cut(cyl(25,y,1.34,1.35,3.07))
    floor=cyl(25,y,4.4,1.35,.1).cut(cyl(25,y,4.39,.9,.12))
    row={'center_mm':[25,y],'continuous_insert_sweep_collision_mm3':s.common(sweep).Volume,
         'screw_passage_collision_mm3':s.common(passage).Volume,
         'straight_socket_wall_missing_mm3':wall.cut(s).Volume,
         'seating_shoulder_missing_mm3':floor.cut(s).Volume}
    assert max(row[k] for k in row if k.endswith('mm3'))<1e-5,row
    checks.append(row)
unchanged={}
def center(shape):
    return sum((solid.CenterOfMass*solid.Volume for solid in shape.Solids),V())/sum(solid.Volume for solid in shape.Solids)
for name in ['RearCoverWithPCBPosts','WheelControlsA','CenterButtonControlsA','MainPCB','ControlsBoard','RearCoverFasteners']:
    a=d.getObject(name).Shape;b=i.getObject(name).Shape
    error=max(abs(a.Volume-b.Volume),abs(a.Area-b.Area),(center(a)-center(b)).Length)
    assert error<1e-7,(name,error)
    if name in ['RearCoverWithPCBPosts','WheelControlsA','CenterButtonControlsA']:
        assert a.cut(b).Volume+b.cut(a).Volume<1e-5
    unchanged[name]={'volume_area_centroid_equal':True,'boolean_equal_checked':name in ['RearCoverWithPCBPosts','WheelControlsA','CenterButtonControlsA']}
added=s.cut(i.HousingControlsA.Shape).Volume
assert added<1e-5
report={'socket_checks':checks,'unchanged_geometry':unchanged,'housing_material_added_mm3':added,
        'rear_fastener_original_geometry_retained':True,'nominal_screw_tip_clearance_mm':.55,
        'nominal_radial_glue_gap_mm':.10,'glue_joint_pullout_and_torque_tested':False,
        'insertion_method':'Continuous maximum-OD axial cylinder swept from rear with cover and electronics removed; no tooling/gripper simulation'}
(O/'insert-check.json').write_text(json.dumps(report,indent=2))
print('INSERT_CHECK',json.dumps(report),flush=True)
