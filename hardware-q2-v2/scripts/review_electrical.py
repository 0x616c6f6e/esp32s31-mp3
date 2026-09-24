"""Apply reviewed V2 electrical corrections and documented symbol pin types."""
from pathlib import Path
import json,sys,re
P=Path(__file__).resolve().parents[1];ROOT=P.parent
sys.path.insert(0,str(ROOT/'hardware-q2-v2-plan/scripts'));from sexpr import *
fn=P/'q2-v2.kicad_pcb';board=parse(fn.read_text(encoding='utf8'));fs={prop(f,'Reference')[2]:f for f in children(board,'footprint')}
contract=json.loads((P/'output/design-contract.json').read_text(encoding='utf8'));cs=contract['components'];changes=[]
def connect(ref,pin,n):
 old=cs[ref]['nets'][pin]
 for a in children(fs[ref],'pad'):
  if a[1]!=pin:continue
  a[:]=[z for z in a if not(isinstance(z,list) and z and z[0]=='net')]
  if n:a.append(['net',S(n)])
 cs[ref]['nets'][pin]=n
 if old!=n:changes.append({'ref':ref,'pin':pin,'old':old,'new':n})
# CS43131 DS1155F2 Table 1-1: QFN pin 1 SCL, 39 SDA. V1 PCB swapped these.
connect('U2','1','CS43131_SCL_1V8');connect('U2','39','CS43131_SDA_1V8')
# These named V1 nets have no external connection; represent explicitly as NC.
for ref,pins in [('U3',['2','3','4','12','24']),('U15',['9'])]:
 for n in pins:connect(ref,n,'')
typed={
 'U1':{'power_in':[1,7,8,10],'input':[2],'bidirectional':[3],'open_collector':[6],'power_out':[9]},
 'U2':{'power_in':[4,7,8,13,17,19,25,26,31,35,41],'input':[1,2,28,37,40],'bidirectional':[29,32,34,38,39],'output':[14,16,33,36],'open_collector':[27]},
 'U3':{'power_in':[1,17,18,25],'power_out':[15,16,22,23],'passive':[10,11,13,14,19,20,21],'input':[5,8,9,12],'bidirectional':[2,3,6],'open_collector':[4,7,24]},
 'U4':{'input':[1,5],'power_in':[2,4],'power_out':[3]},
 'U5':{'input':[3],'power_in':[1,2],'power_out':[5],'no_connect':[4]},
 'U6':{'input':[1,3],'power_in':[2,6],'output':[4,5]},
 'U7':{'power_in':[1,2],'passive':[7],'input':[8],'bidirectional':[3,4,5,6]},
 'U8':{'input':[1,2,4,5,9,10,12,13],'power_in':[7,14,15],'output':[3,6,8,11]},
 'U11':{'power_in':[6,8,10],'power_out':[1],'input':[2,4,5],'bidirectional':[3],'output':[7,9]},
 'U12':{'power_in':[1,2,3,9,17],'power_out':[6],'input':[5],'output':[4,12,13],'bidirectional':[7,8]},
 'U14':{'power_in':[5,9],'input':[3,8,10],'bidirectional':[2,7],'open_collector':[1],'passive':[6],'no_connect':[4]},
 'U15':{'power_in':[5,6,7,8],'input':[1,12,13],'bidirectional':[14],'output':[4,9],'passive':[2,3],'no_connect':[10,11]},
 'U17':{'power_in':[1,5],'input':[2,10],'passive':[3,4,6,7,8,9]},
}
for ref,types in typed.items():
 for pin,meta in cs[ref]['pins'].items():
  meta['type']=next((t for t,ns in types.items() if pin.isdigit() and int(pin) in ns),'passive')
# Track exact layout after collision resolution.
for ref,c in cs.items():
 at=get(fs[ref],'at');c['x']=round(float(at[1])-128.868,6);c['y']=round(float(at[2])-67.647,6);c['angle']=float(at[3]) if len(at)>3 else 0
contract['electrical_review_changes']=changes
(P/'output/design-contract.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2),encoding='utf8');fn.write_text(dump(board),encoding='utf8')
print('Electrical changes:',len(changes))
