"""Run in a separate FreeCAD GUI process to persist colors and review views."""
from pathlib import Path
import FreeCAD as A,FreeCADGui as G,json
from PySide import QtCore
P=Path(__file__).resolve().parents[1];O=P/'mechanical'
d=A.openDocument(str(O/'Q2_Controls_Assembly.FCStd'));colors=json.loads((O/'colors.json').read_text())
exterior=['HousingControlsA','RearCoverWithPCBPosts','WheelControlsA','CenterButtonControlsA','CoverLens','LensBlackMask','ControlSymbols']
controls=['ControlsBoard','WheelCopper']+[o.Name for o in d.Objects if o.Name.startswith('CTRL_')]
internal=controls+['MainPCB','BatteryReference','Motor_C08_005','MotorHolderProposal','LCDModule','DisplayFPCRoute','ControlBoardFasteners','ControlFFC40mm']+[o.Name for o in d.Objects if o.Name.startswith('PCB_')]
def show(names):
 for o in d.Objects:
  if o.ViewObject:
   o.ViewObject.Visibility=o.Name in names or o.Name in ['Enclosure','ControlsPCB','References']
   if o.Name in colors:
    o.ViewObject.ShapeColor=tuple(colors[o.Name]);o.ViewObject.LineColor=(.08,.10,.12)
    if 'DisplayMode' in o.ViewObject.PropertiesList:o.ViewObject.DisplayMode='Shaded'
 for name,col in {'ControlsBoard':(.08,.42,.27),'WheelCopper':(.8,.62,.28),'MainPCB':(.08,.33,.22),'BatteryReference':(.62,.69,.77),'Motor_C08_005':(.9,.65,.25),'CoverLens':(.06,.09,.14)}.items():
  d.getObject(name).ViewObject.ShapeColor=col
def camera():
 z=A.Vector(-1,1,1.8);x=A.Vector(0,0,1).cross(z);y=z.cross(x)
 v=G.activeDocument().activeView();v.setCameraType('Orthographic');v.setCameraOrientation(A.Rotation(x,y,z,'ZXY').Q);v.fitAll();return v
def phase1():
 show(exterior);camera();QtCore.QTimer.singleShot(800,phase2)
def phase2():
 G.activeDocument().activeView().saveImage(str(O/'exterior.png'),1000,1400,'White')
 show(internal+['HousingControlsA']);d.HousingControlsA.ViewObject.Transparency=88;d.BatteryReference.ViewObject.Transparency=65;camera();QtCore.QTimer.singleShot(800,phase3)
def phase3():
 G.activeDocument().activeView().saveImage(str(O/'assembly-cutaway.png'),1200,1500,'White')
 show(controls+['WheelControlsA','CenterButtonControlsA']);d.WheelControlsA.ViewObject.Transparency=72;d.CenterButtonControlsA.ViewObject.Transparency=72;camera();QtCore.QTimer.singleShot(800,phase4)
def phase4():
 G.activeDocument().activeView().saveImage(str(O/'controls-and-keycaps.png'),1400,1100,'White')
 show(['PCB_FPC1','CTRL_J1','ControlFFC40mm']);camera()
 QtCore.QTimer.singleShot(800,phase5)

def phase5():
 G.activeDocument().activeView().saveImage(str(O/'ffc-interconnect.png'),1500,1000,'White')
 d.MainPCB.ViewObject.Transparency=0;d.ControlsBoard.ViewObject.Transparency=0
 d.HousingControlsA.ViewObject.Transparency=0;d.WheelControlsA.ViewObject.Transparency=0;d.CenterButtonControlsA.ViewObject.Transparency=0
 show(exterior);camera();d.recompute();d.save()
 (O/'views-ready.txt').write_text('Exterior default; References/ControlFFC40mm shows the nominal 40 mm stock cable. Mainboard mounting posts and actual cable fit remain to be verified.\n')
 A.closeDocument(d.Name);QtCore.QTimer.singleShot(200,G.getMainWindow().close)
def guarded(fn):
 def call():
  try:fn()
  except Exception:
   import traceback
   (O/'views-error.txt').write_text(traceback.format_exc())
   d.Modified=False
   G.getMainWindow().close()
 return call
for n in ['phase1','phase2','phase3','phase4','phase5']:globals()[n]=guarded(globals()[n])
QtCore.QTimer.singleShot(800,phase1)
