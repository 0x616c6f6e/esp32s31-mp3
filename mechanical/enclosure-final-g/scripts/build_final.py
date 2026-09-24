from pathlib import Path
import FreeCAD as A,Part,Import,MeshPart,json,math,hashlib
R=Path(__file__).resolve().parents[3];O=R/'mechanical/enclosure-final-g';V=A.Vector
params=json.loads((O/'parameters.json').read_text());src=json.loads((O/'source.json').read_text())
for v in src.values():assert hashlib.sha256((R/v['path']).read_bytes()).hexdigest()==v['sha256']
d=A.openDocument(str(O/'front-development.FCStd'));d.Label='Q2 G / thin resin assembly sample / final CH32 boards'
def box(x,y,z,w,l,h):return Part.makeBox(w,l,h,V(x,y,z))
def cyl(x,y,z,r,h):return Part.makeCylinder(r,h,V(x,y,z))
def add(n,s,label=None,group=None):
 o=d.getObject(n) or d.addObject('PartDesign::Feature',n);o.Shape=s;o.Label=label or n
 if group:group.addObject(o)
 return o
case=d.addObject('App::DocumentObjectGroup','PrintableParts');case.Label='01 Printable parts / resin'
boards=d.addObject('App::DocumentObjectGroup','Electronics');boards.Label='02 Final boards / do not print'
refs=d.addObject('App::DocumentObjectGroup','AssemblyReferences');refs.Label='03 Battery, lens, cables, screws / do not print'
diag=d.addObject('App::DocumentObjectGroup','Diagnostics');diag.Label='04 Rejected header envelopes / keep hidden'
for n in ['PCB_CN2','PCB_CN3','BatteryPlugKeepout','MotorPlugKeepout','CN2SolderTailKeepout','CN3SolderTailKeepout','MotorHolderGeometry']:
 diag.addObject(d.getObject(n))
 for prop,value in [('AssemblyStatus','NOT FITTED / reference only')]:
  if prop not in d.getObject(n).PropertiesList:d.getObject(n).addProperty('App::PropertyString',prop)
  setattr(d.getObject(n),prop,value)
# Rebuild the rear supports from the final board coordinates; the previous
# manual +0.5 mm SCREW3 shift is replaced by actual final-board hole axes.
f=A.openDocument(str(R/'mechanical/enclosure-q2-f/ESP32S31_MP3_Q2_F.FCStd'))
rear=f.getObject('Q2RearCover').Shape.copy();A.closeDocument(f.Name)
posts=[];mounts=[]
for row in src['main']['footprints']:
 if not row['ref'].startswith('SCREW'):continue
 x,y=176.868-row['xy'][0],row['xy'][1]-65.647
 post=cyl(x,y,1.0,1.9,3.2).cut(cyl(x,y,1.2,.8,3.2));posts.append(post)
 mounts.append({'ref':row['ref'],'case_xy':[x,y],'actual_board_hole_diameter':row['holes'][0][1],'pilot_diameter':1.6,'support_top_z':4.2})
rear=rear.multiFuse(posts).cut(box(47.55,48.161,1.325,1.17,7.1,1.175)).removeSplitter()
rear=rear.cut(box(1.25,10.9,1.65,1.55,19,1)).removeSplitter()
add('RearCoverWithPCBPosts',rear,'02 Rear cover / final board hole axes',case)
for n in ['HousingControlsA','WheelControlsA','CenterButtonControlsA']:case.addObject(d.getObject(n))
for o in d.Objects:
 if o.Name.startswith(('PCB_','CTRL_')) and o.Name not in ['PCB_CN2','PCB_CN3'] or o.Name in ['MainPCB','ControlsBoard','WheelCopper']:boards.addObject(o)
for n in ['LCDModule','LCDActiveArea','CoverLens','LensBlackMask','LensAdhesive','ControlSymbols','DisplayFPCRoute','ControlBoardFasteners','ControlFFC40mm','Motor_C08_005','MotorAdhesive']:refs.addObject(d.getObject(n))
bx,by,bz=params['battery_origin_mm'];bw,bl,bt=params['battery_max_initial_pack_mm']
add('BatteryPack',box(bx,by,bz,bw,bl,bt),'Battery pack max 21 x 33 x 3 / procurement envelope',refs)
add('BatteryAdhesive',box(bx,by,10.8,bw,bl,.2),'Removable adhesive 0.2 / pull-tab fixation',refs)
add('BatteryInsulation',box(bx,by,11.0,bw,bl,.1),'PET insulation 0.1 / below controls PCB',refs)
add('BatteryExpandedKeepout',box(bx,by,bz-.3,bw,bl,bt+.3),'Battery +0.3 thickness allowance / supplier to confirm',diag)
# Wires are round clearance corridors, not a cut-to-length or bend-strain proof.
def wire(n,pts,r=.275):
 shapes=[]
 for a,b in zip(pts,pts[1:]):
  a,b=V(*a),V(*b);v=b-a
  if v.Length>1e-6:shapes.append(Part.makeCylinder(r,v.Length,a,v))
 for p in pts[1:-1]:shapes.append(Part.makeSphere(r,V(*p)))
 return add(n,Part.makeCompound(shapes),'AWG30 flexible wire corridor / dress bends on sample',refs)
for i,y in enumerate([57.132,54.632,52.132]):
 # Stagger the edge crossing and wire entry to keep three wires separate.
 h=9.4-i*.6; ey=39+i*.8
 wire('BatteryWire'+str(i+1),[(4.347,y,3.25),(1.61,y,3.25),(1.61,y,h),(1.61,ey,h),(9.9,ey,h),(10.5,ey,h)])
for i,y in enumerate([70.106,67.606]):
 ry=55.8+i*.6; h=10.6-i*.6
 wire('MotorWire'+str(i+1),[(4.22,y,3.25),(1.61,y,3.25),(1.61,y,h),(1.61,ry,h),(6+i*2,ry,h),(6+i*2,ry,7.1),(33.7,ry,7.1),(35,59.6+i*.8,8.0),(38.9,59.6+i*.8,8.0)],.225)
# Soft strain-relief spots are adhesive references, not hard printed clamps.
add('BatteryWireStrainRelief',box(3.3,51.2,2.65,2,7,1),'Flexible silicone/UV wire relief / no conductive adhesive',refs)
add('MotorWireStrainRelief',box(3.2,66.6,2.65,2,4.5,1),'Flexible strain relief / solder on existing pads',refs)
fasteners=[]
for m in mounts:
 x,y=m['case_xy'];fasteners.append(cyl(x,y,1.8,1,4).fuse(cyl(x,y,5.8,1.8,1.0)))
add('MainBoardFasteners',Part.makeCompound(fasteners),'4 x M2 x 4 / actual head envelope to check',refs)
add('RearCoverFasteners',Part.makeCompound([cyl(25,y,.65,.8,6).fuse(cyl(25,y,.15,1.6,.5)) for y in [3,77]]),'2 x M1.6 x 6 / recessed heads',refs)
table=d.addObject('Spreadsheet::Sheet','DesignParameters')
for i,(k,v) in enumerate(params.items(),1):table.set('A'+str(i),k);table.set('B'+str(i),str(v))
d.recompute()
for o in case.Group:assert o.Shape.isValid() and len(o.Shape.Solids)==1,o.Name
d.saveAs(str(O/'Q2_G_Thin_Assembly.FCStd'))
(O/'mounting.json').write_text(json.dumps(mounts,indent=2))
print('FINAL_MODEL_SAVED',flush=True)
