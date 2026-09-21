"""Conservative local octilinear repair. Native KiCad DRC is the acceptance gate."""
from pathlib import Path
import json,math,heapq,time,uuid,sys,collections
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'hardware-q2';sys.path.insert(0,str(ROOT/'tmp'))
from sexpr import parse,dump,get,children,S
G=json.loads((P/'output/geometry.json').read_text(encoding='utf8'));items=G['items'];byid={o['id']:o for o in items}
D=json.loads(Path(sys.argv[1] if len(sys.argv)>1 else P/'output/repair-drc.json').read_text(encoding='utf8'))
STEP=.05;X0=100;Y0=50;W=981;H=1581;LS=[0,6,8,2];CLR=.127
EXTRA=.015 if '--fine' in sys.argv else .04
def pix(pt):return (round((pt[0]-X0)/STEP),round((pt[1]-Y0)/STEP))
def real(q):return [round(X0+q[0]*STEP,6),round(Y0+q[1]*STEP,6)]
def width_for(net):
    if net in ['VBAT','GBAT','VBUS_5V']:return .4
    if net in ['VCC_3V3','Net-(U11-VDD)','MOTOR_OUT_N','MOTOR_OUT_P','VCC_LCD_BG']:return .25
    if 'HPOUT' in net:return .2032
    if 'USB_D' in net:return .18
    return .127
def draw_obj(draw,o,margin):
    x,y=o['pos'];cx,cy=pix((x,y))
    if o['kind'] in ['track','arc']:
        pts=[o['pos'],o['end']] if o['kind']=='track' else [o['pos'],o['mid'],o['end']]
        if o['kind']=='arc':
            a,m,b=[np.array(pt) for pt in pts]
            try:
                center=np.linalg.solve(2*np.array([m-a,b-a]),np.array([np.dot(m,m)-np.dot(a,a),np.dot(b,b)-np.dot(a,a)]))
                r=float(np.linalg.norm(a-center));angles=[math.atan2(*(pt-center)[::-1]) for pt in [a,m,b]]
                sweep=(angles[2]-angles[0])%(2*math.pi)
                if (angles[1]-angles[0])%(2*math.pi)>sweep:sweep-=2*math.pi
                pts=[(center+r*np.array([math.cos(t),math.sin(t)])).tolist() for t in np.linspace(angles[0],angles[0]+sweep,max(3,math.ceil(abs(sweep)*r/.02)))]
            except np.linalg.LinAlgError:pass
        wd=math.ceil((o['width']+2*margin)/STEP);pp=[pix(v) for v in pts];draw.line(pp,fill=1,width=wd)
        for px,py in pp:draw.ellipse((px-wd/2,py-wd/2,px+wd/2,py+wd/2),fill=1)
    elif o['kind']=='via':
        r=(o['width']/2+margin)/STEP;draw.ellipse((cx-r,cy-r,cx+r,cy+r),fill=1)
    else:
        sx,sy=[v/2+margin for v in o['size']]
        if o['shape']==0:draw.ellipse((cx-sx/STEP,cy-sy/STEP,cx+sx/STEP,cy+sy/STEP),fill=1)
        else:
            a=math.radians(o['angle']);pp=[pix((x+dx*math.cos(a)+dy*math.sin(a),y-dx*math.sin(a)+dy*math.cos(a))) for dx,dy in [(-sx,-sy),(-sx,sy),(sx,sy),(sx,-sy)]];draw.polygon(pp,fill=1)
def border_mask(margin):
    im=Image.new('1',(W,H),1);dr=ImageDraw.Draw(im)
    dr.rounded_rectangle((*pix((101+margin,51+margin)),*pix((147-margin,127-margin))),radius=(10-margin)/STEP,fill=0)
    for x,y in [(124,52),(124,126)]:
        r=2.8+margin;dr.ellipse((*pix((x-r,y-r)),*pix((x+r,y+r))),fill=1)
    for poly in G['keepouts']:
        dr.polygon([pix(pt) for pt in poly],fill=1);dr.line([pix(pt) for pt in poly+[poly[0]]],fill=1,width=math.ceil(2*margin/STEP))
    # Imported USB internal mechanical slots; conservative bounding cuts.
    for o in items:
        hole=o.get('hole',0);diam=max(hole) if isinstance(hole,list) else hole
        if o.get('npth') and diam:
            x,y=o['pos'];r=diam/2+margin;dr.ellipse((*pix((x-r,y-r)),*pix((x+r,y+r))),fill=1)
    return im
def masks(net,width):
    images=[border_mask(.3+width/2+.015) for _ in LS];vi=border_mask(.3+.25+.015)
    draws=[ImageDraw.Draw(im) for im in images];vd=ImageDraw.Draw(vi)
    power=P/'output/power-keepouts.json'
    if power.exists():
        for z in json.loads(power.read_text(encoding='utf8')):
            if net==z['net']:continue
            pp=[pix(pt) for pt in z['points']]
            for draw,extra in [(draws[0],width/2+.15),(vd,.4)]:
                draw.polygon(pp,fill=1);draw.line(pp+[pp[0]],fill=1,width=math.ceil(2*extra/STEP))
    for o in items:
        if o['net']!=net:
            for i,l in enumerate(LS):
                if l in o['layers']:draw_obj(draws[i],o,CLR+width/2+EXTRA)
            draw_obj(vd,o,CLR+.25+EXTRA)
        hole=o.get('hole',0);diam=max(hole) if isinstance(hole,list) else hole
        if diam:
            cx,cy=pix(o['pos']);r=(diam/2+.25+.125)/STEP;vd.ellipse((cx-r,cy-r,cx+r,cy+r),fill=1)
    return np.array([np.array(im,dtype=bool) for im in images]),np.array(vi,dtype=bool)
def route(a,b,net,width):
    mask,via=masks(net,width)
    for o,other in [(a,b),(b,a)]:
        pts=[o['pos']]+([o['end']] if o['kind'] in ['track','arc'] else [])
        pts=[pt for pt in pts if 0<=pix(pt)[0]<W and 0<=pix(pt)[1]<H and any(not mask[LS.index(l),pix(pt)[1],pix(pt)[0]] for l in o['layers'] if l in LS)]
        if not pts:return None,'endpoint blocked'
        o['pos']=min(pts,key=lambda pt:math.dist(pt,other['pos']))
    sp=pix(a['pos']);ep=pix(b['pos'])
    als=[LS.index(l) for l in a['layers'] if l in LS and not mask[LS.index(l),sp[1],sp[0]]]
    bls=[LS.index(l) for l in b['layers'] if l in LS and not mask[LS.index(l),ep[1],ep[0]]]
    if not als or not bls:return None,'no available endpoint layer'
    def h(x,y,l):return 1.4*math.hypot(x-ep[0],y-ep[1])+(0 if l in bls else 45)
    heap=[];cost={};parent={};ends={(l,ep[1],ep[0]) for l in bls}
    for l in als:k=(l,sp[1],sp[0]);cost[k]=0;heapq.heappush(heap,(h(sp[0],sp[1],l),0,k))
    dirs=[(1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.414214),(1,-1,1.414214),(-1,1,1.414214),(-1,-1,1.414214)]
    visited=0
    while heap:
        _,g,key=heapq.heappop(heap)
        if g>cost.get(key,1e30)+1e-8:continue
        if key in ends:
            path=[key]
            while key in parent:key=parent[key];path.append(key)
            return path[::-1],visited
        visited+=1
        if visited>700000:return None,'search limit'
        l,y,x=key
        for dx,dy,dc in dirs:
            nx=x+dx;ny=y+dy
            if not(0<=nx<W and 0<=ny<H) or mask[l,ny,nx]:continue
            if dx and dy and (mask[l,y,nx] or mask[l,ny,x]):continue
            ng=g+dc;k=(l,ny,nx)
            if ng<cost.get(k,1e30):cost[k]=ng;parent[k]=key;heapq.heappush(heap,(ng+h(nx,ny,l),ng,k))
        if not via[y,x]:
            for nl in range(len(LS)):
                if nl==l or mask[nl,y,x]:continue
                ng=g+80;k=(nl,y,x)
                if ng<cost.get(k,1e30):cost[k]=ng;parent[k]=key;heapq.heappush(heap,(ng+h(x,y,nl),ng,k))
    return None,'no route'
results=[];new=[]
pending=[]
for v in D['unconnected_items']:
    a,b=[byid.get(i['uuid']) for i in v['items'][:2]]
    if not a or not b or (a['net']=='GND' and '--ground' not in sys.argv):continue
    pending.append((a,b,v.get('width',width_for(a['net']))))
pending.sort(key=lambda ab:(0 if 'USB_D' in ab[0]['net'] else 1,math.dist(ab[0]['pos'],ab[1]['pos'])))
for index,(aa,bb,width) in enumerate(pending):
    a,b=dict(aa),dict(bb);net=a['net'];t=time.time();path,detail=route(a,b,net,width)
    print(index+1,'/',len(pending),net,bool(path),detail,round(time.time()-t,2),flush=True)
    results.append({'net':net,'success':bool(path),'detail':detail})
    if not path:continue
    pts=[path[0]]
    for i in range(1,len(path)-1):
        prev,cur,nxt=path[i-1:i+2]
        if tuple(cur[j]-prev[j] for j in range(3))!=tuple(nxt[j]-cur[j] for j in range(3)):pts.append(cur)
    pts.append(path[-1])
    def tr(start,end,l):return {'kind':'track','id':str(uuid.uuid4()),'net':net,'pos':start,'end':end,'width':width,'layers':[l]}
    start=real((pts[0][2],pts[0][1]));end=real((pts[-1][2],pts[-1][1]))
    adds=[tr(a['pos'],start,LS[pts[0][0]]),tr(end,b['pos'],LS[pts[-1][0]])]
    for u,v in zip(pts,pts[1:]):
        pa=real((u[2],u[1]));pb=real((v[2],v[1]))
        if u[0]!=v[0]:adds.append({'kind':'via','id':str(uuid.uuid4()),'net':net,'pos':pa,'width':.5,'hole':.25,'layers':G['layers']})
        elif pa!=pb:adds.append(tr(pa,pb,LS[u[0]]))
    adds=[o for o in adds if o['kind']=='via' or o['pos']!=o['end']];new.extend(adds);items.extend(adds)
tree=parse((P/'hardware.kicad_pcb').read_text(encoding='utf8'));names={0:'F.Cu',4:'In1.Cu',6:'In2.Cu',8:'In3.Cu',10:'In4.Cu',2:'B.Cu'}
for o in new:
    if o['kind']=='via':n=['via',['at',*map(str,o['pos'])],['size','.5'],['drill','.25'],['layers',S('F.Cu'),S('B.Cu')],['net',S(o['net'])],['uuid',S(o['id'])]]
    else:n=['segment',['start',*map(str,o['pos'])],['end',*map(str,o['end'])],['width',str(o['width'])],['layer',S(names[o['layers'][0]])],['net',S(o['net'])],['uuid',S(o['id'])]]
    tree.append(n)
(P/'hardware.kicad_pcb').write_text(dump(tree)+'\n',encoding='utf8')
(P/'output/route-results.json').write_text(json.dumps({'results':results,'added_items':len(new)},indent=2),encoding='utf8')
print('ROUTE_REPAIR_COMPLETE',len(new),collections.Counter(r['success'] for r in results),flush=True)
