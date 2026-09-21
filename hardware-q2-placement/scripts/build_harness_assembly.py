"""FreeCAD headless: updated PCB + E enclosure + proposed motor and harness.

All new geometry is a planning envelope. Does not overwrite revision E.
Run after KiCad STEP export. Coordinates are enclosure coordinates in mm.
"""
from pathlib import Path
import runpy,json,math
import FreeCAD as App,Part
P=Path(__file__).resolve().parents[1];ROOT=P.parent
c=runpy.run_path(str(P/'scripts/check_mechanical.py'))
parts=c['parts'];obstacles=c['obstacles'];enclosure=c['enclosure']
out=ROOT/'mechanical/connector-layout';out.mkdir(exist_ok=True)
doc=App.newDocument('Q2_Connector_Layout')
def add(name,shape,note=''):
    obj=doc.addObject('PartDesign::Feature',name);obj.Shape=shape
    obj.addProperty('App::PropertyString','PlanningNote');obj.PlanningNote=note
    return obj
for name,shape in obstacles.items():add(name,shape,'Copied reference-E geometry; battery is a reserved envelope, not a selected pack.')
for ref,shape in parts.items():add('PCB_'+ref,shape,'Current unrouted hardware-q2-placement')
# STEP board body retains its native absolute frame; KiCad surface convention
# is normalized only for component placement by check_mechanical.py.
board=next(o for o in c['assembly'].OutList if hasattr(o,'Shape') and o.Label in c['unmatched'])
shape=board.Shape.copy();shape.rotate(App.Vector(),App.Vector(0,0,1),180)
shape.translate(App.Vector(149,-49,-shape.BoundBox.ZMin))
matrix=App.Matrix();matrix.A33=1/shape.BoundBox.ZLength
shape=shape.transformGeometry(matrix);shape.translate(App.Vector(0,0,4.2))
add('MainPCB',shape,'Nominal back surface Z=4.2; front component plane Z=5.2.')
center=(39,57);base=7.1
motor=Part.makeCylinder(4,3.3,App.Vector(*center,base))
motor_max=Part.makeCylinder(4.05,3.45,App.Vector(*center,base))
add('Motor_C08_005',motor,'Candidate PMD C08-005; diameter 8 +/-0.1, height 3.3 +/-0.15; 1.8 Vrms LRA. Datasheet revision 004.')
floor=Part.makeCylinder(4.6,.3,App.Vector(*center,6.7))
ring=Part.makeCylinder(4.6,1.1,App.Vector(*center,7)).cut(Part.makeCylinder(4.15,1.2,App.Vector(*center,7)))
ring=ring.cut(Part.makeBox(2,2,1.2,App.Vector(34,56,7)))
web=Part.makeBox(6.0,1.6,1.1,App.Vector(43,56.2,7))
holder=floor.fuse(ring).fuse(web).removeSplitter()
add('MotorHolderProposal',holder,'Side-wall attached candidate seat; 0.1 mm adhesive above floor. Manufacturing/strength not validated.')
add('MotorAdhesive',Part.makeCylinder(3.9,.1,App.Vector(*center,7)),'0.1 mm adhesive assumption; prototype validation required.')
def cable(points,radius):
    vv=[App.Vector(*p) for p in points];sh=[]
    for a,b in zip(vv,vv[1:]):
        delta=b-a;sh.append(Part.makeCylinder(radius,delta.Length,a,delta))
    sh.extend(Part.makeSphere(radius,a) for a in vv[1:-1])
    result=sh[0]
    for s in sh[1:]:result=result.fuse(s)
    return result
routes={};route_points={}
for i,dy in enumerate([-.6,.6]):
    points=[(21.3,64+dy,6.0),(22.8,64+dy,7.15),(31+i*.7,64+dy,7.15),(31+i*.7,60.5+dy,7.15),(32.9+i*.7,60.5+dy,7.15),(33.5+i*.7,60.5+dy,8.1),(33.5+i*.7,57+dy,8.1),(35.05,57+dy,8.1)]
    name=f'MotorWire{i+1}';routes[name]=cable(points,.25);route_points[name]=points
for i,dy in enumerate([-1.2,0,1.2]):
    xx=10.5+i*.85
    points=[(9.3,60+dy,6.0),(xx,60+dy,7.15),(xx,36.4,7.15),(xx,36.4,9.0),(xx,37,9.0)]
    name=f'BatteryWire{i+1}';routes[name]=cable(points,.315);route_points[name]=points
for name,shape in routes.items():add(name,shape,'Concept wire corridor; rounded bends, slack and cable strain relief require prototype confirmation.')
newshapes={'MotorMaximumEnvelope':motor_max,'MotorHolderProposal':holder,**routes}
conflicts=[];clearances=[]
for name,shape in newshapes.items():
    for other,solid in {**parts,**obstacles}.items():
        # Intended connections: motor carrier touches side wall; wire starts at
        # its mated connector and battery lead ends at the pack envelope.
        if name=='MotorHolderProposal' and other=='HousingWithControlPosts':continue
        if name.startswith('MotorWire') and other=='H1':continue
        if name.startswith('BatteryWire') and other in ['H2','BatteryReference']:continue
        if c['bb_overlap'](shape,solid):
            vol=shape.common(solid).Volume
            if vol>1e-5:conflicts.append({'part':name,'against':other,'volume_mm3':round(vol,6)})
    if name in ['MotorMaximumEnvelope','MotorHolderProposal']:
        for other in ['BatteryReference','ControlBoard','ControlBoardFasteners','ControlFPCRoute','DisplayFPCRoute']:
            clearances.append({'part':name,'against':other,'nominal_mm':round(shape.distToShape(obstacles[other])[0],4)})
for name,wire in routes.items():
    vol=wire.common(holder).Volume
    if vol>1e-5:conflicts.append({'part':name,'against':'MotorHolderProposal','volume_mm3':round(vol,6)})
for i,(name,wire) in enumerate(routes.items()):
    for other,shape in list(routes.items())[i+1:]:
        vol=wire.common(shape).Volume
        if vol>1e-5:conflicts.append({'part':name,'against':other,'volume_mm3':round(vol,6)})
doc.recompute();doc.saveAs(str(out/'Q2_Connector_Layout.FCStd'))
report={'pcb_sha256':c['report']['pcb_sha256'],'base_component_check_pass':c['report']['pass'],'new_geometry_conflicts':conflicts,'pass':c['report']['pass'] and not conflicts,'motor_center_case_xy_mm':center,'motor_base_z_mm':base,'motor_maximum_diameter_height_mm':[8.1,3.45],'battery_reservation_case_xyz_mm':[8.3,37,7.8,24,34,3],'clearances':clearances,'wire_centerlines_case_mm':route_points,'scope':'Planning model only. JST bodies are conservative mated envelopes. Excludes real cable bend limits, insertion tooling, manufacturing tolerance stack and cell expansion qualification. Motor holder attachment to wall is intentional. Battery model is not a purchasing specification.'}
report['source_enclosure_sha256']=c['report']['source_enclosure_sha256']
report['populated_step_sha256']=c['report']['populated_step_sha256']
(out/'fit-check.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('HARNESS_ASSEMBLY',json.dumps(report))
