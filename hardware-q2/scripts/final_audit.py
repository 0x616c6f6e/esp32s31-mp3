from pathlib import Path
import pcbnew as p,json,hashlib,collections,math
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'hardware-q2';orig=p.LoadBoard(str(ROOT/'hardware/hardware.kicad_pcb'));b=p.LoadBoard(str(P/'hardware.kicad_pcb'))
def padmap(board):return {(f.GetReference(),a.GetNumber(),a.m_Uuid.AsString()):a.GetNetname() for f in board.GetFootprints() for a in f.Pads()}
pm0,pm=padmap(orig),padmap(b);diff=[{'pad':k,'old':pm0.get(k),'new':pm.get(k)} for k in set(pm)|set(pm0) if pm.get(k)!=pm0.get(k)]
def placement(board):return {f.GetReference():{'position_mm':[f.GetPosition().x/1e6,f.GetPosition().y/1e6],'rotation_deg':f.GetOrientationDegrees(),'side':'bottom' if f.IsFlipped() else 'top'} for f in board.GetFootprints()}
old,new=placement(orig),placement(b);changes=[{'ref':k,'old':old.get(k),'new':v} for k,v in new.items() if old.get(k)!=v]
usb={};power={}
for net in sorted({t.GetNetname() for t in b.GetTracks()}):
    if 'USB_D' not in net and net not in ['VBAT','VBUS_5V','VCC_3V3','Net-(U4-SW)','Net-(D2-A)']:continue
    data={}
    for label,board in [('original',orig),('q2',b)]:
        tt=[t for t in board.GetTracks() if t.GetNetname()==net];segments=[t for t in tt if not isinstance(t,p.PCB_VIA)]
        data[label]={'total_trace_mm':sum(t.GetLength()/1e6 for t in segments),'vias':sum(isinstance(t,p.PCB_VIA) for t in tt),'widths_mm':sorted(set(round(t.GetWidth()/1e6,6) for t in segments)),'layers':sorted(set(board.GetLayerName(t.GetLayer()) for t in segments))}
    (usb if 'USB_D' in net else power)[net]=data
r={'pcb_sha256':hashlib.sha256((P/'hardware.kicad_pcb').read_bytes()).hexdigest(),'original_sha256':hashlib.sha256((ROOT/'hardware/hardware.kicad_pcb').read_bytes()).hexdigest(),'footprints':len(new),'pad_net_changes':diff,'outline_mm':[46,76],'corner_radius_mm':10,'changed_placements':changes,'usb_trace_totals_not_electrical_length':usb,'power_trace_summary':power,'rules_unchanged':json.loads((P/'hardware.kicad_pro').read_text(encoding='utf8'))['board']['design_settings']['rules']==json.loads((ROOT/'hardware/hardware.kicad_pro').read_text(encoding='utf8'))['board']['design_settings']['rules']}
(P/'output/final-audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
(P/'output/placement-changes.json').write_text(json.dumps({'source_sha256':r['original_sha256'],'board_outline_mm':[46,76],'radius_mm':10,'changed_placements':changes,'fpc_case_axis_y_mm':20.4,'screen_case_axis_y_mm':20.4},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in r.items() if k!='changed_placements'},ensure_ascii=True));print('CHANGED_PLACEMENTS',len(changes))
assert not diff and len(new)==126 and r['rules_unchanged']
