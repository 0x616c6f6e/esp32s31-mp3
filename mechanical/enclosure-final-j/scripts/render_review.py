from pathlib import Path
import FreeCAD as A,FreeCADGui as G,Part
from PySide import QtCore
O=Path(__file__).resolve().parents[1]
d=A.openDocument(str(O/'Q2_J_Glue_Insert_Assembly.FCStd'))
def view(n,offset,file,next_fn):
 for o in d.Objects:
  if o.ViewObject:o.ViewObject.Visibility=False
 d.PrintableParts.ViewObject.Visibility=True
 for o in d.PrintableParts.Group:o.ViewObject.Visibility=o.Name=='HousingControlsA'
 d.HousingControlsA.ViewObject.Transparency=75
 s=d.getObject(n).Shape.copy();s.translate(A.Vector(*offset))
 incoming=d.getObject('ReviewIncoming') or d.addObject('PartDesign::Feature','ReviewIncoming')
 incoming.Shape=s;incoming.ViewObject.Visibility=True;incoming.ViewObject.ShapeColor=(.16,.40,.75);incoming.ViewObject.Transparency=35
 clash=d.getObject('ReviewClash') or d.addObject('PartDesign::Feature','ReviewClash')
 clash.Shape=s.common(d.HousingControlsA.Shape);clash.ViewObject.Visibility=True;clash.ViewObject.ShapeColor=(1.,.08,.04)
 v=G.activeDocument().activeView();z=A.Vector(-1,1,-2);x=A.Vector(0,0,1).cross(z);y=z.cross(x)
 v.setCameraType('Orthographic');v.setCameraOrientation(A.Rotation(x,y,z,'ZXY').Q);v.fitAll();G.updateGui()
 def save():
  v.saveImage(str(O/file),1200,1500,'White');next_fn()
 QtCore.QTimer.singleShot(800,save)
def done():
 # Review pictures must not change the released assembly or its visibility.
 d.Modified=False;A.closeDocument(d.Name);G.getMainWindow().close()
def second():view('ControlsBoard',(-1.2,0,-5),'review-controls-entry-collision.png',done)
QtCore.QTimer.singleShot(800,lambda:view('WheelControlsA',(0,0,-5),'review-wheel-entry-collision.png',second))
