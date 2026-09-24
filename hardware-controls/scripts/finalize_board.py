"""Save native PCB, restore explicit project rules after pcbnew saves defaults."""
from pathlib import Path
import json
import pcbnew as p
P=Path(__file__).resolve().parents[1]
b=p.LoadBoard(str(P/'controls.kicad_pcb'))
b.FindFootprintByReference('U1').Reference().SetVisible(False)
b.FindFootprintByReference('U2').Reference().SetVisible(False)
# Recorded post-router correction: separate C3/C4 and U2 courtyards by 0.1 mm.
# Also move every trace endpoint attached to the translated capacitor pads.
for ref in ['C3','C4']:
 f=b.FindFootprintByReference(ref);dx=p.FromMM(16)-f.GetPosition().x
 if dx:
  assert abs(dx)<=p.FromMM(.21),'Unexpected capacitor placement'
  ends={(a.GetPosition().x,a.GetPosition().y) for a in f.Pads()}
  for t in b.GetTracks():
   if isinstance(t,p.PCB_VIA):continue
   for getter,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
    pt=getter()
    if (pt.x,pt.y) in ends:setter(p.VECTOR2I(pt.x+dx,pt.y))
  f.SetPosition(p.VECTOR2I(p.FromMM(16),f.GetPosition().y))
for a in b.FindFootprintByReference('J1').Pads():
 if a.GetNumber() in ['7','8','9','10']:
  a.GetNet().SetNetname('unconnected-(J1-Pad'+a.GetNumber()+')')
# Keep the adjacent unused-input via clear of the corrected C3 position.
for via in list(b.GetTracks()):
 if isinstance(via,p.PCB_VIA) and via.GetNetname()=='/UNUSED_INPUTS' and abs(via.GetPosition().x-p.FromMM(14.9661))<1000 and abs(via.GetPosition().y-p.FromMM(31.3062))<1000:
  pt=via.GetPosition();new=p.VECTOR2I(pt.x-p.FromMM(.15),pt.y)
  for t in b.GetTracks():
   if isinstance(t,p.PCB_VIA):continue
   if t.GetStart()==pt:t.SetStart(new)
   if t.GetEnd()==pt:t.SetEnd(new)
  via.SetPosition(new)
for f in b.GetFootprints():
 if f.GetReference().startswith('TP'):
  f.Reference().SetVisible(True);f.Reference().SetPosition(p.VECTOR2I(f.GetPosition().x,p.FromMM(11.5 if f.GetReference()=='TP11' else 10.3)))
if not any(isinstance(t,p.PCB_TEXT) and t.GetText()=='1' for t in b.GetDrawings()):
 t=p.PCB_TEXT(b);t.SetText('1');t.SetLayer(p.B_SilkS);t.SetMirrored(True)
 t.SetPosition(p.VECTOR2I(p.FromMM(11.4),p.FromMM(4.6)));t.SetTextSize(p.VECTOR2I(p.FromMM(.8),p.FromMM(.8)));t.SetTextThickness(p.FromMM(.12));b.Add(t)
s=b.GetDesignSettings();s.m_MinClearance=p.FromMM(.15);s.m_TrackMinWidth=p.FromMM(.15);s.m_CopperEdgeClearance=p.FromMM(.25)
p.SaveBoard(str(P/'controls.kicad_pcb'),b)
project=json.loads((P/'controls.kicad_pro').read_text())
ds=project['board']['design_settings'];ds['meta']={'version':2}
ds['rules'].update({'min_clearance':.15,'min_track_width':.15,'min_via_diameter':.5,'min_via_annular_width':.1,'min_through_hole_diameter':.3,'min_copper_edge_clearance':.25,'min_hole_clearance':.25,'min_hole_to_hole':.25,'min_silk_clearance':.1,'min_text_height':.8,'min_text_thickness':.1})
for c in project['net_settings']['classes']:
 c.update({'clearance':.15,'track_width':.15,'via_diameter':.6,'via_drill':.3})
(P/'controls.kicad_pro').write_text(json.dumps(project,indent=2)+'\n')
print('RULES_SAVED',len(b.GetTracks()))
