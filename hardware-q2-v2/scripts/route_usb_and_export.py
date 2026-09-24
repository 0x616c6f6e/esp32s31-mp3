from pathlib import Path
import sys,json,math,collections
import pcbnew as p
P=Path(__file__).resolve().parents[1];ROOT=P.parent;sys.path.insert(0,str(ROOT/'hardware-q2-v2-plan/scripts'))
from sexpr import *
fn=P/'q2-v2.kicad_pcb';tree=parse(fn.read_text(encoding='utf8'))
# These retained V1 routes conflict with newly placed devices; reroute their nets.
badnets={'PWR_3V3_EN','N_2N16','BAT_TS','USB_HS_DP','USB_HS_DM'}
tree[:]=[a for a in tree if not(isinstance(a,list) and a and a[0] in ['segment','arc','via'] and (get(a,'net') or [None,None])[1] in badnets)]
fn.write_text(dump(tree),encoding='utf8')
b=p.LoadBoard(str(fn));pro=(P/'q2-v2.kicad_pro').read_bytes();nets={a.GetNetname():a for a in b.GetNetsByNetcode().values()};org=(128.868,67.647)
# Clear the entrance to the USB mux; retain nearby local bypass on the same face.
b.FindFootprintByReference('C51').SetPosition(p.VECTOR2I(p.FromMM(org[0]+27.4),p.FromMM(org[1]+59.2)))
V=lambda xy:p.VECTOR2I(p.FromMM(xy[0]+org[0]),p.FromMM(xy[1]+org[1]))
def pad(ref,num):return next(a for a in b.FindFootprintByReference(ref).Pads() if a.GetNumber()==num)
def xy(a):return (p.ToMM(a.GetPosition().x)-org[0],p.ToMM(a.GetPosition().y)-org[1])
def via(n,v):
 a=p.PCB_VIA(b);a.SetPosition(V(v));a.SetWidth(p.FromMM(.45));a.SetDrill(p.FromMM(.2));a.SetLayerPair(p.F_Cu,p.B_Cu);a.SetNet(nets[n]);b.Add(a)
def track(n,pts,layer,w=.15):
 for x,y in zip(pts,pts[1:]):
  a=p.PCB_TRACK(b);a.SetStart(V(x));a.SetEnd(V(y));a.SetLayer(layer);a.SetWidth(p.FromMM(w));a.SetNet(nets[n]);b.Add(a)
def length(pts):return sum(math.dist(a,z) for a,z in zip(pts,pts[1:]))
checks={}
for n,r,pn,lane in [('USB_HS_DP','R109','7',26.0),('USB_HS_DM','R108','6',26.4)]:
 start=xy(pad(r,'2'));end=xy(pad('U17',pn));a=(start[0],start[1]+.70);z=(end[0],end[1]-(1.20 if n.endswith('DP') else .70))
 v1=(lane,26.2);v2=(lane,z[1]-(lane-z[0]));v0=(a[0],26.2-(a[0]-lane))
 pts=[a,v0,v1,v2,z]
 track(n,[start,a],p.F_Cu);via(n,a);track(n,pts,p.In3_Cu);via(n,z);track(n,[z,end],b.FindFootprintByReference('U17').GetLayer())
 checks[n]={'length_mm':length([start,a])+length(pts)+length([z,end]),'vias':2,'layer':'In3.Cu','width_mm':.15,'lane_pitch_mm':.4}
for a in b.GetTracks():
 if isinstance(a,p.PCB_VIA) and a.GetWidth(p.F_Cu)<p.FromMM(.45):a.SetWidth(p.FromMM(.45));a.SetDrill(p.FromMM(.2))
p.SaveBoard(str(fn),b);(P/'q2-v2.kicad_pro').write_bytes(pro)
checks['length_skew_mm']=abs(checks['USB_HS_DP']['length_mm']-checks['USB_HS_DM']['length_mm']);checks['impedance']='NOT VERIFIED: supplier stackup and field-solver width/gap required'
(P/'output/usb-routing.json').write_text(json.dumps(checks,indent=2))
p.ExportSpecctraDSN(b,str(P/'output/native.dsn'))
t=parse((P/'output/native.dsn').read_text().replace('(string_quote ")','(string_quote QUOTE)'));st=get(t,'structure');network=get(t,'network')
for cls in [st]+children(network,'class'):
 for rule in list(children(cls,'rule')):cls.remove(rule)
 cls.append(['rule',['width','150'],['clearance','100'],['clearance','100',['type','smd_smd']]])
settings=['autoroute_settings',['fanout','on'],['autoroute','on'],['postroute','on']]
for i,la in enumerate(children(st,'layer')):settings.append(['layer_rule',la[1],['active','off' if i in [1,4] else 'on'],['preferred_direction','horizontal' if i%2==0 else 'vertical']])
st.append(settings)
power={'VBAT','GBAT','VBUS_5V','VCC','VCC_3V3','VCC_PMID','VCC_1V8','MCU_1V8','MCU_VDD_SPI','MCU_VDDA34','VCC_3V3_AON','MOTOR_OUT_P','MOTOR_OUT_N','N_5N15'}
for cls in children(network,'class'):cls[:]=[a for a in cls if not(isinstance(a,str) and a in power)]
network.append(['class','v2_power',*sorted(power),['circuit',['use_via',S('Via[0-5]_450:200_um')]],['rule',['width','300'],['clearance','100']]])
for item in get(t,'wiring')[1:]:
 if isinstance(item,list) and item[0] in ['wire','via']:
  item[:]=[a for a in item if not(isinstance(a,list) and a and a[0]=='type')];item.append(['type','protect'])
(P/'output/routing.dsn').write_text(dump(t).replace('(string_quote QUOTE)','(string_quote ")'),encoding='utf8')
# Disable networking/telemetry; run local command-line router only.
(P/'output/router-userdata').mkdir(exist_ok=True)
cfg={'version':'2.4.1','profile':{'id':'f769856a-f58a-4899-b7d9-ccf4428d2d70','allow_telemetry':False,'allow_contact':False},'gui':{'enabled':False},'api_server':{'enabled':False},'mcp_server':{'enabled':False},'usage_and_diagnostic_data':{'disable_analytics':True},'router':{'max_passes':20,'optimizer':{'max_threads':1}}}
(P/'output/router-userdata/freerouting.json').write_text(json.dumps(cfg))
print(json.dumps(checks,indent=2))


