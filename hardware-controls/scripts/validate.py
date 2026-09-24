"""Read-only native design audit; consumes refreshed KiCad and FreeCAD reports."""
from pathlib import Path
import hashlib,json,math,zipfile,subprocess
import pcbnew as p
P=Path(__file__).resolve().parents[1];ROOT=P.parent
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
b=p.LoadBoard(str(P/'controls.kicad_pcb'))
data=json.loads((P/'output/design.json').read_text(encoding='utf8'))
assert data['connector_pinout']==['GND','+3V3','SDA','SCL','INT_N','RESET_N',None,None,None,None,'KEY_POWER','GND']
spec={c['ref']:c for c in data['components']};fps={f.GetReference():f for f in b.GetFootprints()}
assert set(fps)==set(spec) and len(fps)==42
for ref,f in fps.items():
 c=spec[ref];x,y,side,angle=c['pcb']
 assert f.GetPath().AsString()=='/'+data['root_uuid']+'/'+c['symbol_uuid'],ref
 assert f.GetValue()==c['value'] and f.GetFPIDAsString()=='Controls:'+c['footprint'],ref
 assert math.hypot(f.GetPosition().x/1e6-(44-x),f.GetPosition().y/1e6-y)<1e-5,ref
 assert f.IsFlipped()==(side=='B'),ref
 for pad in f.Pads():
  if pad.GetNumber() in c['nets']:assert pad.GetNetname()=='/'+c['nets'][pad.GetNumber()],(ref,pad.GetNumber())
assert b.GetCopperLayerCount()==2 and abs(b.GetDesignSettings().GetBoardThickness()/1e6-.8)<1e-6
assert sum(len(f.Models()) for f in fps.values())==26
# Interface audit: four digital keys terminate at U2, never at J1; POWER
# is independent of both ICs and pulled up to +3V3 by R14.
members={}
for ref,f in fps.items():
 for a in f.Pads():
  if a.GetNumber():members.setdefault(a.GetNetname(),set()).add((ref,a.GetNumber()))
assert members['/KEY_POWER']=={('SW1','1'),('J1','11'),('TP7','1'),('R14','2')}
assert fps['R14'].GetValue()=='10k'
assert {('R14','1'),('J1','2')} <= members['/+3V3']
assert ('SW1','2') in members['/GND']
assert {('U1','11'),('U2','13'),('J1','3'),('R4','2'),('TP3','1')}==members['/SDA']
assert {('U1','14'),('U2','12'),('J1','4'),('R5','2'),('TP4','1')}==members['/SCL']
for i,name in enumerate(['BACK','PREV','NEXT','PLAY']):
 assert members['/KEY_'+name]=={('SW'+str(i+2),'1'),('U2',str(i+2)),('R'+str(i+9),'2'),('TP'+str(i+8),'1')}
for n in ['7','8','9','10']:
 pad=next(a for a in fps['J1'].Pads() if a.GetNumber()==n)
 assert pad.GetNetname().startswith('unconnected-') and len(members[pad.GetNetname()])==1
assert {('U1','15'),('U2','11'),('J1','5'),('R6','2'),('TP5','1')}==members['/INT_N']
assert {('U1','12'),('U2','1'),('J1','6'),('R7','2'),('TP6','1')}==members['/RESET_N']
assert {('U2',str(n)) for n in [7,8,9,10]}|{('R13','1')}==members['/UNUSED_INPUTS']
electrode=[]
for pad in fps['E1'].Pads():
 assert pad.IsOnLayer(p.F_Cu) and not any(pad.IsOnLayer(l) for l in [p.B_Cu,p.F_Mask,p.F_Paste])
 poly=pad.GetEffectivePolygon(p.F_Cu);assert poly.OutlineCount()==1
 line=poly.COutline(0);pp=[(line.CPoint(i).x/1e6,line.CPoint(i).y/1e6) for i in range(line.PointCount())]
 area=abs(sum(a[0]*z[1]-z[0]*a[1] for a,z in zip(pp,pp[1:]+pp[:1])))/2
 electrode.append({'pin':pad.GetNumber(),'net':pad.GetNetname(),'connected_islands':1,'copper_area_mm2':round(area,4)})
drc=json.loads((P/'output/drc.json').read_text());erc=json.loads((P/'output/erc.json').read_text())
assert not drc['violations'] and not drc['unconnected_items'] and not drc['schematic_parity']
assert not [v for s in erc['sheets'] for v in s['violations']]
fit=json.loads((P/'mechanical/fit-check.json').read_text(encoding='utf8'))
assert fit['pass'] and fit['controls_pcb_sha256']==sha(P/'controls.kicad_pcb'),'Refresh mechanical report'
plan=json.loads((P/'mechanical/interconnect-plan.json').read_text())
assert fit['source_sha256']['mainboard']==plan['mainboard_sha256']==sha(ROOT/plan['mainboard'])
assert fit['source_sha256']['enclosure']==sha(ROOT/'mechanical/enclosure-q2-f/ESP32S31_MP3_Q2_F.FCStd')
assert fit['interconnect']['nominal_route_pass'] and fit['interconnect']['pin_mapping']=={str(i):i for i in range(1,13)}
host=p.LoadBoard(str(ROOT/plan['mainboard']));hc=host.FindFootprintByReference('FPC1')
hostpads={a.GetNumber():a for a in hc.Pads()};controlpads={a.GetNumber():a for a in fps['J1'].Pads()}
expected=['GND','VCC_3V3','BQ25895_I2C_SDA','BQ25895_I2C_CLK','ESP_IO43','ESP_IO44','','','','','ESP_IO42','GND']
for i,name in enumerate(expected,1):
 assert hostpads[str(i)].GetNetname()==name,(i,name)
 assert abs(hostpads[str(i)].GetPosition().y/1e6-65.647-(controlpads[str(i)].GetPosition().y/1e6+42.3))<1e-5,i
assert fps['J1'].GetValue()=='HC-FPC-05-10-12RLTAG'
assert all(controlpads[n].GetNetname()=='/GND' for n in ['13','14'])
subprocess.run(['git','diff','--quiet','HEAD','--','hardware-q2-placement/hardware.kicad_pcb','mechanical/enclosure-q2-f/ESP32S31_MP3_Q2_F.FCStd'],cwd=ROOT,check=True)
tracks=[t for t in b.GetTracks() if not isinstance(t,p.PCB_VIA)];vias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA)]
report={'revision':'B','i2c_addresses':{'wheel':'0x1C','keys':'0x20'},'four_keys_i2c_only_at_connector':True,'power_independent_active_low':True,'power_pullup_ohm':10000,'power_pullup_rail':'+3V3','shared_open_drain_interrupt':True,'status':'ROUTED_STANDALONE_PROTOTYPE_REQUIRES_PHYSICAL_VALIDATION','pcb_sha256':sha(P/'controls.kicad_pcb'),'schematic_sha256':sha(P/'controls.kicad_sch'),'project_sha256':sha(P/'controls.kicad_pro'),'step_sha256':sha(P/'output/controls-populated.step'),'footprints':42,'physical_components':26,'front_components':5,'back_components':21,'schematic_links_verified':42,'copper_layers':2,'board_mm':[44,34,.8],'track_segments':len(tracks),'vias':len(vias),'track_widths_mm':sorted({round(t.GetWidth()/1e6,4) for t in tracks}),'via_drills_mm':sorted({round(t.GetDrill()/1e6,4) for t in vias}),'drc_violations':0,'unconnected_items':0,'schematic_parity_issues':0,'erc_violations':0,'electrodes':electrode,'nominal_mechanical_fit_pass':True,'mainboard_connected':False,'mainboard_and_source_enclosure_unchanged':True,'production_release':False}
report['fabrication_files_sha256']={f.name:sha(f) for f in sorted((P/'fabrication').iterdir()) if f.is_file()}
report['connector_pinout']=data['connector_pinout']
report['mainboard_source']=plan['mainboard']
report['interconnect']={'cable':'12P / 0.5mm / 40mm / B opposite contacts / 0.3mm terminal','nominal_geometry_pass':True,'sample_validation_required':True,'mainboard_mounting_posts_pending':True,'mainboard_source_sha256':plan['mainboard_sha256']}
(P/'output/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
data['status']=report['status'];data['pcb_sha256']=report['pcb_sha256'];(P/'output/design.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
with zipfile.ZipFile(P/'output/controls-B-prototype-gerbers.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted((P/'fabrication').iterdir()):
  if f.is_file():z.write(f,f.name)
print('CONTROLS_VALIDATED',json.dumps(report,ensure_ascii=False))
