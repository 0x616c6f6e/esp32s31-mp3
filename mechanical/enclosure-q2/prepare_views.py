"""Run in FreeCAD GUI after both headless builds. Geometry is not changed."""
import FreeCAD as App, FreeCADGui as Gui, Part, json, math
from pathlib import Path
from PySide import QtCore
HERE=Path(__file__).resolve().parent;OUT=HERE/'exports'
def settle():
    loop=QtCore.QEventLoop();QtCore.QTimer.singleShot(650,loop.quit)
    if hasattr(loop,'exec'):loop.exec()
    else:loop.exec_()
def open_doc(filename):
    path=HERE/filename
    d=next((d for d in App.listDocuments().values() if d.FileName and Path(d.FileName).resolve()==path.resolve()),None)
    if d is None:d=App.openDocument(str(path))
    App.setActiveDocument(d.Name);return d
def visible(d,names,colors):
    for o in d.Objects:
        if o.ViewObject:
            o.ViewObject.Visibility=o.Name in names
            if o.Name in colors:
                o.ViewObject.ShapeColor=tuple(colors[o.Name]);o.ViewObject.LineColor=(.13,.14,.15)
                if 'DisplayMode' in o.ViewObject.PropertiesList:o.ViewObject.DisplayMode='Shaded'
def view(z=None,front=False):
    v=Gui.activeDocument().activeView();v.setCameraType('Orthographic')
    if front:v.setCameraOrientation(App.Rotation(App.Vector(1,0,0),0).Q)
    else:
        z=App.Vector(*z);x=App.Vector(0,0,1).cross(z);y=z.cross(x)
        v.setCameraOrientation(App.Rotation(x,y,z,'ZXY').Q)
    settle();v.fitAll();settle();Gui.updateGui();return v
def save(v,name,w=1300,h=1500):v.saveImage(str(OUT/name),w,h,'White')

lcd=open_doc('LCD209_36x43.FCStd');lc=json.loads((OUT/'display-model-colors.json').read_text())
visible(lcd,list(lc),lc)
# Front: +X goes right, +Y is down; a camera above the face must mirror X or Y.
# Use 180deg about Z, as in assembly views, to put module top at image top.
v=Gui.activeDocument().activeView();v.setCameraOrientation(App.Rotation(App.Vector(0,0,1),180).Q);settle();v.fitAll();settle();save(v,'lcd-flat-front.png',850,1500)
save(view((-1,1,2)),'lcd-flat-isometric.png',1100,1500);lcd.save()
d=open_doc('ESP32S31_MP3_Q2_B.FCStd');colors=json.loads((OUT/'display-colors.json').read_text())
assembled=['Q2Housing','Q2RearCover','Q2Wheel','Q2CenterButton','CoverLens','ControlSymbols']
# Pure graphical demo on the cover face. Does not change any manufactured geometry.
if not d.getObject('ScreenDemo'):
    symbols=[]
    def rr(w,h,r,x,y):
        a=Part.makeBox(w-2*r,h,.005,App.Vector(x+r,y,14.201));b=Part.makeBox(w,h-2*r,.005,App.Vector(x,y+r,14.201));s=a.fuse(b)
        for xx,yy in [(x+r,y+r),(x+w-r,y+r),(x+r,y+h-r),(x+w-r,y+h-r)]:s=s.fuse(Part.makeCylinder(r,.005,App.Vector(xx,yy,14.201)))
        return s.removeSplitter()
    for j,h in enumerate([2.2,5,8.5,13,17,13,8.5,5,2.2]):symbols.append(rr(1.4,h,.65,18.3+j*2,23-h/2))
    symbols+=[rr(24,.35,.15,13,33.1),rr(8,.8,.3,29,33),rr(3,.7,.2,11,8)]
    demo=d.addObject('Part::Feature','ScreenDemo');demo.Label='屏幕示意图 / cosmetic only, not exported';demo.Shape=Part.makeCompound(symbols)
    d.ReferenceParts.addObject(demo)
colors['ScreenDemo']=[.35,.66,.70];assembled.append('ScreenDemo')
visible(d,assembled,colors)
v=Gui.activeDocument().activeView();v.setCameraOrientation(App.Rotation(App.Vector(0,0,1),180).Q);settle();v.fitAll();settle();save(v,'q2-front.png',1000,1500)
save(view((-1,1,1.6)),'q2-assembled.png',1250,1500)
visible(d,['Q2Housing','ExistingPCB','ExistingPCBCollision','ExistingComponentsCollision'],colors)
d.Q2Housing.ViewObject.Transparency=80
save(view((-1,1,1.8)),'pcb-conflict-review.png',1250,1500)
d.Q2Housing.ViewObject.Transparency=0
visible(d,['LCDModule','LCDActiveArea','InstalledFPCRoutingStudy'],colors)
save(view((-1,1,-1.1)),'lcd-fold-study.png',1250,1000)
if not d.getObject('ExplodedReview'):
    group=d.addObject('App::DocumentObjectGroup','ExplodedReview');group.Label='爆炸图快照 / excludes incompatible existing PCB'
    for name,dz in [('Q2RearCover',-12),('Q2Housing',0),('InstalledFPCRoutingStudy',15),('LCDModule',15),('Q2Wheel',25),('Q2CenterButton',30),('ControlSymbols',25),('CoverLens',30),('ScreenDemo',30)]:
        src=d.getObject(name);o=d.addObject('Part::Feature','Exploded_'+name);o.Label=src.Label;s=src.Shape.copy();s.translate(App.Vector(0,0,dz));o.Shape=s;group.addObject(o);colors[o.Name]=colors[name]
visible(d,[o.Name for o in d.ExplodedReview.Group],colors);save(view((-1,1,1.4)),'q2-exploded.png',1300,1800)
visible(d,assembled,colors);view((-1,1,1.6));d.recompute();d.save()
print('Q2_PREVIEWS_SAVED',d.FileName)
