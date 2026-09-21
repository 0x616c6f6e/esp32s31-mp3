"""Reversible KiCad-native Q2 layout revision, always starts from preserved Rev A."""
from pathlib import Path
import pcbnew as p, json, math, hashlib, sys, uuid
ROOT=Path(__file__).resolve().parents[2];DST=ROOT/'hardware-q2';SRC=ROOT/'hardware/hardware.kicad_pcb'
b=p.LoadBoard(str(SRC));fps={f.GetReference():f for f in b.GetFootprints()}
sys.path.insert(0,str(ROOT/'tmp'))
from sexpr import parse, dump, children, get, S
V=lambda x,y:p.VECTOR2I(round(x*1e6),round(y*1e6))
xy=lambda q:(q.x/1e6,q.y/1e6)
oldpads=[];changes=[]
for f in b.GetFootprints():
    for a in f.Pads():oldpads.append((a,xy(a.GetPosition()),a.GetNetname(),f.GetReference()))
targets={'U9':(133.719,72.931),'FPC2':(140.148,69.400),
 'R29':(119.749,66.454),'C40':(121.019,63.914),'C41':(119.749,63.914),'C39':(121.019,66.581),
 'R7':(140.45,85.909),'R8':(141.85,85.909),
 'U11':(122.5,115.5),'H1':(122.5,121.85),'C5':(119.7,117.078),'C58':(118.43,117.078),
 'CN1':(112.565,118.425),'SCREW1':(104.3,114.5),'SCREW4':(145.5,92.5),'R1':(140.5,95.5),
 'R26':(123.466,70.2775),'R30':(123.464,71.812),
 'R20':(141.594,62.850),'R25':(141.594,64.376),'R2':(146.2,88.672),
 'R33':(140.85,91.085),'C43':(142.6,90.628)}
for ref in ['U16','R40','C42','R44','L4','C55','R41','R42','C56','C57','R43']:
    x,y=xy(fps[ref].GetPosition());targets[ref]=(x,y+3.0)
flips=['R35','R38','R39','R37','R36','C49','C50','R5','C43','R33','R2']
for ref in set(targets)|set(flips):
    f=fps[ref];old=xy(f.GetPosition());side='B' if f.IsFlipped() else 'F'
    if ref in targets:f.SetPosition(V(*targets[ref]))
    if ref=='R1':f.SetOrientationDegrees(f.GetOrientationDegrees()+90)
    if ref in flips:f.Flip(f.GetPosition(),False)
    changes.append({'ref':ref,'old_xy':old,'new_xy':xy(f.GetPosition()),'old_side':side,'new_side':'B' if f.IsFlipped() else 'F'})
anchors=[]
for pad,old,net,ref in oldpads:
    new=xy(pad.GetPosition());anchors.append((old,new,net,ref))
def mapped(q,net):
    x,y=xy(q)
    exact=[a for a in anchors if a[2]==net and math.hypot(a[0][0]-x,a[0][1]-y)<.015]
    if exact:
        a=min(exact,key=lambda a:math.dist(a[0],(x,y)));return V(x+a[1][0]-a[0][0],y+a[1][1]-a[0][1])
    a=min(anchors,key=lambda a:math.dist(a[0],(x,y)))
    if math.dist(a[0],(x,y))<1.8:
        return V(x+a[1][0]-a[0][0],y+a[1][1]-a[0][1])
    if x>124.9 and y<81.3:return V(x-3,y+4.5)
    return q
for t in b.GetTracks():
    if isinstance(t,p.PCB_VIA):t.SetPosition(mapped(t.GetPosition(),t.GetNetname()))
    elif isinstance(t,p.PCB_ARC):
        t.SetStart(mapped(t.GetStart(),t.GetNetname()));t.SetMid(mapped(t.GetMid(),t.GetNetname()));t.SetEnd(mapped(t.GetEnd(),t.GetNetname()))
    else:t.SetStart(mapped(t.GetStart(),t.GetNetname()));t.SetEnd(mapped(t.GetEnd(),t.GetNetname()))
# Serialize native placement/routing edits before constructing the new outline.
p.SaveBoard(str(DST/'hardware.kicad_pcb'),b)
print('NATIVE_PLACEMENTS_SAVED',flush=True)
tree=parse((DST/'hardware.kicad_pcb').read_text(encoding='utf8'))
# Exact rounded47x76 outline: case(1.5,2)..(48.5,78), R10.5.
# The central rear-cover bosses get open-ended semicircular clearance notches.
tree[:]=[g for g in tree if not(isinstance(g,list) and g[0].startswith('gr_') and get(g,'layer',['layer',''])[1]=='Edge.Cuts')]
def edge(kind,pts):
    tree.append([kind]+[[key,*[str(round(v,6)) for v in pt]] for key,pt in pts]+[['stroke',['width','0.05'],['type','default']],['layer',S('Edge.Cuts')],['uuid',S(str(uuid.uuid4()))]])
def seg(a,c):
    edge('gr_line',[('start',a),('end',c)])
def arc(c,r,a0,a1):
    pt=lambda a:(c[0]+r*math.cos(math.radians(a)),c[1]+r*math.sin(math.radians(a)))
    edge('gr_arc',[('start',pt(a0)),('mid',pt((a0+a1)/2)),('end',pt(a1))])
x0,y0,x1,y1,r=101,51,147,127,10
# Housing bosses at case(25,3),(25,77) -> KiCad(124,52),(124,126).
notchr=2.8;dx=math.sqrt(notchr**2-1)
seg((x0+r,y0),(124-dx,y0));seg((124+dx,y0),(x1-r,y0))
a=math.degrees(math.asin(-1/notchr));arc((124,52),notchr,180-a,a)
seg((x1,y0+r),(x1,y1-r));seg((x0,y1-r),(x0,y0+r))
seg((x1-r,y1),(124+dx,y1));seg((124-dx,y1),(x0+r,y1))
a=math.degrees(math.asin(1/notchr));arc((124,126),notchr,a,180-a-360)
for c,a in [((x1-r,y0+r),-90),((x1-r,y1-r),0),((x0+r,y1-r),90),((x0+r,y0+r),180)]:arc(c,r,a,a+90)
# Existing antenna rule area was a whole-board strip. Replace its polygon with
# the translated antenna projection to avoid unrelated TF pads; no rule relaxation.
for z in children(tree,'zone'):
    if get(z,'keepout'):
        poly=get(z,'polygon');poly[1]=['pts']+[['xy',str(x),str(y)] for x,y in [(122.592,51),(144.846,51),(144.846,60.669),(122.592,60.669)]]
    z[:]=[v for v in z if not(isinstance(v,list) and v[0]=='filled_polygon')]
# The FPC side channel is a mechanical component restriction, not an all-copper
# ban: copper inside the board remains allowed. It is checked in FreeCAD.
(DST/'hardware.kicad_pcb').write_text(dump(tree)+'\n',encoding='utf8')
report={'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'board_outline_mm':[46,76],'radius_mm':10,'changed_placements':sorted(changes,key=lambda a:a['ref']),'fpc_case_axis_y_mm':20.4,'screen_case_axis_y_mm':20.4,'state':'PLACED_ROUTE_REPAIR_IN_PROGRESS'}
(DST/'output/placement-changes.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('PLACEMENT_WRITTEN',len(changes))
