"""Executed inside build_enclosure.py: corrected stack and two separate FPC paths."""
V=App.Vector
main_z=params['MainRearZ'];front_z=main_z+params['MainThickness']
for oldname,newname,label,col in [('PCB','MainPCB','主板 / ESP32 面朝屏幕',(.12,.40,.27)),('ComponentEnvelopes','MainComponents','主板元件 / flipped together with PCB',(.42,.45,.49))]:
    sh=Part.Shape();sh.read(str(HERE/'reference'/('source-'+oldname+'.brep')))
    sh.rotate(V(25,0,0),V(0,1,0),180);sh.translate(V(0,0,8.1+main_z))
    ref(newname,label,sh,col,'Rigid transformation of the source board: x_new=50-x_old; z_new=8.1+MainRearZ-z_old. XY and pads are NOT rearranged.')
component_refs=[f['reference'] for f in layout['footprints'] if not f['reference'].startswith('SCREW')]
component_shapes=dict(zip(component_refs,doc.MainComponents.Shape.Solids))
esp=ref('ESP32Front','ESP32 / 主板正面，朝屏幕',component_shapes['U9'].copy(),(.70,.73,.75),'Envelope height3.2 mm assumed; source footprint XY retained.')
fpc2_shape=Part.makeBox(3.2,7.9,1.0,V(7.652,16.450,main_z-1.0))
fpc2=ref('ScreenConnectorFPC2','FPC2 / rear / verified 1.0 mm height',fpc2_shape,(.70,.22,.18),'AFE03 drawing:7.9 x3.2 x1.0, lower contact, FPC0.20 +/-0.03. Internal slot Z and screen tail thickness unconfirmed. Solid outer envelope, no fictional slot.')

target=rounded('PCBTargetEnvelope',46,76,10,p('MainThickness'),2,2,p('MainRearZ'))
ref_native(target,'新板机械空间 / 46 x76 R10 clearance reference; actual routed board is MainPCB',(.1,.49,.36))
battery=box('BatteryReference',p('BatteryWidth'),p('BatteryLength'),p('BatteryThickness'),p('BatteryX'),p('BatteryY'),p('BatteryZ'))
ref_native(battery,'电池占位 / 主板正面与操作板之间，24 x 34 x 3',(.46,.50,.55))
rf=ref('AntennaKeepoutReference','天线区域 / screen backing still needs RF review',Part.makeBox(22.254,9.669,6.64,V(4.154,2,front_z)),(.85,.25,.12))

# One independent rounded PCB: both ring electrodes and all five keys go on this board.
control_mounts=[(6,53),(44,53),(6,69),(44,69)]
control=rounded('ControlBoardBlank',p('ControlBoardWidth'),p('ControlBoardLength'),p('ControlBoardRadius'),p('ControlBoardThickness'),p('ControlBoardX'),p('ControlBoardY'),p('ControlBoardZ'))
control=cut('ControlBoard',control,fuse('ControlMountHoles',[cylinder('ControlHole'+str(i),.9,2,x,y,10.5) for i,(x,y) in enumerate(control_mounts)]))
ref_native(control,'独立滑环+五键板 / 44 x 34 x 0.8 / R10 / 4xD1.8',(.07,.44,.30))
control.addProperty('App::PropertyString','Status','PCB').Status='MECHANICAL OUTLINE ONLY: no schematic, copper, assigned pins or electrical implementation.'
control.addProperty('App::PropertyString','LocalDatum','PCB').LocalDatum='Local origin is case (3,44.3). Hole centers (3,8.7),(41,8.7),(3,24.7),(41,24.7); diameter1.8.'
control_top=params['ControlBoardZ']+params['ControlBoardThickness']
key_positions=[('Power',25,61.3),('Back',25,48.3),('Previous',38,61.3),('Next',12,61.3),('PlayPause',25,74.3)]
switches=[]
for name,x,y in key_positions:
    sw=box('Tact'+name,3,3,p('ControlSwitchHeight'),x-1.5,y-1.5,control_top)
    ref_native(sw,name+' / 3 x 3 x 0.55 tact keepout, part TBD',(.25,.28,.32));switches.append(sw)
electrodes=[]
for i in range(12):
    shape=Part.makeCylinder(15.5,.012,V(25,61.3,control_top),V(0,0,1),26).cut(Part.makeCylinder(10.5,.03,V(25,61.3,control_top-.01)))
    shape.rotate(V(25,61.3,0),V(0,0,1),i*30+2);electrodes.append(shape)
sensor=ref('ControlRingElectrodeGuide','滑环电极位置示意 / 12 sectors, NOT copper design',Part.makeCompound(electrodes),(.76,.56,.24),'Only an illustrative electrode band. Key keepouts, electrode shapes, shielding and sensing IC are not designed.')
daughterconn=ref('ControlFPCConnector','操作板背面 FPC 座预留 / pin count TBD',Part.makeBox(7.5,3,1,V(37,48.5,10.1)),(.14,.16,.19),'7.5 x 3 x 1 mm placeholder, not a chosen part or pinout.')
mainconn=ref('MainControlFPCReserve','主板正面预留 FPC 座 / not present in current KiCad',Part.makeBox(7.5,3,1,V(37,34,front_z)),(.20,.25,.31),'NEW mainboard connector reserved for later PCB design. No current hardware net assignment.')

# Native housing posts support the small PCB at its top face. M1.6 heads are on its rear.
parts.removeObject(housing);construction.addObject(housing)
posts=[]
for i,(x,y) in enumerate(control_mounts):
    posts.append(cut('ControlPost'+str(i),cylinder('ControlPostOuter'+str(i),2,1.0,x,y,control_top),cylinder('ControlPilot'+str(i),.65,1.5,x,y,control_top-.1)))
housing=fuse('HousingWithControlPosts',[housing]+posts)
housing=final(housing,'HousingWithControlPosts','01 Q2 机身 / 独立操作板四点安装柱',(.74,.77,.80))
fasteners=[]
for x,y in control_mounts:
    fasteners.append(Part.makeCylinder(.8,2.0,V(x,y,10.6)).fuse(Part.makeCylinder(1.65,.5,V(x,y,10.6))))
control_screws=ref('ControlBoardFasteners','4 x M1.6 螺钉包络 / length and head TBD',Part.makeCompound(fasteners),(.68,.71,.73))

# Screen: rotate the display installation 180deg in its own plane, so its tail exits LEFT.
# Channel topology: front -> board left edge -> rear -> service loop -> original FPC2.
r=params['FPCWrapRadius'];t=params['FPCThicknessEstimated'];wrapx=params['FPCWrapX']
edge=params['LCDInstalledX'];cy=params['LCDInstalledY']+params['LCDWidth']/2
ztop=12.1;zrun=params['FPCBackRunZ'];ru=params['FPCServiceRadius'];zreturn=zrun+2*ru
tx=wrapx+r;topcenter=ztop-r;bottomcenter=zrun+r
tipx=8.352;tipy=cy
prefix=edge-tx+math.pi*r+(topcenter-bottomcenter)
neck_remaining=params['FPCNeckLengthEstimated']-prefix
assert neck_remaining>0
nx=tx+neck_remaining
def route_length(a):return prefix+neck_remaining+math.hypot(a-nx,tipy-cy)+math.pi*ru+(a-tipx)
lo,hi=max(nx,tipx)+1,40
for _ in range(70):
    mid=(lo+hi)/2
    if route_length(mid)<params['FPCExtension']:lo=mid
    else:hi=mid
turnx=(lo+hi)/2
def annulus(cx,cz,rad,width,yy):
    return Part.makeCylinder(rad+t/2,width,V(cx,yy-width/2,cz),V(0,1,0)).cut(Part.makeCylinder(rad-t/2,width+2,V(cx,yy-width/2-1,cz),V(0,1,0)))
upper=annulus(tx,topcenter,r,18,cy).common(Part.makeBox(r+t,20,r+t,V(tx-r-t,cy-10,topcenter)))
lower=annulus(tx,bottomcenter,r,18,cy).common(Part.makeBox(r+t,20,r+t,V(tx-r-t,cy-10,bottomcenter-r-t)))
loop=annulus(turnx,(zrun+zreturn)/2,ru,6.6,tipy).common(Part.makeBox(ru+t,8,2*ru+2*t,V(turnx,tipy-4,zrun-t)))
def strip_x(x1,x2,y1,y2,z,width):
    # A sheared clearance ribbon. NOT a developability or flex-strain proof.
    pts=[V(x1,y1-width/2,z-t/2),V(x1,y1+width/2,z-t/2),V(x1,y1+width/2,z+t/2),V(x1,y1-width/2,z+t/2)]
    return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(x2-x1,y2-y1,0))
routeparts=[Part.makeBox(edge-tx,18,t,V(tx,cy-9,ztop-t/2)),upper,Part.makeBox(t,18,topcenter-bottomcenter,V(wrapx-t/2,cy-9,bottomcenter)),lower,Part.makeBox(neck_remaining,18,t,V(tx,cy-9,zrun-t/2)),strip_x(nx,turnx,cy,tipy,zrun,6.6),loop,Part.makeBox(turnx-tipx,6.6,t,V(tipx,tipy-3.3,zreturn-t/2))]
fpc=ref('DisplayFPCRoute','屏幕 FPC / 上移1.5 mm后的自然轴线，尚未插接',Part.makeCompound(routeparts),(.9,.55,.16),'Centerline46.14 mm; no lateral shear. Natural axisY20.400 = socketY20.400; XY aligned. R0.65/R0.675 and tip X/Z are assumptions; not mated or fabrication-ready.')
fpc.addProperty('App::PropertyLength','NeutralRouteLength','Routing').NeutralRouteLength=route_length(turnx)
fpc.addProperty('App::PropertyVector','TerminalTip','Routing').TerminalTip=V(tipx,tipy,zreturn)
fpc.addProperty('App::PropertyString','Connection','Routing').Connection='LCD front -> LEFT edge wrap -> rear loop; XY aligned, connector insertion thickness/slot remain unverified'
# Daughterboard interconnect: a separate freely selected cable, endpoints are both reserved.
controlpath=[V(40.75,50.0,10.55),V(40.75,43.6,10.55),V(40.75,43.6,8.0),V(40.75,35.5,8.0),V(40.75,35.5,6.0)]
ctrlsh=[]
for a,b in zip(controlpath,controlpath[1:]):
    # Orthogonal rectangular keepout ribbons intentionally show topology; fold radii pending part selection.
    if abs(a.z-b.z)<1e-6:ctrlsh.append(Part.makeBox(6.5,abs(b.y-a.y),.15,V(a.x-3.25,min(a.y,b.y),a.z-.075)))
    else:ctrlsh.append(Part.makeBox(6.5,.15,abs(b.z-a.z),V(a.x-3.25,a.y-.075,min(a.z,b.z))))
controlfpc=ref('ControlFPCRoute','操作板 FPC 通道 / 独立于屏幕排线',Part.makeCompound(ctrlsh),(.20,.57,.85),'Routing channel only. Proposed cable25 mm, width6.5. Bend radii, insertion lengths, contacts and pin count require connector selection.')

# Rear-cover integral M2 standoffs follow actual new KiCad NPTH centers.
mainmounts=[(149-f['position_mm'][0],f['position_mm'][1]-49) for f in layout['footprints'] if f['reference'].startswith('SCREW')]
parts.removeObject(rear);construction.addObject(rear)
pcbposts=[]
for i,(x,y) in enumerate(mainmounts):
    pcbposts.append(cut('MainPCBPost'+str(i),cylinder('MainPCBPostOuter'+str(i),1.9,3.2,x,y,1.0),cylinder('MainPCBPostPilot'+str(i),.8,3.5,x,y,1.2)))
rear=final(fuse('RearCoverWithPCBPosts',[rear]+pcbposts),'RearCoverWithPCBPosts','02 Rear cover / four actual-PCB M2 support posts',(.67,.70,.73))
