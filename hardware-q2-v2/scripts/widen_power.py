"""Widen supply copper where existing neighbouring copper and drills allow it."""
from finish_grid import *
items,cu,holes,keepouts,shapes=database();log=[]
limits={'VBAT':.6,'GBAT':.6,'VBUS_5V':.6,'VCC':.6,'VCC_3V3':.45,'VCC_1V8':.4}
if (P/'power-only-0402.json').exists():
 limits.update({'VCC_3V3_AON':.4,'MCU_1V8':.3,'MCU_VDD_SPI':.3,'MCU_VDDA34':.3})
for net,limit in limits.items():
 items,cu,holes,keepouts,shapes=database()
 obs={l:unary_union([s for n,ss in cu[l].items() if n!=net for s in ss]) for l in layers}
 holeobs=unary_union([s.buffer(c+.002) for n,s,c in holes if n!=net])
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA) or t.GetNetname()!=net:continue
  l=t.GetLayer();old=p.ToMM(t.GetWidth());line=LineString([xy(t.GetStart()),xy(t.GetEnd())]);new=old
  for w in sorted(set([limit,old,.5,.45,.4,.35,.3,.25,.2,.15,.1]),reverse=True):
   if w>max(limit,old):continue
   copper=line.buffer(w/2)
   if copper.distance(obs[l])<.102 or copper.intersects(holeobs) or not outline.buffer(-.252).contains(copper):continue
   new=w;break
  if abs(new-old)>.001:t.SetWidth(p.FromMM(new));log.append({'uuid':t.m_Uuid.AsString(),'net':net,'length_mm':round(p.ToMM(t.GetLength()),4),'old':old,'new':new})
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(fn),b);(P/'q2-v2.kicad_pro').write_bytes(pro)
(P/'output/power-width-review.json').write_text(json.dumps(log,indent=2));print('Widened',len(log),'supply segments',flush=True)
