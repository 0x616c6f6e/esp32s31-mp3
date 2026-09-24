from finish_grid import *
held=[]
for d in list(b.GetDrawings()):
 if isinstance(d,p.PCB_TEXT) and d.GetText() in {'Q2 V2','S31NRV16','ANT','LCD','BAT+','NTC','BAT-','M+','M-','CTRL','1','-'}:held.append(d);b.Remove(d)
items,cu,holes,ko,shapes=database();occupied={}
for l in [p.F_Cu,p.B_Cu]:
 occupied[l]=unary_union([shapes[u][l] for u,a in items.items() if isinstance(a,(p.PAD,p.PCB_VIA)) and l in shapes[u]]).buffer(.16)
log=[];taken={p.F_Cu:[],p.B_Cu:[]}
def label(text,x,y,side=p.F_Cu,radius=2):
 t=p.PCB_TEXT(b);t.SetText(text);t.SetTextSize(V((1,1)));t.SetTextThickness(p.FromMM(.15));t.SetLayer(p.F_SilkS if side==p.F_Cu else p.B_SilkS);t.SetMirrored(side==p.B_Cu)
 candidates=sorted([(math.hypot(dx,dy),x+dx,y+dy) for dx in np.arange(-radius,radius+.01,.25) for dy in np.arange(-radius,radius+.01,.25)])
 for _,X,Y in candidates:
  t.SetPosition(V((128.868+float(X),67.647+float(Y))));bb=t.GetBoundingBox();rect=box(p.ToMM(bb.GetX()),p.ToMM(bb.GetY()),p.ToMM(bb.GetRight()),p.ToMM(bb.GetBottom()))
  if occupied[side].intersects(rect) or not outline.buffer(-.3).contains(rect) or any(s.intersects(rect.buffer(.1)) for s in taken[side]):continue
  b.Add(t);taken[side].append(rect);log.append({'text':text,'side':'F' if side==p.F_Cu else 'B','xy':[float(X),float(Y)]});return
 print('NO LABEL SPACE',text,flush=True)
label('Q2 V2',24,35.8,radius=1)
label('S31NRV16',24,38,radius=1)
label('ANT',33.5,4,radius=1.5)
label('LCD',34,32.5,radius=1.5)
label('BAT+',40,55.132,radius=.75)
label('NTC',40,52.632,radius=.75)
label('BAT-',40,50.132,radius=.75)
label('M+',40.5,68.106,radius=.75)
label('M-',40.5,65.606,radius=.75)
label('CTRL',18.5,44,p.B_Cu,1)
label('1',22.7,46.5,p.B_Cu,.5)
label('BAT+',40,55.132,p.B_Cu,1)
label('NTC',40,52.632,p.B_Cu,1)
label('BAT-',40,50.132,p.B_Cu,1)
label('-',41.8,50.132,p.B_Cu,.5)
label('1',27,31.5,p.F_Cu,.75)
# The model is a nominal mechanical envelope, not a purchased crystal's tolerance model.
f=b.FindFootprintByReference('Y101')
if len(f.Models())==0:
 m=p.FP_3DMODEL();m.m_Filename='${KIPRJMOD}/models3d/Crystal_3225_H065_nominal.step';f.Models().push_back(m)
p.SaveBoard(str(fn),b);(P/'q2-v2.kicad_pro').write_bytes(pro)
(P/'output/markings.json').write_text(json.dumps(log,indent=2));print(log)
