from pathlib import Path
import FreeCAD as A,FreeCADGui as G,json
from PySide import QtCore
O=Path(__file__).resolve().parents[1]
d=A.openDocument(str(O/'Q2_H_Reinforced_Assembly.FCStd'))
for i,(k,v) in enumerate(json.loads((O/'parameters.json').read_text()).items(),1):d.DesignParameters.set('A'+str(i),k);d.DesignParameters.set('B'+str(i),str(v))
colors=json.loads((O.parent/'final-board-review/colors.json').read_text())
colors.update({'HousingControlsA':(.68,.74,.78),'RearCoverWithPCBPosts':(.68,.74,.78),'WheelControlsA':(.18,.21,.24),'CenterButtonControlsA':(.25,.29,.32),'CoverLens':(.035,.05,.065),'BatteryPack':(.72,.75,.79),'Motor_C08_005':(.62,.64,.66),'DisplayFPCRoute':(.9,.55,.1),'ControlFFC40mm':(.88,.86,.75)})
groups=['PrintableParts','Electronics','AssemblyReferences']
def show(names):
 for n in groups:d.getObject(n).ViewObject.Visibility=True
 for o in d.Objects:
  if not o.ViewObject:continue
  if o.Name in groups:continue
  o.ViewObject.Visibility=o.Name in names
  if hasattr(o,'Shape'):
   c=colors.get(o.Name,(.1,.38,.2) if o.Name in ['MainPCB','ControlsBoard'] else (.35,.36,.38))
   if o.Name.startswith('BatteryWire'):c=(.7,.1,.1)
   if o.Name.startswith('MotorWire'):c=(.8,.6,.1)
   o.ViewObject.ShapeColor=tuple(c);o.ViewObject.LineColor=(.12,.13,.14);o.ViewObject.DisplayMode='Shaded';o.ViewObject.Transparency=0
def camera(back=False):
 v=G.activeDocument().activeView();z=A.Vector(-1,1,-2 if back else 2);x=A.Vector(0,0,1).cross(z);y=z.cross(x)
 v.setCameraType('Orthographic');v.setCameraOrientation(A.Rotation(x,y,z,'ZXY').Q);G.updateGui();v.fitAll();G.updateGui();v.fitAll()
exterior=['HousingControlsA','RearCoverWithPCBPosts','WheelControlsA','CenterButtonControlsA','CoverLens','ControlSymbols','PCB_USB1','PCB_CN1','RearCoverFasteners']
def phase1():
 show(exterior);camera();QtCore.QTimer.singleShot(900,phase2)
def phase2():
 G.activeDocument().activeView().saveImage(str(O/'front-assembled.png'),1200,1500,'White')
 names=[o.Name for o in d.Electronics.Group+d.AssemblyReferences.Group]+['HousingControlsA','WheelControlsA','CenterButtonControlsA']
 show(names);d.HousingControlsA.ViewObject.Transparency=82;d.MainPCB.ViewObject.Transparency=78;camera(True);QtCore.QTimer.singleShot(900,phase3)
def phase3():
 G.activeDocument().activeView().saveImage(str(O/'back-internals.png'),1200,1500,'White')
 show(['HousingControlsA','RearCoverWithPCBPosts','WheelControlsA','CenterButtonControlsA'])
 d.RearCoverWithPCBPosts.Placement.Base=A.Vector(60,0,0);camera(True);QtCore.QTimer.singleShot(900,phase4)
def phase4():
 G.activeDocument().activeView().saveImage(str(O/'shell-parts.png'),1600,1100,'White')
 d.RearCoverWithPCBPosts.Placement.Base=A.Vector();show(['HousingControlsA']);camera(True);QtCore.QTimer.singleShot(900,phase5)
def phase5():
 G.activeDocument().activeView().saveImage(str(O/'reinforced-upper-shell.png'),1200,1500,'White')
 d.RearCoverWithPCBPosts.Placement.Base=A.Vector();show(exterior);camera();d.recompute();d.save()
 (O/'views-ready.txt').write_text('Four views rendered; assembly placements restored.')
 A.closeDocument(d.Name);QtCore.QTimer.singleShot(200,G.getMainWindow().close)
def guard(fn):
 def run():
  try:fn()
  except Exception:
   import traceback
   (O/'views-error.txt').write_text(traceback.format_exc());d.Modified=False;G.getMainWindow().close()
 return run
for name in ['phase1','phase2','phase3','phase4','phase5']:globals()[name]=guard(globals()[name])
QtCore.QTimer.singleShot(800,phase1)
