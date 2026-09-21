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
provenance=json.loads((HERE/'reference/source-manifest.json').read_text(encoding='utf8'))
assert hashlib.sha256((ROOT/'hardware/hardware.kicad_pcb').read_bytes()).hexdigest()==provenance['pcb_source_sha256'],'PCB changed: refresh the frozen reference BREP shapes before rebuilding.'
assert hashlib.sha256((ROOT/'hardware/output/layout-data.json').read_bytes()).hexdigest()==provenance['layout_data_sha256'],'Layout data changed: refresh the reference shapes before rebuilding.'
DOCNAME='Q2_Enclosure_B'
if any(n in App.listDocuments() for n in [DOCNAME,'ESP32S31_MP3_Q2_B']):
    raise RuntimeError('The enclosure document is already open. Save/close it before rebuilding.')
doc=App.newDocument(DOCNAME)
doc.Label='ESP32-S31 MP3 / Q2 appearance B / PCB redesign required'
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

def ref(name,label,shape,color,note=''):
    o=doc.addObject('Part::Feature',name);o.Label=label;o.Shape=shape;refs.addObject(o);colors[o.Name]=color
    o.addProperty('App::PropertyString','DesignNote','Design').DesignNote=note
    return o

def ref_native(o,label,color):
    construction.removeObject(o);refs.addObject(o);o.Label=label;colors[o.Name]=color;return o

W,L,H=p('Width'),p('Length'),p('Height')
z0=p('RearThickness')+'+'+p('Seam')
outer=rounded('HousingBlank',W,L,p('CornerRadius'),H+'-('+z0+')',z=z0)
doc.recompute()
rounded_edges=feature('Part::Fillet','HousingEdgeRoll')
rounded_edges.Base=outer
rounded_edges.Edges=[(i+1,.55,.55) for i,e in enumerate(outer.Shape.Edges) if e.Vertexes and max(v.Point.z for v in e.Vertexes)-min(v.Point.z for v in e.Vertexes)<1e-6]
doc.recompute()
assert not rounded_edges.Shape.isNull(),'Body edge fillet failed'
cavity=rounded('HousingCavity',W+'-2*Parameters.Wall',L+'-2*Parameters.Wall','Parameters.CornerRadius-Parameters.Wall',H+'-Parameters.FrontThickness+1','Parameters.Wall','Parameters.Wall',-1)
housing=cut('HousingHollow',rounded_edges,cavity)
bosses=[]
for i,y in enumerate([3,77]):
    boss=cylinder('RearScrewBoss'+str(i),2.4,9.4,25,y,1.2)
    pilot=cylinder('RearScrewPilot'+str(i),.65,8.4,25,y,.8)
    bosses.append(cut('RearScrewSocket'+str(i),boss,pilot))
housing=fuse('HousingWithBosses',[housing]+bosses)
# Landscape installation: the module's 43.45 mm dimension is horizontal.
pocket=rounded('LCDClearance','Parameters.LCDLength+2*Parameters.LCDFitClearance','Parameters.LCDWidth+2*Parameters.LCDFitClearance','Parameters.LCDRadiusEstimated+Parameters.LCDFitClearance',4,'Parameters.LCDInstalledX-Parameters.LCDFitClearance','Parameters.LCDInstalledY-Parameters.LCDFitClearance',11)
glass_seat=rounded('LensSeat','Parameters.LensWidth+0.3','Parameters.LensLength+0.3','Parameters.LensRadius+0.15',1,'Parameters.LensX-0.15','Parameters.LensY-0.15',13.42)
wheel_seat=cylinder('WheelSeat','Parameters.WheelDiameter/2+0.2',2,'Parameters.Width/2',p('WheelY'),12.85)
keyhole=cylinder('CenterKeyHole',6,5,'Parameters.Width/2',p('WheelY'),10)
housing=cut('HousingFrontOpenings',housing,fuse('FrontCutter',[pocket,glass_seat,wheel_seat,keyhole]))
# Port coordinates follow the existing MP3 electrical design, not Q2's dual-jack electronics.
usb=rounded('USBTool',12,5.5,1,5)
orient(usb,App.Rotation(App.Vector(1,0,0),90),30.449,81,2.75)
jack=cylinder('JackTool',3.6,5)
orient(jack,App.Rotation(App.Vector(1,0,0),90),12.065,81,4.4)
tf=rounded('MicroSDTool',15.6,2.4,.5,8)
orient(tf,App.Rotation(App.Vector(0,0,1),90).multiply(App.Rotation(App.Vector(1,0,0),90)),-1,9.35,4.95)
housing=cut('Q2Housing',housing,fuse('PortCutters',[usb,jack,tf]))
housing=final(housing,'Q2Housing','01 Q2 大圆角机身 / prototype, PCB redesign required',(.74,.77,.80))

rear=rounded('RearBlank',W,L,p('CornerRadius'),p('RearThickness'))
lipout=rounded('RearLipOuter',47.2,77.2,10.6,1.2,1.4,1.4,1)
lipin=rounded('RearLipInner',45.6,75.6,9.8,1.6,2.2,2.2,.8)
rear=fuse('RearWithLip',[rear,cut('RearLocatingLip',lipout,lipin)])
holes=[]
for i,y in enumerate([3,77]):
    holes += [cylinder('RearScrewThrough'+str(i),.9,4,25,y,-1),cylinder('RearHeadSeat'+str(i),1.65,.75,25,y,-.1),cylinder('RearBossClearance'+str(i),2.65,2,25,y,1.1)]
rear=cut('Q2RearCover',rear,fuse('RearCutters',holes))
rear=final(rear,'Q2RearCover','02 后盖 / two recessed M1.6 screws',(.67,.70,.73))
wheel=cylinder('WheelBlank','Parameters.WheelDiameter/2',p('WheelThickness'),'Parameters.Width/2',p('WheelY'),p('WheelZ'))
wheel=cut('Q2Wheel',wheel,cylinder('WheelCenterBore',6.15,3,'Parameters.Width/2',p('WheelY'),12))
wheel=final(wheel,'Q2Wheel','03 黑色操作环面片 / sensor electronics pending',(.045,.050,.057))
button=fuse('Q2CenterButton',[cylinder('ButtonFace','Parameters.CenterButtonDiameter/2',.9,'Parameters.Width/2',p('WheelY'),12.6),cylinder('ButtonStem',4,.65,'Parameters.Width/2',p('WheelY'),12),cylinder('ButtonRetainer',6.9,.25,'Parameters.Width/2',p('WheelY'),11.9)])
button=final(button,'Q2CenterButton','04 中心电源键 / switch travel must be tuned',(.77,.79,.82))
lcd=rounded('LCDModule',p('LCDLength'),p('LCDWidth'),p('LCDRadiusEstimated'),p('LCDThickness'),p('LCDInstalledX'),p('LCDInstalledY'),p('LCDRearZ'))
ref_native(lcd,'LCD 36.33 x 43.45 x 1.46 / rotated 90 degrees',(.12,.13,.15))
aa=rounded('LCDActiveArea',p('AALength'),p('AAWidth'),p('AARadiusEstimated'),.01,'Parameters.LCDInstalledX+Parameters.AATopInset','Parameters.LCDInstalledY+(Parameters.LCDWidth-Parameters.AAWidth)/2','Parameters.LCDRearZ+Parameters.LCDThickness-0.01')
ref_native(aa,'LCD AA 34.18 x 40.05 / no touch layer supplied',(.04,.055,.07))
lens=rounded('CoverLens',p('LensWidth'),p('LensLength'),p('LensRadius'),p('LensThickness'),p('LensX'),p('LensY'),p('LensZ'))
ref_native(lens,'外加保护盖板 / 46 x 40 x 0.6 assumed, NOT supplied TP',(.025,.032,.042))
# Black masking is represented by a ring; its clear opening matches the supplied AA.
mask=cut('LensBlackMask',lens,rounded('MaskOpening',p('AALength'),p('AAWidth'),p('AARadiusEstimated'),2,'Parameters.LCDInstalledX+Parameters.AATopInset','Parameters.LCDInstalledY+(Parameters.LCDWidth-Parameters.AAWidth)/2',13))
ref_native(mask,'盖板黑边示意 / silkscreen mask',(.017,.020,.025))
adhesive=cut('LensAdhesive',rounded('AdhesiveBlank',p('LensWidth'),p('LensLength'),p('LensRadius'),.18,p('LensX'),p('LensY'),13.42),pocket)
ref_native(adhesive,'盖板周边胶框 / 0.18 mm assumed',(.10,.11,.12))

# Illustrative full-length folded cable. R and neck dimensions are estimates, not vendor bend data.
r=params['FPCBendRadiusEstimated'];t=params['FPCThicknessEstimated'];edge=params['LCDInstalledX']+params['LCDLength']
cy=params['LCDInstalledY']+params['LCDWidth']/2;zc=12.1-r
ring=Part.makeCylinder(r+t/2,18,App.Vector(edge,cy-9,zc),App.Vector(0,1,0)).cut(Part.makeCylinder(r-t/2,20,App.Vector(edge,cy-10,zc),App.Vector(0,1,0)))
bend=ring.common(Part.makeBox(3,20,4,App.Vector(edge,cy-10,zc-2)))
necklen=params['FPCNeckLengthEstimated']-math.pi*r
straight=params['FPCExtension']-math.pi*r
fpcs=bend.fuse(Part.makeBox(necklen,18,t,App.Vector(edge-necklen,cy-9,zc-r-t/2))).fuse(Part.makeBox(straight-necklen+.1,params['FPCWidth'],t,App.Vector(edge-straight,cy-params['FPCWidth']/2,zc-r-t/2))).removeSplitter()
fpc=ref('InstalledFPCRoutingStudy','FPC 46.14 mm / one-fold routing STUDY, connector not mated',fpcs,(.88,.52,.13),'46.14 mm neutral-line length including pi*R bend. Neck width 18, neck length 12.8, thickness 0.12 and R0.8 are unconfirmed. Proposed terminal differs from existing FPC2; not a verified assembly.')
sensor=cylinder('WheelSensorKeepout',16,.7,25,p('WheelY'),11.0)
ref_native(sensor,'操作环电路预留 / main PCB has no wheel circuit',(.12,.42,.32))
switch=ref('CenterSwitchKeepout','中心开关预留 / wire to KEY+GND, select real switch',Part.makeBox(6,6,1.8,App.Vector(22,58.3,10.0)),(.18,.19,.2),'Assumed tact-switch space, not an identified part.')

# Frozen read-only reference shapes from revision A; rebuilding does not touch open A documents.
for oldname,newname,label,col in [('PCB','ExistingPCB','现有 PCB / clashes with Q2 corners',(.20,.44,.28)),('ComponentEnvelopes','ExistingComponents','现有器件包络 / heights assumed',(.4,.44,.48)),('BatteryEnvelope','BatteryReference','电池占位 26 x 34 x 3 / unconfirmed',(.38,.43,.50))]:
    source_shape=Part.Shape();source_shape.read(str(HERE/'reference'/('source-'+oldname+'.brep')))
    ref(newname,label,source_shape,col,'Frozen from revision A; do not infer real assembly clearance from assumed heights.')
target=rounded('PCBTargetEnvelope',47,76,10.5,1,1.5,2,7.1)
ref_native(target,'PCB 新轮廓建议 / constraint solid only, NOT routed board',(.08,.50,.39))
rf=ref('AntennaKeepoutReference','现有天线区域 / screen overlap requires RF review',Part.makeBox(22,6.169,2,App.Vector(26.719,1.431,8.2)),(.91,.23,.12),'LCD metal backing overlaps antenna XY; mechanical gap is not RF clearance.')

# Printed/laser-marked icons are separate visual references, never included in shell STL.
def stroke(points,width=.16):
    points=[(50-x,y) for x,y in points]
    ss=[]
    for a,b in zip(points,points[1:]):
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        s=Part.makeBox(length,width,.025,App.Vector(0,-width/2,0));s.rotate(App.Vector(),App.Vector(0,0,1),math.degrees(math.atan2(dy,dx)));s.translate(App.Vector(a[0],a[1],13.55));ss.append(s)
    return Part.makeCompound(ss)
icons=[]
for cx,sign in [(12,1),(38,-1)]:
    for shift in [-.5,.5]:icons.append(stroke([(cx+sign*.6+shift,60.4),(cx-sign*.3+shift,61.3),(cx+sign*.6+shift,62.2)]))
icons += [stroke([(24,47.9),(26,47.9),(26.7,48.6),(26.4,49.4),(24.6,49.4),(24,48.9)]),stroke([(24,47.9),(24.5,47.4)]),stroke([(24,47.9),(24.7,48.3)])]
icons += [stroke([(23.8,73.4),(25.1,74.3),(23.8,75.2),(23.8,73.4)]),stroke([(25.8,73.4),(25.8,75.2)]),stroke([(26.5,73.4),(26.5,75.2)])]
ink=ref('ControlSymbols','按键图标 / return, previous, next, play-pause',Part.makeCompound(icons),(.72,.75,.77))
doc.recompute()
manufactured=[housing,rear,wheel,button]
checks={'status':'APPEARANCE_AND_LCD_PROTOTYPE_NOT_ASSEMBLY_RELEASE','body_mm':[50,80,13.5],'with_cover_mm':[50,80,14.2],'display_module_mm':[36.33,43.45,1.46],'display_active_mm':[34.18,40.05],'installed_rotation_degrees':90,'fpc_extension_mm':46.14,'solid_checks':{},'part_interferences_mm3':{},'existing_pcb_conflicts_mm3':{},'pcb_source_sha256':hashlib.sha256((ROOT/'hardware/hardware.kicad_pcb').read_bytes()).hexdigest()}
for o in manufactured:
    checks['solid_checks'][o.Name]={'valid':o.Shape.isValid(),'solids':len(o.Shape.Solids),'volume':o.Shape.Volume}
    assert o.Shape.isValid() and len(o.Shape.Solids)==1,o.Name
for a,b in [(housing,rear),(housing,wheel),(housing,button),(housing,lcd),(housing,lens),(housing,fpc),(rear,button),(wheel,button),(lcd,fpc)]:
    vol=round(a.Shape.common(b.Shape).Volume,6);checks['part_interferences_mm3'][a.Name+' / '+b.Name]=vol
for name in ['ExistingPCB','ExistingComponents']:
    obj=doc.getObject(name)
    checks['existing_pcb_conflicts_mm3'][name]=round(obj.Shape.common(housing.Shape).Volume,6)
    clash=ref(name+'Collision','红色实体：'+obj.Label+' 与新壳干涉',obj.Shape.common(housing.Shape),(.95,.08,.03),'Measured geometric intersection with Q2Housing, not a manufacturable part.')
checks['outside_envelope_mm3']={o.Name:round(o.Shape.cut(Part.makeBox(50,80,14.2)).Volume,6) for o in manufactured+[lcd,lens,fpc]}
checks['external_geometry_pass']=all(v<1e-5 for v in checks['part_interferences_mm3'].values()) and all(v<1e-5 for v in checks['outside_envelope_mm3'].values())
checks['pcb_fits']=all(v<1e-5 for v in checks['existing_pcb_conflicts_mm3'].values())
checks['component_conflicts']=[]
component_refs=[f['reference'] for f in layout['footprints'] if not f['reference'].startswith('SCREW')]
assert len(component_refs)==len(doc.ExistingComponents.Shape.Solids)
for name,s in zip(component_refs,doc.ExistingComponents.Shape.Solids):
    v=round(s.common(housing.Shape).Volume,6)
    if v>1e-5:checks['component_conflicts'].append({'reference':name,'intersection_mm3':v,'height_is_assumed':True})
checks['fpc_proposed_terminal_x_mm']=edge-straight
checks['unconfirmed']=['LCD/AA corner radii','LCD cover glass, adhesive and front masks','FPC thickness, neck geometry, bend radius, contact side and mating connector','Wheel PCB and switches','Battery size/capacity and all component heights','Current PCB corners, mounting and RF placement require redesign']
(OUT/'validation.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf8')
assert checks['external_geometry_pass'],checks['part_interferences_mm3']
(OUT/'display-colors.json').write_text(json.dumps(colors),encoding='utf8')
doc.recompute();doc.saveAs(str(HERE/'ESP32S31_MP3_Q2_B.FCStd'))
for obj,stem in [(housing,'q2-housing'),(rear,'q2-rear-cover'),(wheel,'q2-wheel-face'),(button,'q2-center-button')]:
    obj.Shape.exportStep(str(OUT/(stem+'.step')))
    mesh=MeshPart.meshFromShape(Shape=obj.Shape,LinearDeflection=.035,AngularDeflection=.12,Relative=False)
    assert mesh.isSolid(),stem
    mesh.write(str(OUT/(stem+'.stl')))
lens.Shape.exportStep(str(OUT/'cover-lens-assumed.step'))
target.Shape.exportStep(str(OUT/'pcb-target-envelope-NOT-ROUTED.step'))
Part.makeCompound([o.Shape for o in manufactured+[lcd,lens,fpc]]).exportStep(str(OUT/'q2-appearance-assembly.step'))
print('Q2_BUILD_COMPLETE',json.dumps(checks,ensure_ascii=False))
