"""Make small clearance-checked shifts after unifying imported 0402 lands."""
import finish_grid as g
p=g.p;b=g.b
targets=['C115','C54','C39','R13','R44','C11']
held=[];moves=[]
for ref in targets:
 f=b.FindFootprintByReference(ref);start=g.xy(f.GetPosition());side=f.GetLayer()
 items,cu,holes,ko,shapes=g.database()
 own={a.m_Uuid.AsString() for a in f.Pads()}
 foreign={a.GetNetname():g.unary_union([s[side] for u,s in shapes.items() if u not in own and side in s and items[u].GetNetname()!=a.GetNetname()]).buffer(.102) for a in f.Pads()}
 drills={a.GetNetname():g.unary_union([s.buffer(c+.002) for n,s,c in holes if n!=a.GetNetname()]) for a in f.Pads()}
 courts=[]
 for o in b.GetFootprints():
  if o.GetReference()==ref or o.GetLayer()!=side:continue
  o.BuildCourtyardCaches();cy=o.GetCourtyard(side)
  if cy and cy.OutlineCount():courts.append(g.psgeom(cy))
 court=g.unary_union(courts)
 for _,dx,dy in sorted((dx*dx+dy*dy,dx*.05,dy*.05) for dx in range(-24,25) for dy in range(-24,25)):
  f.SetPosition(g.V((start[0]+dx,start[1]+dy)));f.BuildCourtyardCaches();cy=f.GetCourtyard(side);body=g.psgeom(cy)
  if not g.outline.buffer(-.25).contains(body) or body.intersects(court):continue
  if any(g.geometry(a,side).intersects(foreign[a.GetNetname()].union(drills[a.GetNetname()])) for a in f.Pads()):continue
  moves.append({'ref':ref,'delta_mm':[dx,dy],'position_mm':g.xy(f.GetPosition())});break
 else:f.SetPosition(g.V(start));raise RuntimeError('No local legal position '+ref)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(g.fn),b);(g.P/'q2-v2.kicad_pro').write_bytes(g.pro)
(g.P/'output/unified-0402-clearance-moves.json').write_text(g.json.dumps(moves,indent=2))
print(moves,flush=True)
