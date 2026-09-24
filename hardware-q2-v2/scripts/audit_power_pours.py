"""Verify the saved pour-only supply distribution and draw its actual filled copper."""
from pathlib import Path
import collections, hashlib, html, json, subprocess
import pcbnew as p

P = Path(__file__).resolve().parents[1]
out = P / 'output'
b = p.LoadBoard(str(P / 'q2-v2.kicad_pcb'))
policy = json.loads((P / 'power-only-0402.json').read_text())
dc = set(policy['rails']) - {'GND'}
allowed = dc | {'GND'} | set(policy['local_power_nodes'])
drc = json.loads((out / 'drc.json').read_text(encoding='utf8'))
items = {a.m_Uuid.AsString(): a for f in b.GetFootprints() for a in f.Pads()}
items.update({a.m_Uuid.AsString(): a for a in b.GetTracks()})
items.update({a.m_Uuid.AsString(): a for a in b.Zones()})
assert all(i['uuid'] in items for e in drc['unconnected_items'] for i in e['items'])
missing = [e for e in drc['unconnected_items'] if any(items[i['uuid']].GetNetname() in allowed for i in e['items'])]
inner = [t for t in b.GetTracks() if not isinstance(t, p.PCB_VIA) and t.GetNetname() in dc and t.GetLayer() not in [p.F_Cu, p.B_Cu]]
signals = [t for t in b.GetTracks() if t.GetNetname() not in allowed]
assert not drc['violations'] and not drc['schematic_parity'] and not missing and not inner and not signals
assert all(t.GetLength() > 0 for t in b.GetTracks() if not isinstance(t, p.PCB_VIA))

# Compare to the previously committed layout without modifying the working PCB.
baseline = out / 'power-audit-head.kicad_pcb'
baseline.write_bytes(subprocess.check_output(['git', 'show', 'HEAD:hardware-q2-v2/q2-v2.kicad_pcb'], cwd=P.parent))
old = p.LoadBoard(str(baseline))
def component_signature(board):
    return {f.GetReference(): (f.m_Uuid.AsString(), f.GetPosition().x, f.GetPosition().y,
        f.GetOrientationDegrees(), f.GetLayer(), f.GetFPID().GetUniStringLibId(),
        sorted((a.m_Uuid.AsString(), a.GetNumber(), a.GetNetname(), a.GetPosition().x,
                a.GetPosition().y, a.GetSize().x, a.GetSize().y) for a in f.Pads())) for f in board.GetFootprints()}
assert component_signature(old) == component_signature(b)
regions = []
for z in b.Zones():
    if z.GetNetname() in dc:
        regions.append({'uuid': z.m_Uuid.AsString(), 'net': z.GetNetname(),
                        'layer': b.GetLayerName(z.GetLayer()), 'filled_area_mm2': round(z.GetFilledArea()/1e12, 6)})
surface = [t for t in b.GetTracks() if not isinstance(t, p.PCB_VIA) and t.GetNetname() in dc]
report = json.loads((P / 'power-pours.json').read_text())
report.update(status='VALIDATED_POWER_POURS_MANUAL_SIGNAL_ROUTING_REQUIRED',
    board_sha256=hashlib.sha256((P / 'q2-v2.kicad_pcb').read_bytes()).hexdigest(),
    regions=regions, geometry_drc=0, schematic_parity=0, power_and_ground_unconnected=0,
    intentional_signal_unconnected=len(drc['unconnected_items']), remaining_signal_copper=0,
    inner_supply_track_segments=0, component_placement_and_pad_nets_unchanged=True,
    surface_supply_access_segments=len(surface),
    longest_surface_supply_segment_mm=round(max(p.ToMM(t.GetLength()) for t in surface), 4))
(P / 'power-pours.json').write_text(json.dumps(report, indent=2), encoding='utf8')

# Plot filled polygons, including actual clearances/holes, rather than zone boundaries.
colors = ['#e7902f','#59adcf','#e56579','#a981cd','#acd355','#d3bb70',
          '#3dbb9b','#cc89b0','#ac9c83','#79aaf3','#cce35b','#f09068']
palette = dict(zip(sorted(dc), colors))
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="900" viewBox="0 0 1000 900">',
       '<rect width="1000" height="900" fill="#18212c"/>',
       '<g font-family="Arial" fill="#edf3fa">',
       '<text x="40" y="30" font-size="21">Q2 V2 - power copper / top-view coordinates</text>']
for column, layer in enumerate([p.In2_Cu, p.In3_Cu]):
    x0 = 50 + column*500
    svg.append(f'<text x="{x0}" y="65" font-size="18">{b.GetLayerName(layer)} / inner layer {2+column}</text>')
    svg.append(f'<rect x="{x0}" y="85" width="368" height="608" fill="#0b121a" stroke="#c9d3df"/>')
    def point(v):
        return f'{x0+(p.ToMM(v.x)-128.868)*8:.3f},{85+(p.ToMM(v.y)-67.647)*8:.3f}'
    for z in b.Zones():
        if z.GetLayer() != layer or z.GetNetname() not in dc: continue
        ps = z.GetFilledPolysList(layer)
        for n in range(ps.OutlineCount()):
            chains = [ps.COutline(n)] + [ps.CHole(n, j) for j in range(ps.HoleCount(n))]
            path = ' '.join('M '+' L '.join(point(c.CPoint(j)) for j in range(c.PointCount()))+' Z' for c in chains)
            svg.append(f'<path d="{path}" fill="{palette[z.GetNetname()]}" fill-rule="evenodd"/>')
    for t in b.GetTracks():
        if isinstance(t, p.PCB_VIA) and t.GetNetname() in dc:
            x, y = point(t.GetPosition()).split(',')
            svg.append(f'<circle cx="{x}" cy="{y}" r="1.1" fill="#18212c" stroke="white" stroke-width="0.5"/>')
for i, net in enumerate(sorted(dc)):
    x, y = 40+(i%4)*240, 735+(i//4)*34
    svg.append(f'<rect x="{x}" y="{y-12}" width="15" height="15" fill="{palette[net]}"/><text x="{x+23}" y="{y}" font-size="14">{html.escape(net)}</text>')
svg += ['<text x="40" y="860" font-size="15">In1 + In4: continuous GND. Surface pad access / local converter loops retained.</text>',
        '<text x="40" y="885" font-size="15">174 signal connections remain for manual routing. Not a fabrication release.</text>', '</g></svg>']
(out / 'power-map.svg').write_text('\n'.join(svg)+'\n', encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k!='regions'}, indent=2))
