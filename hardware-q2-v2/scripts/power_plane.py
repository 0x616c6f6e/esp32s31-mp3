from pathlib import Path
import pcbnew as p,json,math
P=Path(__file__).resolve().parents[1];fn=P/'q2-v2.kicad_pcb';b=p.LoadBoard(str(fn));pro=json.loads((P/'q2-v2.kicad_pro').read_text());V=lambda x,y:p.VECTOR2I(p.FromMM(x),p.FromMM(y));xy=lambda v:(p.ToMM(v.x),p.ToMM(v.y));held=[]
pro['board']['design_settings']['rules']['min_hole_to_hole']=.2
# Two VDDA fanout vias overlap. Keep one through hole and join the old centre on used layers.
remove=next(t for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname()=='MCU_VDDA34' and math.dist(xy(t.GetPosition()),(161.668,80.297))<.001)
target=(161.493,80.397);pos=xy(remove.GetPosition());used=set()
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA) or t.GetNetname()!='MCU_VDDA34':continue
 if min(math.dist(pos,xy(t.GetStart())),math.dist(pos,xy(t.GetEnd())))<.18:used.add(t.GetLayer())
for layer in used:
 t=p.PCB_TRACK(b);t.SetStart(V(*pos));t.SetEnd(V(*target));t.SetWidth(p.FromMM(.15));t.SetNet(remove.GetNet());t.SetLayer(layer);b.Add(t)
held.append(remove);b.Remove(remove)
if not any(z.GetNetname()=='VCC_3V3' for z in b.Zones()):
 z=p.ZONE(b);z.SetLayer(p.In2_Cu);z.SetNet(b.FindNet('VCC_3V3'));z.SetLocalClearance(p.FromMM(.2));z.SetMinThickness(p.FromMM(.15));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetMinIslandArea(int(1e12));z.Outline().NewOutline()
 for x,y in [(151,73),(172,73),(172,120),(165.8,120),(165.8,100),(151,100)]:z.Outline().Append(int(p.FromMM(x)),int(p.FromMM(y)))
 b.Add(z)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(fn),b);(P/'q2-v2.kicad_pro').write_text(json.dumps(pro,indent=2))
print('Added 3.3 V distribution copper; replaced overlapping VDDA holes with one via')
