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
DOCNAME='Q2_Enclosure_D'
if any(n in App.listDocuments() for n in [DOCNAME,'ESP32S31_MP3_Q2_D']):
    raise RuntimeError('The enclosure document is already open. Save/close it before rebuilding.')
doc=App.newDocument(DOCNAME)
doc.Label='ESP32-S31 MP3 / Q2 D / screen raised 1.5 mm / full housing visible'
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
wheel_seat=cylinder('WheelSeat','Parameters.WheelDiameter/2+0.2',4,'Parameters.Width/2',p('WheelY'),11.7)
keyhole=cylinder('CenterKeyHole',6,5,'Parameters.Width/2',p('WheelY'),10)
housing=cut('HousingFrontOpenings',housing,fuse('FrontCutter',[pocket,glass_seat,wheel_seat,keyhole]))
# Port coordinates follow the existing MP3 electrical design, not Q2's dual-jack electronics.
usb=rounded('USBTool',12,5.5,1,5)
orient(usb,App.Rotation(App.Vector(1,0,0),90),7.551,81,4.05)
jack=cylinder('JackTool',3.6,5)
orient(jack,App.Rotation(App.Vector(1,0,0),90),37.935,81,7.9)
tf=rounded('MicroSDTool',15.6,2.4,.5,8)
orient(tf,App.Rotation(App.Vector(0,0,1),90).multiply(App.Rotation(App.Vector(1,0,0),90)),43,9.35,4.95)
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
wheelface=cut('WheelFace',cylinder('WheelBlank','Parameters.WheelDiameter/2',p('WheelThickness'),'Parameters.Width/2',p('WheelY'),p('WheelZ')),cylinder('WheelCenterBore',6.15,4,25,p('WheelY'),11))
collar=cut('WheelCollar',cylinder('WheelCollarOuter',16.5,.76,25,p('WheelY'),12.2),cylinder('WheelCollarInner',15.8,1.1,25,p('WheelY'),12.0))
flange=cut('WheelRetentionFlange',cylinder('WheelFlangeOuter',17.2,.20,25,p('WheelY'),12.03),cylinder('WheelFlangeInner',15.8,.5,25,p('WheelY'),11.9))
actuators=[cylinder('WheelActuator'+str(i),.85,.41,x,y,12.55) for i,(x,y) in enumerate([(25,48.3),(12,61.3),(38,61.3),(25,74.3)])]
wheel=final(fuse('Q2Wheel',[wheelface,collar,flange]+actuators),'Q2Wheel','03 滑环面片 / four-way rocking actuator concept',(.045,.05,.057))
keyflange=cut('CenterRetainerRing',cylinder('CenterRetainerOuter',6.9,.2,25,p('WheelY'),12.0),cylinder('CenterRetainerVoid',3.2,.4,25,p('WheelY'),11.9))
keysleeve=cut('CenterSleeve',cylinder('CenterSleeveOuter',5.3,.6,25,p('WheelY'),12.15),cylinder('CenterSleeveInner',3.2,.8,25,p('WheelY'),12.05))
button=final(fuse('Q2CenterButton',[cylinder('CenterFace',5.7,.8,25,p('WheelY'),12.7),cylinder('CenterActuator',1.2,.2,25,p('WheelY'),12.55),keyflange,keysleeve]),'Q2CenterButton','04 中心键 / 0.10 mm nominal actuator gap',(.77,.79,.82))
lcd=rounded('LCDModule',p('LCDLength'),p('LCDWidth'),p('LCDRadiusEstimated'),p('LCDThickness'),p('LCDInstalledX'),p('LCDInstalledY'),p('LCDRearZ'))
ref_native(lcd,'LCD 36.33 x 43.45 x 1.46 / rotated 90 degrees',(.12,.13,.15))
aa=rounded('LCDActiveArea',p('AALength'),p('AAWidth'),p('AARadiusEstimated'),.01,'Parameters.LCDInstalledX+Parameters.LCDLength-Parameters.AATopInset-Parameters.AALength','Parameters.LCDInstalledY+(Parameters.LCDWidth-Parameters.AAWidth)/2','Parameters.LCDRearZ+Parameters.LCDThickness-0.01')
ref_native(aa,'LCD AA 34.18 x 40.05 / no touch layer supplied',(.04,.055,.07))
lens=rounded('CoverLens',p('LensWidth'),p('LensLength'),p('LensRadius'),p('LensThickness'),p('LensX'),p('LensY'),p('LensZ'))
ref_native(lens,'外加保护盖板 / 46 x 40 x 0.6 assumed, NOT supplied TP',(.025,.032,.042))
# Black masking is represented by a ring; its clear opening matches the supplied AA.
mask=cut('LensBlackMask',lens,rounded('MaskOpening',p('AALength'),p('AAWidth'),p('AARadiusEstimated'),2,'Parameters.LCDInstalledX+Parameters.LCDLength-Parameters.AATopInset-Parameters.AALength','Parameters.LCDInstalledY+(Parameters.LCDWidth-Parameters.AAWidth)/2',13))
ref_native(mask,'盖板黑边示意 / silkscreen mask',(.017,.020,.025))
adhesive=cut('LensAdhesive',rounded('AdhesiveBlank',p('LensWidth'),p('LensLength'),p('LensRadius'),.18,p('LensX'),p('LensY'),13.42),pocket)
ref_native(adhesive,'盖板周边胶框 / 0.18 mm assumed',(.10,.11,.12))

exec(compile((HERE/'assembly_layout.py').read_text(encoding='utf8'),str(HERE/'assembly_layout.py'),'exec'))

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
exec(compile((HERE/'validate_and_export.py').read_text(encoding='utf8'),str(HERE/'validate_and_export.py'),'exec'))
