"""Revision D defaults to a complete case, with a separate honest PCB conflict view."""
import FreeCAD as App, FreeCADGui as Gui, Part, json
from pathlib import Path
from PySide import QtCore
HERE=Path(__file__).resolve().parent;OUT=HERE/'exports'
path=HERE/'ESP32S31_MP3_Q2_D.FCStd'
doc=next((d for d in App.listDocuments().values() if d.FileName and Path(d.FileName).resolve()==path.resolve()),None)
if doc is None:doc=App.openDocument(str(path))
App.setActiveDocument(doc.Name)
colors=json.loads((OUT/'display-colors.json').read_text(encoding='utf8'))
def settle():
    e=QtCore.QEventLoop();QtCore.QTimer.singleShot(500,e.quit);e.exec_()
def show(names):
    for o in doc.Objects:
        if o.ViewObject:
            o.ViewObject.Visibility=o.Name in names
            if o.Name in colors:
                o.ViewObject.ShapeColor=tuple(float(c) for c in colors[o.Name]);o.ViewObject.LineColor=(.12,.15,.17)
                if 'DisplayMode' in o.ViewObject.PropertiesList:o.ViewObject.DisplayMode='Shaded'
def camera(z):
    z=App.Vector(*z);x=App.Vector(0,0,1).cross(z);y=z.cross(x)
    v=Gui.activeDocument().activeView();v.setCameraType('Orthographic');v.setCameraOrientation(App.Rotation(x,y,z,'ZXY').Q);settle();v.fitAll();settle();return v
def save(v,name,w=1200,h=1500):v.saveImage(str(OUT/name),w,h,'White')
external=['HousingWithControlPosts','Q2RearCover','Q2Wheel','Q2CenterButton','CoverLens','ControlSymbols']
show(external);save(camera((-1,1,1.8)),'exterior-D.png')
v=Gui.activeDocument().activeView();v.setCameraOrientation(App.Rotation(App.Vector(0,0,1),180).Q);settle();v.fitAll();settle();save(v,'front-D.png',1000,1500)
show(external+['MainPCB','ESP32Front','ScreenConnectorFPC2','MainPCBHousingCollision','MainComponentsHousingCollision'])
doc.HousingWithControlPosts.ViewObject.Transparency=78;doc.CoverLens.ViewObject.Transparency=88;doc.MainPCB.ViewObject.Transparency=35
save(camera((-1,1,1.8)),'current-PCB-conflicts.png')
doc.HousingWithControlPosts.ViewObject.Transparency=0;doc.CoverLens.ViewObject.Transparency=0;doc.MainPCB.ViewObject.Transparency=0
show(external);camera((-1,1,1.8))
doc.addProperty('App::PropertyString','ReviewStatus') if 'ReviewStatus' not in doc.PropertiesList else None
doc.ReviewStatus='Screen raised1.5 mm; complete exterior is default. Existing PCB still collides with shell; see current-PCB-conflicts.png and validation.json. Not production-ready.'
doc.recompute();doc.save()
print('D_VIEWS_COMPLETE')
