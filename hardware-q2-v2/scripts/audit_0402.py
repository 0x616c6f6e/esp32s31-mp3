"""Check every 0402 instance against the two canonical project footprints."""
from pathlib import Path
import pcbnew as p,json,math,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(P/'q2-v2.kicad_pcb'))
report=json.loads((P/'0402-standardization.json').read_text(encoding='utf8'))
contract=json.loads((P/'output/design-contract.json').read_text(encoding='utf8'))
xml=ET.parse(P/'output/v2-netlist.xml').getroot()
sch={c.attrib['ref']:c.findtext('footprint') for c in xml.find('components')}
uids=[f.m_Uuid.AsString() for f in b.GetFootprints()]+[a.m_Uuid.AsString() for f in b.GetFootprints() for a in f.Pads()]
assert len(uids)==len(set(uids)),'Duplicated instance UUID'
counts={};errors=[]
for c in report['components']:
 f=b.FindFootprintByReference(c['ref']);name=c['library_id'].split(':')[1]
 canonical=p.FootprintLoad(str(P/'V2.pretty'),name);pads={a.GetNumber():a for a in f.Pads()};std={a.GetNumber():a for a in canonical.Pads()}
 assert f.GetFPIDAsString()==c['library_id']==sch[c['ref']]
 assert contract['components'][c['ref']]['footprint']==name
 assert math.isclose(math.dist([pads['1'].GetPosition().x,pads['1'].GetPosition().y],[pads['2'].GetPosition().x,pads['2'].GetPosition().y]), math.dist([std['1'].GetPosition().x,std['1'].GetPosition().y],[std['2'].GetPosition().x,std['2'].GetPosition().y]),abs_tol=3)
 for n,a in pads.items():
  z=std[n]
  assert a.GetSize()==z.GetSize() and a.GetShape()==z.GetShape() and a.GetRoundRectRadiusRatio()==z.GetRoundRectRadiusRatio()
  assert a.GetLocalSolderMaskMargin()==z.GetLocalSolderMaskMargin() and a.GetLocalSolderPasteMargin()==z.GetLocalSolderPasteMargin()
 assert [m.m_Filename for m in f.Models()]==[m.m_Filename for m in canonical.Models()]
 counts[c['library_id']]=counts.get(c['library_id'],0)+1
 c['position_mm']=[p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y)];c['angle_deg']=f.GetOrientationDegrees()
report['verification']={'canonical_instance_counts':counts,'pad_geometry_mask_paste_models_match':True,'schematic_footprint_links_match':True,'unique_footprint_pad_uuids':True,'errors':errors}
(P/'0402-standardization.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
audit={'models':[],'missing_files':[],'without_models':[],'scope':'Nominal models; generic passives and nominal MCU/crystal bodies are not supplier tolerance verification'}
for f in b.GetFootprints():
 models=[m.m_Filename for m in f.Models()];audit['models'].append({'ref':f.GetReference(),'models':models})
 if not models:audit['without_models'].append(f.GetReference())
 for m in models:
  resolved=m.replace('${KIPRJMOD}',str(P)).replace('${KICAD10_3DMODEL_DIR}','D:/KiCad/10.0/share/kicad/3dmodels')
  if not Path(resolved).is_file():audit['missing_files'].append({'ref':f.GetReference(),'path':m})
assert not audit['missing_files']
(P/'output/model-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
print(report['verification'])
