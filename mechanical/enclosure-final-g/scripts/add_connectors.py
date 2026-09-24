from pathlib import Path
import FreeCAD as A,Part,json
R=Path(__file__).resolve().parents[3];O=R/'mechanical/enclosure-final-g';V=A.Vector
d=A.openDocument(str(O/'front-development.FCStd'))
def box(x,y,z,w,l,h):return Part.makeBox(w,l,h,V(x,y,z))
def add(n,s,note):
 o=d.getObject(n) or d.addObject('PartDesign::Feature',n);o.Shape=s
 if 'Basis' not in o.PropertiesList:o.addProperty('App::PropertyString','Basis')
 o.Basis=note
 return o
# Conservative maximum body envelopes registered to actual silkscreen and pad row.
# Hollow sockets are intentionally represented solid for case clearance.
add('PCB_CN2',box(4.097,49.507,-2.4,7.92,10.25,6.6),'Bossie BX-HA2.54-3PWZ manufacturer drawing: 10 +/-0.25 wide; 7.42 +/-0.2 depth; 6.35 +/-0.25 height. Envelope, not a mating CAD model.')
add('PCB_CN3',box(4.34,64.906,-1.85,7.4,7.9,6.05),'Hanxia HX-XH2.54-2PWZ-B drawing: 7.5 width, 7 +/-0.2 depth, 5.8 +/-0.2 height; extra 0.05 height allowed. Envelope only.')
add('BatteryPlugKeepout',box(11.5,49.5,-1.8,6.5,10.3,5.5),'Assumed mating housing + wire-exit keepout; actual harness drawing pending. Not a purchased part model.')
add('MotorPlugKeepout',box(11.2,65,-1.3,6.5,7.8,5),'Assumed mating housing + wire-exit keepout; actual harness drawing pending.')
src=json.loads((O/'source.json').read_text())
for f in src['main']['footprints']:
 if f['ref'] not in ['CN2','CN3']:continue
 x,y=f['xy'];x=176.868-x;y-=65.647
 offsets=[-2.5,0,2.5] if f['ref']=='CN2' else [-1.25,1.25]
 shapes=[Part.makeCylinder(.5,1.8,V(x,y+a,5.8)) for a in offsets]
 add(f['ref']+'SolderTailKeepout',Part.makeCompound(shapes),'Through-hole leads trimmed to <=1.8 mm above board front; includes solder allowance.')
d.recompute();d.save()
print('CONNECTOR_ENVELOPES_ADDED')
