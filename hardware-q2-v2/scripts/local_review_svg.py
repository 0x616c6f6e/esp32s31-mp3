from finish_grid import *
items,cu,holes,ko,shapes=database();clip=box(151.5,87,155.5,91)
out=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1200" viewBox="151.5 87 4 4"><rect x="151.5" y="87" width="4" height="4" fill="#222"/>']
for uid,a in items.items():
 if p.F_Cu not in shapes[uid]:continue
 s=shapes[uid][p.F_Cu]
 if not s.intersects(clip):continue
 color='#49c47c' if a.GetNetname()=='GND' else '#cf774d'
 out.append(s.intersection(clip).svg(fill_color=color,opacity=.85).replace('stroke-width="2.0"','stroke-width="0.005"'))
 if isinstance(a,p.PAD):
  x,y=xy(a.GetPosition());out.append(f'<text x="{x}" y="{y}" font-size=".09" text-anchor="middle" fill="white">{a.GetParentFootprint().GetReference()}:{a.GetNumber()}</text>')
for n,s,c in holes:
 if s.intersects(clip):out.append(s.svg(fill_color='#111').replace('stroke-width="2.0"','stroke-width="0.005"'))
out.append('</svg>');(P/'output/local-ground.svg').write_text(''.join(out))
