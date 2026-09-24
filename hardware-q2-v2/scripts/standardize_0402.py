"""Unify 0402 land patterns and schematic links using two local KiCad footprints.

Preserve pad numbering, connectivity, UUIDs, side and physical pad-1 direction.
Run native DRC and repair any changed pad/track clearances afterwards.
"""
from pathlib import Path
import pcbnew as p,json,math,re
P=Path(__file__).resolve().parents[1];fn=P/'q2-v2.kicad_pcb'
b=p.LoadBoard(str(fn));pro=(P/'q2-v2.kicad_pro').read_bytes()
V=lambda x,y:p.VECTOR2I(p.FromMM(float(x)),p.FromMM(float(y)))
xy=lambda v:[p.ToMM(v.x),p.ToMM(v.y)]
templates={};plugin=p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP)
for kind,family in [('R','Resistor'),('C','Capacitor')]:
 name=f'{kind}_0402_1005Metric'
 f=p.FootprintLoad(f'D:/KiCad/10.0/share/kicad/footprints/{family}_SMD.pretty',name)
 f.SetFPIDAsString('V2:'+name);plugin.FootprintSave(str(P/'V2.pretty'),f);templates[kind]=f

def signature(f):
 a={x.GetNumber():x for x in f.Pads()};d=a['2'].GetPosition()-a['1'].GetPosition()
 return {'pitch_mm':round(math.hypot(d.x,d.y)/1e6,4),
 'pad_size_mm':{k:xy(v.GetSize()) for k,v in a.items()},
 'pad_shapes':{k:int(v.GetShape()) for k,v in a.items()},
 'models':[m.m_Filename for m in f.Models()]}

changes=[];mapping={};uuids={};held=[]
for old in list(b.GetFootprints()):
 ref=old.GetReference()
 if not(re.fullmatch('[RC][0-9]+',ref) or ref=='L105'):continue
 pads={a.GetNumber():a for a in old.Pads()}
 if set(pads)!={'1','2'}:continue
 before=signature(old)
 if not .65<before['pitch_mm']<1.2:continue
 kind='C' if ref.startswith('C') else 'R';family='Capacitor' if kind=='C' else 'Resistor'
 f=p.FootprintLoad(f'D:/KiCad/10.0/share/kicad/footprints/{family}_SMD.pretty',f'{kind}_0402_1005Metric')
 f.SetFPIDAsString(templates[kind].GetFPIDAsString())
 oldid=old.GetFPIDAsString();newid=templates[kind].GetFPIDAsString();mapping[oldid]=newid
 f.SetReference(ref);f.SetValue(old.GetValue());f.SetPath(old.GetPath())
 f.SetSheetname(old.GetSheetname());f.SetSheetfile(old.GetSheetfile());f.SetDNP(old.IsDNP())
 f.SetPosition(V(*xy(old.GetPosition())))
 b.Add(f)
 if old.IsFlipped():f.Flip(f.GetPosition(),p.FLIP_DIRECTION_LEFT_RIGHT)
 newpads={a.GetNumber():a for a in f.Pads()}
 od=pads['2'].GetPosition()-pads['1'].GetPosition();nd=newpads['2'].GetPosition()-newpads['1'].GetPosition()
 angle=math.degrees(math.atan2(nd.y,nd.x)-math.atan2(od.y,od.x))
 f.Rotate(f.GetPosition(),p.EDA_ANGLE(angle,p.DEGREES_T))
 uuids[f.m_Uuid.AsString()]=old.m_Uuid.AsString()
 for n,a in newpads.items():a.SetNet(pads[n].GetNet());uuids[a.m_Uuid.AsString()]=pads[n].m_Uuid.AsString()
 # Match the old land-pattern centre even for imported offset origins.
 oc=(pads['1'].GetPosition()+pads['2'].GetPosition())/2
 nc=(newpads['1'].GetPosition()+newpads['2'].GetPosition())/2
 f.Move(oc-nc)
 nd=newpads['2'].GetPosition()-newpads['1'].GetPosition()
 assert (od.x*nd.x+od.y*nd.y)>0 and abs(od.x*nd.y-od.y*nd.x)<4e6,ref
 f.Reference().SetVisible(False);f.Value().SetVisible(False)
 changes.append({'ref':ref,'old_library_id':oldid,'library_id':newid,'before':before,'after':signature(f),'position_mm':xy(f.GetPosition()),'angle_deg':f.GetOrientationDegrees(),'side':'B' if f.IsFlipped() else 'F'})
 held.append(old);b.Remove(old)

assert changes
print('Replaced',len(changes),'footprints; refilling zones',flush=True)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(fn),b);(P/'q2-v2.kicad_pro').write_bytes(pro)
s=fn.read_text(encoding='utf8')
for new,old in uuids.items():s=s.replace(new,old)
fn.write_text(s,encoding='utf8')
# Exact quoted IDs only: no electrical or diagram changes.
for f in list(P.glob('*.kicad_sch'))+[P/'V2.kicad_sym']:
 s=f.read_text(encoding='utf8');old=s
 for a,z in mapping.items():s=s.replace('"'+a+'"','"'+z+'"')
 if s!=old:f.write_text(s,encoding='utf8')
contract=json.loads((P/'output/design-contract.json').read_text(encoding='utf8'))
for c in changes:
 d=contract['components'][c['ref']];d.update(footprint=c['library_id'].split(':')[1],package='0402 (1005 metric)',x=c['position_mm'][0]-128.868,y=c['position_mm'][1]-67.647,angle=c['angle_deg'])
(P/'output/design-contract.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2),encoding='utf8')
# Remove only obsolete per-reference footprints no longer used by this board.
used={f.GetFPIDAsString() for f in b.GetFootprints()}
for old in mapping:
 if old not in used and old.startswith('V2:FP_'):
  f=P/'V2.pretty'/(old.split(':')[1]+'.kicad_mod')
  if f.is_file():f.unlink()
report={'standard':'KiCad 10 IPC nominal-density 0402 (1005 metric), separate R/C land patterns','components':changes,'count':len(changes)}
(P/'0402-standardization.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('Unified',len(changes),'footprints; R',sum(c['library_id'].startswith('V2:R_') for c in changes),'C',sum(c['library_id'].startswith('V2:C_') for c in changes),flush=True)
