import FreeCAD as App,Part,Mesh,json
from pathlib import Path

def main():
    here=Path(__file__).resolve().parent
    doc=App.openDocument(str(here/'ESP32S31_MP3_Enclosure_A.FCStd'))
    doc.recompute()
    results={}
    for name,stem in [('RearKeyRelief','rear-shell'),('FrontWithSwitchSupport','front-shell'),('PowerButton','power-button')]:
        s=Part.Shape();s.read(str(here/'exports'/ (stem+'.step')))
        m=Mesh.Mesh(str(here/'exports'/ (stem+'.stl')))
        expected=doc.getObject(name).Shape.Volume
        assert s.isValid() and len(s.Solids)==1 and m.isSolid(),stem
        assert abs(s.Volume-expected)<.001,(stem,s.Volume,expected)
        results[stem]={'step_valid':s.isValid(),'step_solids':len(s.Solids),'stl_closed':m.isSolid(),'stl_facets':m.CountFacets,'step_volume_mm3':s.Volume}
    before=doc.RearKeyRelief.Shape.Volume
    cell=doc.Parameters.getCellFromAlias('Wall');old=doc.Parameters.get(cell)
    doc.Parameters.set(cell,'0.80');doc.recompute()
    after=doc.RearKeyRelief.Shape.Volume
    assert doc.RearKeyRelief.Shape.isValid() and after>before+1
    doc.Parameters.set(cell,str(old));doc.recompute()
    assert abs(doc.RearKeyRelief.Shape.Volume-before)<.001
    results['native_parameter_recompute']={'passed':True,'parameter':'Wall','from_mm':.75,'to_mm':.80,'volume_before_mm3':before,'volume_changed_mm3':after,'restored':True,'source_document_saved':False}
    (here/'exports/export-validation.json').write_text(json.dumps(results,indent=2),encoding='utf8')
    print('EXPORT_VALIDATION_PASSED',json.dumps(results))
    App.closeDocument(doc.Name)

if __name__ == '__main__':
    main()
