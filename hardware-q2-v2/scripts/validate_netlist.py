from pathlib import Path
import pcbnew as p,xml.etree.ElementTree as ET,json,hashlib,collections
P=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(P/'q2-v2.kicad_pcb'));xml=ET.parse(P/'output/v2-netlist.xml').getroot()
expected={}
for n in xml.find('nets'):
 name=n.attrib['name']
 for node in n.findall('node'):expected[(node.attrib['ref'],node.attrib['pin'])]=name
errors=[];actual={};refs=set()
for f in b.GetFootprints():
 refs.add(f.GetReference())
 for a in f.Pads():
  if not a.GetNumber():continue
  key=(f.GetReference(),a.GetNumber());n=a.GetNetname();e=expected.get(key,'')
  if e.startswith('unconnected-'):e=''
  if n.startswith('unconnected-'):n=''
  actual[key]=n
  if n!=e:errors.append({'ref':key[0],'pin':key[1],'pcb':n,'schematic':e})
for key,e in expected.items():
 if key not in actual and not e.startswith('unconnected-'):errors.append({'missing_pcb_pin':key,'schematic':e})
schrefs={c.attrib['ref'] for c in xml.find('components') if not c.attrib['ref'].startswith('#')}
source=P.parent/'hardware-q2/ProPrj_esp32s31-mp4_2026-09-22.kicad_pcb'
sourcehash=hashlib.sha256(source.read_bytes()).hexdigest()
out={'component_count':len(refs),'unique_numbered_pads':len(actual),'net_mismatches':errors,'pcb_only_refs':sorted(refs-schrefs),'schematic_only_refs':sorted(schrefs-refs),'v1_sha256':sourcehash,'v1_unchanged':sourcehash=='7b2c5f1ed64687aac5a914b5cf3baac07e9dedfb0c56e9c651b8901a608ac4d9'}
(P/'output/netlist-consistency.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(out,ensure_ascii=False,indent=2))
assert not errors and refs==schrefs and out['v1_unchanged']
