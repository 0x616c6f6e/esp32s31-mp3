import FreeCAD as App, Part, Mesh, json, hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;OUT=HERE/'exports'
d=App.openDocument(str(HERE/'ESP32S31_MP3_Q2_D.FCStd'))
r={'screen_shift_up_mm':1.5,'exports':{},'current_board_fits':False}
assert abs(d.LCDModule.Shape.BoundBox.YMin-2.235)<1e-6
assert abs(d.CoverLens.Shape.BoundBox.YMin-.5)<1e-6
assert abs(d.ScreenConnectorFPC2.Shape.BoundBox.ZLength-1)<1e-6
for name,stem in [('HousingWithControlPosts','q2-d-housing'),('Q2RearCover','q2-d-rear-cover'),('Q2Wheel','q2-d-wheel-rocker'),('Q2CenterButton','q2-d-center-button')]:
    s=Part.Shape();s.read(str(OUT/(stem+'.step')));m=Mesh.Mesh(str(OUT/(stem+'.stl')))
    assert s.isValid() and len(s.Solids)==1 and m.isSolid()
    assert abs(s.Volume-d.getObject(name).Shape.Volume)<.01
    r['exports'][stem]={'step_valid':True,'stl_watertight':True}
pcbpath=HERE.parents[1]/'hardware/hardware.kicad_pcb'
sha=hashlib.sha256(pcbpath.read_bytes()).hexdigest()
assert sha=='60deebc60149e9abd5f80077752135f7d0ae33c0fbd682f53f78e2fe683c044c'
r['PCB_unchanged']=True
bb=d.HousingWithControlPosts.Shape.optimalBoundingBox(False,False)
assert abs(bb.XLength-50)<1e-5 and abs(bb.YLength-80)<1e-5
r['body_mm']=[bb.XLength,bb.YLength,13.5]
r['screen_socket_axis_offset_mm']=2.366
assert d.MainPCB.Shape.common(d.HousingWithControlPosts.Shape).Volume>1
(OUT/'export-verification.json').write_text(json.dumps(r,indent=2),encoding='utf8')
print('D_VERIFICATION_COMPLETE',json.dumps(r))
