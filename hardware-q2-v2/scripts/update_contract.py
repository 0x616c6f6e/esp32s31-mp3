from pathlib import Path
import pcbnew as p,json
P=Path(__file__).resolve().parents[1];fn=P/'output/design-contract.json';d=json.loads(fn.read_text(encoding='utf8'));b=p.LoadBoard(str(P/'q2-v2.kicad_pcb'))
for c in d['components'].values():
 f=b.FindFootprintByReference(c['ref']);c.update(x=round(p.ToMM(f.GetPosition().x)-128.868,6),y=round(p.ToMM(f.GetPosition().y)-67.647,6),angle=f.GetOrientationDegrees())
d['components']['USB1']['nets']['13']='GND';d['components']['USB1']['nets']['14']='GND'
d['electrical_review_changes'].append({'ref':'USB1','change':'Connect both shield mounting-pad groups 13/14 to GND; align schematic with actual PCB shield copper'})
fn.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
f=P/'q2-v2.kicad_pro';q=json.loads(f.read_text(encoding='utf8'));q['meta']['filename']=f.name;q['board']['design_settings']['rules']['min_hole_clearance']=.2
q['board']['design_settings']['rules']['min_silk_clearance']=.15
default=q['net_settings']['classes'][0];power=dict(default);power.update(name='Power',description='0.30 mm local distribution; widen main supply trunks as polygons',track_width=.3)
q['net_settings']['classes']=[default,power]
q['net_settings']['netclass_patterns']=[{'netclass':'Power','pattern':n} for n in ['VBAT','GBAT','VBUS_5V','VCC','VCC_3V3','VCC_1V8','VCC_3V3_AON','VCC_PMID','MCU_1V8','MCU_VDD_SPI','MCU_VDDA34']]
f.write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf8');print('Updated positions, shield nets and documented fabrication rules')
