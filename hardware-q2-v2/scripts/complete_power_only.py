"""Complete only the explicitly allowlisted power connections in native DRC."""
import finish_grid as g
import json
policy=json.loads((g.P/'power-only-0402.json').read_text())
allowed=set(policy['rails'])|set(policy['local_power_nodes'])
drc=json.loads((g.P/'output/drc.json').read_text(encoding='utf8'))
for e in drc['unconnected_items']:
 ids=[i['uuid'] for i in e['items']]
 items={a.m_Uuid.AsString():a for f in g.b.GetFootprints() for a in f.Pads()}
 items.update({a.m_Uuid.AsString():a for a in g.b.GetTracks()})
 if len(ids)!=2 or any(i not in items for i in ids):continue
 net=items[ids[0]].GetNetname()
 if net not in allowed:continue
 print('POWER',net,flush=True)
 if net=='GND':g.route(ids[0],ground=True)
 else:g.route(*ids)
