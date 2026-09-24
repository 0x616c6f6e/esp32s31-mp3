"""Bridge 3.3 V plane islands using protected local copper on the other inner layer."""
import finish_grid as g
import json
p=g.p;P=g.P
drc=json.loads((P/'output/drc.json').read_text(encoding='utf8'))
spine=P/'output/power-pour-spines.kicad_pcb'
# Work from the CURRENT board in memory. Import only inner supply spine tracks
# into this temporary model and write the guide file, never the current PCB.
guide=p.LoadBoard(str(spine));dc=set(json.loads((P/'power-only-0402.json').read_text())['rails'])-{'GND'}
present={t.m_Uuid.AsString() for t in g.b.GetTracks()}
for t in guide.GetTracks():
 if not isinstance(t,p.PCB_VIA) and t.GetNetname() in dc and t.GetLayer() in [p.In2_Cu,p.In3_Cu] and t.m_Uuid.AsString() not in present:
  item=p.PCB_TRACK(g.b);item.SetStart(t.GetStart());item.SetEnd(t.GetEnd());item.SetWidth(t.GetWidth());item.SetLayer(t.GetLayer());item.SetNet(g.b.FindNet(t.GetNetname()));g.b.Add(item)
g.fn=spine
for e in drc['unconnected_items']:
 g.layers=[p.F_Cu,p.In2_Cu,p.In3_Cu,p.B_Cu];items,cu,holes,ko,shapes=g.database();ids=[i['uuid'] for i in e['items']]
 if any(u not in items for u in ids) or items[ids[0]].GetNetname()!='VCC_3V3':continue
 anchors=[]
 for u in ids:
  _,seen=g.group(u,items,shapes)
  via=next((v for v in seen if isinstance(items[v],p.PCB_VIA)),None)
  assert via,(u,'No plane access via');anchors.append(via)
 g.layers=[p.In3_Cu,p.In2_Cu]
 assert g.route(*anchors,width=.25,clearance=.152,step=.05,allow_new_vias=False),anchors
p.SaveBoard(str(spine),g.b);(P/'q2-v2.kicad_pro').write_bytes(g.pro)
