"""Verify electrical migration and unchanged mechanical interface in candidate."""
from pathlib import Path
import json,sys,xml.etree.ElementTree as ET,hashlib
import pcbnew as p
R=Path(__file__).resolve().parents[2];P=R/'hardware-controls';O=P/'output/ch32v006-review';C=O/'candidate'
sys.path.insert(0,str(R/'tmp'));from sexpr import parse,get,children
before=p.LoadBoard(str(O/'before/controls.kicad_pcb'));b=p.LoadBoard(str(C/'controls.kicad_pcb'))
xy=lambda v:[round(p.ToMM(v.x),6),round(p.ToMM(v.y),6)]
def mechanical(f):
    pads=[]
    for a in f.Pads():
        polys=[]
        for layer in [p.F_Cu,p.B_Cu]:
            if not a.IsOnLayer(layer):continue
            ps=a.GetEffectivePolygon(layer)
            polys.extend([[xy(ps.COutline(i).CPoint(k)) for k in range(ps.COutline(i).PointCount())] for i in range(ps.OutlineCount())])
        pads.append([a.GetNumber(),xy(a.GetPosition()),xy(a.GetSize()),xy(a.GetDrillSize()),polys])
    return [xy(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer(),pads]
unchanged=['J1','E1']+['SW'+str(i) for i in range(1,6)]+['H'+str(i) for i in range(1,5)]
for ref in unchanged:assert mechanical(before.FindFootprintByReference(ref))==mechanical(b.FindFootprintByReference(ref)),ref
def edges(path):
    return [v for v in parse(path.read_text()) if isinstance(v,list) and v[0].startswith('gr_') and get(v,'layer') and get(v,'layer')[1]=='Edge.Cuts']
assert edges(O/'before/controls.kicad_pcb')==edges(C/'controls.kicad_pcb')
assert b.GetDesignSettings().GetBoardThickness()==p.FromMM(.8)
d=json.loads((O/'design.json').read_text());refs={f.GetReference():f for f in b.GetFootprints()}
assert set(refs)=={c['ref'] for c in d['components']}
assert 'U2' not in refs and 'R13' not in refs and 'C4' not in refs
for c in d['components']:
    f=refs[c['ref']]
    assert f.GetValue()==c['value'],c['ref']
    for a in f.Pads():
        n=a.GetNumber()
        if n in c['nets']:assert a.GetNetname()=='/'+c['nets'][n],(c['ref'],n,a.GetNetname())
power={(f.GetReference(),a.GetNumber()) for f in refs.values() for a in f.Pads() if a.GetNetname()=='/KEY_POWER'}
assert power=={('J1','11'),('SW1','1'),('R14','2')}
report={'revision':'C','mechanical_interface_unchanged':unchanged,'outline_unchanged':True,'thickness_mm':.8,'component_count':len(refs),'purchased_component_count':len(refs)-6,'mcu':refs['U1'].GetValue(),'mcu_pinmap_verified':True,'power_independent_active_low':True,'j1_pinout_unchanged':True,'tracks':sum(not isinstance(t,p.PCB_VIA) for t in b.GetTracks()),'vias':sum(isinstance(t,p.PCB_VIA) for t in b.GetTracks()),'firmware_implemented':False,'physical_calibration_completed':False,'whole_device_interference_rechecked':False,'sha256':{s:hashlib.sha256((C/('controls.'+s)).read_bytes()).hexdigest() for s in ['kicad_sch','kicad_pcb','kicad_pro']}}
for name in ['final-erc','final-drc']:
    v=json.loads((O/(name+'.json')).read_text())
    if name.endswith('drc'):
        report['drc']={k:len(v[k]) for k in ['violations','unconnected_items','schematic_parity']}
        assert not any(report['drc'].values()),report['drc']
    else:
        issues=[a for sheet in v['sheets'] for a in sheet['violations']]
        report['erc_violations']=len(issues);assert not issues,issues
(O/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
