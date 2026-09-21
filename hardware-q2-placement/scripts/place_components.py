"""Create an unrouted placement proposal from the preserved routed Q2 board.

Run only when regenerating the proposal, before manual routing. IC locations are
engineering choices; a bounded search orients/places each supporting passive near
its relevant pins while reserving placement gaps. It does not route any copper.
"""
from pathlib import Path
import sys,json,math,hashlib,collections
import pcbnew as pcb
P=Path(__file__).resolve().parents[1];ROOT=P.parent;SRC=ROOT/'hardware-q2/hardware.kicad_pcb'
sys.path.insert(0,str(ROOT/'tmp'));from sexpr import parse,dump,get,children
tree=parse(SRC.read_text(encoding='utf8'))
removed=collections.Counter(n[0] for n in tree if isinstance(n,list) and (n[0] in ['segment','arc','via'] or n[0]=='zone' and not get(n,'keepout')))
tree[:]=[n for n in tree if not(isinstance(n,list) and (n[0] in ['segment','arc','via'] or n[0]=='zone' and not get(n,'keepout')))]
boardpath=P/'hardware.kicad_pcb';boardpath.write_text(dump(tree)+'\n',encoding='utf8')
b=pcb.LoadBoard(str(boardpath));fps={f.GetReference():f for f in b.GetFootprints()}
V=lambda x,y:pcb.VECTOR2I(round(x*1e6),round(y*1e6))
xy=lambda v:(v.x/1e6,v.y/1e6)
def state(f):return {'xy':xy(f.GetPosition()),'angle':f.GetOrientationDegrees(),'side':'B' if f.IsFlipped() else 'F'}
before={r:state(f) for r,f in fps.items()}
def setpart(r,x,y,side,angle=None):
    f=fps[r]
    if f.IsFlipped()!=(side=='B'):f.Flip(f.GetPosition(),pcb.FLIP_DIRECTION_LEFT_RIGHT)
    f.SetPosition(V(x,y))
    if angle is not None:f.SetOrientationDegrees(angle)
    f.SetLocked(False)
def bounds(f):
    bb=f.GetBoundingBox(False,False);lo=xy(bb.GetOrigin());hi=xy(bb.GetEnd());return (*lo,*hi)
def pads(f):return [{'num':a.GetNumber(),'net':a.GetNetname(),'xy':xy(a.GetPosition())} for a in f.Pads()]

# Preserve the ports, antenna placement and all enclosure screw centers.
anchors=['U9','CARD2','CN1','USB1','FPC2','H1','H2']+[r for r in fps if r.startswith('SCREW')]
groups={
 'mcu':('U9',['R29','C39','C40','C41','R20','R25','C45','C46']),
 'storage':('CARD2',['R35','R36','R37','R38','R39','C49','C50']),
 'display':('U16',['R40','C42','L4','C55','C56','C57','R41']),
 'imu':('U15',['C47','C48']),
 'dac':('U2',['C8','C17','C18','C19','C20','C21','C22','C23','C24','C25','C26','C27','C28','C29']),
 'clock':('X1',['C32','C33']),
 'i2c_level':('U7',['R17','R18','R19','C34','R26','R30']),
 'i2s_level':('U8',['C35']),
 'analog_ldo':('U5',['C30','C31']),
 'motor':('U11',['C4','C5','C58','L3','R44']),
 'usb_esd':('D1',['R31','R32']),
 'usb_mux':('U17',['C36','R21','R22']),
 'usb_uart':('U12',['C37','C38','C44','R27','R28']),
 'charger':('U3',['L2','D2','C9','C10','C11','C12','C14','C15','C16','R9','R10','R11','R12','R13','R14','R43']),
 'buck':('U4',['L1','C1','C2','R3','R4','R5']),
 'power_key':('U6',['C3']),
 'fuel_gauge':('U14',['R1','R2','R33','R34','C43']),
 'rtc':('U1',['C6','C7','C53','C54','R7','R8','R42'])
}
assigned=anchors+[r for ic,pp in groups.values() for r in [ic]+pp]
assert set(assigned)==set(fps),(set(fps)-set(assigned),set(assigned)-set(fps))
# Coordinates are KiCad's top-view frame, mm. Backside is an actual footprint flip.
ics={'U15':(117.7,78,'F',90),'U2':(111.7,105.69,'F',0),'X1':(111.1,99.65,'F',90),
 'U7':(107.4,95,'F',-90),'U8':(117,94,'F',-90),'U5':(121,99.5,'F',0),
 'U11':(122.5,115.5,'F',180),'D1':(135.5,115.4,'F',90),
 'U17':(134,103,'B',0),'U12':(134,94.5,'B',-90),
 'U3':(138,112.2,'B',90),'U4':(126,87,'B',90),'U6':(126,95,'B',-90),
 'U14':(140.3,100,'B',180),'U1':(139,86.5,'B',0)}
for r,(x,y,s,a) in ics.items():setpart(r,x,y,s,a)
# These original local clusters already satisfy port/FPC/antenna constraints.
fixedgroups=['mcu','storage','display','dac']
fixed=set(anchors)|set(ics)|{r for g in fixedgroups for r in [groups[g][0]]+groups[g][1]}
for r in anchors:fps[r].SetLocked(True)
occupied={r:bounds(fps[r]) for r in fixed};side={r:('B' if fps[r].IsFlipped() else 'F') for r in fixed}
regions={'imu':(113,74,122,83),'clock':(107,96.5,115,102.5),
 'i2c_level':(102.5,88,113,98),'i2s_level':(113,89,121,98),
 'analog_ldo':(117,96,127,105),'motor':(118,110,128,121),
 'usb_esd':(129.5,113,141,119.2),'usb_mux':(129,98,138,108),
 'usb_uart':(129,88,139,98.5),'charger':(127,105.5,145,119.5),
 'buck':(120.5,82,132,92),'power_key':(121,92,130,99),
 'fuel_gauge':(137,95,145.5,107.5),'rtc':(135,81.5,144.5,92)}
preferred={'C4':(124.4,112),'L3':(126,118),'C5':(120,117.8),'C58':(118.5,117.8),
 'R31':(132,117.2),'R32':(139,117.2),'C32':(111.8,101.5),'C33':(108.6,99),
 'R1':(143,104),'C14':(138,116),'L2':(134,111),'D2':(132,113),
 'C16':(132,116),'R26':(110.4,94),'R30':(110.4,95.4)}
special_targets={'R31':['USB1'],'R32':['USB1'],'C32':['X1','U2'],'C33':['X1','U2'],
 'C2':['L1'],'C12':['L2'],'C15':['L2','U3'],'L3':['U11'],'R1':['H2','U14'],
 'R26':['U7'],'R30':['U7'],'C7':['U1'],'C6':['U1'],'C53':['U1'],'C54':['U1']}
manifest=json.loads((P/'models3d/model-manifest.json').read_text(encoding='utf8'))
heights={r:m['model_bounds_xyz_mm'][5] for m in manifest['models'] for r in m['references']}
def inside(x,y,margin=.3):
    if not(101+margin<=x<=147-margin and 51+margin<=y<=127-margin):return False
    cx=min(137,max(111,x));cy=min(117,max(61,y))
    if math.hypot(x-cx,y-cy)>10-margin:return False
    if any(math.hypot(x-124,y-yy)<2.8+margin for yy in [52,126]):return False
    return True
def overlap(a,c,gap=0):return a[0]<c[2]+gap and a[2]>c[0]-gap and a[1]<c[3]+gap and a[3]>c[1]-gap
def allowed(r,bb,s):
    if not all(inside(x,y) for x in [bb[0],bb[2]] for y in [bb[1],bb[3]]):return False
    if overlap(bb,(122.592,51,144.846,60.669),.3):return False
    for other,ob in occupied.items():
        if other.startswith('SCREW'):
            x,y=xy(fps[other].GetPosition());qx=min(bb[2],max(bb[0],x));qy=min(bb[3],max(bb[1],y))
            if math.hypot(qx-x,qy-y)<2.1:return False
        elif side[other]==s and overlap(bb,ob,.20):return False
        elif other in ['H1','H2','USB1','CARD2'] and overlap(bb,ob,.20):return False
    if s=='B' and overlap(bb,(128,65.6,147,73.2),.2):return False
    if s=='F' and heights.get(r,0)>2.3 and overlap(bb,(116.7,86,140.7,120),.3):return False
    return True

placement_cost={}
for group,(ic,parts) in groups.items():
    if group in fixedgroups:continue
    ss='B' if fps[ic].IsFlipped() else 'F';ix,iy=xy(fps[ic].GetPosition());region=regions[group]
    # Larger supporting components first. Explicit high-current/clock parts lead.
    order=sorted(parts,key=lambda r:(r not in ['L1','L2','D2','R1','L3','C32','C33'],-(bounds(fps[r])[2]-bounds(fps[r])[0])*(bounds(fps[r])[3]-bounds(fps[r])[1])))
    for r in order:
        targetrefs=special_targets.get(r,[ic]);targetpads=[p for rr in targetrefs for p in pads(fps[rr])]
        # Local named nets add their already placed cluster neighbours.
        local=[p for rr in [ic]+parts if rr in occupied for p in pads(fps[rr]) if p['net'].startswith('Net-(')]
        best=None;pref=preferred.get(r,(ix,iy))
        for angle in [0,90,180,-90]:
            setpart(r,0,0,ss,angle);rel=pads(fps[r]);bb=bounds(fps[r])
            for xi in range(math.ceil((region[0]-bb[0])*4),math.floor((region[2]-bb[2])*4)+1):
                x=xi/4
                for yi in range(math.ceil((region[1]-bb[1])*4),math.floor((region[3]-bb[3])*4)+1):
                    y=yi/4;box=(x+bb[0],y+bb[1],x+bb[2],y+bb[3])
                    if not allowed(r,box,ss):continue
                    cost=.10*math.dist((x,y),pref)+.03*math.dist((x,y),(ix,iy));matched=0
                    for pad in rel:
                        net=pad['net']
                        if net in ['', 'GND'] or net.startswith('unconnected-'):continue
                        tt=[p['xy'] for p in targetpads if p['net']==net]
                        if net.startswith('Net-('):tt += [p['xy'] for p in local if p['net']==net]
                        if tt:
                            weight=2 if net.startswith('Net-(') else 1
                            cost+=weight*min(math.dist((x+pad['xy'][0],y+pad['xy'][1]),q) for q in tt);matched+=1
                    if not matched:cost+=math.dist((x,y),pref)
                    candidate=(cost,x,y,angle,box)
                    if best is None or candidate[:4]<best[:4]:best=candidate
        assert best is not None,('NO_PLACEMENT_SPACE',r,group)
        cost,x,y,angle,bb=best;setpart(r,x,y,ss,angle);occupied[r]=bb;side[r]=ss;placement_cost[r]=round(cost,3)
        print('PLACED',r,ss,x,y,angle,flush=True)
pcb.SaveBoard(str(boardpath),b)
after={r:state(f) for r,f in fps.items()};changes=[{'ref':r,'old':before[r],'new':after[r]} for r in sorted(fps) if before[r]!=after[r]]
report={'status':'PLACEMENT_ONLY_UNROUTED','source_pcb_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'pcb_sha256':hashlib.sha256(boardpath.read_bytes()).hexdigest(),'source_project':'hardware-q2','outline_mm':[46,76],'removed':dict(removed),'fixed_mechanical_references':anchors,'groups':{g:{'anchor':a,'support':pp} for g,(a,pp) in groups.items()},'changes':changes,'counts_by_side':dict(collections.Counter(v['side'] for v in after.values())),'footprints':[{'reference':r,'value':f.GetValue(),**state(f),'bounds':bounds(f),'pads':pads(f)} for r,f in fps.items()]}
(P/'output/placement.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('PLACEMENT_SAVED',len(changes),'changes',report['counts_by_side'])
