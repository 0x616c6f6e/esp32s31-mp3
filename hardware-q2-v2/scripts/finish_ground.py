from pathlib import Path
import pcbnew as p,json
P=Path(__file__).resolve().parents[1];fn=P/'q2-v2.kicad_pcb';b=p.LoadBoard(str(fn));pro=(P/'q2-v2.kicad_pro').read_bytes();gnd=b.FindNet('GND');V=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y))
for a in b.FindFootprintByReference('USB1').Pads():
 if a.GetNumber() in ['13','14']:a.SetNet(gnd)
for layer in [p.F_Cu,p.B_Cu]:
 if any(z.GetLayer()==layer for z in b.Zones()):continue
 z=p.ZONE(b);z.SetLayer(layer);z.SetNet(gnd);z.SetLocalClearance(p.FromMM(.2));z.SetMinThickness(p.FromMM(.15));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetMinIslandArea(int(1e12));z.SetThermalReliefGap(p.FromMM(.2));z.SetThermalReliefSpokeWidth(p.FromMM(.3));z.Outline().NewOutline()
 for x,y in [(128.868,67.647),(174.868,67.647),(174.868,143.647),(128.868,143.647)]:z.Outline().Append(int(p.FromMM(x)),int(p.FromMM(y)))
 b.Add(z)
# Narrow the RF escape at the 0.35 mm pitch QFN pin. Wider matching line remains intact.
for a,z in [((162.258948,80.231950),(162.193,80.297898)),((162.193,80.297898),(162.193,80.747001))]:
 t=p.PCB_TRACK(b);t.SetStart(V(*a));t.SetEnd(V(*z));t.SetLayer(p.F_Cu);t.SetWidth(p.FromMM(.15));t.SetNet(b.FindNet('RF_CHIP'));b.Add(t)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(fn),b);(P/'q2-v2.kicad_pro').write_bytes(pro)
print('Ground pours and RF narrow escape saved')
