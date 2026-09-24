"""Read back every K STEP/STL and compare to the saved native geometry."""
from pathlib import Path
import FreeCAD as A, Part, Mesh, json, hashlib
O=Path(__file__).resolve().parents[1]; R=O.parents[1]; V=A.Vector
d=A.openDocument(str(O/'Q2_L_AM213_Adapter_Study.FCStd'))
report={'source_hashes':{},'exports':[]}
for k,v in json.loads((O/'source.json').read_text()).items():
 h=hashlib.sha256((R/v['path']).read_bytes()).hexdigest()
 report['source_hashes'][k]={'matches':h==v['sha256'],'sha256':h}; assert h==v['sha256']
for e in json.loads((O/'export-check.json').read_text()):
 p=O/'prototype-parts-not-released'/e['part']; s=Part.read(str(p.with_suffix('.step'))); m=Mesh.Mesh(str(p.with_suffix('.stl')))
 expected=d.getObject(e['object']).Shape
 shifted=s.copy();shifted.translate(-V(*e['translation_from_assembly_mm']))
 delta=shifted.cut(expected).Volume+expected.cut(shifted).Volume
 b=m.BoundBox
 row={'part':e['part'],'step_valid':s.isValid(),'step_solids':len(s.Solids),'step_shells':len(s.Shells),
 'stl_closed':m.isSolid(),'stl_components':m.countComponents(),'stl_nonmanifold':m.hasNonManifolds(),
 'stl_self_intersection':m.hasSelfIntersections(),'stl_bad_normals':m.hasNonUniformOrientedFacets(),
 'step_vs_saved_model_symmetric_difference_mm3':delta,'mesh_vs_step_volume_relative_error':abs(abs(m.Volume)-s.Volume)/s.Volume,
 'dimensions_mm':[b.XLength,b.YLength,b.ZLength]}
 report['exports'].append(row);print('READBACK',json.dumps(row),flush=True)
 assert row['step_valid'] and row['step_solids']==1 and row['step_shells']==1
 assert row['stl_closed'] and row['stl_components']==1
 assert not any(row[k] for k in ['stl_nonmanifold','stl_self_intersection','stl_bad_normals'])
 assert delta<1e-4 and row['mesh_vs_step_volume_relative_error']<.01
report['assembly_sha256']=hashlib.sha256((O/'Q2_L_AM213_Adapter_Study.FCStd').read_bytes()).hexdigest()
(O/'export-readback-check.json').write_text(json.dumps(report,indent=2)); print('READBACK_PASS',flush=True)
