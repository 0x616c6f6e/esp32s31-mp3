"""FreeCAD headless: reimport exports, check dimensions and parameter recomputation."""
import FreeCAD as App, Part, Mesh, json
from pathlib import Path
HERE=Path(__file__).resolve().parent;OUT=HERE/'exports'
def main():
    if any(d.FileName and Path(d.FileName).parent.resolve()==HERE for d in App.listDocuments().values()):
        raise RuntimeError('Save and close the Q2/LCD documents before running verification; no open document will be changed.')
    d=App.openDocument(str(HERE/'ESP32S31_MP3_Q2_B.FCStd'))
    result={'export_checks':{},'parameter_recompute':{}}
    for name,stem in [('Q2Housing','q2-housing'),('Q2RearCover','q2-rear-cover'),('Q2Wheel','q2-wheel-face'),('Q2CenterButton','q2-center-button')]:
        s=Part.Shape();s.read(str(OUT/(stem+'.step')))
        m=Mesh.Mesh(str(OUT/(stem+'.stl')))
        source=d.getObject(name).Shape
        check={'step_valid':s.isValid(),'step_solids':len(s.Solids),'volume_error_mm3':abs(s.Volume-source.Volume),'stl_watertight':m.isSolid()}
        assert check['step_valid'] and check['step_solids']==1 and check['volume_error_mm3']<.01 and check['stl_watertight'],stem
        result['export_checks'][stem]=check
    old=d.Q2Housing.Shape.Volume
    cell=d.Parameters.getCellFromAlias('LCDFitClearance');original=d.Parameters.get(cell)
    d.Parameters.set(cell,'0.4');d.recompute()
    assert d.Q2Housing.Shape.isValid() and d.Q2Housing.Shape.Volume<old
    d.Parameters.set(cell,str(original));d.recompute()
    assert abs(d.Q2Housing.Shape.Volume-old)<1e-5
    result['parameter_recompute']['housing_clearance_0.3_to_0.4_and_restore']=True
    App.closeDocument(d.Name)
    d=App.openDocument(str(HERE/'LCD209_36x43.FCStd'))
    cell=d.Parameters.getCellFromAlias('LCDThickness');original=d.Parameters.get(cell)
    d.Parameters.set(cell,'1.51');d.recompute()
    assert abs(d.LCDGlass.Shape.BoundBox.ZMax-1.51)<1e-6
    d.Parameters.set(cell,str(original));d.recompute()
    result['parameter_recompute']['lcd_thickness_1.46_to_1.51_and_restore']=True
    s=Part.Shape();s.read(str(OUT/'lcd209-module-only.step'));bb=s.BoundBox
    result['lcd_module_step_mm']=[bb.XLength,bb.YLength,bb.ZLength]
    assert all(abs(a-b)<1e-6 for a,b in zip(result['lcd_module_step_mm'],[36.33,43.45,1.46]))
    result['native_documents_saved_during_verification']=False
    App.closeDocument(d.Name)
    (OUT/'export-verification.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print('Q2_EXPORT_VERIFIED',json.dumps(result))
if __name__=='__main__':main()
