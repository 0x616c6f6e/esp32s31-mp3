"""Rebuild copper-only sensing keepouts and ground planes on the C candidate."""
from pathlib import Path
import sys
import pcbnew as p
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'tmp/controls-ground-deps'))
from shapely.geometry import Polygon,LineString,Point,box
from shapely.ops import unary_union
C=R/'hardware-controls/output/ch32v006-review/candidate'
pro=(C/'controls.kicad_pro').read_bytes();b=p.LoadBoard(str(C/'controls.kicad_pcb'))
assert not list(b.Zones()),'Run once on a board without zones'
shapes=[]
for pad in b.FindFootprintByReference('E1').Pads():
    poly=pad.GetEffectivePolygon(p.F_Cu)
    for i in range(poly.OutlineCount()):
        line=poly.COutline(i)
        shapes.append(Polygon([(p.ToMM(line.CPoint(k).x),p.ToMM(line.CPoint(k).y)) for k in range(line.PointCount())]).buffer(.8))
for t in b.GetTracks():
    if not t.GetNetname().startswith(('/WHEEL','/SENSE')):continue
    xy=lambda v:(p.ToMM(v.x),p.ToMM(v.y))
    geom=Point(xy(t.GetPosition())) if isinstance(t,p.PCB_VIA) else LineString([xy(t.GetStart()),xy(t.GetEnd())])
    width=t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth()
    shapes.append(geom.buffer(p.ToMM(width)/2+.5))
exclude=unary_union(shapes).simplify(.015,preserve_topology=True)
def outline(z,poly):
    o=z.Outline();o.NewOutline()
    for x,y in list(poly.exterior.coords)[:-1]:o.Append(p.FromMM(x),p.FromMM(y))
    for ring in poly.interiors:
        o.NewHole()
        for x,y in list(ring.coords)[:-1]:o.Append(p.FromMM(x),p.FromMM(y),0,o.HoleCount(0)-1)
for layer in [p.F_Cu,p.B_Cu]:
    for i,poly in enumerate(exclude.geoms if hasattr(exclude,'geoms') else [exclude]):
        z=p.ZONE(b);z.SetLayer(layer);z.SetIsRuleArea(True)
        z.SetZoneName('C touch copper exclusion '+str(i+1))
        z.SetDoNotAllowTracks(False);z.SetDoNotAllowVias(False);z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False);z.SetDoNotAllowZoneFills(True)
        outline(z,poly);b.Add(z)
    z=p.ZONE(b);z.SetLayer(layer);z.SetNet(b.FindNet('/GND'))
    z.SetZoneName('C GND outside touch sensing')
    z.SetLocalClearance(p.FromMM(.2));z.SetMinThickness(p.FromMM(.25))
    z.SetPadConnection(p.ZONE_CONNECTION_THERMAL);z.SetThermalReliefGap(p.FromMM(.2));z.SetThermalReliefSpokeWidth(p.FromMM(.2))
    z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
    outline(z,box(-1,-1,45,35));b.Add(z)
p.SaveBoard(str(C/'controls.kicad_pcb'),b);(C/'controls.kicad_pro').write_bytes(pro)
print('Added touch keepouts and two ground planes; refill with native CLI')
