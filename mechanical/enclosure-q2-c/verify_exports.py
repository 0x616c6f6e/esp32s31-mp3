import FreeCAD as App, Part, Mesh, json
from pathlib import Path
HERE=Path(__file__).resolve().parent;OUT=HERE/'exports'
def main():
    if any(d.FileName and Path(d.FileName).parent.resolve()==HERE for d in App.listDocuments().values()):raise RuntimeError('Save and close revision C before verification.')
    d=App.openDocument(str(HERE/'ESP32S31_MP3_Q2_C.FCStd'))
    result={'exports':{},'orientation':{},'parameter_recompute':{}}
    for name,stem in [('HousingWithControlPosts','q2-c-housing'),('Q2RearCover','q2-c-rear-cover'),('Q2Wheel','q2-c-wheel-rocker'),('Q2CenterButton','q2-c-center-button'),('ControlBoard','control-board-mechanical')]:
        s=Part.Shape();s.read(str(OUT/(stem+'.step')));delta=abs(s.Volume-d.getObject(name).Shape.Volume)
        assert s.isValid() and len(s.Solids)==1 and delta<.01,stem
        result['exports'][stem]={'step_valid':True,'single_solid':True,'volume_delta_mm3':delta}
        if name!='ControlBoard':
            m=Mesh.Mesh(str(OUT/(stem+'.stl')));assert m.isSolid();result['exports'][stem]['stl_watertight']=True
    bb=d.ControlBoard.Shape.BoundBox
    assert all(abs(a-b)<1e-6 for a,b in zip([bb.XLength,bb.YLength,bb.ZLength],[44,34,.8]))
    assert d.ESP32Front.Shape.BoundBox.ZMin>=5.2-1e-6
    assert d.ScreenConnectorFPC2.Shape.BoundBox.ZMax<=4.2+1e-6
    assert abs(d.DisplayFPCRoute.NeutralRouteLength.Value-46.14)<1e-6
    result['orientation']={'ESP32_min_z':d.ESP32Front.Shape.BoundBox.ZMin,'FPC2_max_z':d.ScreenConnectorFPC2.Shape.BoundBox.ZMax,'main_pcb_bounds_z':[d.MainPCB.Shape.BoundBox.ZMin,d.MainPCB.Shape.BoundBox.ZMax],'control_board_mm':[bb.XLength,bb.YLength,bb.ZLength]}
    cell=d.Parameters.getCellFromAlias('ControlBoardWidth');old=d.Parameters.get(cell)
    d.Parameters.set(cell,'44.4');d.recompute();assert abs(d.ControlBoard.Shape.BoundBox.XLength-44.4)<1e-6 and d.ControlBoard.Shape.isValid()
    d.Parameters.set(cell,str(old));d.recompute();assert abs(d.ControlBoard.Shape.BoundBox.XLength-44)<1e-6
    result['parameter_recompute']['control_width_44_to_44.4_and_restore']=True
    App.closeDocument(d.Name)
    # Reimport the DXF using FreeCAD's consumer, rather than trusting text generation.
    import importDXF
    dx=App.newDocument('ControlDXFVerification');importDXF.insert(str(OUT/'control-board-outline.dxf'),dx.Name);dx.recompute()
    shapes=[o.Shape for o in dx.Objects if hasattr(o,'Shape') and not o.Shape.isNull()]
    assert shapes,'DXF import yielded no geometry'
    bb=Part.makeCompound(shapes).BoundBox
    assert abs(bb.XLength-44)<1e-5 and abs(bb.YLength-34)<1e-5
    result['dxf_import_mm']=[bb.XLength,bb.YLength]
    App.closeDocument(dx.Name)
    (OUT/'export-verification.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print('C_EXPORT_VERIFIED',json.dumps(result))
if __name__=='__main__':main()
