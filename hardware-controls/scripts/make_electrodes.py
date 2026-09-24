"""Generate three interpolated wheel electrodes; run with Python + Shapely.

Geometry follows QT2120 Figure 5-2: three channels with radial teeth <=4 mm.
The switch windows are project-specific and require assembled touch tuning.
"""
from pathlib import Path
import sys,math,json
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'tmp/controls-deps'))
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
cx,cy=22,17
def point(r,a):
    a=math.radians(a);return (cx+r*math.cos(a),cy+r*math.sin(a))
def wave(r):
    t=((r-7.5)/4)%1
    return -46+184*(t if t<=.5 else 1-t)
rr=[7.5+i*.025 for i in range(321)]
windows=unary_union([box(19.6,2.5,24.4,5.5),box(19.6,28.5,24.4,31.5),
    box(7.5,14.6,10.5,19.4),box(33.5,14.6,36.5,19.4)])
parts=[];shapes=[]
for i in range(3):
    points=[point(r,i*120+wave(r)+15) for r in rr]
    points += [point(15.5,i*120+wave(15.5)+15+a) for a in range(1,121)]
    points+=[point(r,(i+1)*120+wave(r)+15) for r in reversed(rr)]
    points += [point(7.5,(i+1)*120+wave(7.5)+15-a) for a in range(1,121)]
    poly=Polygon(points).buffer(-.15,join_style='round').difference(windows)
    poly=poly.buffer(-.2).buffer(.2).simplify(.003,preserve_topology=True)
    geoms=[poly] if poly.geom_type=='Polygon' else list(poly.geoms)
    assert all(g.area>.05 for g in geoms)
    shapes.append(poly)
    parts.append({'channel':i,'area_mm2':poly.area,'polygons':[
        {'points':list(g.exterior.coords)[:-1],'anchor':list(g.representative_point().coords)[0]} for g in geoms]})
gaps=[shapes[i].distance(shapes[j]) for i in range(3) for j in range(i)]
assert min(gaps)>.29,gaps
(P/'output/electrodes.json').write_text(json.dumps({'center':[22,17],'nominal_id_od_mm':[15,31],
    'minimum_gap_mm':min(gaps),'radial_tooth_pitch_mm':4,'channels':parts},indent=2)+'\n',encoding='utf8')
print('ELECTRODES',[(p['channel'],round(p['area_mm2'],2),len(p['polygons'])) for p in parts],gaps)
