from pathlib import Path
import FreeCAD as A,Part,json,sys
O=Path(__file__).resolve().parents[1];V=A.Vector
d=A.openDocument(str(O/'Q2_L_AM213_Adapter_Study.FCStd'))
def vol(a,b):
 if not a.BoundBox.intersect(b.BoundBox):return 0
 return sum(max(0,x.common(y).Volume) for x in a.Solids for y in b.Solids if x.BoundBox.intersect(y.BoundBox))
def stage(name,parts,targets,poses):
 rows=[]
 for xyz in poses:
  hits=[]
  for a in parts:
   s=a.Shape.copy();s.translate(V(*xyz))
   for b in targets:
    v=vol(s,b.Shape)
    if v>1e-5:hits.append([a.Name,b.Name,round(v,6)])
  rows.append({'offset_mm':xyz,'hits':hits})
  if hits:print(name,xyz,hits,flush=True)
 print('STAGE',name,len(rows),'bad',sum(bool(x['hits']) for x in rows),flush=True)
 return rows
res={}
res['wheel_from_rear_above_short_post']=stage('WHEEL',[d.WheelControlsA],[d.HousingControlsA],
 [[0,-3.5,z] for z in [-18,-14,-10,-8,-6,-5]]+[[0,y,-5] for y in [-3,-2,-1,0]]+[[0,0,z] for z in [-4,-3,-2,-1,-.5,0]])
res['center_from_rear']=stage('CENTER',[d.CenterButtonControlsA],[d.HousingControlsA,d.WheelControlsA],[[0,0,z] for z in [-16,-12,-8,-4,-2,-1,-.5,0]])
control=[d.ControlsBoard]+[o for o in d.Electronics.Group if o.Name.startswith('CTRL_')]
res['controls_before_motor']=stage('CONTROLS',control,[d.HousingControlsA,d.WheelControlsA,d.CenterButtonControlsA,d.ControlEdgePad],
 [[-1.3,-3,z] for z in [-18,-14,-10,-8,-6,-4,-2,-1,-.5]]+ [[-1.3,y,-.5] for y in [-2,-1.5,-1,-.5,0]]+ [[-1.3,0,z] for z in [-.3,0]]+[[x,0,0] for x in [-.9,-.6,-.3,0]])
res['motor_module_after_controls']=stage('MOTOR',[d.MotorCarrier,d.Motor_C08_005,d.MotorAdhesive],[d.HousingControlsA]+control+[d.ControlBoardFasteners,d.ControlWashers],[[0,0,z] for z in [-14,-10,-6,-4,-2,-1,-.5,0]])
res['lcd_from_front']=stage('LCD',[d.LCDModule,d.CoverLens,d.OLEDOpticalBond,d.ScreenRearFPCEnvelope],[d.HousingControlsA,d.LensAdhesive,d.DisplayAdapterPCB,d.DisplayAdapterComponents,d.DisplayAdapterConnectors],[[0,0,z] for z in [10,6,3,1,.5,.2,0]])
res['adapter_reservation_from_rear']=stage('ADAPTER',[d.DisplayAdapterPCB,d.DisplayAdapterComponents,d.DisplayAdapterConnectors],[d.HousingControlsA,d.LCDModule,d.ScreenRearFPCEnvelope],[[0,0,z] for z in [-15,-10,-5,-2,-1,-.5,0]])
if '--rear' in sys.argv:
 main=[o for o in d.Electronics.Group if o.Name.startswith('PCB_') or o.Name=='MainPCB']+[d.RearCoverWithPCBPosts,d.MainBoardFasteners]
 fixed=[d.HousingControlsA,d.ControlsBoard,d.WheelControlsA,d.CenterButtonControlsA,d.MotorCarrier,d.Motor_C08_005,d.LCDModule,d.RearInsertTop,d.RearInsertBottom,d.ControlBoardFasteners,d.ControlWashers,d.ControlEdgePad,d.BatteryPack,d.ScreenRearFPCEnvelope,d.DisplayAdapterPCB,d.DisplayAdapterComponents,d.DisplayAdapterConnectors]+[o for o in d.Electronics.Group if o.Name.startswith('CTRL_')]
 res['rear_mainboard_closing']=stage('REAR',main,fixed,[[0,0,z] for z in [-15,-10,-5,-2,-1,-.5,0]])
res['method']='Staged rigid poses; motor fitted after controls, LCD from front before lens, rear PCB last; cables not rigidly translated. Screen free tail and adapter cable are not yet routed; adapter is an envelope only. This is not continuous swept-volume, tooling or flex simulation.'
(O/'assembly-path-check.json').write_text(json.dumps(res,indent=2))
