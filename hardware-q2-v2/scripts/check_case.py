"""Read-only nominal STEP fit review against L case; original files never saved."""
from pathlib import Path
import FreeCAD as A,Part,Import,json,math
P=Path(__file__).resolve().parents[1];R=P.parent;V=A.Vector
d=A.newDocument('V2StepFit');Import.insert(str(P/'output/q2-v2-assembly.step'),d.Name)
c=A.openDocument(str(R/'mechanical/enclosure-final-l/Q2_L_AM213_Adapter_Study.FCStd'))
names=['HousingControlsA','RearCoverWithPCBPosts','LCDModule','ScreenRearFPCEnvelope','BatteryExpandedKeepout','BatteryPack','BatteryWire1','BatteryWire2','BatteryWire3','MotorWire1','MotorWire2','ControlFFC40mm','ControlsBoard','MotorCarrier','Motor_C08_005','ControlEdgePad','MainBoardFasteners','RearCoverFasteners']
obstacles=[c.getObject(n) for n in names];assert all(obstacles)
contract=json.loads((P/'output/design-contract.json').read_text(encoding='utf8'))['components']
report=[];compounds=[];components=[]
def leaves(o):
 if hasattr(o,'Group'):
  for v in o.Group:yield from leaves(v)
 elif o.TypeId in ['Part::Feature','PartDesign::Feature']:yield o
for top in d.RootObjects[0].Group:
 pieces=[]
 for obj in leaves(top):
  sh=obj.Shape.copy();sh.Placement=obj.getGlobalPlacement();pieces.append(sh)
 if not pieces:continue
 shape=Part.makeCompound(pieces);shape.rotate(V(),V(0,0,1),180);shape.translate(V(48,2,4.205));compounds.append(shape)
 pos=top.getGlobalPlacement().Base
 nearest=min(contract,key=lambda k:math.hypot(contract[k]['x']-pos.x,contract[k]['y']+pos.y))
 matches=math.hypot(contract[nearest]['x']-pos.x,contract[nearest]['y']+pos.y)<.05
 label=nearest if matches else top.Label
 if matches:components.append((label,shape))
 for o in obstacles:
  if not shape.BoundBox.intersect(o.Shape.BoundBox):continue
  vol=shape.common(o.Shape).Volume
  if vol>1e-5:report.append({'part':label,'object':o.Name,'volume_mm3':round(vol,6)})
pairs=[]
for i,(name,shape) in enumerate(components):
 for other,sh in components[i+1:]:
  if not shape.BoundBox.intersect(sh.BoundBox):continue
  vol=shape.common(sh).Volume
  if vol>1e-5:pairs.append({'parts':[name,other],'volume_mm3':round(vol,6)})
out={'scope':'Nominal STEP bodies vs selected L-case physical parts and conservative battery/FPC keepouts. Missing models listed separately. No tolerances, screen tail bend/reach or insertion paths verified. Original case unchanged.','collisions':report,'component_collisions':pairs,'component_groups':len(compounds),'step_component_top_z_mm':1.595,'transform':'Rotate 180deg about Z, translate (48,2,4.205), align front model seating to case Z5.8'}
(P/'output/case-fit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(out,ensure_ascii=False,indent=2))
