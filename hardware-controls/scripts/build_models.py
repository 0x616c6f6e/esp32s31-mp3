"""FreeCAD nominal models from the manufacturer's package drawings."""
from pathlib import Path
import FreeCAD as A,Part,Import
P=Path(__file__).resolve().parents[1]
V=A.Vector
def box(x,y,z,w,h,d):return Part.makeBox(w,h,d,V(x,y,z))
def export(name,shapes):
    doc=A.newDocument(name)
    objs=[]
    for i,(shape,color) in enumerate(shapes):
        o=doc.addObject('PartDesign::Feature',name+'_'+str(i));o.Shape=shape;objs.append(o)
        if o.ViewObject:o.ViewObject.ShapeColor=color
    doc.recompute();Import.export(objs,str(P/'models3d'/(name+'.step')));A.closeDocument(doc.Name)
black=(.12,.12,.14);metal=(.72,.73,.75);gold=(.8,.63,.2)
shapes=[(box(-1.5,-1.5,.05,3,3,.8),black),(box(-.775,-.775,0,1.55,1.55,.05),metal)]
for j in range(5):
    a=-.9+j*.45
    shapes.extend([(box(-1.5,a-.11,0,.4,.22,.05),metal),(box(1.1,a-.11,0,.4,.22,.05),metal),(box(a-.11,-1.5,0,.22,.4,.05),metal),(box(a-.11,1.1,0,.22,.4,.05),metal)])
export('QT2120_VQFN20',shapes)
# TCA6408A RGT: nominal 3 x 3 body, maximum 1.0 mm package height.
shapes=[(box(-1.5,-1.5,.05,3,3,.95),black),(box(-.725,-.725,0,1.45,1.45,.05),metal)]
for j in range(4):
    a=-.75+j*.5
    shapes.extend([(box(-1.5,a-.12,0,.4,.24,.05),metal),(box(1.1,a-.12,0,.4,.24,.05),metal),(box(a-.12,-1.5,0,.24,.4,.05),metal),(box(a-.12,1.1,0,.24,.4,.05),metal)])
export('TCA6408A_VQFN16',shapes)
export('SKSW_3x2',[(box(-1.5,-1,0,3,2,.4),metal),(Part.makeCylinder(.45,.2,V(0,0,.4)),black),(box(-1.75,-.65,0,.4,1.3,.04),gold),(box(1.35,-.65,0,.4,1.3,.04),gold)])
shapes=[(box(-4,-1.5,.05,8,2.5,.65),black),(box(-3.6,-1.5,.65,7.2,.8,.25),black)]
shapes += [(box(-2.825+i*.5,.6,0,.15,.9,.1),gold) for i in range(12)]
shapes += [(box(x-.15,-1.65,0,.3,.5,.1),metal) for x in [-3.75,3.75]]
export('FH19C_12',shapes)
print('MODELS_SAVED')
