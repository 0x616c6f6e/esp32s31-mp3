"""Front half update; final electrical board files are read-only."""
from pathlib import Path
import FreeCAD as A,Part,json,math
R=Path(__file__).resolve().parents[3];O=R/'mechanical/enclosure-final-g';V=A.Vector
d=A.openDocument(str(O/'current-import.FCStd'))
def box(x,y,z,w,l,h):return Part.makeBox(w,l,h,V(x,y,z))
def cyl(x,y,z,r,h):return Part.makeCylinder(r,h,V(x,y,z))
def ring(x,y,z,ro,ri,h):return cyl(x,y,z,ro,h).cut(cyl(x,y,z-.1,ri,h+.2))
def add(n,s):
 o=d.getObject(n) or d.addObject('PartDesign::Feature',n);o.Shape=s;return o
housing=d.getObject('HousingControlsA').Shape.copy()
# Strengthen the functional rocker and retention flanges without moving key centers.
wheel=ring(25,59.3,12.70,16.5,6.15,.85).fuse(ring(25,59.3,12.35,16.5,15.8,.36)).fuse(ring(25,59.3,12.35,17.2,15.8,.40))
for x,y in [(25,46.3),(38,59.3),(12,59.3),(25,72.3)]:wheel=wheel.fuse(cyl(x,y,12.65,.85,.1))
wheel=wheel.cut(cyl(25,59.3,12.69,7.3,.36)).removeSplitter();add('WheelControlsA',wheel)
button=d.getObject('CenterButtonControlsA').Shape.fuse(ring(25,59.3,12.35,6.9,3.2,.3)).removeSplitter();add('CenterButtonControlsA',button)
# More radial/vertical clearance around the enlarged flange; front opening unchanged.
housing=housing.cut(ring(25,59.3,11.95,17.5,16.7,.95)).removeSplitter()
# Attach the repositioned coin motor pocket to the right sidewall. It remains below the PCB.
cx,cy=43,60
base=cyl(cx,cy,6.4,4.8,.6)
rim=ring(cx,cy,6.95,4.8,4.2,1.2)
bridge=box(46.3,58.8,6.4,2.8,2.4,1.0)
holder=base.fuse(rim).fuse(bridge).cut(cyl(cx,cy,7.0,4.2,3)).cut(box(38,59.25,7.0,2.4,1.5,2))
holder=holder.cut(cyl(44.7,65.4995,5.7,2.1,2)).removeSplitter()
housing=housing.fuse(holder).removeSplitter()
add('MotorHolderGeometry',holder)
add('HousingControlsA',housing)
add('Motor_C08_005',cyl(cx,cy,7.1,4.05,3.45))
add('MotorAdhesive',cyl(cx,cy,7.0,3.95,.1))
import sys
sys.path.insert(0,str(O/'scripts'))
from display_route import build
flex,report=build();add('DisplayFPCRoute',flex)
(O/'display-route.json').write_text(json.dumps(report,indent=2))
for n in ['HousingControlsA','WheelControlsA','CenterButtonControlsA']:
 s=d.getObject(n).Shape;assert s.isValid() and len(s.Solids)==1,(n,s.isValid(),len(s.Solids))
d.recompute();d.saveAs(str(O/'front-development.FCStd'))
print('FRONT_SAVED')
