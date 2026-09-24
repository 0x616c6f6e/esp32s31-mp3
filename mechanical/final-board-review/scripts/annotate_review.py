from pathlib import Path
import FreeCAD as A,Part,json,math,hashlib
ROOT=Path(__file__).resolve().parents[3];O=ROOT/'mechanical/final-board-review'
d=A.openDocument(str(O/'Q2_Final_Mainboard_Assembly.FCStd'))
old=A.openDocument(str(ROOT/'mechanical/enclosure-q2-f/ESP32S31_MP3_Q2_F.FCStd'))
import sys
sys.path.insert(0,str(O/'scripts'))
from mounting_adjustment import apply as apply_mounting_adjustment
mounting_adjustment=apply_mounting_adjustment(old)
report=json.loads((O/'fit-check.json').read_text());md=json.loads((O/'mainboard-reference.json').read_text())
g=d.getObject('ReviewDiagnostics') or d.addObject('App::DocumentObjectGroup','ReviewDiagnostics');colors=json.loads((O/'colors.json').read_text())
def add(name,label,shape,color):
 o=d.getObject(name) or d.addObject('PartDesign::Feature',name);o.Label=label;o.Shape=shape;g.addObject(o);colors[name]=color;return o
for i,c in enumerate(report['full_mainboard_review']['model_conflicts']):
 a=d.getObject('PCB_'+c['part']);b=d.getObject(c['against'])
 add('Conflict'+str(i),'INTERFERENCE: '+c['part']+' / '+c['against'],a.Shape.common(b.Shape),(1.,.05,.03))
posts=[]
for o in old.Objects:
 if o.Name.startswith('MainPCBPostOuter'):
  pos=o.Placement.Base;posts.append({'name':o.Name,'center_case_mm':[pos.x,pos.y],'top_z_mm':pos.z+o.Height.Value})
holes=[]
for f in md['footprints']:
 if not f['ref'].startswith('SCREW'):continue
 x=176.868-f['xy'][0];y=f['xy'][1]-65.647
 closest=min(posts,key=lambda a:math.dist((x,y),a['center_case_mm']))
 holes.append({'reference':f['ref'],'case_xy_mm':[round(x,4),round(y,4)],'nearest_old_post':closest['name'],'center_offset_mm':round(math.dist((x,y),closest['center_case_mm']),4)})
 add('RequiredPost_'+f['ref'],'Required support axis: '+f['ref'],Part.makeCylinder(.3,5.8,A.Vector(x,y,0)),(.95,.65,.05))
report['mounting_review']={'existing_posts':posts,'actual_mainboard_holes':holes,'all_aligned':all(a['center_offset_mm']<.05 for a in holes)}
report['mounting_adjustment']=mounting_adjustment
# Check a proposed motor position only; preserve the reviewed assembly position.
proposal=[]
exclude={'Motor_C08_005','MotorHolderProposal','MotorAdhesive','HousingSourceF','RearCoverSourceF'}
targets=[o for o in d.Objects if (o.Name.startswith(('PCB_','CTRL_')) or o.Name in ['MainPCB','ControlsBoard','HousingControlsA','RearCoverWithPCBPosts','BatteryReference','DisplayFPCRoute','ControlFFC40mm','ControlBoardFasteners']) and o.Name not in exclude]
for x,y in [(41,59.6),(42,59.6),(42.5,59.6),(43,59.6),(42,60),(43,60)]:
 conflicts=[];minimum=1e9
 for name in ['Motor_C08_005','MotorHolderProposal','MotorAdhesive']:
  sh=d.getObject(name).Shape.copy();sh.translate(A.Vector(x-39,y-62,0))
  for o in targets:
   if name=='MotorHolderProposal' and o.Name=='HousingControlsA':continue
   a,b=sh.BoundBox,o.Shape.BoundBox
   if a.XMin<b.XMax and a.XMax>b.XMin and a.YMin<b.YMax and a.YMax>b.YMin and a.ZMin<b.ZMax and a.ZMax>b.ZMin:
    v=sh.common(o.Shape).Volume
    if v>1e-5:conflicts.append([name,o.Name,round(v,6)])
   if o.Name in ['PCB_CN1','CTRL_J1','ControlFFC40mm']:minimum=min(minimum,sh.distToShape(o.Shape)[0])
 proposal.append({'motor_center_case_xy_mm':[x,y],'nominal_conflicts':conflicts,'min_distance_to_jack_J1_FFC_mm':round(minimum,4)})
report['motor_reposition_candidates_not_applied']=proposal
report['mainboard_mounting_posts_match_new_hole_pattern']=report['mounting_review']['all_aligned']
report['review_conclusion']='FAIL: motor/jack and C13/display-flex overlaps. SCREW3 support moved 0.5 mm inward; source PCB hole has not been moved. CN2/CN3 models absent.'
report['pass']=False
report['scope_note']='Final hardware-q2 review with SCREW3 mechanical support offset +0.5 mm in case X. PCB unchanged; mounting mismatch is intentional pending PCB update. Other recorded conflicts remain.'
for name in ['MainPCB','ControlsBoard','PCB_CN1','PCB_C13','PCB_FPC1','PCB_FPC2','CTRL_J1','DisplayFPCRoute','ControlFFC40mm']:
 bb=d.getObject(name).Shape.BoundBox
 report.setdefault('selected_bounds_case_mm',{})[name]=[round(v,4) for v in [bb.XMin,bb.YMin,bb.ZMin,bb.XMax,bb.YMax,bb.ZMax]]
for obj in d.Objects:
 if hasattr(obj,'Shape') and not obj.Shape.isNull():assert obj.Shape.isValid(),obj.Name
(O/'fit-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(O/'colors.json').write_text(json.dumps(colors,indent=2))
d.recompute();d.save()
print('MOUNTING_REVIEW',json.dumps(report['mounting_review']))
print('MOTOR_CANDIDATES',json.dumps(proposal))
print('ANNOTATION_SAVED')
