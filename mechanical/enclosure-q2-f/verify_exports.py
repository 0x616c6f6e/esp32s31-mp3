"""Read back deliverables and check saved dimensions, STL integrity and hashes."""
from pathlib import Path
import FreeCAD as App,Part,Mesh,json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent
doc=App.openDocument(str(HERE/'ESP32S31_MP3_Q2_F.FCStd'))
report=json.loads((HERE/'exports/validation.json').read_text(encoding='utf8'))
assert report['new_geometry_pass'] and report['entire_current_hardware_fits']
assert hashlib.sha256((ROOT/'hardware-q2-placement/hardware.kicad_pcb').read_bytes()).hexdigest()==report['pcb_source_sha256']
shell=doc.HousingWithControlPosts.Shape;lens=doc.CoverLens.Shape
b=shell.optimalBoundingBox();a=lens.optimalBoundingBox()
assert max(abs(b.XLength-50),abs(b.YLength-81.5),abs(b.YMin+1.5))<1e-6
gaps=[a.XMin-b.XMin,b.XMax-a.XMax,a.YMin-b.YMin]
assert all(abs(v-2)<1e-6 for v in gaps)
assert abs(doc.ControlBoard.Shape.BoundBox.YMin-42.3)<1e-6
assert abs(doc.Q2Wheel.Shape.Solids[0].CenterOfMass.y-59.3)<1e-6
results={}
for name,stem in [('HousingWithControlPosts','q2-f-housing'),('RearCoverWithPCBPosts','q2-f-rear-cover'),('Q2Wheel','q2-f-wheel-rocker'),('Q2CenterButton','q2-f-center-button'),('ControlBoard','control-board-mechanical')]:
    shape=doc.getObject(name).Shape;loaded=Part.Shape();loaded.read(str(HERE/'exports'/f'{stem}.step'))
    assert loaded.isValid() and len(loaded.Solids)==1
    error=abs(shape.Volume-loaded.Volume)/shape.Volume
    assert error<1e-5
    item={'step_valid':True,'step_relative_volume_error':error}
    if name!='ControlBoard':
        mesh=Mesh.Mesh(str(HERE/'exports'/f'{stem}.stl'));assert mesh.isSolid()
        item['stl_closed']=True
    results[stem]=item
results['saved_cover_border_left_right_top_mm']=gaps
results['pcb_unchanged']=True
results['files_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/'exports').iterdir() if p.suffix in ['.step','.stl','.dxf','.csv']}
(HERE/'exports/export-verification.json').write_text(json.dumps(results,indent=2),encoding='utf8')
print('F_EXPORTS_VERIFIED',json.dumps({k:v for k,v in results.items() if k!='files_sha256'}))
