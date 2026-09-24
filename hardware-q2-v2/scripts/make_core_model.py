"""Nominal package envelope from ESP32-S31 datasheet v0.5 p104, simplified contacts."""
from pathlib import Path
import FreeCAD as A,Part
P=Path(__file__).resolve().parents[1];d=A.newDocument('Q2V2CoreModel');V=A.Vector
def add(name,shape):
 o=d.addObject('PartDesign::Feature',name);o.Shape=shape;return o
body=add('Body',Part.makeBox(8,8,.647,V(-4,-4,.203)))
body.addProperty('App::PropertyString','ModelScope');body.ModelScope='Nominal 8x8x0.85; maximum height 0.9 mm; datasheet v0.5 p104; contacts simplified'
ep=add('ExposedPad',Part.makeBox(6.5,6.5,.203,V(-3.25,-3.25,0)))
pins=[]
for side in range(4):
 for i in range(20):
  sh=Part.makeBox(.4,.17,.183,V(-4,-3.325+i*.35-.085,.02));sh.rotate(V(),V(0,0,1),side*90);pins.append(sh)
lead=add('Leads',Part.makeCompound(pins));d.recompute()
Part.export([body,ep,lead],str(P/'models3d/ESP32-S31_QFN80_8x8.step'));d.saveAs(str(P/'models3d/ESP32-S31_QFN80_8x8.FCStd'))
print('QFN nominal body 8 x 8 x 0.85 mm; saved model')
