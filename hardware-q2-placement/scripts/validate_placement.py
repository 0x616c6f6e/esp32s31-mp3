"""Validate current PCB against the repaired, unrouted 2026-09-21 baseline.

Regenerate output/current-netlist.xml, placement-drc.json, placement-erc.json,
the STEP and mechanical check before running. Never modifies design files.
"""
from pathlib import Path
import csv,json
from board_snapshot import snapshot,sha
from relink_schematic import run
P=Path(__file__).resolve().parents[1];ROOT=P.parent
base=json.loads((P/'review/placement-baseline.json').read_text(encoding='utf8'))
now=snapshot(P/'hardware.kicad_pcb');layout=json.loads((P/'output/placement.json').read_text(encoding='utf8'))
assert now['pcb_sha256']==layout['pcb_sha256'],'Stale placement data'
assert set(base['footprints'])==set(now['footprints'])
for ref,old in base['footprints'].items():
    new=now['footprints'][ref]
    for key in ['uuid','path','value','fpid','dnp','pads']:
        assert old[key]==new[key],(ref,key)
    if ref in layout['fixed_mechanical_references']:
        for key in ['xy','angle','side']:assert old[key]==new[key],(ref,key)
        assert new['locked'],ref
for key in ['outline_sha256','zones_sha256','layers_sha256','stackup_sha256']:
    assert now[key]==base[key],key
for name,expected in base['schematic_sha256'].items():assert sha(P/name)==expected,(name,'schematic changed since review')
assert len(now['footprints'])==125 and now['model_instances']==121
assert now['tracks_arcs_vias']==now['copper_zones']==0
run(P/'output/current-netlist.xml')
drc=json.loads((P/'output/placement-drc.json').read_text(encoding='utf8'))
assert not drc['violations'] and not drc['schematic_parity']
mechanical=json.loads((P/'output/mechanical-check.json').read_text(encoding='utf8'))
assert mechanical['pass'] and mechanical['pcb_sha256']==now['pcb_sha256']
assert mechanical['populated_step_sha256']==sha(P/'output/placement-populated.step')
assert mechanical['source_enclosure_sha256']==sha(ROOT/mechanical['source_enclosure'])
erc=json.loads((P/'output/placement-erc.json').read_text(encoding='utf8'))
issues=[v for s in erc['sheets'] for v in s['violations']]
errors=sum(v['severity']=='error' for v in issues)
assert errors==0
report={'status':'PLACEMENT_ONLY_REQUIRES_MANUAL_ROUTING','pcb_sha256':now['pcb_sha256'],
    'footprints':125,'physical_components':121,'pads':sum(len(f['pads']) for f in now['footprints'].values()),
    'schematic_links_verified':125,'moved_or_flipped_count':len(layout['changes']),
    'front_components':sum(f['side']=='F' for r,f in now['footprints'].items() if not r.startswith('SCREW')),
    'back_components':sum(f['side']=='B' for f in now['footprints'].values()),
    'pad_identity_and_nets_unchanged_since_repair':True,'user_schematics_preserved':True,
    'outline_antenna_and_stackup_unchanged':True,'locked_mechanical_references':layout['fixed_mechanical_references'],
    'tracks_arcs_vias':0,'copper_zones':0,'drc_violations':0,'schematic_parity_issues':0,
    'expected_unconnected_items':len(drc['unconnected_items']),'erc_errors':errors,
    'erc_warnings':sum(v['severity']=='warning' for v in issues),'mechanical_nominal_solids_pass':True,
    'manufacturing_release':False}
(P/'output/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
with (P/'output/component-placement.csv').open('w',encoding='utf8',newline='') as out:
    writer=csv.writer(out);writer.writerow(['Reference','Side','X_mm','Y_mm','Rotation_deg','Value','Locked'])
    for r,f in sorted(now['footprints'].items()):writer.writerow([r,f['side'],*f['xy'],f['angle'],f['value'],f['locked']])
print('PLACEMENT_VERIFIED',json.dumps(report,ensure_ascii=False))
