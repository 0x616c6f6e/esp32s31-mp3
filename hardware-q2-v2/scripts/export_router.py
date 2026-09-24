"""Export current board without moving parts or deleting copper."""
from pathlib import Path
import pcbnew as p,sys,json
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'hardware-q2-v2-plan/scripts'))
from sexpr import *
b=p.LoadBoard(str(P/'q2-v2.kicad_pcb'));p.ExportSpecctraDSN(b,str(P/'output/native.dsn'))
t=parse((P/'output/native.dsn').read_text().replace('(string_quote ")','(string_quote QUOTE)'));st=get(t,'structure');network=get(t,'network')
for cls in [st]+children(network,'class'):
 for rule in list(children(cls,'rule')):cls.remove(rule)
 cls.append(['rule',['width','100' if 'finish' in sys.argv else '150'],['clearance','100'],['clearance','100',['type','smd_smd']]])
for i,la in enumerate(children(st,'layer')):
 if i in [1,4]:get(la,'type')[1]='power'
for plane in list(children(st,'plane')):
 if str(get(plane,'polygon')[1]) not in ['GND1','GND2']:st.remove(plane)
power={'VBAT','GBAT','VBUS_5V','VCC','VCC_3V3','VCC_PMID','VCC_1V8','MCU_1V8','MCU_VDD_SPI','MCU_VDDA34','VCC_3V3_AON','MOTOR_OUT_P','MOTOR_OUT_N','N_5N15'}
for cls in children(network,'class'):cls[:]=[a for a in cls if not(isinstance(a,str) and a in power)]
network.append(['class','v2_power',*sorted(power),['circuit',['use_via',S('Via[0-5]_450:200_um')]],['rule',['width','150' if 'finish' in sys.argv else '300'],['clearance','100']]])
if 'finish' in sys.argv:
 for cls in children(network,'class'):
  circuit=get(cls,'circuit');via=get(circuit,'use_via');via[1]=S('Via[0-5]_350:150_um')
for item in get(t,'wiring')[1:]:
 if isinstance(item,list) and item[0] in ['wire','via']:
  item[:]=[a for a in item if not(isinstance(a,list) and a and a[0]=='type')];item.append(['type','protect'])
(P/'output/routing.dsn').write_text(dump(t).replace('(string_quote QUOTE)','(string_quote ")'),encoding='utf8')
cfg={'version':'2.4.1','profile':{'id':'f769856a-f58a-4899-b7d9-ccf4428d2d70','allow_telemetry':False,'allow_contact':False},'gui':{'enabled':False},'api_server':{'enabled':False},'mcp_server':{'enabled':False},'usage_and_diagnostic_data':{'disable_analytics':True},'router':{'max_passes':20,'copper_to_edge_clearance_um':250,'hole_clearance_um':250,'automatic_neckdown':True,'strict_drc':True,'optimizer':{'max_threads':1}}}
(P/'output/router-userdata/freerouting.json').write_text(json.dumps(cfg))
print('Exported',len(b.GetFootprints()),'components and',len(b.GetTracks()),'protected copper items')
