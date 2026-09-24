"""Release only the checked K print geometry; verify archive bytes and hashes."""
from pathlib import Path
import json,hashlib,zipfile,shutil
O=Path(__file__).resolve().parents[1]; P=O/'print-package'
def read(n):return json.loads((O/n).read_text())
fit=read('fit-check.json'); paths=read('assembly-path-check.json'); exports=read('export-readback-check.json')
assert not fit['static_conflicts'] and not fit['invalid_shapes'] and not fit['battery_expanded_conflicts']
count=0
for rows in paths.values():
 if not isinstance(rows,list):continue
 count+=len(rows);assert all(not row['hits'] for row in rows)
assert count==66 and len(exports['exports'])==6
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert exports['assembly_sha256']==sha(O/'Q2_K_Assembly_Access.FCStd')
assert all(v['matches'] for v in exports['source_hashes'].values())
for v in read('source.json').values():assert sha(O.parents[1]/v['path'])==v['sha256']
ready={'revision':'K','status':'NOMINAL_CAD_PASS_FOR_PROTOTYPE_REVIEW',
 'factory_approval_obtained':False,'physical_assembly_tested':False,
 'static_unintended_interferences':0,'assembly_discrete_poses_passed':count,
 'printable_parts_required':5,'optional_coupons':1,'case_overall_mm':[50,81.5,15.1],
 'required_changes_from_J':['Use complete K printed set; add separate motor carrier',
 'Controls screws M1.6x2.5 under head plus 0.3mm washers',
 'Rear glue bores OD3.0 for OD2.5 x L3 inserts; fit coupon recommended',
 'Motor carrier glued AFTER controls installation'],
 'remaining_checks':['Material-specific factory thin-wall review','Actual FPC geometry and bend behavior',
 'Finished battery dimensions and charging configuration','Print tolerance, adhesive strength and screw torque'],
 'native_model_sha256':exports['assembly_sha256']}
(O/'production-readiness.json').write_text(json.dumps(ready,indent=2))
names=['README.md','source.json','parameters.json','fit-check.json','assembly-path-check.json',
 'detail-check.json','display-route.json','export-check.json','export-readback-check.json','production-readiness.json',
 'front-assembled.png','shell-parts.png','back-internals.png','controls-mount-view.png','insert-section.png']
for n in names:shutil.copyfile(O/n,P/n)
(P/'PRINT-INSTRUCTIONS.txt').write_text(
 'Q2 K / 单位 mm / 请勿缩放\n'
 '01上壳、02后盖、03滑环、04中央键、05马达托座：每件1个。06螺母小样建议1个。\n'
 '同名STEP/STL是同一零件的两种格式，二选一上传，不要重复下单。\n'
 '五件全部使用K版，不与旧版混装；LCD盖板和电子件不打印。\n'
 '韧性SLA树脂装机样件；局部最薄功能壁约0.85mm，须材料审核。\n'
 '后盖螺母由用户冷胶粘接：M1.6，最大外径2.5，长3.0mm。孔径3.0mm。\n'
 '按键小板：3颗M1.6×2.5头下长度，分别加0.3mm平垫。\n'
 '马达托座必须在小板装好后粘接，主板后盖最后合装。完整步骤见README.md。\n'
 '检查通过限于名义CAD及导出文件；不代表工厂接单批准或完成实物装机。\n',encoding='utf-8-sig')
files=sorted(p for p in P.iterdir() if p.is_file() and p.name!='manifest.json')
manifest={'revision':'K','units':'mm','files':{p.name:sha(p) for p in files}}
(P/'manifest.json').write_text(json.dumps(manifest,indent=2))
archive=O/'Q2-K-assembly-sample.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in files+[P/'manifest.json']:z.write(p,p.name)
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for n,h in manifest['files'].items():
  assert hashlib.sha256(z.read(n)).hexdigest()==h
  assert z.read(n)==(P/n).read_bytes()
(O/'package-check.json').write_text(json.dumps({'zip':archive.name,'sha256':sha(archive),
 'crc_pass':True,'all_manifest_hashes_pass':True,'all_zip_bytes_match_folder':True,'file_count':len(files)+1},indent=2))
print('PACKAGE_PASS',archive,len(files)+1,archive.stat().st_size,flush=True)
