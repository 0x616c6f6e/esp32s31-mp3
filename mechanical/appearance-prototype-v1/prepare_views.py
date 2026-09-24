from pathlib import Path
import FreeCAD as A,FreeCADGui as G,json
from PySide import QtCore
O=Path(__file__).resolve().parent
d=A.openDocument(str(O/'Q2_Appearance_Prototype_V1.FCStd'))
for c in json.loads((O/'manifest.json').read_text(encoding='utf8'))['parts']:
 o=d.getObject(c['source_object']);o.ViewObject.ShapeColor=tuple(c['color']);o.ViewObject.LineColor=(.1,.1,.1);o.ViewObject.DisplayMode='Shaded';o.ViewObject.Visibility=True
def camera():
 v=G.activeDocument().activeView();z=A.Vector(-1,1,1.8);x=A.Vector(0,0,1).cross(z);y=z.cross(x)
 v.setCameraType('Orthographic');v.setCameraOrientation(A.Rotation(x,y,z,'ZXY').Q);G.updateGui();v.fitAll();G.updateGui();v.fitAll()
def first():
 camera();QtCore.QTimer.singleShot(700,second)
def second():
 camera();G.activeDocument().activeView().saveImage(str(O/'reference/appearance-preview.png'),1000,1300,'White')
 d.recompute();d.save();(O/'views-ready.txt').write_text('Appearance-only sample; five separate parts.\n');A.closeDocument(d.Name);QtCore.QTimer.singleShot(200,G.getMainWindow().close)
QtCore.QTimer.singleShot(700,first)
