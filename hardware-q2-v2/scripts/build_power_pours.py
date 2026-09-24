"""Build inner-layer supply pours from connected copper backbones.

Temporary routing spines guide contiguous pour geometry. The delivered board
contains zones and short outer pad/via access tracks, not these inner tracks.
GND planes and local converter/charge-pump routing are preserved.
"""
import finish_grid as g
import sys,json,math,collections
p=g.p;b=g.b;P=g.P
dc=set(json.loads((P/'power-only-0402.json').read_text())['rails'])-{'GND'}
spinefile=P/'output/power-pour-spines.kicad_pcb'

def route_spines():
 final_file=g.fn
 # Write routing experiments ONLY to the intermediate guide. The live PCB is
 # changed later by pour(), which preserves all current non-zone board items.
 if spinefile.exists():
  previous=p.LoadBoard(str(spinefile))
  for t in previous.GetTracks():
   if not isinstance(t,p.PCB_VIA) and t.GetNetname() in dc and t.GetLayer() in [p.In2_Cu,p.In3_Cu]:
    item=p.PCB_TRACK(b);item.SetStart(t.GetStart());item.SetEnd(t.GetEnd());item.SetWidth(t.GetWidth());item.SetLayer(t.GetLayer());item.SetNet(b.FindNet(t.GetNetname()));b.Add(item)
 g.fn=spinefile
 # Prefer In3 for local rails, leaving In2 principally a 3.3 V distribution plane.
 g.layers=[p.In3_Cu,p.In2_Cu]
 for net in ['MCU_1V8','MCU_VDDA34','MCU_VDD_SPI','GBAT','VCC_1V8','VBAT','N_5N15','VCC_PMID','VCC','VBUS_5V','VCC_3V3_AON']:
  for attempt in range(100):
   items,cu,holes,ko,shapes=g.database()
   anchors=[u for u,a in items.items() if a.GetNetname()==net and any(not s.is_empty for s in shapes[u].values()) and isinstance(a,(p.PCB_VIA,p.PAD))]
   assert anchors,net
   _,seen=g.group(anchors[0],items,shapes);connected=[u for u in anchors if u in seen];remaining=[u for u in anchors if u not in seen]
   if not remaining:break
   u,v=min(((u,v) for u in connected for v in remaining),key=lambda uv:math.dist(g.xy(items[uv[0]].GetPosition()),g.xy(items[uv[1]].GetPosition())))
   print(net,'remaining plane anchors',len(remaining),flush=True)
   if not g.route(u,v,width=.25,clearance=.152,step=.075,allow_new_vias=False):
    if not g.route(u,v,width=.18,clearance=.152,step=.05,allow_new_vias=False):raise RuntimeError('Cannot connect plane '+net)
  else:raise RuntimeError('Too many spine iterations '+net)
 p.SaveBoard(str(spinefile),b);(P/'q2-v2.kicad_pro').write_bytes(g.pro)
 g.fn=final_file

def make_zone(net,layer,geom,priority):
 zones=[]
 polys=list(geom.geoms) if geom.geom_type=='MultiPolygon' else [geom]
 for poly in polys:
  if poly.is_empty or poly.area<.005:continue
  z=p.ZONE(b);z.SetNet(b.FindNet(net));z.SetLayer(layer);z.SetAssignedPriority(priority)
  z.SetLocalClearance(p.FromMM(.15));z.SetMinThickness(p.FromMM(.12));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetMinIslandArea(int(.05*1e12))
  z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
  ps=z.Outline();ps.NewOutline()
  for x,y in list(poly.exterior.coords)[:-1]:ps.Append(p.FromMM(float(x)),p.FromMM(float(y)))
  for hole in poly.interiors:
   index=ps.NewHole()
   for x,y in list(hole.coords)[:-1]:ps.Append(p.FromMM(float(x)),p.FromMM(float(y)),-1,index)
  b.Add(z);zones.append(z)
 return zones

def pour():
 global b
 # Preserve the CURRENT board's footprints, vias, outer routing and settings.
 # The intermediate board is a read-only source of inner supply spine geometry.
 # Never overwrite the current PCB with an earlier intermediate board.
 b=p.LoadBoard(str(g.fn));g.b=b;guide=p.LoadBoard(str(spinefile))
 guide_nets={t.GetNetname() for t in guide.GetTracks() if not isinstance(t,p.PCB_VIA) and t.GetLayer() in [p.In2_Cu,p.In3_Cu]}
 assert dc-{'VCC_3V3'}<=guide_nets,('Incomplete guide; current board not modified',dc-guide_nets)
 held=[]
 for z in list(b.Zones()):
  if z.GetNetname() in dc:held.append(z);b.Remove(z)
 cores={l:collections.defaultdict(list) for l in [p.In2_Cu,p.In3_Cu]}
 for f in b.GetFootprints():
  for a in f.Pads():
   for l in cores:
    if a.IsOnLayer(l):cores[l][a.GetNetname()].append(g.geometry(a,l))
 for a in b.GetTracks():
  for l in cores:
   if a.IsOnLayer(l):cores[l][a.GetNetname()].append(g.geometry(a,l))
 for a in guide.GetTracks():
  if not isinstance(a,p.PCB_VIA) and a.GetNetname() in dc and a.GetLayer() in cores:
   cores[a.GetLayer()][a.GetNetname()].append(g.geometry(a,a.GetLayer()))
 shapes={l:{n:g.unary_union(v) for n,v in nets.items()} for l,nets in cores.items()}
 # The principal rail uses the full In2 outline; other supply zones on this
 # layer take precedence but cannot consume the protected 3.3 V via landings.
 make_zone('VCC_3V3',p.In2_Cu,g.outline.buffer(-.3),0)
 report=[]
 for l in [p.In3_Cu,p.In2_Cu]:
  for priority,net in enumerate(sorted(dc),10):
   if net=='VCC_3V3' and l==p.In2_Cu:continue
   own=shapes[l].get(net)
   if own is None or own.is_empty:continue
   # Only create a local secondary-layer zone if that rail has a spine here.
   tracks=[t for t in guide.GetTracks() if not isinstance(t,p.PCB_VIA) and t.GetNetname()==net and t.GetLayer()==l]
   if not tracks:continue
   backbone=g.unary_union([g.geometry(t,l) for t in tracks])
   own=g.unary_union([s for s in cores[l][net] if s.distance(backbone)<.002])
   foreign=g.unary_union([s for n,s in shapes[l].items() if n!=net])
   area=own.buffer(.9,join_style=2).difference(foreign.buffer(.16,join_style=2)).intersection(g.outline.buffer(-.3)).buffer(0).simplify(.002,preserve_topology=True)
   zones=make_zone(net,l,area,priority)
   report.append({'net':net,'layer':b.GetLayerName(l),'nominal_area_mm2':round(area.area,3),'zones':len(zones)})
 # Delete the temporary internal distribution tracks, keeping only pad access.
 removed=0
 for t in list(b.GetTracks()):
  if not isinstance(t,p.PCB_VIA) and t.GetNetname() in dc and t.GetLayer() in cores:
   held.append(t);b.Remove(t);removed+=1
 p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(g.fn),b);(P/'q2-v2.kicad_pro').write_bytes(g.pro)
 (P/'power-pours.json').write_text(json.dumps({'status':'PENDING_NATIVE_DRC','dc_nets':sorted(dc),'regions':report,'removed_temporary_inner_segments':removed,'preserved':'GND planes; short surface pad-to-via access; local switching, feedback and charge-pump circuits','via_policy':'Ordinary power access uses tented 0.45/0.20 mm through vias outside SMD solder lands; existing QFN GND thermal vias retained'},indent=2),encoding='utf8')
 print('POURS',report,flush=True)

if __name__=='__main__':
 if 'pour-only' not in sys.argv:route_spines()
 pour()
