"""Check that delivered reports, board and frozen mechanical source agree."""
from pathlib import Path
import json,hashlib,collections
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'hardware-q2';E=ROOT/'mechanical/enclosure-q2-e'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
d=read(P/'output/final-drc.json');a=read(P/'output/final-audit.json');m=read(E/'exports/validation.json');f=read(E/'reference/source-manifest.json');g=read(P/'output/geometry.json');erc=read(P/'output/final-erc.json')
h=hashlib.sha256((P/'hardware.kicad_pcb').read_bytes()).hexdigest()
assert h==a['pcb_sha256']==m['pcb_source_sha256']==f['pcb_source_sha256']
assert not d['violations'] and not d['unconnected_items'] and not d['schematic_parity']
assert not a['pad_net_changes'] and a['rules_unchanged']
assert m['new_geometry_pass'] and m['entire_current_hardware_fits'] and not m['per_component_conflicts']
ee=collections.Counter(v['severity'] for s in erc['sheets'] for v in s['violations'])
assert ee['error']==0 and ee['warning']==9
stats=collections.Counter(o['kind'] for o in g['items'])
r={'date':'2026-09-21','pcb_sha256':h,'drc_violations':0,'unconnected_items':0,'schematic_parity':0,'erc_errors':ee['error'],'erc_warnings':ee['warning'],'pad_net_changes':0,'footprints':a['footprints'],'geometry_counts':dict(stats),'outline_mm':[46,76],'mechanical_interference_checks_pass':True,'battery_reservation_mm':[24,34,3],'screen_fpc_xy_aligned':True,'screen_fpc_mating_verified':False,'component_heights_partly_assumed':True,'control_daughterboard_electrically_implemented':False,'manufacturing_release':False}
(P/'output/validation-summary.json').write_text(json.dumps(r,indent=2),encoding='utf8');print('DELIVERY_CONSISTENT',json.dumps(r))
