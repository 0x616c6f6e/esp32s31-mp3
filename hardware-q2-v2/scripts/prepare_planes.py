"""Correct USB locator holes from manufacturer drawing, add real GND planes."""
from pathlib import Path
import pcbnew as p,json
P=Path(__file__).resolve().parents[1];fn=P/'q2-v2.kicad_pcb';b=p.LoadBoard(str(fn));pro=(P/'q2-v2.kicad_pro').read_bytes()
V=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y))
held=[];f=b.FindFootprintByReference('USB1')
for g in list(f.GraphicalItems()):
 if g.GetLayer()!=p.Edge_Cuts:continue
 center=g.GetBoundingBox().GetCenter();held.append(g);f.Remove(g)
 a=p.PAD(f);a.SetNumber('');a.SetAttribute(p.PAD_ATTRIB_NPTH);a.SetShape(p.PAD_SHAPE_CIRCLE)
 a.SetPosition(center);a.SetSize(V(.55,.55));a.SetDrillSize(V(.55,.55));a.SetLayerSet(p.LSET.AllCuMask());f.Add(a)
# Keep the hole coordinates; trim 0.02 mm from the locator-facing ends of two ground pads.
for a in f.Pads():
 if a.GetNumber() in ['A1B12','B1A12']:
  a.SetSize(V(.55,1.08));a.SetPosition(a.GetPosition()+V(0,-.01))
# The 0.1292 mm power stub is left over from the module reference import.
for a in list(b.GetTracks()):
 if not isinstance(a,p.PCB_VIA) and a.m_Uuid.AsString()=='a6bf3f1a-e4b9-4b94-80b1-ef626721f80e':held.append(a);b.Remove(a)
assert not b.Zones(),'Planes already exist; do not duplicate them'
gnd=b.FindNet('GND')
for layer in [p.In1_Cu,p.In4_Cu]:
 z=p.ZONE(b);z.SetLayer(layer);z.SetNet(gnd);z.SetLocalClearance(p.FromMM(.2));z.SetMinThickness(p.FromMM(.15));z.SetPadConnection(p.ZONE_CONNECTION_FULL)
 z.SetThermalReliefGap(p.FromMM(.2));z.SetThermalReliefSpokeWidth(p.FromMM(.3));z.SetMinIslandArea(int(1e12))
 z.Outline().NewOutline()
 for x,y in [(128.868,67.647),(174.868,67.647),(174.868,143.647),(128.868,143.647)]:z.Outline().Append(int(p.FromMM(x)),int(p.FromMM(y)))
 b.Add(z)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(fn),b);(P/'q2-v2.kicad_pro').write_bytes(pro)
plugin=p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP)
for ref in ['USB1','JRF1']:plugin.FootprintSave(str(P/'V2.pretty'),b.FindFootprintByReference(ref))
print('Added two GND planes; USB locator holes 0.55 mm NPTH per manufacturer drawing')
