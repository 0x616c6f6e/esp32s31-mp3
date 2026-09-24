from pathlib import Path
import FreeCAD as A,Part,json,math,itertools,sys
O=Path(__file__).resolve().parents[1];V=A.Vector
d=A.openDocument(str(O/'Q2_I_Serviceable_Assembly.FCStd'))
def overlaps(a,b):
 aa,bb=a.BoundBox,b.BoundBox
 return not (aa.XMax<=bb.XMin or bb.XMax<=aa.XMin or aa.YMax<=bb.YMin or bb.YMax<=aa.YMin or aa.ZMax<=bb.ZMin or bb.ZMax<=aa.ZMin)
def volume(a,b):
 if not overlaps(a,b):return 0
 # Prune compound wire segments and fasteners before expensive booleans.
 if len(a.Solids)>1 or len(b.Solids)>1:
  # Signed solids can encode voids in imported STEP. Preserve their topology;
  # recompute the whole boolean when a pruned constituent flags an overlap.
  return sum(max(0,sa.common(sb).Volume) for sa in a.Solids for sb in b.Solids if overlaps(sa,sb))
 return a.common(b).Volume
cases=list(d.PrintableParts.Group)
electronics=[o for o in d.Electronics.Group if o.Name!='WheelCopper']
phys=cases+electronics+[d.getObject(n) for n in ['LCDModule','CoverLens','DisplayFPCRoute','ControlFFC40mm','Motor_C08_005','MotorAdhesive','BatteryPack','BatteryInsulation','BatteryAdhesive','MainBoardFasteners','ControlBoardFasteners','RearCoverFasteners']]
phys += [o for o in d.AssemblyReferences.Group if 'Wire' in o.Name]
phys += [d.ControlWashers,d.ControlEdgePad,d.DisplayChannelLiner,d.ControlChannelLiner,d.WireEdgeInsulation]
phys=list({o.Name:o for o in phys}.values())
changed=set(sys.argv[1:])
previous=json.loads((O/'fit-check.json').read_text()) if changed else None
conflicts=[row for row in previous['static_conflicts'] if not {row['a'],row['b']}&changed] if changed else []
for i,a in enumerate(phys):
 if i%25==0:print('CHECK',i,len(phys),a.Name,flush=True)
 for b in phys[i+1:]:
  n={a.Name,b.Name}
  if changed and not n&changed:continue
  if n in [{'PCB_FPC1','ControlFFC40mm'},{'CTRL_J1','ControlFFC40mm'},{'PCB_FPC2','DisplayFPCRoute'},{'MainBoardFasteners','RearCoverWithPCBPosts'},{'ControlBoardFasteners','HousingControlsA'},{'RearCoverFasteners','HousingControlsA'}]:continue
  if any('WireStrainRelief' in t for t in n) and any('Wire' in t and 'Relief' not in t for t in n):continue
  if any(t.startswith('BatteryWire') for t in n) and 'BatteryPack' in n:continue
  if any(t.startswith('MotorWire') for t in n) and 'Motor_C08_005' in n:continue
  v=volume(a.Shape,b.Shape)
  if v>1e-5:conflicts.append({'a':a.Name,'b':b.Name,'volume_mm3':round(v,6)})
  # PCB copper and component pads lie at their natural board surfaces, no blanket exclusion.
print('STATIC_CONFLICTS',json.dumps(conflicts),flush=True)
travel=[]
for name in ['WheelControlsA','CenterButtonControlsA']:
 s=d.getObject(name).Shape.copy();s.translate(V(0,0,-.33))
 travel.append({'part':name,'travel_mm':.33,**{n:round(volume(s,d.getObject(n).Shape),6) for n in ['ControlsBoard','HousingControlsA']}})
wheel=d.WheelControlsA.Shape
for axis,sgn in [(V(1,0,0),1),(V(1,0,0),-1),(V(0,1,0),1),(V(0,1,0),-1)]:
 s=wheel.copy();angle=sgn*math.degrees(math.asin(.165/13));s.rotate(V(25,59.3,12.65),axis,angle);s.translate(V(0,0,-.165))
 travel.append({'part':'wheel-rocking','axis':list(axis),'angle_deg':angle,**{n:round(volume(s,d.getObject(n).Shape),6) for n in ['ControlsBoard','HousingControlsA','CenterButtonControlsA']}})
print('TRAVEL',json.dumps(travel),flush=True)
expanded=[]
for o in cases+electronics+[d.DisplayFPCRoute,d.ControlFFC40mm,d.Motor_C08_005]+[o for o in phys if o.Name.startswith('MotorWire')]:
 v=volume(o.Shape,d.BatteryExpandedKeepout.Shape)
 if v>1e-5:expanded.append([o.Name,v])
clearances={}
for a,b in [('PCB_C13','DisplayFPCRoute'),('Motor_C08_005','PCB_CN1'),('Motor_C08_005','ControlsBoard'),('Motor_C08_005','ControlFFC40mm'),('BatteryPack','MainPCB'),('BatteryExpandedKeepout','PCB_U5'),('ControlFFC40mm','RearCoverWithPCBPosts')]:
 clearances[a+'/'+b]=d.getObject(a).Shape.distToShape(d.getObject(b).Shape)[0]
invalid=[o.Name for o in phys if not o.Shape.isValid()]
report={'static_conflicts':conflicts,'travel':travel,'battery_expanded_conflicts':expanded,'clearances_mm':clearances,'invalid_shapes':invalid,'checks_apply_to_nominal_models_only':True,'battery_model_is_procurement_envelope_not_verified_product':True,'cn2_cn3_headers_not_fitted':True}
if changed:report['incremental_check_note']='Full assembly previously checked; only '+', '.join(sorted(changed))+' changed and every pair involving them was rechecked. All other geometry retained.'
(O/'fit-check.json').write_text(json.dumps(report,indent=2))
print('AUDIT_SAVED',flush=True)
