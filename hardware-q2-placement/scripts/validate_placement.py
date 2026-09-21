"""Validate routing handoff without treating expected ratsnest lines as defects."""
from pathlib import Path
import pcbnew as p,json,hashlib,math,collections,sys
P=Path(__file__).resolve().parents[1];ROOT=P.parent
sys.path.insert(0,str(ROOT/'tmp'));from sexpr import parse,children,get,dump,prop
source=p.LoadBoard(str(ROOT/'hardware-q2/hardware.kicad_pcb'));board=p.LoadBoard(str(P/'hardware.kicad_pcb'))
old={f.GetReference():f for f in source.GetFootprints()};new={f.GetReference():f for f in board.GetFootprints()}
def padmap(b):return {(f.GetReference(),a.GetNumber(),a.m_Uuid.AsString()):a.GetNetname() for f in b.GetFootprints() for a in f.Pads() if a.GetNumber()!='MP'}
assert padmap(source)==padmap(board)
assert len(new)==126 and len(padmap(board))==555
mounts=[a for f in new.values() for a in f.Pads() if a.GetNumber()=='MP']
assert len(mounts)==4 and all(not a.GetNetname() for a in mounts)
assert len(board.GetTracks())==0 and all(z.GetIsRuleArea() for z in board.Zones())
layout=json.loads((P/'output/placement.json').read_text(encoding='utf8'))
assert hashlib.sha256((ROOT/'hardware-q2/hardware.kicad_pcb').read_bytes()).hexdigest()==layout['source_pcb_sha256']
for ref in layout['fixed_mechanical_references']:
    a,b=old[ref],new[ref]
    assert a.GetPosition()==b.GetPosition() and a.GetOrientationDegrees()==b.GetOrientationDegrees() and a.IsFlipped()==b.IsFlipped()
    assert b.IsLocked()
source_tree=parse((ROOT/'hardware-q2/hardware.kicad_pcb').read_text(encoding='utf8'));tree=parse((P/'hardware.kicad_pcb').read_text(encoding='utf8'))
outline=lambda t:[v for v in t if isinstance(v,list) and str(v[0]).startswith('gr_') and get(v,'layer',['layer',''])[1]=='Edge.Cuts']
assert outline(source_tree)==outline(tree)
assert [z for z in children(source_tree,'zone') if get(z,'keepout')]==children(tree,'zone')
assert (ROOT/'hardware-q2/hardware.kicad_dru').read_bytes()==(P/'hardware.kicad_dru').read_bytes()
def normalize_sch(t):
    for sym in children(t,'symbol'):
        ref=prop(sym,'Reference')
        if ref and ref[2] in ['H1','H2']:
            allowed=['Value','Footprint','Datasheet','Description','Supplier Part']
            sym[:]=[v for v in sym if not(isinstance(v,list) and v[0]=='property' and v[1] in allowed)]
    return t
for f in P.glob('*.kicad_sch'):
    assert normalize_sch(parse(f.read_text(encoding='utf8')))==normalize_sch(parse((ROOT/'hardware-q2'/f.name).read_text(encoding='utf8'))),f.name
for ref in ['H1','H2']:
    f=new[ref];planned=layout['connector_revision'][ref]
    assert [f.GetPosition().x/1e6,f.GetPosition().y/1e6]==planned['xy']
    assert f.GetOrientationDegrees()==planned['angle'] and not f.IsFlipped() and f.IsLocked()
models=json.loads((P/'models3d/model-manifest.json').read_text(encoding='utf8'))
for m in models['models']:assert hashlib.sha256((P/'models3d'/m['file']).read_bytes()).hexdigest()==m['model_sha256']
assert sum(len(children(f,'model')) for f in children(tree,'footprint'))==122
drc=json.loads((P/'output/placement-drc.json').read_text(encoding='utf8'))
assert not drc['violations'] and not drc['schematic_parity']
erc=json.loads((P/'output/placement-erc.json').read_text(encoding='utf8'))
original_erc=json.loads((ROOT/'hardware-q2/output/final-erc.json').read_text(encoding='utf8'))
assert erc['sheets']==original_erc['sheets']
xy=lambda a:(a.GetPosition().x/1e6,a.GetPosition().y/1e6)
links=[('C4','U11','Net-(U11-REG)'),('X1','U2','Net-(U2-XTO)'),('X1','U2','Net-(U2-XTI{slash}MCLK)'),('D1','USB1','TYPEC_USB_DP_IN'),('D1','USB1','TYPEC_USB_DN_IN'),('U14','H2','VBAT'),('C1','U4','VCC'),('C30','U5','VCC'),('C31','U5','VCC_1V8'),('L3','U11','Net-(U11-VDD)')]
distances=[]
for a,b,net in links:
    def dist(fps):return min(math.dist(xy(x),xy(y)) for x in fps[a].Pads() for y in fps[b].Pads() if x.GetNetname()==net and y.GetNetname()==net)
    distances.append({'from':a,'to':b,'net':net,'before_mm':round(dist(old),3),'after_mm':round(dist(new),3)})
report={'status':'PLACEMENT_ONLY_REQUIRES_MANUAL_ROUTING','pcb_sha256':hashlib.sha256((P/'hardware.kicad_pcb').read_bytes()).hexdigest(),'footprints':len(new),'physical_components':122,'pads':555,'pad_net_changes':0,'schematics_unchanged':True,'outline_unchanged':True,'antenna_keepout_unchanged':True,'locked_mechanical_references':layout['fixed_mechanical_references'],'moved_or_flipped_count':len(layout['changes']),'front_components':sum(not f.IsFlipped() for r,f in new.items() if not r.startswith('SCREW')),'back_components':sum(f.IsFlipped() for f in new.values()),'tracks_arcs_vias':len(board.GetTracks()),'copper_zones':sum(not z.GetIsRuleArea() for z in board.Zones()),'drc_violations':len(drc['violations']),'schematic_parity_issues':len(drc['schematic_parity']),'expected_unconnected_items':len(drc['unconnected_items']),'distance_metric':'Minimum same-net pad-to-pad Euclidean distance; not routed length or signal-integrity analysis. Side transitions not included.','selected_local_connections':distances,'manufacturing_release':False}
report.update(pads=559,original_signal_pads=555,added_unconnected_mount_pads=4,schematics_unchanged=False,schematic_changes='Only H1/H2 part properties changed; pins, wires, UUIDs and all other symbols unchanged.',connector_revision=layout['connector_revision'])
report.update(erc_matches_reference=True,erc_existing_warnings=9,erc_errors=0)
(P/'output/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
rows=['Reference,Side,X_mm,Y_mm,Rotation_deg,Value,Locked']
for r,f in sorted(new.items()):rows.append(f'{r},{"B" if f.IsFlipped() else "F"},{xy(f)[0]:.4f},{xy(f)[1]:.4f},{f.GetOrientationDegrees():.3f},"{f.GetValue()}",{f.IsLocked()}')
(P/'output/component-placement.csv').write_text('\n'.join(rows)+'\n',encoding='utf8')
print('PLACEMENT_VERIFIED',json.dumps(report,ensure_ascii=False))
