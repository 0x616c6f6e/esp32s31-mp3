"""Render the review in an isolated FreeCAD GUI; default to the imported PCBs."""
from pathlib import Path
import FreeCAD as A,FreeCADGui as G,Part,json
from PySide import QtCore
O=Path(__file__).resolve().parents[1]
d=A.openDocument(str(O/'Q2_Final_Mainboard_Assembly.FCStd'))
colors=json.loads((O/'colors.json').read_text())
clip=d.getObject('DisplayFlexDetail') or d.addObject('PartDesign::Feature','DisplayFlexDetail')
clip.Label='Display flex clipped for detail view only'
clip.Shape=d.DisplayFPCRoute.Shape.common(Part.makeBox(5,5,3,A.Vector(17,20,2)))
d.ReviewDiagnostics.addObject(clip);colors[clip.Name]=(.9,.55,.14)
internals=['MainPCB','ControlsBoard','WheelCopper','HousingControlsA','BatteryReference','Motor_C08_005','MotorHolderProposal','DisplayFPCRoute','ControlFFC40mm','ControlBoardFasteners']+[o.Name for o in d.Objects if o.Name.startswith(('PCB_','CTRL_','Conflict'))]
def show(names):
 for o in d.Objects:
  if not o.ViewObject:continue
  o.ViewObject.Visibility=o.Name in names or o.Name in ['Enclosure','ControlsPCB','References','ReviewDiagnostics']
  if o.Name in colors:
   o.ViewObject.ShapeColor=tuple(colors[o.Name]);o.ViewObject.LineColor=(.1,.12,.15)
  if 'Transparency' in o.ViewObject.PropertiesList:o.ViewObject.Transparency=0
  if o.Name in colors and 'DisplayMode' in o.ViewObject.PropertiesList:o.ViewObject.DisplayMode='Shaded'
def camera():
 v=G.activeDocument().activeView();z=A.Vector(-1,1,1.8);x=A.Vector(0,0,1).cross(z);y=z.cross(x)
 v.setCameraType('Orthographic');v.setCameraOrientation(A.Rotation(x,y,z,'ZXY').Q)
 G.updateGui();v.fitAll();G.updateGui();v.fitAll()
def overview():
 show(internals)
 for n,t in [('HousingControlsA',90),('ControlsBoard',55),('BatteryReference',80),('MainPCB',20)]:d.getObject(n).ViewObject.Transparency=t
 camera()
def phase1():
 overview();QtCore.QTimer.singleShot(700,phase2)
def phase2():
 camera()
 G.activeDocument().activeView().saveImage(str(O/'assembly-review.png'),1200,1500,'White')
 show(['PCB_CN1','CTRL_J1','Motor_C08_005','MotorHolderProposal','Conflict0','Conflict1'])
 d.PCB_CN1.ViewObject.Transparency=65;d.Motor_C08_005.ViewObject.Transparency=45
 camera();QtCore.QTimer.singleShot(700,phase3)
def phase3():
 G.activeDocument().activeView().saveImage(str(O/'motor-jack-conflict.png'),1300,900,'White')
 show(['PCB_C13','DisplayFlexDetail','Conflict2']);d.PCB_C13.ViewObject.Transparency=65;camera();QtCore.QTimer.singleShot(700,phase4)
def phase4():
 G.activeDocument().activeView().saveImage(str(O/'display-flex-conflict.png'),1300,900,'White')
 overview();d.recompute();d.save();(O/'views-ready.txt').write_text('Imported final hardware-q2 and controls. Red objects show collisions. Original source PCBs unchanged.\n')
 A.closeDocument(d.Name);QtCore.QTimer.singleShot(200,G.getMainWindow().close)
def guard(fn):
 def run():
  try:fn()
  except Exception:
   import traceback
   (O/'views-error.txt').write_text(traceback.format_exc());d.Modified=False;G.getMainWindow().close()
 return run
for n in ['phase1','phase2','phase3','phase4']:globals()[n]=guard(globals()[n])
QtCore.QTimer.singleShot(700,phase1)
