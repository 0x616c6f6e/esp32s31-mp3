"""Apply physical flex transition vias to imported island routing, once."""
from pathlib import Path
import pcbnew as p,json
O=Path(__file__).resolve().parent/'am213-fpc-adapter'
b=p.LoadBoard(str(O/'am213-fpc-adapter.kicad_pcb'))
d=json.loads((O/'output/design.json').read_text(encoding='utf-8'))
v=lambda x,y:p.VECTOR2I(round(x*1e6),round(y*1e6))
def track(a,z,n,w=.12,layer=p.F_Cu):
    t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*z));t.SetWidth(p.FromMM(w));t.SetLayer(layer);t.SetNet(b.FindNet('/'+n));b.Add(t)
def via(x,y,n):
    t=p.PCB_VIA(b);t.SetPosition(v(x,y));t.SetWidth(p.FromMM(.4));t.SetDrill(p.FromMM(.2));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(b.FindNet('/'+n));b.Add(t)
for num,n in d['host_nets'].items():
    i=int(num);x=50.95 if i%2 else 50.4;y=66.4005-(i-1)*.4;oldy=65.4005-(i-1)*.3
    via(x,y,n)
    track((48.0,oldy),(50.25,y),n,.12)
    track((50.25,y),(x,y),n,.12)
# Trim the straight tail before its pitch-expanding fanout.
for t in b.GetTracks():
    if not isinstance(t,p.PCB_VIA) and t.GetLength()>p.FromMM(60):t.SetEnd(v(48.0,p.ToMM(t.GetEnd().y)))
# Merge the two adjacent supply conductors away from fingers and island fanout.
for t in list(b.GetTracks()):
    if isinstance(t,p.PCB_TRACK) and not isinstance(t,p.PCB_VIA) and t.GetLength()>p.FromMM(60) and t.GetNetname()=='/VCC_3V3':b.Remove(t)
for i in [13,14]:
    y=65.4005-(i-1)*.3
    track((-17.5,y),(-16.6,y),'VCC_3V3',.14)
    track((-16.6,y),(-16.2,61.6505),'VCC_3V3',.14)
    track((47.5,61.6505),(48.0,y),'VCC_3V3',.14)
track((-16.2,61.6505),(47.5,61.6505),'VCC_3V3',.44)
# Tip ground stitches are inside the 3.5 mm stiffened insertion section.
via(-16.9,60.7505,'GND');track((-17.15,60.6005),(-16.9,60.7505),'GND',.14)
for layer in [p.F_Cu,p.B_Cu]:
    z=p.ZONE(b);z.SetLayer(layer);z.SetNet(b.FindNet('/GND'));z.SetZoneName('GND island' if layer==p.F_Cu else 'GND island and flex return')
    z.SetLocalClearance(p.FromMM(.1));z.SetMinThickness(p.FromMM(.1));z.SetPadConnection(p.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(p.FromMM(.12));z.SetThermalReliefSpokeWidth(p.FromMM(.12));z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
    pts=[(50.2,50.2),(66.8,50.2),(66.8,71.8),(50.2,71.8)] if layer==p.F_Cu else [(50.2,50.2),(66.8,50.2),(66.8,71.8),(50.2,71.8),(50.2,65.8),(49.8,65.5005),(-17.2,65.5005),(-17.2,59.3005),(49.8,59.3005),(50.2,59)]
    o=z.Outline();o.NewOutline()
    for x,y in pts:o.Append(p.FromMM(x),p.FromMM(y))
    b.Add(z)
p.SaveBoard(str(O/'am213-fpc-adapter.kicad_pcb'),b)
print('Physical terminal vias, widened supply and ground zones added')
