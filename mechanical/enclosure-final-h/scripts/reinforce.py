"""Reinforce controls mounting without changing external dimensions or PCB positions."""
from pathlib import Path
import FreeCAD as A,Part,json,hashlib
O=Path(__file__).resolve().parents[1];R=O.parents[1];V=A.Vector
src=json.loads((O/'source.json').read_text())
for v in src.values():assert hashlib.sha256((R/v['path']).read_bytes()).hexdigest()==v['sha256']
d=A.openDocument(str(O.parent/'enclosure-final-g/Q2_G_Thin_Assembly.FCStd'))
d.Label='Q2 H / reinforced controls mounts / thin resin sample'
s=d.HousingControlsA.Shape.copy();screws=[];rows=[]
for i,(x,y) in enumerate([(6,51),(44,51),(6,67),(44,67)],1):
 # Wider bearing surface and tapered root distribute load into the front skin.
 post=Part.makeCylinder(2.5,.9,V(x,y,11.9)).fuse(Part.makeCone(2.5,3,.5,V(x,y,11.9)))
 # A low rib connects the boss to the adjacent side wall above the PCB.
 start,end=(1.1,x) if x<25 else (x,48.9)
 rib=Part.makeBox(end-start,1.4,.65,V(start,y-.7,11.9))
 s=s.fuse(post).fuse(rib)
 # Blind pilot only: M1.6 threads made with a controlled bottoming tap.
 s=s.cut(Part.makeCylinder(.65,1.4,V(x,y,11.8)))
 screws.append(Part.makeCylinder(.8,2,V(x,y,11.1)).fuse(Part.makeCylinder(1.65,.5,V(x,y,10.6))))
 rows.append({'position_case_mm':[x,y],'contact_diameter_mm':5,'root_diameter_mm':6,'pilot_diameter_mm':1.3,'pilot_start_z':11.9,'pilot_end_z':13.2,'front_z':13.5,'minimum_nominal_roof_mm':.3,'screw_under_head_length_mm':2,'screw_tip_z':13.1,'tip_to_pilot_end_mm':.1,'nominal_engagement_mm':1.2})
s=s.removeSplitter();assert s.isValid() and len(s.Solids)==1
d.HousingControlsA.Shape=s;d.HousingControlsA.Label='01 Housing H / four reinforced controls bosses'
d.ControlBoardFasteners.Shape=Part.makeCompound(screws)
d.ControlBoardFasteners.Label='4 x M1.6 x 2 UNDER HEAD / head D3.3 x 0.5 max'
params=json.loads((O/'parameters.json').read_text())
for i,(k,v) in enumerate(params.items(),1):d.DesignParameters.set('A'+str(i),k);d.DesignParameters.set('B'+str(i),str(v))
d.recompute();d.saveAs(str(O/'Q2_H_Reinforced_Assembly.FCStd'))
(O/'reinforcement.json').write_text(json.dumps({'source':'../enclosure-final-g/Q2_G_Thin_Assembly.FCStd','changed_objects':['HousingControlsA','ControlBoardFasteners'],'mounts':rows,'not_structural_FEA':True},indent=2))
print('H_MODEL_SAVED',flush=True)
