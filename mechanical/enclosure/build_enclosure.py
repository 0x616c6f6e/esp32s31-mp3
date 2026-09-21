"""Build native, spreadsheet-driven FreeCAD enclosure features and review exports.

Run with FreeCAD's Python interpreter, or run Rebuild.FCMacro in FreeCAD.
The source PCB is read only. All dimensional assumptions are in parameters.json.
"""
import FreeCAD as App, Part, MeshPart
if App.GuiUp:
    import FreeCADGui as Gui
from pathlib import Path
import json, math, hashlib

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
OUT=HERE/'exports'; OUT.mkdir(exist_ok=True)
params=json.loads((HERE/'parameters.json').read_text(encoding='utf8'))
layout=json.loads((ROOT/'hardware/output/layout-data.json').read_text(encoding='utf8'))
DOCNAME='MP3_Enclosure_A'
if any(n in App.listDocuments() for n in [DOCNAME,'ESP32S31_MP3_Enclosure_A']):
    raise RuntimeError('The enclosure document is already open. Save/close it before rebuilding.')
doc=App.newDocument(DOCNAME)
doc.Label='ESP32-S31 MP3 - 50 x 80 mm enclosure A'
table=doc.addObject('Spreadsheet::Sheet','Parameters');table.Label='尺寸参数 / mm - editable'
table.set('A1','Parameter');table.set('B1','mm')
for row,(key,value) in enumerate(params.items(),2):
    table.set('A'+str(row),key);table.set('B'+str(row),str(value));table.setAlias('B'+str(row),key)
table.setColumnWidth('A',190);table.setColumnWidth('B',95)
construction=doc.addObject('App::DocumentObjectGroup','Construction');construction.Label='Native editable construction / 参数特征'
parts=doc.addObject('App::DocumentObjectGroup','EnclosureParts');parts.Label='外壳零件 / export these'
refs=doc.addObject('App::DocumentObjectGroup','ReferenceParts');refs.Label='PCB and ASSUMED component envelopes / 不打印'
colors={}; counter=0
def p(k):return 'Parameters.'+k
def exp(o,prop,value):
    if isinstance(value,str):o.setExpression(prop,value)
    else:setattr(o,prop,value)
def pos(o,x,y,z):
    for axis,v in zip('xyz',[x,y,z]):
        if isinstance(v,str):o.setExpression('Placement.Base.'+axis,v)
        else:setattr(o.Placement.Base,axis,v)
    # Placement is a value type: numeric coordinates must be assigned as a whole.
    base=o.Placement.Base
    for axis,v in zip('xyz',[x,y,z]):
        if not isinstance(v,str):setattr(base,axis,v)
    o.Placement.Base=base
def feature(kind,name,label=None):
    o=doc.addObject(kind,name);o.Label=label or name;construction.addObject(o);return o
def box(name,w,l,h,x=0,y=0,z=0):
    o=feature('Part::Box',name)
    for k,v in [('Length',w),('Width',l),('Height',h)]:exp(o,k,v)
    pos(o,x,y,z);return o
def cylinder(name,r,h,x=0,y=0,z=0):
    o=feature('Part::Cylinder',name);exp(o,'Radius',r);exp(o,'Height',h);pos(o,x,y,z);return o
def fuse(name,items):
    o=feature('Part::MultiFuse',name);o.Shapes=items;o.Refine=True;return o
def cut(name,base,tool):
    o=feature('Part::Cut',name);o.Base=base;o.Tool=tool;o.Refine=True;return o
def rounded(name,w,l,r,h,x='0',y='0',z='0'):
    w,l,r,h,x,y,z=map(str,[w,l,r,h,x,y,z])
    solids=[box(name+'CoreX',f'({w})-2*({r})',l,h,f'({x})+({r})',y,z),box(name+'CoreY',w,f'({l})-2*({r})',h,x,f'({y})+({r})',z)]
    for i,(xx,yy) in enumerate([(f'({x})+({r})',f'({y})+({r})'),(f'({x})+({w})-({r})',f'({y})+({r})'),(f'({x})+({w})-({r})',f'({y})+({l})-({r})'),(f'({x})+({r})',f'({y})+({l})-({r})')]):
        solids.append(cylinder(name+'Corner'+str(i),r,h,xx,yy,z))
    return fuse(name,solids)
def orient(obj,rotation,x,y,z):obj.Placement.Rotation=rotation;pos(obj,x,y,z);return obj
def final(o,name,label,color):
    o.Label=label;construction.removeObject(o);parts.addObject(o);colors[o.Name]=color
    o.addProperty('App::PropertyString','ManufacturingNote','Design').ManufacturingNote='Dimensional prototype; confirm real parts before production'
    return o
W,L,H=p('Width'),p('Length'),p('Height');wall=p('Wall');floor=p('Floor');split=p('SplitZ')
outer=rounded('RearOuter',W,L,p('CornerRadius'),split)
cavity=rounded('RearCavity',W+'-2*'+wall,L+'-2*'+wall,p('CornerRadius')+'-'+wall,split,wall,wall,floor)
rear=cut('RearHollow',outer,cavity)
mounts=[]
for f in layout['footprints']:
    if f['reference'].startswith('SCREW'):
        x,y=f['position_mm'];mounts.append((f['reference'],x-100,y-50))
mounts.sort()
bosses=[]
for ref,x,y in mounts:
    xx=p('PCBX')+f'+{x}';yy=p('PCBY')+f'+{y}'
    if ref=='SCREW4':
        shoulder=cylinder('RearBossShoulder'+ref,p('BossRadius'),p('PCBRearZ')+'-'+floor+'-1.6',xx,yy,floor)
        neck=cylinder('RearBossNeck'+ref,'1.6','1.65',xx,yy,p('PCBRearZ')+'-1.65')
        b=fuse('RearBoss'+ref,[shoulder,neck])
    else:
        b=cylinder('RearBoss'+ref,p('BossRadius'),p('PCBRearZ')+'-'+floor,xx,yy,floor)
    hole=cylinder('Pilot'+ref,p('PilotDiameter')+'/2',p('PCBRearZ'),xx,yy,1.6)
    bosses.append(cut('BossBore'+ref,b,hole))
rear=fuse('RearWithBosses',[rear]+bosses)

# Front lid, stepped locating lip. The thin side wall is only beside the PCB.
lid_z=split+'+'+p('SeamGap')
lid=rounded('FrontOuter',W,L,p('CornerRadius'),H+'-('+lid_z+')',z=lid_z)
lc=rounded('FrontCavity',W+'-2*'+p('FrontWall'),L+'-2*'+p('FrontWall'),'0.5',H+'-'+p('FaceThickness')+'-('+lid_z+')+0.2',p('FrontWall'),p('FrontWall'),'('+lid_z+')-0.2')
lid=cut('FrontHollow',lid,lc)
lip_offset=wall+'+'+p('LipClearance')
lip_z=split+'-'+p('LipDepth')
lip_outer=rounded('LipOuter',W+'-2*('+lip_offset+')',L+'-2*('+lip_offset+')','1.0',p('LipDepth')+'+'+p('SeamGap')+'+0.35',lip_offset,lip_offset,lip_z)
lip_inner=rounded('LipInner',W+'-2*('+lip_offset+'+'+p('LipWall')+')',L+'-2*('+lip_offset+'+'+p('LipWall')+')','0.4','2.0','('+lip_offset+')+'+p('LipWall'),'('+lip_offset+')+'+p('LipWall'),'('+lip_z+')-0.1')
lip=cut('RegistrationLip',lip_outer,lip_inner)
posts=[]
for ref,x,y in mounts:
    if ref=='SCREW2':continue  # This screw is underneath the LCD; secure PCB first.
    posts.append(cylinder('FrontPost'+ref,p('BossRadius'),H+'-('+p('PCBRearZ')+'+'+p('PCBThickness')+')',p('PCBX')+f'+{x}',p('PCBY')+f'+{y}',p('PCBRearZ')+'+'+p('PCBThickness')))
lid=fuse('FrontWithPosts',[lid,lip]+posts)
lcdcx=W+'/2';lcdcy=p('LCDTopOffset')+'+'+p('LCDLength')+'/2'
window=rounded('DisplayWindow',p('WindowWidth'),p('WindowLength'),'2.5','5','('+W+'-'+p('WindowWidth')+')/2','('+lcdcy+')-'+p('WindowLength')+'/2','10')
lcdpocket=rounded('LCDRearPocket',p('LCDWidth')+'+0.6',p('LCDLength')+'+0.6','1','3.3','('+W+'-'+p('LCDWidth')+'-0.6)/2',p('LCDTopOffset')+'-0.3','9.7')
lenspocket=rounded('LensAdhesiveRecess',p('LensWidth')+'+0.6',p('LensLength')+'+0.6','3.2','1','('+W+'-'+p('LensWidth')+'-0.6)/2','('+lcdcy+')-('+p('LensLength')+'+0.6)/2',H+'-0.3')
lid=cut('DisplayPockets',lid,fuse('DisplayTools',[window,lcdpocket,lenspocket]))
lidholes=[]
for ref,x,y in mounts:
    if ref=='SCREW2':continue
    xx=p('PCBX')+f'+{x}';yy=p('PCBY')+f'+{y}'
    lidholes.append(cylinder('FrontScrew'+ref,p('ScrewClearance')+'/2','7',xx,yy,p('PCBRearZ')+'+'+p('PCBThickness')+'-0.1'))
    lidholes.append(cylinder('HeadSeat'+ref,p('HeadDiameter')+'/2',p('HeadDepth')+'+0.2',xx,yy,H+'-'+p('HeadDepth')))
lid=cut('FrontScrewHoles',lid,fuse('FrontFastenerTools',lidholes))

# Full-depth bottom openings allow plug shoulders into the recessed ports.
usb=rounded('USBPort',p('USBOpeningWidth'),p('USBOpeningHeight'),'1.0','4')
orient(usb,App.Rotation(App.Vector(1,0,0),90),p('PCBX')+'+35.449-'+p('USBOpeningWidth')+'/2',L+'+1',p('USBOpeningZ')+'-'+p('USBOpeningHeight')+'/2')
jack=cylinder('JackPort',p('JackOpeningDiameter')+'/2','4')
orient(jack,App.Rotation(App.Vector(1,0,0),90),p('PCBX')+'+11.065',L+'+1',p('JackOpeningZ'))
tf=rounded('TFPort',p('TFOpeningLength'),p('TFOpeningHeight'),'0.5','4')
rot=App.Rotation(App.Vector(0,0,1),90).multiply(App.Rotation(App.Vector(1,0,0),90))
orient(tf,rot,'-1',p('TFOpeningY')+'-'+p('TFOpeningLength')+'/2',p('TFOpeningZ')+'-'+p('TFOpeningHeight')+'/2')
port_tools=fuse('PortTools',[usb,jack,tf]);rear=cut('RearPorts',rear,port_tools)

# Flush side power key with retaining flange, switch support, and tool-access pocket.
keyhole=box('KeyOpening','3','6.8','2.8',W+'-2',p('ButtonY')+'-3.4',p('ButtonZ')+'-1.4')
keypocket=box('KeyFlangePocket','1.3','8.8','3.8',W+'-2.0',p('ButtonY')+'-4.4',p('ButtonZ')+'-1.9')
keytools=fuse('KeyTools',[keyhole,keypocket]);rear=cut('RearKeyRelief',rear,keytools);lid=cut('FrontKeyRelief',lid,keytools)
switch_support=box('SwitchBacking','0.65','7.5','2.9',W+'-6.2',p('ButtonY')+'-3.75','9.7')
lid=fuse('FrontWithSwitchSupport',[lid,switch_support])
cap=box('PowerKeyCap','0.70','6.3','2.3',W+'-0.85',p('ButtonY')+'-3.15',p('ButtonZ')+'-1.15')
flange=box('PowerKeyFlange','0.45','8.0','3.2',W+'-1.3',p('ButtonY')+'-4',p('ButtonZ')+'-1.6')
stem=box('PowerKeyStem','1.6','2.2','1.8',W+'-2.9',p('ButtonY')+'-1.1',p('ButtonZ')+'-0.9')
button=fuse('PowerButton',[cap,flange,stem])
rear=final(rear,'RearShell','01 后壳 / 0.75 mm resin prototype',(0.19,0.22,0.27))
lid=final(lid,'FrontShell','02 前盖 / screen bezel',(0.88,0.43,0.20))
button=final(button,'PowerButton','03 电源键 / flush cap',(0.73,0.75,0.79))

def reference(name,label,shape,color,assumption=''):
    o=doc.addObject('Part::Feature',name);o.Label=label;o.Shape=shape;refs.addObject(o);colors[o.Name]=color
    o.addProperty('App::PropertyString','Assumption','Design').Assumption=assumption
    return o
pcbshape=Part.Shape();pcbshape.read(str(ROOT/'hardware/output/board-only.step'))
pcbshape.rotate(App.Vector(),App.Vector(1,0,0),180)
pcbshape.translate(App.Vector(params['PCBX'],params['PCBY'],params['PCBRearZ']+(1+.91)/2))
pcb=reference('PCB','PCB - imported KiCad body, read only',pcbshape,(0.12,0.43,0.30),'Source body 0.91 mm, nominal PCB 1.0 mm')
pos(pcb,p('PCBX'),p('PCBY'),p('PCBRearZ')+'+0.955')
# Native rounded reference solids can also be edited through Parameters.
lcd=rounded('LCDEnvelope',p('LCDWidth'),p('LCDLength'),'1',p('LCDThickness'),'('+W+'-'+p('LCDWidth')+')/2',p('LCDTopOffset'),p('LCDRearZ'))
lens=rounded('LensReference',p('LensWidth'),p('LensLength'),'3',p('LensThickness'),'('+W+'-'+p('LensWidth')+')/2','('+lcdcy+')-'+p('LensLength')+'/2',p('LensBottomZ'))
battery=box('BatteryEnvelope',p('BatteryWidth'),p('BatteryLength'),p('BatteryThickness'),p('BatteryX'),p('BatteryY'),p('BatteryZ'))
for obj,label,color in [(lcd,'ASSUMED LCD envelope',(0.12,0.14,0.18)),(lens,'ASSUMED cover lens',(0.055,0.08,0.11)),(battery,'ASSUMED battery / 26 x 34 x 3 mm',(0.45,0.51,0.59))]:
    construction.removeObject(obj);refs.addObject(obj);obj.Label=label;colors[obj.Name]=color
    obj.addProperty('App::PropertyString','Assumption','Design').Assumption='Dimension placeholder, not a confirmed purchasable component'
component_boxes=[]
for f in layout['footprints']:
    ref=f['reference']
    if ref.startswith('SCREW'):continue
    (x0,y0),(x1,y1)=f['bounds_mm'];x0+=params['PCBX']-100;x1+=params['PCBX']-100;y0+=params['PCBY']-50;y1+=params['PCBY']-50
    h=.7 if ref.startswith('R') else 1.0 if ref.startswith('C') else 1.3
    if ref.startswith('L'):h=2.5
    h={'U9':3.2,'CARD2':1.8,'USB1':3.2,'CN1':5.5,'H1':5.5,'H2':5.5,'FPC2':1.5}.get(ref,h)
    # Actual body edges for the two sockets, instead of the larger courtyard.
    if ref=='USB1':x0,x1,y0,y1=30.949+params['PCBX'],40.021+params['PCBX'],71.349+params['PCBY'],76.921+params['PCBY']
    if ref=='CN1':x0,x1,y0,y1=7.865+params['PCBX'],14.345+params['PCBX'],63.77+params['PCBY'],77.91+params['PCBY']
    z=params['PCBRearZ']-h if f['side']=='top' else params['PCBRearZ']+params['PCBThickness']
    shape=Part.makeBox(x1-x0,y1-y0,h,App.Vector(x0,y0,z))
    component_boxes.append((ref,shape,h))
components=reference('ComponentEnvelopes','ASSUMED component heights / 122 bounding envelopes',Part.makeCompound([s for _,s,_ in component_boxes]),(.42,.44,.48),'XY from footprint/courtyard; Z assumed. H1/H2 must be <=5.8 mm or replaced by wired low-profile connections.')
pos(components,p('PCBX')+'-'+str(params['PCBX']),p('PCBY')+'-'+str(params['PCBY']),p('PCBRearZ')+'-'+str(params['PCBRearZ']))
switchshape=Part.makeBox(2.5,6,1.8,App.Vector(params['Width']-5.45,params['ButtonY']-3,params['ButtonZ']-.9))
switch=reference('PowerSwitchEnvelope','ASSUMED wired power tact switch',switchshape,(0.25,.28,.32),'Not on main PCB. Select an actual switch and wire normally-open contacts to GEK100_KEY and GND.')
pos(switch,p('Width')+'-'+str(params['Width']),p('ButtonY')+'-'+str(params['ButtonY']),p('ButtonZ')+'-'+str(params['ButtonZ']))
# Small spacers/screw envelopes make fastening requirements inspectable.
screws=[]
for ref,x,y in mounts:
    cx=x+params['PCBX'];cy=y+params['PCBY']
    z=params['PCBRearZ']+params['PCBThickness'] if ref=='SCREW2' else params['Height']-params['HeadDepth']
    length=6.0 if ref=='SCREW2' else 10.0
    shape=Part.makeCylinder(.95,length,App.Vector(cx,cy,z-length)).fuse(Part.makeCylinder(1.85,1.4,App.Vector(cx,cy,z)))
    screws.append(shape)
fasteners=reference('Fasteners','3 x M2x10 + 1 x M2x6 / assumed low heads',Part.makeCompound(screws),(.7,.72,.74),'Head <=3.8 diameter / 1.6 high. Nylon fastener preferred at antenna-side SCREW5. Tap resin pilots before assembly.')
doc.recompute()
for obj in doc.Objects:
    if hasattr(obj,'Shape') and not obj.Shape.isNull() and not obj.Shape.isValid():raise RuntimeError('Invalid shape: '+obj.Name)
manufactured=[rear,lid,button]
for obj in manufactured:
    assert len(obj.Shape.Solids)==1,(obj.Name,len(obj.Shape.Solids))
    assert obj.Shape.Volume>0

def overlap(a,b):return round(a.common(b).Volume,7)
checks={'outer_envelope_mm':[params['Width'],params['Length'],max(params['Height'],params['LensBottomZ']+params['LensThickness'])], 'main_body_mm':[params['Width'],params['Length'],params['Height']], 'pcb_source_sha256':hashlib.sha256((ROOT/'hardware/hardware.kicad_pcb').read_bytes()).hexdigest(), 'solid_checks':{}, 'interferences_mm3':{}, 'assumptions':{'LCD':[params['LCDWidth'],params['LCDLength'],params['LCDThickness']],'battery':[params['BatteryWidth'],params['BatteryLength'],params['BatteryThickness']],'header_height_max_modeled':5.5,'all_component_heights':'assumed; source lacks full models'}, 'coordinate_system':'KiCad top component-side XY + (1,1); Y toward bottom connectors; Z toward display; PCB rear copper Z=7.1, front copper Z=8.1'}
for o in manufactured:checks['solid_checks'][o.Name]={'valid':o.Shape.isValid(),'solids':len(o.Shape.Solids),'volume_mm3':o.Shape.Volume}
for name,a,b in [('rear_vs_lid',rear.Shape,lid.Shape),('key_vs_rear',button.Shape,rear.Shape),('key_vs_lid',button.Shape,lid.Shape),('rear_vs_pcb',rear.Shape,pcb.Shape),('lid_vs_pcb',lid.Shape,pcb.Shape),('rear_vs_battery',rear.Shape,battery.Shape),('lid_vs_lcd',lid.Shape,lcd.Shape),('lid_vs_lens',lid.Shape,lens.Shape),('key_vs_switch',button.Shape,switch.Shape),('lid_vs_switch',lid.Shape,switch.Shape),('battery_vs_components',battery.Shape,components.Shape),('lcd_vs_components',lcd.Shape,components.Shape),('lcd_vs_screws',lcd.Shape,fasteners.Shape)]:
    checks['interferences_mm3'][name]=overlap(a,b)
checks['component_shell_conflicts']=[]
for ref,s,h in component_boxes:
    for name,obj in [('rear',rear),('lid',lid)]:
        vol=overlap(s,obj.Shape)
        if vol>.0001:checks['component_shell_conflicts'].append({'ref':ref,'shell':name,'volume_mm3':vol,'assumed_height':h})
checks['antenna_to_lcd_xy_gap_mm']=params['LCDTopOffset']-(params['PCBY']+6.169)
checks['pcb_side_clearance_mm']=(params['Width']-2*params['Wall']-48)/2
checks['lens_fastener_clearance_mm']=lens.Shape.distToShape(fasteners.Shape)[0]
assert checks['lens_fastener_clearance_mm']>=.3,'Lens too close to a screw head'
checks['notes']=['Geometric checks are only for the modeled envelopes, not verified actual components.','TF and USB openings include manual plug/card access allowance; test with real parts.','0.75 mm side walls are a thin resin fit prototype, not an FDM or CNC production design.']
bb=pcb.Shape.BoundBox
checks['pcb_actual_bounds_mm']=[bb.XMin,bb.YMin,bb.ZMin,bb.XMax,bb.YMax,bb.ZMax]
assert abs(bb.XMin-params['PCBX'])<1e-6 and abs(bb.YMin-params['PCBY'])<1e-6
assert abs(bb.ZMin-(params['PCBRearZ']+.045))<1e-6 and abs(bb.ZMax-(params['PCBRearZ']+.955))<1e-6
case_envelope=Part.makeBox(params['Width'],params['Length'],checks['outer_envelope_mm'][2])
checks['outside_overall_envelope_mm3']={o.Name:round(o.Shape.cut(case_envelope).Volume,7) for o in manufactured+[pcb,lcd,lens,battery,components,switch]}
checks['geometric_checks_passed']=not checks['component_shell_conflicts'] and all(v<.0001 for v in checks['interferences_mm3'].values()) and all(v<.0001 for v in checks['outside_overall_envelope_mm3'].values())
(OUT/'validation.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf8')
assert checks['geometric_checks_passed'],'Modeled interference detected; review exports/validation.json before manufacturing'
(OUT/'display-colors.json').write_text(json.dumps(colors),encoding='utf8')
if App.GuiUp:
    for obj in doc.Objects:
        if obj.ViewObject:obj.ViewObject.Visibility=False
    for obj in manufactured+[lens]:
        obj.ViewObject.Visibility=True;obj.ViewObject.ShapeColor=colors[obj.Name];obj.ViewObject.LineColor=(.12,.12,.14)
    Gui.activeDocument().activeView().viewAxonometric();Gui.activeDocument().activeView().fitAll()
doc.recompute()
doc.saveAs(str(HERE/'ESP32S31_MP3_Enclosure_A.FCStd'))
for obj,stemname in [(rear,'rear-shell'),(lid,'front-shell'),(button,'power-button')]:
    obj.Shape.exportStep(str(OUT/(stemname+'.step')))
    mesh=MeshPart.meshFromShape(Shape=obj.Shape,LinearDeflection=.06,AngularDeflection=.15,Relative=False)
    assert mesh.isSolid(),stemname
    mesh.write(str(OUT/(stemname+'.stl')))
Part.makeCompound([o.Shape for o in manufactured+[pcb,lcd,lens,battery,components,switch,fasteners]]).exportStep(str(OUT/'assembly-reference.step'))
print('ENCLOSURE_BUILD_COMPLETE',json.dumps(checks,ensure_ascii=False))
