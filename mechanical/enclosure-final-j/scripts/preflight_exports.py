"""Read-back verification of the actual J print files, without rebuilding them."""
from pathlib import Path
import FreeCAD as A,Part,Mesh,json,hashlib,zipfile
O=Path(__file__).resolve().parents[1];R=O.parents[1];V=A.Vector
d=A.openDocument(str(O/'Q2_J_Glue_Insert_Assembly.FCStd'))
report={'source_hashes':{},'exports':[],'zip_errors':[]}
for k,v in json.loads((O/'source.json').read_text()).items():
 h=hashlib.sha256((R/v['path']).read_bytes()).hexdigest()
 report['source_hashes'][k]={'matches':h==v['sha256'],'sha256':h}
 assert h==v['sha256']
def box(x,y,z,w,l,h):return Part.makeBox(w,l,h,V(x,y,z))
def carrier(s,size,edge):
 x,y=25-size/2,59.3-size/2
 q=box(x,y,11.5,size,size,2.6).cut(box(x+2,y+2,11.4,size-4,size-4,2.8))
 for sign in [-1,1]:
  a,b=sorted([25+sign*edge,25+sign*(size/2-1.8)])
  q=q.fuse(box(a,58.9,12.4,b-a,.8,.3))
 return s.fuse(q).removeSplitter()
expected={'01-housing':d.HousingControlsA.Shape,'02-rear-cover':d.RearCoverWithPCBPosts.Shape,
 '03-wheel-with-carrier':carrier(d.WheelControlsA.Shape,42,16.9),
 '04-center-with-carrier':carrier(d.CenterButtonControlsA.Shape,20,6.6),
 '05-insert-fit-coupon-optional':d.InsertFitCoupon.Shape}
for e in json.loads((O/'export-check.json').read_text()):
 n=e['part'];p=O/'print-package'/n
 s=Part.read(str(p.with_suffix('.step')));m=Mesh.Mesh(str(p.with_suffix('.stl')))
 shifted=s.copy();shifted.translate(-V(*e['translation_from_assembly_mm']))
 delta=shifted.cut(expected[n]).Volume+expected[n].cut(shifted).Volume
 b=m.BoundBox
 row={'part':n,'step_valid':s.isValid(),'step_solids':len(s.Solids),'step_shells':len(s.Shells),
 'stl_closed':m.isSolid(),'stl_components':m.countComponents(),'stl_nonmanifold':m.hasNonManifolds(),
 'stl_self_intersection':m.hasSelfIntersections(),'stl_bad_normals':m.hasNonUniformOrientedFacets(),
 'step_vs_saved_model_symmetric_difference_mm3':delta,'mesh_vs_step_volume_relative_error':abs(abs(m.Volume)-s.Volume)/s.Volume,
 'dimensions_mm':[b.XLength,b.YLength,b.ZLength]}
 report['exports'].append(row);print('EXPORT_READBACK',json.dumps(row),flush=True)
 assert row['step_valid'] and row['step_solids']==1 and row['step_shells']==1
 assert row['stl_closed'] and row['stl_components']==1
 assert not any(row[k] for k in ['stl_nonmanifold','stl_self_intersection','stl_bad_normals'])
 assert delta<1e-4 and row['mesh_vs_step_volume_relative_error']<.01
with zipfile.ZipFile(O/'Q2-J-glue-insert-sample.zip') as z:
 assert z.testzip() is None
 manifest=json.loads(z.read('manifest.json'))
 for n,h in manifest['files'].items():
  if hashlib.sha256(z.read(n)).hexdigest()!=h:report['zip_errors'].append(n+':hash')
  if z.read(n)!=(O/'print-package'/n).read_bytes():report['zip_errors'].append(n+':folder mismatch')
 assert not report['zip_errors']
report['assembly_sha256']=hashlib.sha256((O/'Q2_J_Glue_Insert_Assembly.FCStd').read_bytes()).hexdigest()
(O/'preflight-export-check.json').write_text(json.dumps(report,indent=2))
print('READBACK_PASS',flush=True)
