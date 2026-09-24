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
    if t.GetNetname()!='/LCD_RST' or not t.IsOnLayer(p.F_Cu):continue
    if isinstance(t,p.PCB_VIA):reset.append(Point(xy(t.GetPosition())).buffer(.2))
    else:reset.append(LineString([xy(t.GetStart()),xy(t.GetEnd())]).buffer(p.ToMM(t.GetWidth())/2))
obstacle=unary_union(reset);ses=parse((O/'output/adapter.ses').read_text());routes=get(ses,'routes');scale=1/(1000*float(get(routes,'resolution')[2]))
for net in children(get(routes,'network_out'),'net'):
    if net[1]!='/GND':continue
    for w in children(net,'wire'):
        a=get(w,'path')
        if a[1]!='F.Cu':continue
        pts=[(float(a[i])*scale,-float(a[i+1])*scale) for i in range(3,len(a),2)]
        for start,end in zip(pts,pts[1:]):
            if LineString([start,end]).distance(obstacle)<.165:continue
            t=p.PCB_TRACK(b);t.SetStart(v(*start));t.SetEnd(v(*end));t.SetWidth(p.FromMM(.12));t.SetLayer(p.F_Cu);t.SetNet(b.FindNet('/GND'));b.Add(t)
for z in b.Zones():z.SetPadConnection(p.ZONE_CONNECTION_FULL)
# NC symbols still have explicit unique no-connect nets in KiCad's netlist.
xml=E.parse(O/'output/netlist.xml').getroot()
for n in xml.find('nets'):
    name=n.attrib['name'];ni=b.FindNet(name)
    if not ni:ni=p.NETINFO_ITEM(b,name);b.Add(ni)
    for nd in n:
        f=b.FindFootprintByReference(nd.attrib['ref'])
        for pad in f.Pads():
            if pad.GetNumber()==nd.attrib['pin']:pad.SetNet(ni)
data=json.loads((O/'output/design.json').read_text(encoding='utf8'))
for c in data['components']:
    f=b.FindFootprintByReference(c['ref']);f.GetField('Description').SetText(c['description'])
p.SaveBoard(str(fn),b)
sfn=O/'am213-fpc-adapter.kicad_sch';s=parse(sfn.read_text(encoding='utf8'))
for sy in children(s,'symbol'):
    ref=next((a[2] for a in children(sy,'property') if a[1]=='Reference'),None)
    if ref in ['J1','TP1']:get(sy,'in_bom')[1]='no'
sfn.write_text(dump(s),encoding='utf8')
print('Ground branches, unique NC nets and component fields synchronized')
