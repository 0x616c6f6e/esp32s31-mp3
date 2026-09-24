"""Preserve applicable proven local connections and export constrained routing input."""
from pathlib import Path
import pcbnew as p,json,sys,collections,math
P=Path(__file__).resolve().parents[1];ROOT=P.parent
sys.path.insert(0,str(ROOT/'hardware-q2-v2-plan/scripts'));from sexpr import parse,dump,children,get,S
fn=P/'q2-v2.kicad_pcb';pro=(P/'q2-v2.kicad_pro').read_bytes();b=p.LoadBoard(str(fn))
assert not b.GetTracks(),'Routing already exists; do not overwrite'
src=p.LoadBoard(str(ROOT/'hardware-q2/ProPrj_esp32s31-mp4_2026-09-22.kicad_pcb'))
dstfs={f.GetReference():f for f in b.GetFootprints()};srcfs={f.GetReference():f for f in src.GetFootprints()};nets={n.GetNetname():n for n in b.GetNetsByNetcode().values()}
oldnodes=collections.defaultdict(list)
for f in src.GetFootprints():
 for a in f.Pads():
  if a.GetNetname():oldnodes[a.GetNetname()].append((f,a))
recover={}
for name,nodes in oldnodes.items():
 if name=='GND' or len(nodes)<2:continue
 shifts=[];newnames=set();ok=True
 for f,a in nodes:
  target=dstfs.get(f.GetReference())
  if not target:ok=False;break
  pads=[x for x in target.Pads() if x.GetNumber()==a.GetNumber()]
  if not pads or target.GetLayer()!=f.GetLayer() or abs(target.GetOrientationDegrees()-f.GetOrientationDegrees())>.01:ok=False;break
  q=pads[0];newnames.add(q.GetNetname());v=q.GetPosition()-a.GetPosition();shifts.append((v.x,v.y))
 if ok and len(newnames)==1 and '' not in newnames and max(abs(x-shifts[0][0])+abs(y-shifts[0][1]) for x,y in shifts)<10:
  recover[name]=(next(iter(newnames)),shifts[0])
count=0
for t in src.GetTracks():
 if t.GetNetname() not in recover:continue
 newname,(dx,dy)=recover[t.GetNetname()]
 t2=t.Duplicate();b.Add(t2);t2.Move(p.VECTOR2I(dx,dy));t2.SetNet(nets[newname]);count+=1
# Preserve official short RF, crystal and PSRAM local copper (only where all
# mapped local footprint coordinates are unchanged by collision cleanup).
refb=p.LoadBoard(str(P/'reference/core-reference.kicad_pcb'));core=refb.FindFootprintByReference('U1');center=core.GetPosition();dest=dstfs['U9'].GetPosition();delta=-90-core.GetOrientationDegrees()
mapping={'ANT':'RF_CHIP','RF':'RF_STAGE1','RF1':'RF_STAGE2','XTAL_N':'XTAL_N','XTAL_P':'XTAL_P','N20805524':'MCU_XTAL_P','VDD_LDO_1P8':'MCU_1V8','N20805107':'MCU_VDDA34'}
localcount=0
for t in refb.GetTracks():
 n=t.GetNetname()
 if n not in mapping:continue
 # Paths to module pins can share XTAL/GPIO nets; constrain to actual local core.
 t2=t.Duplicate();t2.Rotate(center,p.EDA_ANGLE(delta));t2.Move(dest-center)
 ps=[t2.GetStart(),t2.GetEnd()]
 if not all(128.868+18<p.ToMM(v.x)<128.868+43 and 67.647+5<p.ToMM(v.y)<67.647+30 for v in ps):continue
 b.Add(t2);t2.SetNet(nets[mapping[n]]);localcount+=1
# Reference vias under the thermal pad: through via / back mask tented.
for dx in [-2.4,-1.2,0,1.2,2.4]:
 for dy in [-2.4,-1.2,0,1.2,2.4]:
  v=p.PCB_VIA(b);v.SetPosition(dest+p.VECTOR2I(p.FromMM(dx),p.FromMM(dy)));v.SetWidth(p.FromMM(.45));v.SetDrill(p.FromMM(.2));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(nets['GND']);b.Add(v)
p.SaveBoard(str(fn),b);(P/'q2-v2.kicad_pro').write_bytes(pro)
# Refresh library after deliberate mechanical-hole and assembly-layer edits.
plugin=p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP)
for f in b.GetFootprints():plugin.FootprintSave(str(P/'V2.pretty'),f)
p.ExportSpecctraDSN(b,str(P/'output/native.dsn'))
tree=parse((P/'output/native.dsn').read_text().replace('(string_quote ")','(string_quote QUOTE)'))
st=get(tree,'structure');network=get(tree,'network')
for cls in [st]+children(network,'class'):
 for rule in list(children(cls,'rule')):cls.remove(rule)
 cls.append(['rule',['width','150'],['clearance','100'],['clearance','100',['type','smd_smd']]])
# Keep two ground reference layers free of signal routing.
settings=['autoroute_settings',['fanout','on'],['autoroute','on'],['postroute','on']]
for index,la in enumerate(children(st,'layer')):
 lname=la[1];settings.append(['layer_rule',lname,['active','off' if str(lname) in ['In1.Cu','In4.Cu'] else 'on'],['preferred_direction','horizontal' if index%2==0 else 'vertical']])
st.append(settings)
# Existing local copper is protected in the routing session.
for item in get(tree,'wiring')[1:]:
 if isinstance(item,list) and item[0] in ['wire','via']:
  item[:]=[a for a in item if not(isinstance(a,list) and a and a[0]=='type')];item.append(['type','protect'])
(P/'output/routing.dsn').write_text(dump(tree).replace('(string_quote QUOTE)','(string_quote ")'),encoding='utf8')
(P/'output/retained-routing.json').write_text(json.dumps({'source_nets':recover,'source_tracks':count,'official_local_tracks':localcount,'thermal_vias':25},indent=2))
print('Retained original:',count,'official local:',localcount,'DSN ready',flush=True)
