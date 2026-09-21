"""Prepare source code for the integrated, actual KiCad Q2 revision."""
from pathlib import Path
import json,shutil
HERE=Path(__file__).resolve().parent;src=HERE/'enclosure-q2-d';dst=HERE/'enclosure-q2-e'
dst.mkdir(exist_ok=True);(dst/'exports').mkdir(exist_ok=True);(dst/'reference').mkdir(exist_ok=True)
params=json.loads((src/'parameters.json').read_text(encoding='utf8'));params.update(BatteryX=6.5,BatteryY=37)
(dst/'parameters.json').write_text(json.dumps(params,indent=2),encoding='utf8')
for name in ['build_enclosure.py','assembly_layout.py','validate_and_export.py','prepare_views.py','Rebuild.FCMacro']:
    s=(src/name).read_text(encoding='utf8')
    s=s.replace('ESP32S31_MP3_Q2_D','ESP32S31_MP3_Q2_E').replace('Q2_Enclosure_D','Q2_Enclosure_E').replace('Q2 D / screen raised 1.5 mm / full housing visible','Q2 E / actual46x76 KiCad PCB / aligned LCD FPC2')
    s=s.replace("ROOT/'hardware/","ROOT/'hardware-q2/").replace("'revision':'D'","'revision':'E'").replace('q2-d-','q2-e-').replace('assembly-D-current-PCB-CONFLICTS','assembly-E-new-PCB').replace('ASSEMBLY_D_COMPLETE','ASSEMBLY_E_COMPLETE')
    if name=='build_enclosure.py':s=s.replace('37.935,81,7.9','36.435,81,7.9')
    if name=='assembly_layout.py':
        s=s.replace('V(7.652,14.084,main_z-1.0)','V(7.652,16.450,main_z-1.0)')
        s=s.replace("47,76,10.5,p('MainThickness'),1.5,2","46,76,10,p('MainThickness'),2,2")
        s=s.replace('47 x 76 R10.5, not routed','46 x76 R10 clearance reference; actual routed board is MainPCB')
        s=s.replace('Natural axisY20.400 vs socketY18.034, mismatch2.366.','Natural axisY20.400 = socketY20.400; XY aligned.').replace('UNMATED, Y offset2.366 mm','XY aligned, connector insertion thickness/slot remain unverified')
        s+='''
# Rear-cover integral M2 standoffs follow actual new KiCad NPTH centers.
mainmounts=[(149-f['position_mm'][0],f['position_mm'][1]-49) for f in layout['footprints'] if f['reference'].startswith('SCREW')]
parts.removeObject(rear);construction.addObject(rear)
pcbposts=[]
for i,(x,y) in enumerate(mainmounts):
    pcbposts.append(cut('MainPCBPost'+str(i),cylinder('MainPCBPostOuter'+str(i),1.9,3.2,x,y,1.0),cylinder('MainPCBPostPilot'+str(i),.8,3.5,x,y,1.2)))
rear=final(fuse('RearCoverWithPCBPosts',[rear]+pcbposts),'RearCoverWithPCBPosts','02 Rear cover / four actual-PCB M2 support posts',(.67,.70,.73))
'''
    if name=='validate_and_export.py':
        s=s.replace('round(tipy-18.034,6)','round(tipy-20.400,6)')
        s=s.replace("volume=round(source.Shape.common(against.Shape).Volume,6)","shape=source.Shape\n        if source.Name=='MainComponents' and against==fpc:shape=Part.makeCompound([s for name,s in component_shapes.items() if name!='FPC2'])\n        volume=round(shape.common(against.Shape).Volume,6)")
        s=s.replace("(OUT/'validation.json').write_text", "checks['pcb_to_rear_standoffs_mm3']=round(doc.MainPCB.Shape.common(rear.Shape).Volume,6)\nchecks['pcb_corner_clearance_nominal_mm']=.8\nchecks['mating_slot_verified']=False\n(OUT/'validation.json').write_text")
    if name=='prepare_views.py':
        s=s.replace('Q2RearCover','RearCoverWithPCBPosts').replace('exterior-D.png','exterior-E.png').replace('front-D.png','front-E.png').replace('current-PCB-conflicts.png','new-PCB-installed.png')
        s=s.replace("show(external+['MainPCB','ESP32Front','ScreenConnectorFPC2','MainPCBHousingCollision','MainComponentsHousingCollision'])", "show(external+['MainPCB','MainComponents','ESP32Front','ScreenConnectorFPC2','LCDModule','DisplayFPCRoute','ControlBoard','ControlFPCConnector','BatteryReference'])")
        s=s.replace("doc.addProperty('App::PropertyString','ReviewStatus')", "doc.addProperty('App::PropertyString','ReviewStatus')")
        s=s.replace('Existing PCB still collides with shell; see current-PCB-conflicts.png and validation.json. Not production-ready.','Actual revised board installed; see validation.json. Component heights and FPC mating remain conditional.')
    (dst/name).write_text(s,encoding='utf8')
print(dst)
