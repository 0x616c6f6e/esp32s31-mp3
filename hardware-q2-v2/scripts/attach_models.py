from pathlib import Path
import pcbnew as p,shutil,json,re,sys
P=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(P/'q2-v2.kicad_pcb'));pro=(P/'q2-v2.kicad_pro').read_bytes();log=[]
def attach(f,path):
 m=p.FP_3DMODEL();m.m_Filename=path;f.Models().push_back(m)
if len(b.FindFootprintByReference('U9').Models())==0:attach(b.FindFootprintByReference('U9'),'${KIPRJMOD}/models3d/ESP32-S31_QFN80_8x8.step')
b.FindFootprintByReference('CN3').Models().clear()
for f in b.GetFootprints():
 for m in f.Models():
  s=m.m_Filename
  if '${KIPRJMOD}/../' in s:
   source=Path(s.replace('${KIPRJMOD}',str(P))).resolve();target=P/'models3d'/source.name
   if source.exists():
    if source!=target:shutil.copy2(source,target)
    m.m_Filename='${KIPRJMOD}/models3d/'+target.name
 # Imported module passives get generic body models based on the actual pad spacing.
 ref=f.GetReference();pads=list(f.Pads())
 if len(f.Models())==0 and len(pads)==2 and re.match(r'^[RCL]\d',ref):
  dx=p.ToMM(pads[0].GetPosition().x-pads[1].GetPosition().x);dy=p.ToMM(pads[0].GetPosition().y-pads[1].GetPosition().y);pitch=(dx*dx+dy*dy)**.5
  size='0201_0603' if pitch<.65 else '0402_1005' if pitch<1.2 else '0603_1608'
  family={'R':'Resistor','C':'Capacitor','L':'Inductor'}[ref[0]];name=f'{family}_SMD.3dshapes/{ref[0]}_{size}Metric.step'
  if (Path('D:/KiCad/10.0/share/kicad/3dmodels')/name).exists():attach(f,'${KICAD10_3DMODEL_DIR}/'+name);log.append({'ref':ref,'model':name,'scope':'generic body; verify supplier package height'})
p.SaveBoard(str(P/'q2-v2.kicad_pcb'),b);(P/'q2-v2.kicad_pro').write_bytes(pro)
# SWIG vector iteration returns model value copies, so normalize paths in the saved file.
sys.path.insert(0,str(P.parent/'hardware-q2-v2-plan/scripts'));from sexpr import parse,dump,children,get,S
fn=P/'q2-v2.kicad_pcb';t=parse(fn.read_text(encoding='utf8'))
for f in children(t,'footprint'):
 for m in children(f,'model'):
  if '${KIPRJMOD}/../' in m[1]:
   source=Path(m[1].replace('${KIPRJMOD}',str(P))).resolve();target=P/'models3d'/source.name
   if source.exists():
    if source!=target:shutil.copy2(source,target)
    m[1]=S('${KIPRJMOD}/models3d/'+target.name)
fn.write_text(dump(t),encoding='utf8')
(P/'output/model-audit.json').write_text(json.dumps({'generic_models':log,'without_models':[f.GetReference() for f in b.GetFootprints() if len(f.Models())==0]},indent=2))
print('Models missing:',[f.GetReference() for f in b.GetFootprints() if len(f.Models())==0])
