"""One-shot conversion of the routed review candidate to a 0402 power-only layout.

Run only against the original 2026-09-24 candidate. Native DRC and power-net
connectivity checks are required after the conversion and routing completion.
"""
from pathlib import Path
import sys,json,math,collections
import pcbnew as p
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'tmp/v2-kicad-deps'))
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from shapely import affinity
fn=P/'q2-v2.kicad_pcb';b=p.LoadBoard(str(fn));pro=(P/'q2-v2.kicad_pro').read_bytes()
origin=(128.868,67.647)
V=lambda x,y:p.VECTOR2I(p.FromMM(float(x)),p.FromMM(float(y)))
xy=lambda f:(p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y))
rails=['GND','GBAT','VBUS_5V','VBAT','VCC','VCC_PMID','VCC_3V3','VCC_3V3_AON','VCC_1V8','MCU_1V8','MCU_VDD_SPI','MCU_VDDA34']
local_power={
 'N_2N13':'BQ25895 bootstrap','N_2N14':'BQ25895 switch node',
 'N_2N16':'BQ25895 REGN','N_2N19':'BQ25895 input current limit resistor',
 'N_2N84':'TLV62568 switch node','N_2N86':'TLV62568 feedback',
 'N_3N20':'CS43131 negative analog supply','N_3N22':'CS43131 flying capacitor',
 'N_3N23':'CS43131 flying capacitor','N_3N24':'CS43131 flying capacitor',
 'N_3N25':'CS43131 negative charge pump filter','N_3N26':'CS43131 positive charge pump filter',
 'N_3N29':'CS43131 flying capacitor','N_3N30':'CS43131 flying capacitor',
 'N_3N32':'CS43131 negative reference filter','N_3N34':'CS43131 positive reference filter',
 'N_3N63':'PCA9306 reference bias','N_5N15':'DRV2605 supply',
 'N_5N6':'DRV2605 regulator bypass','MOTOR_OUT_P':'motor load power',
 'MOTOR_OUT_N':'motor load power','N_6N67':'CH343 regulator bypass','N_7N55':'RTC regulator bypass'}
keep=set(rails)|set(local_power)
targets=[]
for f in b.GetFootprints():
 pads=list(f.Pads());ref=f.GetReference()
 if len(pads)==2 and (ref.startswith(('R','C')) or ref=='L105'):
  if math.dist(xy(pads[0]),xy(pads[1]))<.65:targets.append(ref)
assert targets,'No 0201 resistors/capacitors remain; refusing to repeat conversion'
archive=P/'output/archive/pre-0402-power-only';archive.mkdir(parents=True,exist_ok=True)
for name in ['q2-v2.kicad_pcb','q2-v2.kicad_pro']:(archive/name).write_bytes((P/name).read_bytes())
removed=[];removed_counts=collections.Counter()
for t in list(b.GetTracks()):
 if t.GetNetname() not in keep:
  removed_counts['signal_vias' if isinstance(t,p.PCB_VIA) else 'signal_segments']+=1
  removed.append(t);b.Remove(t)
# Rebuild local core power fanout after the larger parts are placed. Keep the
# central 5x5 QFN thermal-via array and the main distribution outside this area.
for t in list(b.GetTracks()):
 pts=[xy(t)] if isinstance(t,p.PCB_VIA) else [(p.ToMM(t.GetStart().x),p.ToMM(t.GetStart().y)),(p.ToMM(t.GetEnd().x),p.ToMM(t.GetEnd().y))]
 local=all(148<x<170 and 72<y<93 for x,y in pts)
 thermal=isinstance(t,p.PCB_VIA) and t.GetNetname()=='GND' and 156.3<pts[0][0]<161.5 and 82<pts[0][1]<87.3
 if local and not thermal:removed_counts['local_power_items_rebuilt']+=1;removed.append(t);b.Remove(t)
changes=[];newfps=[];uuid_map={}
for ref in sorted(targets):
 old=b.FindFootprintByReference(ref);family='Capacitor' if ref.startswith('C') else 'Resistor';prefix='C' if ref.startswith('C') else 'R'
 name=f'{prefix}_0402_1005Metric'
 f=p.FootprintLoad(f'D:/KiCad/10.0/share/kicad/footprints/{family}_SMD.pretty',name)
 f.SetReference(ref);f.SetValue(old.GetValue());uuid_map[f.m_Uuid.AsString()]=old.m_Uuid.AsString()
 f.SetFPID(old.GetFPID());f.SetPath(old.GetPath());f.SetSheetname(old.GetSheetname());f.SetSheetfile(old.GetSheetfile());f.SetDNP(old.IsDNP())
 nets={a.GetNumber():a.GetNet() for a in old.Pads()};uids={a.GetNumber():a.m_Uuid for a in old.Pads()}
 f.SetPosition(old.GetPosition());f.SetOrientationDegrees(old.GetOrientationDegrees())
 if old.IsFlipped():f.Flip(f.GetPosition(),p.FLIP_DIRECTION_LEFT_RIGHT)
 for a in f.Pads():a.SetNet(nets[a.GetNumber()]);uuid_map[a.m_Uuid.AsString()]=uids[a.GetNumber()].AsString()
 f.Reference().SetVisible(False);f.Value().SetVisible(False)
 changes.append({'ref':ref,'value':f.GetValue(),'old_position':list(xy(old)),'standard_footprint':family+'_SMD:'+name})
 removed.append(old);b.Remove(old);b.Add(f);newfps.append(f)

def physical(f):
 shapes=[]
 for a in f.Pads():
  bb=a.GetBoundingBox();shapes.append(box(p.ToMM(bb.GetX()),p.ToMM(bb.GetY()),p.ToMM(bb.GetRight()),p.ToMM(bb.GetBottom())))
 geom=unary_union(shapes).convex_hull
 f.BuildCourtyardCaches();cy=f.GetCourtyard(f.GetLayer())
 if cy and cy.OutlineCount():
  line=cy.COutline(0);geom=geom.union(Polygon([(p.ToMM(line.CPoint(j).x),p.ToMM(line.CPoint(j).y)) for j in range(line.PointCount())]))
 return geom.buffer(.08)
outline=affinity.translate(Polygon(json.loads((P.parent/'hardware-q2-v2-plan/outline.json').read_text())[0]),*origin).buffer(-.35)
occupied=[(physical(f),f.GetLayer()) for f in b.GetFootprints() if f.GetReference() not in targets]
# Place bypass capacitors first; all replacements remain on their original side.
for f in sorted(newfps,key=lambda f:(not f.GetReference().startswith('C'),f.GetReference())):
 geom=physical(f);ox,oy=xy(f);obstacles=[g for g,l in occupied if l==f.GetLayer()]
 candidates=sorted((dx*dx+dy*dy,dx*.2,dy*.2) for dx in range(-35,36) for dy in range(-35,36))
 for _,dx,dy in candidates:
  g=affinity.translate(geom,dx,dy)
  if outline.contains(g) and all(not g.intersects(o) for o in obstacles):
   f.SetPosition(V(ox+dx,oy+dy));occupied.append((g,f.GetLayer()));break
 else:raise RuntimeError('No location for '+f.GetReference())
 change=next(c for c in changes if c['ref']==f.GetReference());change['new_position']=list(xy(f));change['angle']=f.GetOrientationDegrees()
 # Write the matching project-local footprint, without modifying unrelated libs.
 libfp=p.FOOTPRINT(f);libfp.SetOrientationDegrees(0);libfp.SetPosition(V(0,0))
 for a in libfp.Pads():a.SetNetCode(0)
 p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(P/'V2.pretty'),libfp)

contract=json.loads((P/'output/design-contract.json').read_text(encoding='utf8'))
for f in newfps:
 c=contract['components'][f.GetReference()];x,y=xy(f);c.update(x=x-origin[0],y=y-origin[1],angle=f.GetOrientationDegrees(),package='0402 (1005 metric)')
contract['status']='POWER_ONLY_0402_MANUAL_SIGNAL_ROUTING_REQUIRED'
(P/'output/design-contract.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2),encoding='utf8')
report={'status':contract['status'],'rails':rails,'local_power_nodes':local_power,'removed':dict(removed_counts),'package_changes':changes,'signal_routing_policy':'Remove every track and via not in rails/local_power_nodes. Ground and supply copper zones retained.','audio_ground':'Common GND plane; HPREFA/HPREFB require independent Kelvin routes to headphone ground before fabrication.'}
(P/'power-only-0402.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(fn),b);(P/'q2-v2.kicad_pro').write_bytes(pro)
text=fn.read_text(encoding='utf8')
for new,old in uuid_map.items():text=text.replace(new,old)
fn.write_text(text,encoding='utf8')
print(json.dumps({'replaced':len(changes),'removed':dict(removed_counts),'positions':changes},indent=2))
