from pathlib import Path
import FreeCAD as A,Part,Import,json,math
R=Path(__file__).resolve().parents[3];O=R/'mechanical/enclosure-final-g';V=A.Vector
sources=json.loads((O/'source.json').read_text())
old=A.openDocument(str(R/'mechanical/final-board-review/Q2_Final_Mainboard_Assembly.FCStd'))
d=A.newDocument('Q2G');d.Label='Q2 G / final boards / resin assembly sample'
def add(n,s,label=None):
 o=d.addObject('PartDesign::Feature',n);o.Shape=s;o.Label=label or n;return o
for n in ['HousingControlsA','RearCoverWithPCBPosts','LCDModule','LCDActiveArea','CoverLens','LensBlackMask','LensAdhesive','ControlSymbols','DisplayFPCRoute','ControlBoardFasteners','MainPCB','WheelCopper','ControlFFC40mm','WheelControlsA','CenterButtonControlsA']:
 add(n,old.getObject(n).Shape.copy())
for o in old.Objects:
 if o.Name.startswith('PCB_'):add(o.Name,o.Shape.copy(),o.Label)
nd=A.newDocument('ControlsImport');Import.insert(str(O/'controls-current.step'),nd.Name)
assembly=max(nd.Objects,key=lambda o:len(o.OutList));fps={f['ref']:f for f in sources['controls']['footprints'] if f['model']}
models={};board=None
for item in assembly.OutList:
 if item.TypeId=='App::Origin':continue
 sh=Part.getShape(item)
 if sh.isNull() or sh.Volume<1e-8:continue
 base=item.Placement.Base
 ref=min(fps,key=lambda r:math.hypot(fps[r]['xy'][0]-base.x,fps[r]['xy'][1]+base.y))
 sh=sh.copy();sh.rotate(V(),V(0,0,1),180)
 if math.hypot(fps[ref]['xy'][0]-base.x,fps[ref]['xy'][1]+base.y)>.005:
  sh.translate(V(47,42.3,-sh.BoundBox.ZMin));mat=A.Matrix();mat.A33=.8/sh.BoundBox.ZLength;sh=sh.transformGeometry(mat);sh.translate(V(0,0,11.1));board=add('ControlsBoard',sh)
 else:
  assert ref not in models,ref
  sh.translate(V(47,42.3,(11.9 if fps[ref]['side']=='F' else 11.1)-base.z))
  models[ref]=add('CTRL_'+ref,sh,ref+' / '+fps[ref]['fp'])
assert set(models)==set(fps),(set(models),set(fps));assert board
A.closeDocument(nd.Name);A.closeDocument(old.Name)
d.recompute();d.saveAs(str(O/'current-import.FCStd'))
print('IMPORTED',len(models),'controls models')
