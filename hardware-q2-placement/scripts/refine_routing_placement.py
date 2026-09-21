"""Bounded, pin-aware placement refinement; never generates copper routing.

Run using KiCad Python with --input and --output. Input must be the reviewed,
reassociated unrouted board. Keep the input snapshot for reproducible metrics.
"""
from pathlib import Path
import argparse, json, math, hashlib
import pcbnew as p

P=Path(__file__).resolve().parents[1]
cli=argparse.ArgumentParser();cli.add_argument('--input',required=True,type=Path);cli.add_argument('--output',required=True,type=Path)
args=cli.parse_args()
assert args.input.resolve()!=args.output.resolve(), 'Write a separate candidate, not the input snapshot'
assert args.output.resolve()!=(P/'hardware.kicad_pcb').resolve(), 'Review and validate the candidate before replacing the project PCB'
b=p.LoadBoard(str(args.input));fs={f.GetReference():f for f in b.GetFootprints()}
assert len(b.GetTracks())==0 and all(z.GetIsRuleArea() for z in b.Zones())
xy=lambda v:(v.x/1e6,v.y/1e6)
V=lambda x,y:p.VECTOR2I(round(x*1e6),round(y*1e6))
def state(f):return {'xy':xy(f.GetPosition()),'angle':f.GetOrientationDegrees(),'side':'B' if f.IsFlipped() else 'F'}
def bounds(f):
 q=f.GetBoundingBox(False,False);return [q.GetX()/1e6,q.GetY()/1e6,q.GetRight()/1e6,q.GetBottom()/1e6]
def pads(f):return [{'num':a.GetNumber(),'net':a.GetNetname(),'xy':xy(a.GetPosition())} for a in f.Pads()]
def setpart(r,x,y,s,angle):
 f=fs[r]
 if f.IsFlipped()!=(s=='B'):f.Flip(f.GetPosition(),p.FLIP_DIRECTION_LEFT_RIGHT)
 f.SetPosition(V(x,y));f.SetOrientationDegrees(angle)
def overlap(a,c,gap=0):return a[0]<c[2]+gap and a[2]>c[0]-gap and a[1]<c[3]+gap and a[3]>c[1]-gap
before={r:state(f) for r,f in fs.items()}
groups=json.loads((P/'output/placement.json').read_text(encoding='utf8'))['groups']
for g in groups.values():g['support']=[r for r in g['support'] if r in fs]
anchors=['U9','CARD2','CN1','USB1','FPC2','H1','H2']+[r for r in fs if r.startswith('SCREW')]

# USB common ports face the receptacle; outputs face MCU and UART branches.
# Place the low-speed RTC away from the USB escape corridor. Motor outputs face H1.
ic_moves={'U17':(136,100,'B',180),'U12':(130.5,94,'B',-90),
 'U14':(142.5,101,'B',0),'U6':(116.5,91,'B',-90),
 'U1':(139,89,'F',0),'U11':(123,115.5,'F',0),
 'D1':(135.5,115.75,'F',0)}
for r,(x,y,s,a) in ic_moves.items():setpart(r,x,y,s,a)
active=['fuel_gauge','usb_mux','usb_uart','usb_esd','power_key','rtc',
        'dac','clock','i2s_level','analog_ldo','motor','display']
moving={r for g in active for r in groups[g]['support']}
moving.add('X1')
occupied={r:bounds(f) for r,f in fs.items() if r not in moving}
sides={r:state(f)['side'] for r,f in fs.items()}
regions={'charger':(129,105.5,146,120),'fuel_gauge':(138,97.5,146,109),
 'usb_mux':(131.5,96,140.5,105),'usb_uart':(125.5,90,135,99),
 'usb_esd':(130,114,141,119),'power_key':(113,87,121,95),
 'rtc':(134,85.5,144.5,95),'buck':(120.5,82,132,92),
 'dac':(102.7,100.4,119.5,112),'clock':(106.5,97,115.5,103),
 'i2s_level':(113,89,122,98),'analog_ldo':(117,96,127,104),
 'motor':(118,110,127,121),'display':(130,73.3,145.5,83.5)}
targets={
 'C27':[('U2','31')], 'C28':[('U2','4')], 'C17':[('U2','7')], 'C23':[('U2','25')],
 'C26':[('U2','26')], 'C29':[('U2','26')],
 'C8':[('U2','5'),('U2','7')], 'C18':[('U2','6'),('U2','9')],
 'C19':[('U2','9')], 'C20':[('U2','10'),('U2','11')],
 'C21':[('U2','21')], 'C22':[('U2','18')],
 'C24':[('U2','23'),('U2','24')], 'C25':[('U2','20'),('U2','23')],
 'C32':[('X1','1'),('U2','36')], 'C33':[('X1','3'),('U2','37')],
 'L2':[('U3','19'),('U3','20'),('U3','15'),('U3','16')],
 'C11':[('U3','21'),('U3','19'),('U3','20')],
 'D2':[('U3','19'),('U3','20'),('U3','23')], 'C16':[('U3','23')],
 'C9':[('U3','22')], 'C14':[('U3','1')], 'C10':[('U3','13'),('U3','14')],
 'C12':[('L2','1'),('L2','2'),('U3','15'),('U3','16')],
 'C15':[('L2','1'),('L2','2'),('U3','15'),('U3','16')],
 'R1':[('H2','3'),('U14','6')], 'R2':[('U14','10')], 'C43':[('U14','9')],
 'R33':[('U14','8')], 'R34':[('R33','2'),('R1','1')],
 'R31':[('USB1','A5')], 'R32':[('USB1','B5')],
 'C1':[('U4','4')], 'C2':[('L1','1'),('L1','2')],
 'R3':[('U4','5')], 'R4':[('U4','5')],
 'C4':[('U11','1')], 'C5':[('U11','10')], 'C58':[('U11','10')],
 'L3':[('U11','10')], 'R40':[('U16','5')],
 'C42':[('L4','1'),('L4','2'),('FPC2','1')],
 'C55':[('L4','1'),('L4','2')], 'C56':[('U16','4')], 'C57':[('U16','4')],
}
heights={r:m.get('model_bounds_xyz_mm',[0,0,0,0,0,3])[5] for m in json.loads((P/'models3d/model-manifest.json').read_text(encoding='utf8'))['models'] for r in m['references']}
def inside(x,y):
 if not(101.3<=x<=146.7 and 51.3<=y<=126.7):return False
 cx=min(137,max(111,x));cy=min(117,max(61,y))
 if math.hypot(x-cx,y-cy)>9.7:return False
 return not any(math.hypot(x-124,y-yy)<3.1 for yy in [52,126])
def allowed(r,bb,s):
 if not all(inside(x,y) for x in [bb[0],bb[2]] for y in [bb[1],bb[3]]):return False
 if overlap(bb,(122.592,51,144.846,60.669),.3):return False
 for other,ob in occupied.items():
  if other==r:continue
  if other.startswith('SCREW'):
   x,y=xy(fs[other].GetPosition());qx=min(bb[2],max(bb[0],x));qy=min(bb[3],max(bb[1],y))
   if math.hypot(qx-x,qy-y)<2.15:return False
  elif sides[other]==s and overlap(bb,ob,.25):return False
 if s=='B' and overlap(bb,(128,65.6,147,73.2),.25):return False
 if s=='F' and overlap(bb,(104.5,83,112,86),.25):return False
 if s=='F' and heights.get(r,0)>2.3 and overlap(bb,(116.7,86,140.7,120),.3):return False
 return True

def optimize(r,ic,region,s,extra=()):
 targetlist=targets.get(r,[(ic,a.GetNumber()) for a in fs[ic].Pads()])
 tp=[a for rr,nn in targetlist for a in pads(fs[rr]) if a['num']==nn]
 tp+=list(extra)
 pref=before[r]['xy'];best=None
 for angle in [0,90,180,-90]:
  setpart(r,0,0,s,angle);rp=pads(fs[r]);box=bounds(fs[r])
  for xi in range(math.ceil((region[0]-box[0])*4),math.floor((region[2]-box[2])*4)+1):
   x=xi/4
   for yi in range(math.ceil((region[1]-box[1])*4),math.floor((region[3]-box[3])*4)+1):
    y=yi/4;bb=[x+box[0],y+box[1],x+box[2],y+box[3]]
    if not allowed(r,bb,s):continue
    cost=.025*math.dist((x,y),pref);matched=False
    for a in rp:
     if a['net'] in ['', 'GND'] or a['net'].startswith('unconnected-'):continue
     tt=[q['xy'] for q in tp if q['net']==a['net']]
     if tt:
      # Pin-specific targets avoid the wrong supply pin on multi-supply ICs.
      distances=[math.dist((x+a['xy'][0],y+a['xy'][1]),q) for q in tt]
      if r=='R1':cost+=3*distances[0]+sum(distances[1:])
      else:
       weight=3 if r=='L2' and a['net']=='Net-(D2-A)' else 1
       cost+=weight*min(distances)
      matched=True
    if not matched:cost+=math.dist((x,y),xy(fs[ic].GetPosition()))
    candidate=(cost,x,y,angle,bb)
    if best is None or candidate[:4]<best[:4]:best=candidate
 assert best is not None, ('No legal site',r,ic,region)
 cost,x,y,a,bb=best;setpart(r,x,y,s,a);occupied[r]=bb;sides[r]=s

# Crystal and decoupling closest to the relevant IC pins get placement priority.
optimize('X1','U2',(107,97.5,115.5,102.2),'F')
priority=['D2','C11','C9','L2','C16','C14','C10','R1','L1','C1','C2',
          'C8','C18','C27','C28','C20','C24','C25','C23','C17','C19',
          'C26','C29','C32','C33','C35','C4','C5','C58','L3','L4','R40']
for group in active:
 g=groups[group];ic=g['anchor'];s=state(fs[ic])['side']
 order=sorted(g['support'],key=lambda r:(priority.index(r) if r in priority else 100,
  -(bounds(fs[r])[2]-bounds(fs[r])[0])*(bounds(fs[r])[3]-bounds(fs[r])[1])))
 for r in order:optimize(r,ic,regions[group],s)
 print('PLACED_GROUP',group,flush=True)

# Reserve two short front-side filter paths. Put VD decoupling directly behind
# pin 4 with a nearby power via and ground return, freeing the filter corridor.
precision={'C8':(106,104.5,'F',180),'C18':(106,106.5,'F',180),
           'C28':(108.5,105,'B',0)}
for r,(x,y,s,a) in precision.items():
 setpart(r,x,y,s,a);occupied[r]=bounds(fs[r]);sides[r]=s

# Refine complete local nets, not just distances from each passive to the IC.
# In particular the SW node couples the diode, inductor and bootstrap capacitor.
def mst(points):
 if len(points)<2:return 0
 reached=[points[0]];left=points[1:];value=0
 while left:
  distance,index=min((math.dist(a,v),i) for a in reached for i,v in enumerate(left))
  value+=distance;reached.append(left.pop(index))
 return value
def refine_cluster(group,passes=2):
 g=groups[group];members=[g['anchor']]+g['support']
 if group=='dac':members+=['X1','C32','C33']
 # Start charger refinement at the already reviewed cluster rather than a
 # greedy arrangement. Other groups retain their current legal placements.
 if group=='charger':
  for r in g['support']:
   st=before[r];setpart(r,*st['xy'],st['side'],st['angle']);occupied[r]=bounds(fs[r])
 for cycle in range(passes):
  order=sorted(g['support'],key=lambda r:(allowed(r,bounds(fs[r]),state(fs[r])['side']),r not in ['C11','C9','C16','D2','L2']))
  for r in order:
   if r in precision:continue
   s=state(fs[r])['side'];region=regions[group]
   others=[a for rr in members if rr!=r for a in pads(fs[rr])]
   targets_here=targets.get(r,[])
   explicit=[a for rr,nn in targets_here for a in pads(fs[rr]) if a['num']==nn]
   def score(candidate):
    if r=='D2':
     anode=next(a['xy'] for a in candidate if a['net']=='Net-(D2-A)')
     sw=[a['xy'] for a in pads(fs['U3']) if a['net']=='Net-(D2-A)']
     if min(math.dist(anode,q) for q in sw)>3:return float('inf')
    cost=0
    for net in set(a['net'] for a in candidate)-{'','GND'}:
     if net.startswith('unconnected-'):continue
     points=[a['xy'] for a in others+candidate if a['net']==net]
     if group=='charger':
      weight={'Net-(D2-A)':8,'Net-(U3-BTST)':8,'Net-(U3-REGN)':6,'VCC_LCD_BG':4}.get(net,1)
      cost+=weight*mst(points)
     elif net.startswith('Net-('):
      cost+=(8 if 'FILT' in net else 3)*mst(points)
     for a in candidate:
      if a['net']!=net:continue
      choices=[q['xy'] for q in explicit if q['net']==net]
      if choices and (net in ['VCC_1V8','VCC'] or group=='charger' and net=='VBAT'):
       cost+=4*min(math.dist(a['xy'],q) for q in choices)
    return cost
   start=state(fs[r]);startpads=pads(fs[r]);best=None
   if allowed(r,bounds(fs[r]),s):best=(score(startpads),*start['xy'],start['angle'],bounds(fs[r]))
   for angle in [0,90,180,-90]:
    setpart(r,0,0,s,angle);rp=pads(fs[r]);box=bounds(fs[r])
    for xi in range(math.ceil((region[0]-box[0])*4),math.floor((region[2]-box[2])*4)+1):
     x=xi/4
     for yi in range(math.ceil((region[1]-box[1])*4),math.floor((region[3]-box[3])*4)+1):
      y=yi/4;bb=[x+box[0],y+box[1],x+box[2],y+box[3]]
      if not allowed(r,bb,s):continue
      pp=[{**a,'xy':(x+a['xy'][0],y+a['xy'][1])} for a in rp]
      cost=score(pp)
      if best is None or cost<best[0]-1e-7:best=(cost,x,y,angle,bb)
   assert best is not None,('No cluster placement',r)
   cost,x,y,angle,bb=best;setpart(r,x,y,s,angle);occupied[r]=bb
  print('REFINED_CLUSTER',group,cycle+1,flush=True)
# Preserve the existing compact charger and buck switching loops.
refine_cluster('dac',2)
for r in anchors:assert state(fs[r])==before[r];fs[r].SetLocked(True)
for r in moving|set(ic_moves):fs[r].SetLocked(False)
p.SaveBoard(str(args.output),b)
data={'input_pcb_sha256':hashlib.sha256(args.input.read_bytes()).hexdigest(),
 'pcb_sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),
 'status':'PLACEMENT_ONLY_UNROUTED','outline_mm':[46,76],
 'fixed_mechanical_references':anchors,'groups':groups,
 'changes':[{'ref':r,'old':before[r],'new':state(f)} for r,f in sorted(fs.items()) if before[r]!=state(f)],
 'footprints':[{'reference':r,'value':f.GetValue(),**state(f),'bounds':bounds(f),'pads':pads(f)} for r,f in fs.items()]}
args.output.with_suffix('.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('CANDIDATE_SAVED',len(data['changes']),args.output)
