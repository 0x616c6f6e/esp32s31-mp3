"""Build CH32V006 review candidate from the saved AT42 board, never overwrite it.
Run with KiCad Python; review and validate candidate before promotion.
"""
from pathlib import Path
import ast, copy, json, uuid, shutil, sys, hashlib, math, subprocess, xml.etree.ElementTree as ET
import pcbnew as p
ROOT=Path(__file__).resolve().parents[2]; P=ROOT/'hardware-controls'
sys.path.insert(0,str(ROOT/'tmp'))
from sexpr import parse, get, children, prop, dump, S
O=P/'output/ch32v006-review'; B=O/'before'; C=O/'candidate'
for d in [O,B,C]:d.mkdir(parents=True,exist_ok=True)
for name in ['controls.kicad_pcb','controls.kicad_sch','controls.kicad_pro','Controls.kicad_sym','README.md','output/design.json']:
    src=P/name; dst=B/name;dst.parent.mkdir(parents=True,exist_ok=True)
    if not dst.exists():shutil.copy2(src,dst)
for name in ['Controls.pretty','models3d']:
    if not (B/name).exists():shutil.copytree(P/name,B/name)
    shutil.copytree(P/name,C/name,dirs_exist_ok=True)
for name in ['controls.kicad_pro','fp-lib-table','sym-lib-table']:shutil.copy2(P/name,C/name)
old=parse((B/'controls.kicad_sch').read_text(encoding='utf8'))
oldpcb=parse((B/'controls.kicad_pcb').read_text(encoding='utf8'))
ns=uuid.UUID('c053e91b-11d7-4ec4-b4fd-226ca4c0f124')
uid=lambda name:str(uuid.uuid5(ns,name));q=lambda s:json.dumps(str(s),ensure_ascii=False)
rootid=get(old,'uuid')[1]; schema={};defs={};instances=[];wires=[];labels=[];ncs=[];annotations=[];components=[]
# Reuse only pure schematic helpers; do not execute historical board generator.
module=ast.parse((P/'scripts/build_design.py').read_text())
for fn in module.body:
    if isinstance(fn,ast.FunctionDef) and fn.name in ['libsymbol','add','note']:
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'<schematic helper>','exec'))
for sym in children(get(old,'lib_symbols'),'symbol'):
    name=str(sym[1]).split(':')[-1]
    if name in ['QT2120','TCA6408A','TestPoint']:continue
    pins=[]
    for sub in children(sym,'symbol'):
        for pin in children(sub,'pin'):
            xy=get(pin,'at');pins.append((str(get(pin,'number')[1]),str(get(pin,'name')[1]),float(xy[1]),float(xy[2]),float(xy[3]),pin[1],float(get(pin,'length')[1])))
    defs[name]=dump(sym);schema[name]={'pins':pins,'height':16.51 if name=='FPC12' else 5.08 if name=='Wheel' else 2.54}
pinout={0:'VSS_EP',1:'PD7/~{RST}',2:'PA1/TKEY1',3:'PA2/TKEY0',4:'VSS',5:'PD0',6:'VDD',7:'PC0/INT',8:'PC1/SDA',9:'PC2/SCL',10:'PC3',11:'PC4/TKEY2',12:'PC5',13:'PC6',14:'PC7',15:'PD1/SWIO',16:'PD2/TKEY3',17:'PD3/TKEY4',18:'PD4/TKEY7',19:'PD5/TKEY5',20:'PD6/TKEY6'}
pins=[]
for side,nums in [(-1,[16,17,18,6,4,0,1,15,2,3,5]),(1,[8,9,7,10,12,13,14,11,19,20])]:
    for i,n in enumerate(nums):
        typ='power_in' if n in [0,4,6] else 'input' if n==1 else 'bidirectional'
        pins.append((str(n),pinout[n],side*20.32,17.78-i*3.81,0 if side<0 else 180,typ,2.54))
libsymbol('CH32V006F8U6',pins,17.78,24.13)
libsymbol('SDI_4',[(str(i),name,-10.16,3.81-(i-1)*2.54,0,'passive',2.54) for i,name in enumerate(['VREF_3V3','SWIO','GND','RESET_N'],1)],7.62,6.35)
u_nets={'0':'GND','1':'RESET_N','4':'GND','6':'VDD_MCU','7':'INT_N','8':'SDA','9':'SCL','10':'KEY_BACK','12':'KEY_PREV','13':'KEY_NEXT','14':'KEY_PLAY','15':'SWIO','16':'SENSE0','17':'SENSE1','18':'SENSE2'}
url='https://www.wch.cn/downloads/CH32V006DS0_PDF.html'
add('U1','CH32V006F8U6','CH32V006F8U6',u_nets,(144.78,66.04),'CH32V006_QFN20',(8.3,29.5,'B',0),'QFN20 3x3 P0.4 EP1.9; hardware TKEY3/4/7; firmware required',url)
add('E1','Wheel','31mm INTERPOLATED WHEEL',{'1':'WHEEL0','2':'WHEEL1','3':'WHEEL2'},(25.4,45.72),'Wheel_D31',(22,17,'F',0),'Original 3-electrode geometry; covered copper, no paste')
fps={str(prop(f,'Reference')[2]):f for f in children(oldpcb,'footprint')}
def oldpos(ref):
    f=fps[ref];a=get(f,'at');return (float(a[1]),float(a[2]),'B' if get(f,'layer')[1]=='B.Cu' else 'F',float(a[3]) if len(a)>3 else 0)
for i in range(3):add('R'+str(i+1),'Resistor','1k',{'1':'WHEEL'+str(i),'2':'SENSE'+str(i)},(73.66,43.18+i*12.7),'R0402',oldpos('R'+str(i+1)),'0402 series resistor; initial 1k, tune charge timing on hardware')
for ref,net,y,schy in [('R4','SDA',25.2,38.1),('R5','SCL',26.7,53.34),('R6','INT_N',32.8,68.58),('R7','RESET_N',32.8,83.82)]:
    add(ref,'Resistor','4.7k' if ref in ['R4','R5'] else '10k',{'1':'+3V3','2':net},(238.76,schy),'R0402',(16 if ref=='R7' else 14,y,'B',0),'3.3 V pull-up; INT_N must be open-drain in firmware')
add('R8','Resistor','0R',{'1':'+3V3','2':'VDD_MCU'},(30.48,116.84),'R0402',(5.3,31.5,'B',0),'MCU supply link; replaces old 22R filter, do not fit 22R')
add('C1','Capacitor','100nF',{'1':'VDD_MCU','2':'GND'},(93.98,116.84),'C0402',(5.2,26.4,'B',0),'X7R 10 V, nearest U1.6 bypass')
add('C2','Capacitor','1uF',{'1':'VDD_MCU','2':'GND'},(157.48,116.84),'C0402',(4.9,29.7,'B',0),'X5R/X7R 10 V reservoir')
add('C3','Capacitor','100nF',{'1':'RESET_N','2':'GND'},(238.76,116.84),'C0402',(18,32.8,'B',0),'Reset RC with R7; configure PD7 as hardware reset in option bytes')
for i,name in enumerate(['POWER','BACK','PREV','NEXT','PLAY'],1):
    ref='SW'+str(i);add(ref,'Switch','SKSWCEE010',{'1':'KEY_'+name,'2':'GND'},(38.1+(i-1)*71.12,162.56),'SKSW_3x2',oldpos(ref),name+(' independent active-low POWER' if i==1 else ' CH32V006 input, active-low, firmware debounce'))
add('R14','Resistor','10k',{'1':'+3V3','2':'KEY_POWER'},(38.1,180.34),'R0402',oldpos('R14'),'POWER remains independent of MCU; released high, pressed low')
for i,name in enumerate(['BACK','PREV','NEXT','PLAY']):
    add('R'+str(i+9),'Resistor','47k',{'1':'+3V3','2':'KEY_'+name},(109.22+i*71.12,180.34),'R0402',([16,18,20,24][i],31,'B',90),'External GPIO pull-up; debounce in firmware')
jnet=['GND','+3V3','SDA','SCL','INT_N','RESET_N',None,None,None,None,'KEY_POWER','GND']
add('J1','FPC12','HC-FPC-05-10-12RLTAG',{**{str(i+1):n for i,n in enumerate(jnet) if n},'13':'GND','14':'GND'},(317.5,58.42),'HCTL_FPC12',oldpos('J1'),'Unchanged 12-pin 0.5mm mainboard interface; pins 7-10 NC')
add('J2','SDI_4','WCH_SDI_PADS',{'1':'VDD_MCU','2':'SWIO','3':'GND','4':'RESET_N'},(81.28,224.79),'SDI_4_Pads',(29,31.7,'B',0),'Bare pogo/solder pads, NO header to populate; 3.3 V WCH-Link single-wire SDI')
for i in range(1,5):
    ref='H'+str(i);add(ref,'MountingHole','M1.6 / NPTH 1.8',{},(157.48+(i-1)*50.8,226.06),'Mount_1.8',oldpos(ref),'Unchanged enclosure mounting position')
for i,n in enumerate(['+3V3','VDD_MCU','GND']):add('#FLG0'+str(i+1),'PowerFlag','PWR_FLAG',{'1':n},(297.18+i*35.56,116.84))
for text,x,y in [('01  CH32V006 / 3-ELECTRODE WHEEL',15.24,17.78),('02  MCU POWER / RESET',15.24,99.06),('03  FOUR GPIO KEYS + INDEPENDENT POWER',15.24,144.78),('04  SINGLE-WIRE SDI PROGRAMMING',15.24,203.2),('05  MECHANICAL MOUNTS',142.24,203.2)]:note(text,x,y,2.032)
note('3.3 V ONLY. J1 pinout and position unchanged.\nI2C target address 0x1C, CUSTOM register protocol.\nINT_N = PC0 open-drain output, active low.\nPD7/RST requires reset option-byte configuration.',289.56,91.44,1.27)
note('SW1 POWER is electrically independent of U1.\nR14 pull-up remains on +3V3; press shorts to GND.\nFour ordinary keys report through MCU I2C.',15.24,191.77,1.27)
note('J2 has bare pads only: VREF, SWIO, GND, RESET.\nKeep PD1 single-wire debug enabled.\nDo not fit the old AT42QT2120 or TCA6408A.',15.24,246.38,1.27)
note('PROTOTYPE: firmware and final-cover calibration required.\nMCU touch SDK includes wheel interpolation; validate circular wrap,\nnoise while charging and standby current before production.',157.48,259.08,1.27)
# Bare pads and fabricated electrode/mounts are not purchased components.
instances=[s.replace('(in_bom yes)','(in_bom no)') if '(reference "J2")' in s else s for s in instances]
sch=f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{rootid}") (paper "A3") (title_block (title "Q2 Controls - CH32V006 Wheel + Keys") (date "2026-09-22") (rev "C") (company "alon") (comment 1 "44 x 34 x 0.8 mm / CUSTOM I2C firmware required")) (lib_symbols '+''.join(defs.values())+')'+''.join(instances+wires+labels+ncs+annotations)+')\n'
(C/'controls.kicad_sch').write_text(sch,encoding='utf8')
(C/'Controls.kicad_sym').write_text('(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor") '+''.join(v.replace('"Controls:', '"') for v in defs.values())+')\n',encoding='utf8')
# Custom land pattern: datasheet QFN20 3x3, pitch .4, exposed pad 1.9.
# Rotate the datasheet top view clockwise to put pin 1 at upper left.
def pad(n,x,y,w,h,layers='"F.Cu" "F.Paste" "F.Mask"'):
    return f'(pad "{n}" smd rect (at {x} {y}) (size {w} {h}) (layers {layers}))'
def fp(name,pads,half,model=None,attr='smd'):
    return f'(footprint "{name}" (version 20250114) (generator "pcbnew") (layer "F.Cu") (attr {attr}) (property "Reference" "REF**" (at 0 {-half-1} 0) (layer "F.SilkS") (effects (font (size .8 .8) (thickness .1)))) (property "Value" "{name}" (at 0 {half+1} 0) (layer "F.Fab") (effects (font (size .8 .8) (thickness .1)))) (fp_rect (start {-half} {-half}) (end {half} {half}) (stroke (width .05) (type default)) (fill none) (layer "F.CrtYd")) '+''.join(pads)+(f'(model "${{KIPRJMOD}}/models3d/{model}.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))' if model else '')+')\n'
up=[]
for i in range(5):
    a=round(-.8+i*.4,3)
    up += [pad(1+i,-1.5,a,.55,.2),pad(6+i,a,1.5,.2,.55),pad(11+i,1.5,-a,.55,.2),pad(16+i,-a,-1.5,.2,.55)]
up += [pad(0,0,0,1.9,1.9,'"F.Cu" "F.Mask"')]
up += [pad('',x,y,.7,.7,'"F.Paste"') for x in [-.45,.45] for y in [-.45,.45]]
up += ['(fp_rect (start -1.5 -1.5) (end 1.5 1.5) (stroke (width .1) (type default)) (fill none) (layer "F.Fab"))','(fp_circle (center -1.85 -1.3) (end -1.8 -1.3) (stroke (width .1) (type default)) (fill solid) (layer "F.SilkS"))']
(C/'Controls.pretty/CH32V006_QFN20.kicad_mod').write_text(fp('CH32V006_QFN20',up,2,'CH32V006_QFN20'))
jp=[pad(i+1,x,y,1,1,'"F.Cu" "F.Mask"') for i,(x,y) in enumerate([(-.9,-.9),(.9,-.9),(-.9,.9),(.9,.9)])]
jp.append('(fp_circle (center -1.8 -0.9) (end -1.68 -0.9) (stroke (width 0.1) (type default)) (fill solid) (layer "F.SilkS"))')
(C/'Controls.pretty/SDI_4_Pads.kicad_mod').write_text(fp('SDI_4_Pads',jp,1.6,attr='exclude_from_pos_files exclude_from_bom'))
# Preserve exact custom electrode, enclosure geometry and existing wheel fanout.
keepnets={'/WHEEL0','/WHEEL1','/WHEEL2','/KEY_POWER'}
netmap={str(n[1]):str(n[2]) for n in children(oldpcb,'net')}
remove={'U1','U2','R13','C4'}
base=[]
for item in oldpcb:
    if isinstance(item,list):
        if item[0]=='zone':continue
        if item[0]=='footprint' and str(prop(item,'Reference')[2]) in remove:continue
        if item[0] in ['segment','via','arc']:
            net=netmap.get(str(get(item,'net')[1]),str(get(item,'net')[1]))
            points=[get(item,k) for k in (['at'] if item[0]=='via' else ['start','end'])]
            if net not in keepnets and (net in ['/VDD_TOUCH','/UNUSED_INPUTS'] or max(float(a[2]) for a in points)>24):continue
        if item[0]=='gr_text' and 'Q2 CTRL' in str(item[1]):item[1]=S('Q2 CTRL C')
    base.append(item)
(C/'controls.kicad_pcb').write_text(dump(base),encoding='utf8')
b=p.LoadBoard(str(C/'controls.kicad_pcb')); refs={f.GetReference():f for f in b.GetFootprints()}
newnets={}
for c in components:
    for num,pn,*_ in schema[c['kind']]['pins']:
        name='/'+c['nets'][num] if num in c['nets'] else f'unconnected-({c["ref"]}-{pn}-Pad{num})' if pn else f'unconnected-({c["ref"]}-Pad{num})'
        if name.startswith('unconnected-'):name=name.replace('/','{slash}')
        if name not in newnets:
            n=b.FindNet(name)
            if not n:n=p.NETINFO_ITEM(b,name);b.Add(n)
            newnets[name]=n
for c in components:
    ref=c['ref'];new=ref not in refs
    f=p.FootprintLoad(str(C/'Controls.pretty'),c['footprint']) if new else refs[ref]
    if new:b.Add(f);refs[ref]=f
    f.SetFPID(p.LIB_ID('Controls',c['footprint']));f.SetReference(ref);f.SetValue(c['value'])
    f.SetPath(p.KIID_PATH('/'+rootid+'/'+c['symbol_uuid']));f.SetSheetfile('controls.kicad_sch');f.SetSheetname('')
    f.SetField('Description',c['description']);f.SetField('Datasheet',c['datasheet'])
    x,y,side,angle=c['pcb'];f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
    if f.IsFlipped()!=(side=='B'):f.Flip(f.GetPosition(),p.FLIP_DIRECTION_LEFT_RIGHT)
    f.SetOrientationDegrees(angle)
    names={str(pin[0]):str(pin[1]) for pin in schema[c['kind']]['pins']}
    for a in f.Pads():
        num=a.GetNumber()
        if not num:continue
        pn=names.get(num,'');name='/'+c['nets'][num] if num in c['nets'] else f'unconnected-({ref}-{pn}-Pad{num})' if pn else f'unconnected-({ref}-Pad{num})'
        if name.startswith('unconnected-'):name=name.replace('/','{slash}')
        a.SetNet(newnets[name]);a.SetPinFunction(pn)
    f.Value().SetVisible(False)
    if new:f.Reference().SetVisible(False)
    if ref=='J2':f.SetAttributes(p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES)
# KiCad supplies canonical NC names (pin-name slash escaping and numeric suppression).
subprocess.run(['D:/KiCad/10.0/bin/kicad-cli.exe','sch','export','netlist','--format','kicadxml','-o',str(O/'netlist.xml'),str(C/'controls.kicad_sch')],check=True,stdout=subprocess.DEVNULL)
for net in ET.parse(O/'netlist.xml').findall('./nets/net'):
    name=net.attrib['name']
    # XML exports a literal slash; board parity uses the canonical escaped form.
    if name.startswith('unconnected-'):name=name.replace('/','{slash}')
    n=b.FindNet(name)
    if not n:n=p.NETINFO_ITEM(b,name);b.Add(n)
    for nd in net.findall('node'):
        for a in refs[nd.attrib['ref']].Pads():
            if a.GetNumber()==nd.attrib['pin']:a.SetNet(n)

# Validated short QFN escapes; global routing follows in a separate step.
V=lambda xy:p.VECTOR2I(p.FromMM(xy[0]),p.FromMM(xy[1]))
u=b.FindFootprintByReference('U1');pads={a.GetNumber():a for a in u.Pads()}
def route(pin,pts,via=True):
    a=pads[str(pin)];seq=[a.GetPosition()]+[V(xy) for xy in pts]
    for start,end in zip(seq,seq[1:]):
        t=p.PCB_TRACK(b);t.SetStart(start);t.SetEnd(end);t.SetWidth(p.FromMM(.15));t.SetLayer(p.B_Cu);t.SetNet(a.GetNet());b.Add(t)
    if via:
        v=p.PCB_VIA(b);v.SetPosition(seq[-1]);v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(a.GetNet());b.Add(v)
route(6,[(7.5,27.8),(6.4,26.8)])
route(7,[(7.9,27.4),(7.5,27.0)])
route(8,[(8.3,26.2)])
route(9,[(8.7,27.4),(9.1,27.0)])
route(10,[(9.8,28.0)])
route(12,[(10.25,29.1),(10.85,28.5)])
route(13,[(10.4,29.5),(10.8,29.1),(11.5,29.1)])
route(14,[(11.5,29.9)])
route(15,[(10.4,30.3),(10.8,30.7)])
route(16,[(9.1,31.1),(10.0,31.9)])
route(17,[(8.7,32.7)])
route(18,[(8.3,31.4),(7.8,31.9)])
route(1,[(6.3,30.3),(6,30.6)])
route(4,[(8.3,29.1)],False)
route(4,[(6.1,29.1)])

pro=(C/'controls.kicad_pro').read_bytes();p.SaveBoard(str(C/'controls.kicad_pcb'),b);(C/'controls.kicad_pro').write_bytes(pro)
(O/'design.json').write_text(json.dumps({'revision':'C','root_uuid':rootid,'components':components,'connector_pinout':jnet,'pinout':pinout,'mcu_nets':u_nets,'source_pcb_sha256':hashlib.sha256((B/'controls.kicad_pcb').read_bytes()).hexdigest()},indent=2),encoding='utf8')
print('Built candidate:',C,'parts',len(components),'preserved tracks',len(b.GetTracks()))
