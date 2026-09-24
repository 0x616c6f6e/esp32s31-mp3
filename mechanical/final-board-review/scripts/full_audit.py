"""Runs inside build_review's geometry context; does not alter PCB sources."""
static_names=['HousingControlsA','RearCoverWithPCBPosts','LCDModule','CoverLens',
 'BatteryReference','Motor_C08_005','MotorHolderProposal','DisplayFPCRoute',
 'ControlBoardFasteners','ControlsBoard','WheelControlsA','CenterButtonControlsA',
 'ControlFFC40mm']
main_conflicts=[]
for name,obj in [('MainPCB',parts['MainPCB'])]+list(main_models.items()):
 for target in static_names:
  # These two overlaps are intentional insertion regions, not free space.
  if (name,target) in [('FPC1','ControlFFC40mm'),('FPC2','DisplayFPCRoute')]:continue
  other=parts[target]
  v=volume(obj.Shape,other.Shape)
  if v>1e-5:
   common=obj.Shape.common(other.Shape);bb=common.BoundBox
   main_conflicts.append({'part':name,'against':target,'volume_mm3':round(v,6),
    'overlap_bounds_case_mm':[round(x,4) for x in [bb.XMin,bb.YMin,bb.ZMin,bb.XMax,bb.YMax,bb.ZMax]]})
 for ref,other in models.items():
  v=volume(obj.Shape,other.Shape)
  if v>1e-5:main_conflicts.append({'part':name,'against':'CTRL_'+ref,'volume_mm3':round(v,6)})
pairs=[]
items=list(main_models.items())
for i,(name,obj) in enumerate(items):
 for name2,other in items[i+1:]:
  v=volume(obj.Shape,other.Shape)
  if v>1e-5:pairs.append({'part':name,'against':name2,'volume_mm3':round(v,6)})
invalid=[]
for name,obj in parts.items():
 if hasattr(obj,'Shape') and not obj.Shape.isNull() and not obj.Shape.isValid():invalid.append(name)
report['full_mainboard_review']={'component_count_with_models':len(main_models),
 'model_conflicts':main_conflicts,'same_mainboard_component_overlaps':pairs,
 'invalid_shapes':invalid,'complete_mainboard_fit_pass':not main_conflicts and not pairs and not invalid,
 'coverage_complete':False,'missing_models':md['missing_component_models'],
 'U10_model_basis':'Conservative 7.9 x 5.3 x 1.9 mm envelope from unresolved model filename, not a vendor solid.',
 'intended_mating_regions_excluded':[['FPC1','ControlFFC40mm'],['FPC2','DisplayFPCRoute']]}
report['controls_only_fit_pass']=report['pass']
report['pass']=report['pass'] and report['full_mainboard_review']['complete_mainboard_fit_pass']
report['production_release']=False
report['source_sha256']=dict(report['source_sha256'])
report['source_sha256']['controls_pcb']=sha(P/'controls.kicad_pcb')
print('FULL_MAINBOARD_REVIEW',json.dumps(report['full_mainboard_review'],ensure_ascii=False),flush=True)
