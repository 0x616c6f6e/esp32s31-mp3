"""Additional checks executed in the enclosure builder's geometry context."""
left=params['LensX'];right=params['Width']-params['LensX']-params['LensWidth']
top=params['LensY']-params['ShellTopY']
assert max(left,right,top)-min(left,right,top)<1e-8
assert abs(params['CornerRadius']-params['LensRadius']-left)<1e-8
assert abs((params['ShellTopY']+params['CornerRadius'])-(params['LensY']+params['LensRadius']))<1e-8
assert abs(params['ControlBoardY']-44.3-params['ControlShiftY'])<1e-8
assert abs(params['WheelY']-61.3-params['ControlShiftY'])<1e-8
checks['source_files']=provenance
checks['cover_lens_border_mm']={'top':top,'left':left,'right':right,'basis':'Visible external cover lens, not LCD active area; corner centers are concentric.'}
checks['top_extension_mm']=-params['ShellTopY']
checks['control_shift_up_mm']=-params['ControlShiftY']
checks['case_origin_y_mm']=params['ShellTopY']
checks['shell_corner_radius_mm']=params['CornerRadius']
checks['cover_to_wheel_gap_mm']=params['WheelY']-params['WheelDiameter']/2-params['LensY']-params['LensLength']
checks['control_holes_local_unchanged']=all(abs(y-expected)<1e-7 for (_,y),expected in zip(checks['control_mounts_local_mm'],[8.7,8.7,24.7,24.7]))
assert checks['control_holes_local_unchanged']
obstacles={o.Name:o.Shape for o in [housing,rear,lcd,lens,battery,control,control_screws,fpc,controlfpc,daughterconn,mainconn,wheel,button]+switches}
obstacles.update(component_shapes)
def intersects(a,b):
    aa,bb=a.BoundBox,b.BoundBox
    return aa.XMin<bb.XMax and aa.XMax>bb.XMin and aa.YMin<bb.YMax and aa.YMax>bb.YMin and aa.ZMin<bb.ZMax and aa.ZMax>bb.ZMin
extra=[]
for o in harness_parts:
    shape=motor_max if o.Name=='Motor_C08_005' else o.Shape
    assert shape.isValid(),o.Name
    for name,other in obstacles.items():
        if o.Name=='MotorHolderProposal' and name==housing.Name:continue # Intended side-wall attachment.
        if o.Name.startswith('MotorWire') and name=='H1':continue
        if o.Name.startswith('BatteryWire') and name in ['H2','BatteryReference']:continue
        if not intersects(shape,other):continue
        volume=shape.common(other).Volume
        if volume>1e-5:extra.append({'part':o.Name,'against':name,'volume_mm3':round(volume,6)})
checks['motor_and_harness_conflicts']=extra
checks['motor_max_to_control_board_mm']=round(motor_max.distToShape(control.Shape)[0],6)
checks['motor_max_to_control_fasteners_mm']=round(motor_max.distToShape(control_screws.Shape)[0],6)
checks['pcb_unchanged']=hashlib.sha256((ROOT/'hardware-q2-placement/hardware.kicad_pcb').read_bytes()).hexdigest()==provenance['pcb_source_sha256']
checks['entire_current_hardware_fits']=not checks['existing_hardware_conflicts'] and not checks['per_component_conflicts'] and not extra
assert checks['pcb_unchanged']
assert checks['entire_current_hardware_fits'],(checks['existing_hardware_conflicts'],checks['per_component_conflicts'],extra)
