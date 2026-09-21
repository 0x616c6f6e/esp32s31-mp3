"""Assembly-level checks using the actual revision-F PCB and component envelopes."""
doc.recompute()
# Cosmetic electrode sectors exclude mechanical switches; these are NOT electrically designed copper.
sensor.Shape=sensor.Shape.cut(Part.makeCompound([s.Shape for s in switches])).removeSplitter()
manufactured=[housing,rear,wheel,button]
newphysical=manufactured+[lcd,lens,battery,control,daughterconn,mainconn]+switches
checks={'revision':'F','status':'MECHANICAL_LAYOUT_PRELIMINARY_ELECTRICAL_DAUGHTERBOARD_NOT_IMPLEMENTED','body_mm':[params['Width'],params['Length'],params['Height']],'with_cover_mm':[params['Width'],params['Length'],14.2],'mainboard':{'ESP32_side':'toward front/screen','FPC2_side':'toward rear cover','rear_copper_z':main_z,'front_copper_z':front_z,'source_rigid_transform':'KiCad x -> 149-x, y -> y-49; per-side nominal mounting plane F=5.2, B=4.2'},'control_board_mm':[44,34,.8],'control_mounts_case_mm':control_mounts,'control_mounts_local_mm':[[x-params['ControlBoardX'],y-params['ControlBoardY']] for x,y in control_mounts],'solid_checks':{},'new_physical_interferences_mm3':{},'existing_hardware_conflicts':[],'pcb_source_sha256':provenance['pcb_source_sha256'],'screen_fpc':{'route_length_mm':route_length(turnx),'available_nominal_mm':46.14,'wrap_x_mm':wrapx,'service_turn_x_mm':turnx,'terminal_tip_case_mm':[tipx,tipy,zreturn],'wrap_radius_assumed_mm':r,'service_radius_assumed_mm':ru,'developable_fold_validated':False,'connector_height_slot_and_insertion_verified':False},'control_fpc':{'independent_from_screen_fpc':True,'nominal_cable_proposal_mm':25,'routing_channel_only':True,'main_connector_exists_in_current_pcb':False,'pinout_assigned':False}}
for o in manufactured+[control]:
    checks['solid_checks'][o.Name]={'valid':o.Shape.isValid(),'solids':len(o.Shape.Solids),'volume_mm3':o.Shape.Volume}
    assert o.Shape.isValid() and len(o.Shape.Solids)==1,o.Name
# Physical parts must not interpenetrate. Cable slots/insertion envelopes and screw engagement are excluded intentionally.
pairs=[(housing,rear),(housing,wheel),(housing,button),(housing,lcd),(housing,lens),(housing,battery),(housing,control),(housing,daughterconn),(housing,mainconn),(rear,battery),(wheel,control),(button,control),(battery,control),(battery,daughterconn),(battery,mainconn),(control,daughterconn),(lcd,control),(lcd,battery),(fpc,housing),(fpc,rear),(fpc,lcd),(fpc,control),(controlfpc,battery),(controlfpc,control)]
for sw in switches:pairs += [(housing,sw),(wheel,sw),(button,sw),(control,sw)]
pairs += [(control_screws,battery),(control_screws,control)]
checks['unmated_fpc_vs_socket_envelope_mm3']=round(fpc.Shape.common(fpc2.Shape).Volume,6)
checks['screen_shift_from_E_mm']=0.0
checks['screen_fpc_axis_offset_mm']=round(tipy-20.400,6)
checks['screen_fpc']['mated']=False
for a,b in pairs:checks['new_physical_interferences_mm3'][a.Name+' / '+b.Name]=round(a.Shape.common(b.Shape).Volume,6)
checks['outside_envelope_mm3']={o.Name:round(o.Shape.cut(Part.makeBox(params['Width'],params['Length'],14.2,V(0,params['ShellTopY'],0))).Volume,6) for o in newphysical+[fpc,controlfpc]}
for source in [doc.MainPCB,doc.MainComponents]:
    for against in [housing,rear,lcd,battery,control,fpc,daughterconn,mainconn,controlfpc,control_screws]:
        shape=source.Shape
        if source.Name=='MainComponents' and against==fpc:shape=Part.makeCompound([s for name,s in component_shapes.items() if name!='FPC2'])
        volume=round(shape.common(against.Shape).Volume,6)
        if volume>1e-5:checks['existing_hardware_conflicts'].append({'source':source.Name,'against':against.Name,'volume_mm3':volume,'includes_approximate_models':source.Name=='MainComponents'})
checks['per_component_conflicts']=[]
for name,shape in component_shapes.items():
    for label,other in [('housing',housing.Shape),('battery',battery.Shape),('control_board',control.Shape),('control_fasteners',control_screws.Shape),('display_fpc',fpc.Shape),('control_fpc',controlfpc.Shape),('new_main_connector',mainconn.Shape)]:
        if name=='FPC2' and label=='display_fpc':continue # Intended connector insertion, not evidence of interference.
        volume=round(shape.common(other).Volume,6)
        if volume>1e-5:checks['per_component_conflicts'].append({'ref':name,'against':label,'volume_mm3':volume,'some_models_approximate':True})
for src in [doc.MainPCB,doc.MainComponents]:
    ref(src.Name+'HousingCollision',src.Label+' / 与壳体干涉',src.Shape.common(housing.Shape),(.95,.12,.06))
ref('DisplayFPCHardwareCollision','屏幕排线通道与当前主板/元件相交',fpc.Shape.common(Part.makeCompound([doc.MainPCB.Shape]+[s for name,s in component_shapes.items() if name!='FPC2'])),(.95,.1,.03))
checks['new_geometry_pass']=all(v<1e-5 for v in checks['new_physical_interferences_mm3'].values()) and all(v<1e-5 for v in checks['outside_envelope_mm3'].values())
checks['entire_current_hardware_fits']=False if checks['existing_hardware_conflicts'] else True
checks['measured_gaps_mm']={'battery_to_control_board':battery.Shape.distToShape(control.Shape)[0],'jack_to_control_board':component_shapes['CN1'].distToShape(control.Shape)[0],'control_board_to_center_retainer':control.Shape.distToShape(button.Shape)[0],'power_tact_to_actuator':switches[0].Shape.distToShape(button.Shape)[0]}
checks['pcb_to_rear_standoffs_mm3']=round(doc.MainPCB.Shape.common(rear.Shape).Volume,6)
checks['pcb_straight_wall_clearance_nominal_mm']=.8
checks['pcb_to_housing_minimum_gap_mm']=round(doc.MainPCB.Shape.distToShape(housing.Shape)[0],6)
checks['mating_slot_verified']=False
checks['battery_reserved_envelope_mm']=[params['BatteryWidth'],params['BatteryLength'],params['BatteryThickness']]
checks['battery_model_selected']=False
exec(compile((HERE/'check_revision.py').read_text(encoding='utf8'),str(HERE/'check_revision.py'),'exec'))
(OUT/'validation.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf8')
assert abs(route_length(turnx)-46.14)<1e-6
assert checks['new_geometry_pass'],checks['new_physical_interferences_mm3']
assert checks['entire_current_hardware_fits'],checks['existing_hardware_conflicts']
(OUT/'display-colors.json').write_text(json.dumps(colors),encoding='utf8')
doc.saveAs(str(HERE/'ESP32S31_MP3_Q2_F.FCStd'))
for obj,stem in [(housing,'q2-f-housing'),(rear,'q2-f-rear-cover'),(wheel,'q2-f-wheel-rocker'),(button,'q2-f-center-button'),(control,'control-board-mechanical')]:
    obj.Shape.exportStep(str(OUT/(stem+'.step')))
    if obj!=control:
        mesh=MeshPart.meshFromShape(Shape=obj.Shape,LinearDeflection=.035,AngularDeflection=.12,Relative=False)
        assert mesh.isSolid(),stem
        mesh.write(str(OUT/(stem+'.stl')))
Part.makeCompound([o.Shape for o in newphysical+[doc.MainPCB,doc.MainComponents,fpc,controlfpc,control_screws]+harness_parts]).exportStep(str(OUT/'assembly-F-current-PCB.step'))
target.Shape.exportStep(str(OUT/'mainboard-reference-envelope.step'))
# Mechanical DXF: local coordinates relative to case(3,44.3), dimensions in mm.
out=['0','SECTION','2','HEADER','9','$INSUNITS','70','4','0','ENDSEC','0','SECTION','2','ENTITIES']
verts=[(10,0,0),(34,0,math.tan(math.pi/8)),(44,10,0),(44,24,math.tan(math.pi/8)),(34,34,0),(10,34,math.tan(math.pi/8)),(0,24,0),(0,10,math.tan(math.pi/8))]
out+=['0','LWPOLYLINE','100','AcDbEntity','8','BOARD_OUTLINE','100','AcDbPolyline','90','8','70','1']
for x,y,b in verts:out+=['10',str(x),'20',str(y),'42',str(b)]
for x,y in control_mounts:out+=['0','CIRCLE','100','AcDbEntity','8','NPTH_HOLES','100','AcDbCircle','10',str(x-3),'20',str(y-params['ControlBoardY']),'30','0','40','.9']
out+=['0','ENDSEC','0','EOF'];(OUT/'control-board-outline.dxf').write_text('\n'.join(out)+'\n',encoding='ascii')
rows=['feature,local_x_mm,local_y_mm,side,size_mm,status']
for name,x,y in key_positions:rows.append(f'{name},{x-3:.3f},{y-params["ControlBoardY"]:.3f},front,3x3x0.55,mechanical keepout only')
for i,(x,y) in enumerate(control_mounts):rows.append(f'Mount{i+1},{x-3:.3f},{y-params["ControlBoardY"]:.3f},through,D1.8,NPTH mechanical proposal')
rows.append('ControlFPC,37.750,5.700,rear,7.5x3x1,connector and pinout TBD')
(OUT/'control-board-features.csv').write_text('\n'.join(rows)+'\n',encoding='utf8')
print('ASSEMBLY_F_COMPLETE',json.dumps(checks,ensure_ascii=False))
