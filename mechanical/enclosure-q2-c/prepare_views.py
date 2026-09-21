"""FreeCAD GUI: show both actual board sides and the separate control PCB."""
import FreeCAD as App, FreeCADGui as Gui, Part, json
from pathlib import Path
from PySide import QtCore
HERE=Path(__file__).resolve().parent;OUT=HERE/'exports'
path=HERE/'ESP32S31_MP3_Q2_C.FCStd'
doc=next((d for d in App.listDocuments().values() if d.FileName and Path(d.FileName).resolve()==path.resolve()),None)
if doc is None:doc=App.openDocument(str(path))
App.setActiveDocument(doc.Name)
colors=json.loads((OUT/'display-colors.json').read_text())
def settle():
    e=QtCore.QEventLoop();QtCore.QTimer.singleShot(650,e.quit)
    if hasattr(e,'exec'):e.exec()
    else:e.exec_()
def show(names):
    for o in doc.Objects:
        if o.ViewObject:
            o.ViewObject.Visibility=o.Name in names
            if o.Name in colors:
                o.ViewObject.ShapeColor=tuple(colors[o.Name]);o.ViewObject.LineColor=(.12,.15,.17)
                if 'DisplayMode' in o.ViewObject.PropertiesList:o.ViewObject.DisplayMode='Shaded'
def camera(z):
    z=App.Vector(*z);x=App.Vector(0,0,1).cross(z);y=z.cross(x)
    v=Gui.activeDocument().activeView();v.setCameraType('Orthographic');v.setCameraOrientation(App.Rotation(x,y,z,'ZXY').Q);settle();v.fitAll();settle();Gui.updateGui();return v
def save(v,name,w=1400,h=1400):v.saveImage(str(OUT/name),w,h,'White')
controls=['ControlBoard','ControlRingElectrodeGuide','ControlFPCConnector','TactPower','TactBack','TactPrevious','TactNext','TactPlayPause']
internals=['MainPCB','MainComponents','ESP32Front','ScreenConnectorFPC2','DisplayFPCRoute','MainControlFPCReserve','ControlFPCRoute','BatteryReference']+controls
show(internals);save(camera((-1,1,1.4)),'internal-front.png')
show(internals+['LCDModule']);doc.LCDModule.ViewObject.Transparency=65
save(camera((-1,1,1.4)),'stack-with-screen.png');doc.LCDModule.ViewObject.Transparency=0
show(['MainPCB','ScreenConnectorFPC2','DisplayFPCRoute','ESP32Front']);doc.MainPCB.ViewObject.Transparency=45;doc.ESP32Front.ViewObject.Transparency=65
save(camera((-1,1,-1.4)),'screen-fpc-rear.png');doc.MainPCB.ViewObject.Transparency=0;doc.ESP32Front.ViewObject.Transparency=0
show(controls);save(camera((-1,1,2.0)),'control-board-isometric.png',1400,1000)
v=Gui.activeDocument().activeView();v.setCameraOrientation(App.Rotation(App.Vector(0,0,1),180).Q);settle();v.fitAll();settle();save(v,'control-board-front.png',1400,1000)
show(['MainPCB','ESP32Front','ScreenConnectorFPC2','DisplayFPCRoute','MainPCBHousingCollision','DisplayFPCHardwareCollision']);doc.MainPCB.ViewObject.Transparency=65;doc.ESP32Front.ViewObject.Transparency=70
save(camera((-1,1,1.2)),'remaining-mainboard-conflicts.png');doc.MainPCB.ViewObject.Transparency=0;doc.ESP32Front.ViewObject.Transparency=0
if not doc.getObject('ExplodedReview'):
    g=doc.addObject('App::DocumentObjectGroup','ExplodedReview');g.Label='C 装配爆炸快照 / 排线在装配图中查看'
    offsets=[('Q2RearCover',-12),('MainPCB',2),('MainComponents',2),('ESP32Front',2),('ScreenConnectorFPC2',2),('BatteryReference',17)]+[(n,33) for n in controls]+[('LCDModule',33),('HousingWithControlPosts',53),('Q2Wheel',62),('Q2CenterButton',66),('ControlSymbols',62),('CoverLens',62)]
    for n,z in offsets:
        src=doc.getObject(n);o=doc.addObject('Part::Feature','Exploded_'+n);s=src.Shape.copy();s.translate(App.Vector(0,0,z));o.Shape=s;o.Label=src.Label;g.addObject(o);colors[o.Name]=colors[n]
show([o.Name for o in doc.ExplodedReview.Group]);save(camera((-1,1,1.4)),'assembly-exploded.png',1300,1800)
external=['HousingWithControlPosts','Q2RearCover','Q2Wheel','Q2CenterButton','CoverLens','ControlSymbols']
show(external);save(camera((-1,1,1.6)),'exterior-C.png',1250,1500)
# Default view intentionally exposes the corrected internal assembly for review.
show(internals);camera((-1,1,1.4));doc.recompute();doc.save()
print('C_PREVIEWS_SAVED',doc.FileName)
