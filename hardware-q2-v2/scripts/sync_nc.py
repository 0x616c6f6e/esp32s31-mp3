from pathlib import Path
import pcbnew as p,xml.etree.ElementTree as E
P=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(P/'q2-v2.kicad_pcb'));pro=(P/'q2-v2.kicad_pro').read_bytes();x=E.parse(P/'output/v2-netlist.xml').getroot();count=0
for n in x.find('nets'):
 name=n.attrib['name'].replace('/','{slash}')
 if not name.startswith('unconnected-'):continue
 net=b.FindNet(name)
 if net is None:net=p.NETINFO_ITEM(b,name);b.Add(net)
 for node in n.findall('node'):
  f=b.FindFootprintByReference(node.attrib['ref'])
  for a in f.Pads():
   if a.GetNumber()==node.attrib['pin']:a.SetNet(net);count+=1
p.SaveBoard(str(P/'q2-v2.kicad_pcb'),b);(P/'q2-v2.kicad_pro').write_bytes(pro);print('Synchronized explicit NC pad nets',count)
