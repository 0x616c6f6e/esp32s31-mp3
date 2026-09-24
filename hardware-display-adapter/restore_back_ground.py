"""Restore safe ground branches and synchronize schematic metadata/net names."""
from pathlib import Path
import pcbnew as p,sys,json,xml.etree.ElementTree as E
R=Path(__file__).resolve().parent;O=R/'am213-fpc-adapter'
sys.path.insert(0,str(R.parent/'tmp'));from sexpr import parse,get,children,dump
sys.path.insert(0,str(R.parent/'tmp/controls-ground-deps'))
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
fn=O/'am213-fpc-adapter.kicad_pcb';b=p.LoadBoard(str(fn));v=lambda x,y:p.VECTOR2I(round(x*1e6),round(y*1e6));xy=lambda a:(p.ToMM(a.x),p.ToMM(a.y))
reset=[]
for t in b.GetTracks():
    if t.GetNetname()!='/LCD_RST' or not t.IsOnLayer(p.B_Cu):continue
    if isinstance(t,p.PCB_VIA):reset.append(Point(xy(t.GetPosition())).buffer(.2))
    else:reset.append(LineString([xy(t.GetStart()),xy(t.GetEnd())]).buffer(p.ToMM(t.GetWidth())/2))
obstacle=unary_union(reset);ses=parse((O/'output/adapter.ses').read_text());routes=get(ses,'routes');scale=1/(1000*float(get(routes,'resolution')[2]))
for net in children(get(routes,'network_out'),'net'):
    if net[1]!='/GND':continue
    for w in children(net,'wire'):
        a=get(w,'path')
        if a[1]!='B.Cu':continue
        pts=[(float(a[i])*scale,-float(a[i+1])*scale) for i in range(3,len(a),2)]
        for start,end in zip(pts,pts[1:]):
            if LineString([start,end]).distance(obstacle)<.165:continue
            t=p.PCB_TRACK(b);t.SetStart(v(*start));t.SetEnd(v(*end));t.SetWidth(p.FromMM(.12));t.SetLayer(p.B_Cu);t.SetNet(b.FindNet('/GND'));b.Add(t)
p.SaveBoard(str(fn),b)
