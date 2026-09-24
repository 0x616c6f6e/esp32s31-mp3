"""Summarize the saved candidate without changing its electrical connectivity."""
from pathlib import Path
import pcbnew as p,json,hashlib,collections,re
P=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(P/'q2-v2.kicad_pcb'));out=P/'output'
contract=json.loads((out/'design-contract.json').read_text(encoding='utf8'))
power_policy=json.loads((P/'power-only-0402.json').read_text()) if (P/'power-only-0402.json').exists() else None
contract['status']='POWER_ONLY_0402_MANUAL_SIGNAL_ROUTING_REQUIRED' if power_policy else 'FULLY_ROUTED_REVIEW_CANDIDATE_NOT_RELEASED_FOR_FABRICATION'
contract['release_holds']=['USB complete-path controlled impedance / coupling / skew with manufacturer stackup','RF transmission line impedance, matching and antenna placement tuning','AM213 3.3 V follows the archived OSPTEK reference circuit; datasheet discrepancy and operating margins still require bench validation','Screen BTB tail reach, contact orientation and insertion clearance with real parts','Power/charging current, AON isolation and shutdown pulse bench validation']
if power_policy:
 contract['release_holds'][:0]=['All signal routing intentionally removed; manual signal routing required','CS43131 HPREFA/HPREFB independent Kelvin returns to headphone reference; current common-net pours do not enforce this topology','0402 RF matching and crystal capacitors need parasitic/load retuning after package change']
 for f in b.GetFootprints():
  c=contract['components'][f.GetReference()];c.update(x=p.ToMM(f.GetPosition().x)-128.868,y=p.ToMM(f.GetPosition().y)-67.647,angle=f.GetOrientationDegrees())
 for c in power_policy['package_changes']:
  f=b.FindFootprintByReference(c['ref']);c['new_position']=[p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y)];c['angle']=f.GetOrientationDegrees()
 (P/'power-only-0402.json').write_text(json.dumps(power_policy,ensure_ascii=False,indent=2),encoding='utf8')
(out/'design-contract.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2),encoding='utf8')
netstats=collections.defaultdict(lambda:{'trace_length_mm':0,'vias':0,'layers':set(),'widths_mm':set()})
for t in b.GetTracks():
 s=netstats[t.GetNetname()]
 if isinstance(t,p.PCB_VIA):s['vias']+=1
 else:s['trace_length_mm']+=p.ToMM(t.GetLength());s['layers'].add(t.GetLayerName());s['widths_mm'].add(round(p.ToMM(t.GetWidth()),4))
for s in netstats.values():s['trace_length_mm']=round(s['trace_length_mm'],6);s['layers']=sorted(s['layers']);s['widths_mm']=sorted(s['widths_mm'])
(out/'net-routing-statistics.json').write_text(json.dumps(netstats,indent=2),encoding='utf8')
drc=json.loads((out/'drc.json').read_text(encoding='utf8'));erc=json.loads((out/'erc.json').read_text(encoding='utf8'))
def countviolations(e):
 if isinstance(e,dict):return len(e.get('violations',[]))+sum(countviolations(v) for k,v in e.items() if k!='violations')
 if isinstance(e,list):return sum(countviolations(v) for v in e)
 return 0
v=collections.Counter()
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA):v[f'{p.ToMM(t.GetWidth(p.F_Cu)):.2f}/{p.ToMM(t.GetDrillValue()):.2f}']+=1
summary={'status':contract['status'],'board_sha256':hashlib.sha256((P/'q2-v2.kicad_pcb').read_bytes()).hexdigest(),'kicad_version':p.GetBuildVersion(),'size_mm':[46,76,1.6],'copper_layers':b.GetCopperLayerCount(),'components':len(list(b.GetFootprints())),'tracks':sum(not isinstance(t,p.PCB_VIA) for t in b.GetTracks()),'vias':sum(v.values()),'via_diameter_drill_mm':dict(v),'drc_violations':len(drc['violations']),'unconnected':len(drc['unconnected_items']),'schematic_parity':len(drc['schematic_parity']),'erc_violations':countviolations(erc),'ignored_drc_checks':drc['ignored_checks'],'without_3d_models':[f.GetReference() for f in b.GetFootprints() if len(f.Models())==0],'release_holds':contract['release_holds']}
assert summary['drc_violations']==summary['schematic_parity']==summary['erc_violations']==0
if power_policy:
 allowed=set(power_policy['rails'])|set(power_policy['local_power_nodes'])
 items={a.m_Uuid.AsString():a for f in b.GetFootprints() for a in f.Pads()};items.update({a.m_Uuid.AsString():a for a in b.GetTracks()})
 missing_power=[e for e in drc['unconnected_items'] if any(items[i['uuid']].GetNetname() in allowed for i in e['items'] if i['uuid'] in items)]
 summary.update(power_unconnected=len(missing_power),intentional_signal_unconnected=len(drc['unconnected_items'])-len(missing_power),remaining_signal_copper_items=sum(t.GetNetname() not in allowed for t in b.GetTracks()),package_replacements=len(power_policy['package_changes']))
 assert not missing_power and summary['remaining_signal_copper_items']==0
 remaining=[]
 for f in b.GetFootprints():
  pads=list(f.Pads())
  if f.GetReference().startswith(('C','R')) and len(pads)==2:
   dist=((pads[0].GetPosition().x-pads[1].GetPosition().x)**2+(pads[0].GetPosition().y-pads[1].GetPosition().y)**2)**.5/1e6
   if dist<.65:remaining.append(f.GetReference())
 summary['remaining_0201_resistors_capacitors']=remaining;assert not remaining
else:assert summary['unconnected']==0
(out/'validation-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
rows=json.loads((P.parent/'hardware-q2-v2-plan/pin-assignment.json').read_text(encoding='utf8'))['rows'];fp=b.FindFootprintByReference('U9');pads={int(a.GetNumber()):a for a in fp.Pads() if a.GetNumber().isdigit()};lines=['# V2 实际主控引脚表','', '从当前 PCB 的 U9 焊盘网络生成；GPIO 与 QFN 物理脚号分别列出。尚未进行固件或上电验证。','', '| QFN 脚号 | 芯片管脚 | GPIO | 当前网络 |','|---|---|---|---|'];head=['/* Generated from V2 PCB net assignments. GPIO numbers, not QFN pin numbers. */','/* Not a compiled or bench-tested BSP. SYS I2C uses LP I2C on GPIO 6/7. */','#pragma once']
for row in rows:
 a=pads[int(row['pin'])];net=a.GetNetname();gpio=row['gpio'];display='NC' if not net or net.startswith('unconnected-') else net
 lines.append(f'| {row["pin"]} | {row["pin_name"]} | {gpio if gpio is not None else "—"} | {display} |')
 if gpio is not None and display!='NC':head.append(f'#define Q2_{re.sub("[^A-Za-z0-9_]","_",net).upper()}_GPIO {gpio}')
(P/'pin-assignment.md').write_text('\n'.join(lines)+'\n',encoding='utf8');(P/'q2_v2_pins.h').write_text('\n'.join(head)+'\n',encoding='utf8')
print(json.dumps(summary,ensure_ascii=False,indent=2))

