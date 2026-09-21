"""FreeCAD GUI script: save clean opening state and assembled/exploded previews."""
import FreeCAD as App, FreeCADGui as Gui, json
from PySide import QtCore
from pathlib import Path
HERE=Path(__file__).resolve().parent;OUT=HERE/'exports'
path=str(HERE/'ESP32S31_MP3_Enclosure_A.FCStd')
doc=next((d for d in App.listDocuments().values() if d.FileName and Path(d.FileName).resolve()==Path(path).resolve()),None)
if doc is None:doc=App.openDocument(path)
App.setActiveDocument(doc.Name)
colors=json.loads((OUT/'display-colors.json').read_text())
def hide_all():
    for o in doc.Objects:
        if o.ViewObject:o.ViewObject.Visibility=False
def show(names):
    for name in names:
        o=doc.getObject(name);o.ViewObject.Visibility=True
        if name in colors:o.ViewObject.ShapeColor=tuple(colors[name])
        o.ViewObject.LineColor=(.10,.12,.14)
        if 'DisplayMode' in o.ViewObject.PropertiesList:o.ViewObject.DisplayMode='Flat Lines'
def settle():
    # Let FreeCAD complete its camera transition before exporting a render.
    loop=QtCore.QEventLoop();QtCore.QTimer.singleShot(900,loop.quit)
    if hasattr(loop,'exec'):loop.exec()
    else:loop.exec_()
def camera(z):
    z=App.Vector(*z);x=App.Vector(0,0,1).cross(z);y=z.cross(x)
    v=Gui.activeDocument().activeView();v.setCameraType('Orthographic');v.setCameraOrientation(App.Rotation(x,y,z,'ZXY').Q);settle();v.fitAll();settle();Gui.updateGui();return v
def save(v,name,w=1500,h=1200):v.saveImage(str(OUT/name),w,h,'White')
assembled=['RearKeyRelief','FrontWithSwitchSupport','PowerButton','LensReference','Fasteners']
hide_all();show(assembled)
save(camera((1,1,1.3)),'assembled.png')
v=Gui.activeDocument().activeView();v.viewTop();v.setCameraOrientation(App.Rotation(App.Vector(0,0,1),180).Q);settle();v.fitAll();settle();Gui.updateGui();save(v,'front-view.png',1000,1400)
hide_all();show(['RearKeyRelief','BatteryEnvelope']);save(camera((1,1,1.9)),'rear-interior.png')
old=doc.getObject('ExplodedReview')
if old:
    for o in list(old.Group):doc.removeObject(o.Name)
    doc.removeObject(old.Name)
group=doc.addObject('App::DocumentObjectGroup','ExplodedReview');group.Label='爆炸图快照 / hide for normal assembly'
items=[('RearKeyRelief',0),('BatteryEnvelope',8),('PCB',22),('ComponentEnvelopes',22),('LCDEnvelope',38),('FrontWithSwitchSupport',52),('PowerButton',52),('LensReference',59),('Fasteners',67)]
enames=[]
for name,dz in items:
    src=doc.getObject(name);obj=doc.addObject('Part::Feature','Exploded_'+name);obj.Label=src.Label
    shape=src.Shape.copy();shape.translate(App.Vector(0,0,dz));obj.Shape=shape;group.addObject(obj);enames.append(obj.Name)
    colors[obj.Name]=colors[name]
hide_all();show(enames);doc.recompute();save(camera((1,1,0.8)),'exploded.png',1250,1600)
hide_all();show(assembled);camera((1,1,1.3));doc.recompute();doc.save()
print('PREVIEWS_SAVED',doc.FileName)
