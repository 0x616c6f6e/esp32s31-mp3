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
DOCNAME='LCD209_FitReview'
if any(n in App.listDocuments() for n in [DOCNAME,'LCD209_dimensioned']):
    raise RuntimeError('The enclosure document is already open. Save/close it before rebuilding.')
doc=App.newDocument(DOCNAME)
doc.Label='2.09 inch LCD / supplied mechanical dimensions'
table=doc.addObject('Spreadsheet::Sheet','Parameters');table.Label='尺寸参数 / mm - editable'
table.set('A1','Parameter');table.set('B1','mm')
for row,(key,value) in enumerate(params.items(),2):
    table.set('A'+str(row),key);table.set('B'+str(row),str(value));table.setAlias('B'+str(row),key)
table.setColumnWidth('A',190);table.setColumnWidth('B',95)
construction=doc.addObject('App::DocumentObjectGroup','Construction');construction.Label='Native editable construction / 参数特征'
parts=doc.addObject('App::DocumentObjectGroup','EnclosureParts');parts.Label='LCD final parts'
refs=doc.addObject('App::DocumentObjectGroup','ReferenceParts');refs.Label='LCD / dimensioned outline and illustrative FPC'
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

bl=rounded('BacklightBody',p('LCDWidth'),p('LCDLength'),p('LCDRadiusEstimated'),'Parameters.LCDThickness-0.3')
glass=rounded('LCDGlass',p('LCDGlassWidth'),p('LCDGlassLength'),'Parameters.LCDRadiusEstimated-0.1',.3,.1,.1,'Parameters.LCDThickness-0.3')
aa=rounded('ActiveArea',p('AAWidth'),p('AALength'),p('AARadiusEstimated'),.01,'(Parameters.LCDWidth-Parameters.AAWidth)/2',p('AATopInset'),'Parameters.LCDThickness-0.01')
fpc=fuse('FlatFPC',[box('FPCNeck',p('FPCNeckWidthEstimated'),p('FPCNeckLengthEstimated'),p('FPCThicknessEstimated'),'(Parameters.LCDWidth-Parameters.FPCNeckWidthEstimated)/2',p('LCDLength'),.25),box('FPCTail',p('FPCWidth'),'Parameters.FPCExtension-Parameters.FPCNeckLengthEstimated+0.1',p('FPCThicknessEstimated'),'(Parameters.LCDWidth-Parameters.FPCWidth)/2','Parameters.LCDLength+Parameters.FPCNeckLengthEstimated-0.1',.25)])
terminals=[]
for i in range(21):
    terminals.append(box('Contact%02d'%(21-i),.18,p('FPCContactLength'),.015,f'(Parameters.LCDWidth-Parameters.FPCTerminalSpan)/2+{i}*Parameters.FPCPitch-0.09','Parameters.LCDLength+Parameters.FPCExtension-Parameters.FPCContactLength','0.25+Parameters.FPCThicknessEstimated'))
pads=fuse('TerminalContacts',terminals)
for o,label,col in [(bl,'BL outline 36.33 +/-0.1 x 43.45 +/-0.1',(.13,.14,.16)),(glass,'LCD glass 36.13 x 43.25 / full LCM t=1.46 +/-0.1',(.045,.05,.06)),(aa,'Active area 34.18 x 40.05 / top inset 1.05',(.035,.055,.073)),(fpc,'FPC extension 46.14 +/-0.5 / tail width 6.6 +/-0.05',(.86,.47,.13)),(pads,'21 contacts / center span 6 / pitch 0.3 / exposure 2.5',(.90,.73,.33))]:
    ref_native(o,label,col)
bl.addProperty('App::PropertyString','DimensionalProvenance','Source').DimensionalProvenance='User drawing; outline and thickness specified. R10 estimated, not dimensioned. Internal BL/glass thickness split 1.16/0.30 is illustrative only.'
fpc.addProperty('App::PropertyString','DimensionalProvenance','Source').DimensionalProvenance='User drawing: length 46.14, tail width 6.6, terminal exposure 2.5, center span 6 and pitch0.3. Neck 18x12.8, t0.12, pad width0.18, copper thickness0.015 estimated. Pin1 at right in supplied front-view drawing; other pins inferred sequentially. This contact geometry is an envelope, not a terminal phototool. FPC insertion thickness, stiffener and physical contact face need confirmation. The drawing 0.3 +/-0.03 is an edge offset, NOT a pitch tolerance; pitch0.3 is inferred from21 contacts over6 mm.'
glass.addProperty('App::PropertyString','Specification','Source').Specification='2.09 inch, 320 RGB x 375, IPS, QSPI, driver 9855, no TP. Datasheet connector OK-F302-21115.'
doc.recompute()
assert all(o.Shape.isValid() for o in [bl,glass,aa,fpc,pads])
module=Part.makeCompound([bl.Shape,glass.Shape])
bb=module.BoundBox
assert abs(bb.XLength-36.33)<1e-6 and abs(bb.YLength-43.45)<1e-6 and abs(bb.ZLength-1.46)<1e-6
assert abs(fpc.Shape.BoundBox.YLength-46.14)<1e-6
doc.saveAs(str(HERE/'LCD209_dimensioned.FCStd'))
Part.makeCompound([bl.Shape,glass.Shape,aa.Shape,fpc.Shape,pads.Shape]).exportStep(str(OUT/'lcd209-flat-reference.step'))
module.exportStep(str(OUT/'lcd209-module-only.step'))
(OUT/'display-model-colors.json').write_text(json.dumps(colors),encoding='utf8')
print('LCD_BUILD_COMPLETE',bb.XLength,bb.YLength,bb.ZLength,'FPC',fpc.Shape.BoundBox.YLength)

