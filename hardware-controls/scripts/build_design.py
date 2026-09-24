"""Create the standalone controls schematic, local libraries and unrouted PCB.
Run with KiCad 10 Python after make_electrodes.py. Refuses to replace routed work.
"""
from pathlib import Path
import json,uuid,math,shutil,re,csv
import pcbnew as p
P=Path(__file__).resolve().parents[1];ROOT=P.parent
LIB=Path('D:/KiCad/10.0/share/kicad');ns=uuid.UUID('c053e91b-11d7-4ec4-b4fd-226ca4c0f124')
uid=lambda name:str(uuid.uuid5(ns,name));q=lambda s:json.dumps(str(s),ensure_ascii=False)
rootid=uid('controls-root');boardfile=P/'controls.kicad_pcb'
if boardfile.exists():assert not p.LoadBoard(str(boardfile)).GetTracks(),'Do not overwrite routed work'
V=lambda x,y:p.VECTOR2I(round(x*1e6),round(y*1e6))
schema={};defs={};instances=[];wires=[];labels=[];ncs=[];annotations=[]
def libsymbol(name,pins,w=7.62,h=5.08,kind='box'):
    body=f'(rectangle (start {-w} {h}) (end {w} {-h}) (stroke (width 0.254) (type default)) (fill (type background)))'
    if kind=='R':body='(rectangle (start -2.54 1.016) (end 2.54 -1.016) (stroke (width .254) (type default)) (fill (type none)))'
    if kind=='C':body=''.join(f'(polyline (pts (xy {x} -2.54) (xy {x} 2.54)) (stroke (width .254) (type default)) (fill (type none)))' for x in [-.508,.508])
    if kind=='SW':body='(polyline (pts (xy -2.54 0) (xy 2.54 2.032)) (stroke (width .254) (type default)) (fill (type none)))'
    if kind=='TP':body='(circle (center 0 0) (radius 1.016) (stroke (width .254) (type default)) (fill (type none)))'
    prefix='U' if name in ['QT2120','TCA6408A'] else name[0]
    props=''.join(f'(property {q(k)} {q(v)} (at 0 {y} 0) (effects (font (size 1.27 1.27)){hide}))' for k,v,y,hide in [('Reference',prefix, h+3.81,''),('Value',name,h+1.27,''),('Footprint','',0,' hide'),('Datasheet','',0,' hide')])
    pp=''
    for num,pn,x,y,angle,ty,length in pins:
        pp+=f'(pin {ty} line (at {x} {y} {angle}) (length {length}) (name {q(pn)} (effects (font (size 1.016 1.016)))) (number {q(num)} (effects (font (size 1.016 1.016)))))'
    defs[name]=f'(symbol "Controls:{name}" (pin_names (offset .508)) (in_bom yes) (on_board yes) {props} (symbol "{name}_0_1" {body}) (symbol "{name}_1_1" {pp}))'
    schema[name]={'pins':pins,'height':h}

two=lambda length=2.54:[('1','',-5.08,0,0,'passive',length),('2','',5.08,0,180,'passive',length)]
libsymbol('Resistor',two(),2.54,1.016,'R');libsymbol('Capacitor',two(4.572),.508,2.54,'C')
libsymbol('Switch',two(),2.54,2.54,'SW')
libsymbol('TestPoint',[('1','',-2.54,0,0,'passive',1.524)],1.016,1.016,'TP')
libsymbol('MountingHole',[],1.27,1.27)
libsymbol('Wheel',[(str(i+1),'CH'+str(i),12.7,2.54-i*2.54,180,'passive',2.54) for i in range(3)],10.16,5.08)
pinout={1:'KEY6',2:'KEY5',3:'KEY4',4:'KEY3',5:'KEY2',6:'KEY1',7:'KEY0',8:'VSS',9:'VDD',10:'MODE',11:'SDA',12:'~{RESET}',13:'NC',14:'SCL',15:'~{CHANGE}',16:'KEY11',17:'KEY10',18:'KEY9',19:'KEY8',20:'KEY7',21:'EP'}
left=[7,6,5,9,8,21,10,11,14,15,12];right=[1,2,3,4,13,16,17,18,19,20]
pins=[]
for side,nums in [(-1,left),(1,right)]:
    for i,n in enumerate(nums):
        ty='power_in' if n in [8,9,21] else 'input' if n in [10,12] else 'open_collector' if n==15 else 'bidirectional' if n in [11,14] else 'no_connect' if n==13 else 'passive'
        pins.append((str(n),pinout[n],side*15.24,12.7-i*2.54,0 if side<0 else 180,ty,2.54))
libsymbol('QT2120',pins,12.7,19.05)
io_pinout={1:'~{RESET}',2:'P0',3:'P1',4:'P2',5:'P3',6:'GND',7:'P4',8:'P5',9:'P6',10:'P7',11:'~{INT}',12:'SCL',13:'SDA',14:'VCCP',15:'VCCI',16:'ADDR',17:'EP'}
pins=[]
for side,nums in [(-1,[15,14,6,17,16,12,13,11,1]),(1,[2,3,4,5,7,8,9,10])]:
    for i,n in enumerate(nums):
        ty='power_in' if n in [6,14,15,17] else 'input' if n in [1,12,16] else 'open_collector' if n==11 else 'bidirectional'
        pins.append((str(n),io_pinout[n],side*15.24,10.16-i*2.54,0 if side<0 else 180,ty,2.54))
libsymbol('TCA6408A',pins,12.7,15.24)
libsymbol('FPC12',[(str(i),str(i),-10.16,13.97-(i-1)*2.54,0,'passive',2.54) for i in range(1,13)]+[('13','SHIELD',10.16,5.08,180,'passive',2.54),('14','SHIELD',10.16,-5.08,180,'passive',2.54)],7.62,16.51)
libsymbol('PowerFlag',[('1','',0,0,90,'power_out',0)],.635,.635)

components=[]
def add(ref,kind,value,nets,pos,foot='',pcb=None,description='',datasheet=''):
    x,y=pos;s=schema[kind];symbolid=uid('symbol-'+ref)
    isflag=kind=='PowerFlag'
    props=''.join(f'(property {q(k)} {q(v)} (at {x} {yy} 0) (effects (font (size {sz} {sz})){hide}))' for k,v,yy,sz,hide in [
        ('Reference',ref,y-s['height']-5.08,1.27,''),('Value',value,y-s['height']-2.54,1.016,''),('Footprint',('Controls:'+foot) if foot else '',y,1.27,' hide'),('Datasheet',datasheet,y,1.27,' hide'),('Description',description,y,1.27,' hide')])
    instances.append(f'(symbol (lib_id "Controls:{kind}") (at {x} {y} 0) (unit 1) (in_bom {"no" if (isflag or kind in ["TestPoint","MountingHole","Wheel"]) else "yes"}) (on_board {"no" if isflag else "yes"}) (dnp no) (uuid "{symbolid}") {props} '+''.join(f'(pin {q(a[0])} (uuid "{uid(ref+"-pin-"+a[0])}"))' for a in s['pins'])+f'(instances (project "controls" (path "/{rootid}" (reference {q(ref)}) (unit 1)))))')
    for num,name,px,py,angle,typ,length in s['pins']:
        a=(round(x+px,5),round(y-py,5));net=nets.get(num)
        if net is None:
            ncs.append(f'(no_connect (at {a[0]} {a[1]}) (uuid "{uid(ref+num+"-nc")}"))');continue
        dx=-5.08 if px<0 else 5.08 if px>0 else 0
        end=(round(a[0]+dx,5),round(a[1]+(5.08 if dx==0 else 0),5))
        wires.append(f'(wire (pts (xy {a[0]} {a[1]}) (xy {end[0]} {end[1]})) (stroke (width 0) (type default)) (uuid "{uid(ref+num+"-wire")}"))')
        justify='right' if px<0 else 'left'
        labels.append(f'(label {q(net)} (at {end[0]} {end[1]} 0) (effects (font (size 1.016 1.016)) (justify {justify} bottom)) (uuid "{uid(ref+num+"-label")}"))')
    if not isflag:components.append({'ref':ref,'value':value,'kind':kind,'nets':nets,'footprint':foot,'symbol_uuid':symbolid,'pcb':pcb,'description':description,'datasheet':datasheet})

qturl='https://ww1.microchip.com/downloads/en/devicedoc/doc9634.pdf'
qt_nets={'5':'SENSE2','6':'SENSE1','7':'SENSE0','8':'GND','9':'VDD_TOUCH','10':'GND','11':'SDA','12':'RESET_N','14':'SCL','15':'INT_N','21':'GND'}
add('U1','QT2120','AT42QT2120-MMHR',qt_nets,(132.08,66.04),'QT2120_VQFN20',(38.3,28.8,'B',0),'3-channel wheel / I2C address 0x1C',qturl)
add('E1','Wheel','31mm INTERPOLATED WHEEL',{str(i+1):'WHEEL'+str(i) for i in range(3)},(25.4,45.72),'Wheel_D31',(22,17,'F',0),'Covered copper, no paste; tune with final nonmetal cover')
for i in range(3):add('R'+str(i+1),'Resistor','10k',{'1':'WHEEL'+str(i),'2':'SENSE'+str(i)},(76.2,43.18+i*12.7),'R0402',(36.2+i*1.8,21.4 if i==2 else 22.2,'B',-90),'1% 0402 electrode series resistor')
for ref,net,xy in [('R4','SDA',(30.8,26)),('R5','SCL',(30.8,28.2)),('R6','INT_N',(32,31)),('R7','RESET_N',(34.2,31))]:
    add(ref,'Resistor','4.7k' if ref in ['R4','R5'] else '10k',{'1':'+3V3','2':net},(190.5,38.1+(int(ref[1])-4)*15.24),'R0402',(*xy,'B',90),'Host-side 3.3 V pull-up; remove R4/R5 if host already supplies adequate I2C pull-ups')
add('R8','Resistor','22R',{'1':'+3V3','2':'VDD_TOUCH'},(30.48,109.22),'R0402',(30.2,21.8,'B',-90),'Low-current RC supply filter')
add('C1','Capacitor','100nF',{'1':'VDD_TOUCH','2':'GND'},(88.9,109.22),'C0402',(36.7,26,'B',0),'X7R 10 V, close to U1 VDD')
add('C2','Capacitor','1uF',{'1':'VDD_TOUCH','2':'GND'},(147.32,109.22),'C0402',(32,24.1,'B',0),'X5R/X7R 10 V reservoir')
keys=[('POWER',22,17,0),('BACK',22,4,0),('PREV',35,17,90),('NEXT',9,17,90),('PLAY',22,30,0)]
for i,(name,x,y,a) in enumerate(keys):
    add('SW'+str(i+1),'Switch','SKSWCEE010',{'1':'KEY_'+name,'2':'GND'},(38.1+i*50.8,147.32),'SKSW_3x2', (x,y,'F',a),name+(' / independent active-low key; local 10k pull-up to +3V3' if name=='POWER' else ' / active-low TCA6408A input; local 47k pull-up; firmware debounce required'),'https://tech.alpsalpine.com/cms.media/product_catalog_ta_02_sksw_en_ee3e98d509.pdf')
jnet=['GND','+3V3','SDA','SCL','INT_N','RESET_N',None,None,None,None,'KEY_POWER','GND']
add('J1','FPC12','HC-FPC-05-10-12RLTAG',{**{str(i+1):n for i,n in enumerate(jnet) if n is not None},'13':'GND','14':'GND'},(276.86,60.96),'HCTL_FPC12',(35.87,9.411,'B',-90),'12 pin, 0.5 pitch, 0.3 FFC; tabs 13/14 GND; pins 7-10 NC; aligned with mainboard FPC1','https://atta.szlcsc.com/upload/public/pdf/source/20221027/B2DE489DA152049D1F105170189CFB4E.pdf')
add('R14','Resistor','10k',{'1':'+3V3','2':'KEY_POWER'},(38.1,160.02),'R0402',(32,1.4,'B',-90),'1% 0402 independent POWER pull-up; released high, pressed low')
io_nets={'1':'RESET_N','2':'KEY_BACK','3':'KEY_PREV','4':'KEY_NEXT','5':'KEY_PLAY','6':'GND','7':'UNUSED_INPUTS','8':'UNUSED_INPUTS','9':'UNUSED_INPUTS','10':'UNUSED_INPUTS','11':'INT_N','12':'SCL','13':'SDA','14':'+3V3','15':'+3V3','16':'GND','17':'GND'}
add('U2','TCA6408A','TCA6408ARGTR',io_nets,(330.2,203.2),'TCA6408A_VQFN16',(25,31,'B',180),'I2C 0x20; P0..P3 four keys; P4..P7 common pull-down, KEEP AS INPUTS','https://www.ti.com/lit/ds/symlink/tca6408a.pdf')
add('R13','Resistor','10k',{'1':'UNUSED_INPUTS','2':'GND'},(383.54,238.76),'R0402',(20,31,'B',90),'Shared pull-down for unused P4..P7; keep all four ports as inputs')
for i,name in enumerate(['BACK','PREV','NEXT','PLAY']):
    add('R'+str(9+i),'Resistor','47k',{'1':'+3V3','2':'KEY_'+name},(228.6,185.42+i*15.24),'R0402',(18-i*2,31,'B',90),'1% 0402 local active-low key pull-up')
for ref,xy,schxy in [('C3',(28,31.8),(279.4,251.46)),('C4',(28,29.8),(340.36,251.46))]:
    add(ref,'Capacitor','100nF',{'1':'+3V3','2':'GND'},schxy,'C0402',(*xy,'B',0),'X7R 10 V; U2 VCCI/VCCP bypass; both supplies on same 3.3 V rail')
for i,n in enumerate(['+3V3','GND','SDA','SCL','INT_N','RESET_N','KEY_POWER','KEY_BACK','KEY_PREV','KEY_NEXT','KEY_PLAY']):
    add('TP'+str(i+1),'TestPoint',n,{'1':n},(25.4+(i%6)*30.48,185.42+(i//6)*20.32),'TestPad',(7+i*2.5,9,'B',0),'Local bench-test pad only; no pin header installed')
for i,xy in enumerate([(3,8.7),(41,8.7),(3,24.7),(41,24.7)]):add('H'+str(i+1),'MountingHole','M1.6 / NPTH 1.8',{},(30.48+i*43.18,238.76),'Mount_1.8',(*xy,'F',0),'Revision-F mounting point')
for i,n in enumerate(['+3V3','VDD_TOUCH','GND']):add('#FLG0'+str(i+1),'PowerFlag','PWR_FLAG',{'1':n},(213.36+i*35.56,109.22))
def note(text,x,y,size=1.524):annotations.append(f'(text {q(text)} (at {x} {y} 0) (effects (font (size {size} {size})) (justify left)) (uuid "{uid(text)}"))')
for txt,x,y in [('01  TOUCH WHEEL / 3.3 V / I2C 0x1C',15.24,17.78),('02  POWER AND LOCAL DECOUPLING',15.24,93.98),('03  FOUR I2C KEYS + INDEPENDENT POWER',15.24,129.54),('04  LOCAL BENCH TEST PADS',15.24,170.18),('05  REVISION-F MECHANICAL MOUNTS',15.24,223.52),('06  I2C KEY INPUTS / 0x20',248.92,170.18)]:note(txt,x,y,2.032)
note('J1 is reserved for a future host. No mainboard connection in this revision.\nSupply regulated 3.3 V at J1 or TP1/TP2 for bench testing.\nDo not apply battery voltage to the 3.3 V rail.',309.88,43.18)
note('SW2..SW5 -> U2 P0..P3, active low. Debounce in firmware.\nSW1 POWER -> J1.11; R14 10k pull-up to +3V3.\nReleased HIGH, pressed LOW; independent of U1/U2.\nJ1.7..10 are NC. TP8..11 are local debug pads only.',276.86,137.16)
note('Enable wheel: register 0x0E = 0xC0. Disable unused KEY3..11.\nFirmware configuration and final-cover calibration are required.\nElectrode shape includes switch clearances; verify 360-degree tracking.',248.92,93.98)
note('U2 P4..P7 share R13 pull-down. Keep 0x03 = 0xFF (all inputs).\nPolarity 0x02 = 0x00; read 0x00, pressed = (~value) & 0x0F.\nINT_N is wired-OR: read BOTH devices until interrupt releases.\nRESET_N resets both ICs; reinitialize both after reset.',15.24,269.24,1.27)
sch=f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{rootid}") (paper "A3") (title_block (title "Q2 Controls - I2C Wheel + Four Keys / Independent POWER") (date "2026-09-21") (rev "B") (company "alon") (comment 1 "44 x 34 x 0.8 mm / Mainboard not connected")) (lib_symbols '+''.join(defs.values())+')'+''.join(instances+wires+labels+ncs+annotations)+')\n'
(P/'controls.kicad_sch').write_text(sch,encoding='utf8')
(P/'Controls.kicad_sym').write_text('(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor") '+''.join(v.replace('"Controls:', '"') for v in defs.values())+')\n',encoding='utf8')
(P/'sym-lib-table').write_text('(sym_lib_table (lib (name "Controls") (type "KiCad") (uri "${KIPRJMOD}/Controls.kicad_sym") (options "") (descr "Local control board symbols")))\n')
(P/'fp-lib-table').write_text('(fp_lib_table (lib (name "Controls") (type "KiCad") (uri "${KIPRJMOD}/Controls.pretty") (options "") (descr "Local verified footprints")))\n')

# Local, portable standard footprints and STEP models.
for dest,src,model in [('R0402','Resistor_SMD/R_0402_1005Metric','Resistor_SMD.3dshapes/R_0402_1005Metric.step'),('C0402','Capacitor_SMD/C_0402_1005Metric','Capacitor_SMD.3dshapes/C_0402_1005Metric.step'),('QT2120_VQFN20','Package_DFN_QFN/VQFN-20-1EP_3x3mm_P0.45mm_EP1.55x1.55mm','Package_DFN_QFN.3dshapes/VQFN-20-1EP_3x3mm_P0.45mm_EP1.55x1.55mm.step')]:
    lib,name=src.split('/');s=(LIB/'footprints'/(lib+'.pretty')/(name+'.kicad_mod')).read_text()
    s=s.replace('(footprint "'+name+'"','(footprint "'+dest+'"',1)
    s=re.sub(r'\(model "[^"]+"',f'(model "${{KIPRJMOD}}/models3d/{dest}.step"',s)
    (P/'Controls.pretty'/(dest+'.kicad_mod')).write_text(s)
    if (LIB/'3dmodels'/model).exists():shutil.copyfile(LIB/'3dmodels'/model,P/'models3d'/(dest+'.step'))

def footprint(name,pads,body,model=None,extra='',attr='smd'):
    x0,y0,x1,y1=body
    s=f'(footprint "{name}" (version 20250114) (generator "pcbnew") (layer "F.Cu") (attr {attr}) (property "Reference" "REF**" (at 0 {y0-1.2} 0) (layer "F.SilkS") (effects (font (size .7 .7) (thickness .12)))) (property "Value" "{name}" (at 0 {y1+1.2} 0) (layer "F.Fab") (effects (font (size .7 .7) (thickness .1))))'
    if name not in ['Wheel_D31','TestPad','Mount_1.8']:
        s+=f'(fp_rect (start {x0} {y0}) (end {x1} {y1}) (stroke (width .1) (type default)) (fill none) (layer "F.Fab"))'
        s+=f'(fp_rect (start {x0-.25} {y0-.25}) (end {x1+.25} {y1+.25}) (stroke (width .05) (type default)) (fill none) (layer "F.CrtYd"))'
    s+=''.join(pads)+extra
    if model:s+=f'(model "${{KIPRJMOD}}/models3d/{model}.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))'
    (P/'Controls.pretty'/(name+'.kicad_mod')).write_text(s+')\n',encoding='utf8')
def pad(num,x,y,w,h,layers='"F.Cu" "F.Paste" "F.Mask"'):
    return f'(pad "{num}" smd rect (at {x} {y}) (size {w} {h}) (layers {layers}))'
footprint('SKSW_3x2',[pad('1',-1.625,0,.55,1.5),pad('2',1.625,0,.55,1.5)],(-1.9,-1,1.9,1),'SKSW_3x2')
# TI RGT0016A land pattern, top view: pin 1 upper left, counterclockwise.
iopads=[]
for i in range(4):
    a=-.75+i*.5
    iopads += [pad(str(1+i),-1.4,a,.6,.24),pad(str(5+i),a,1.4,.24,.6),pad(str(9+i),1.4,-a,.6,.24),pad(str(13+i),-a,-1.4,.24,.6)]
iopads += [pad('17',0,0,1.45,1.45,'"F.Cu" "F.Mask"'),pad('',0,0,1.34,1.34,'"F.Paste"')]
footprint('TCA6408A_VQFN16',iopads,(-1.7,-1.7,1.7,1.7),'TCA6408A_VQFN16',extra='(fp_circle (center -1.85 -1.85) (end -1.75 -1.85) (stroke (width .1) (type default)) (fill solid) (layer "F.SilkS"))')
# FH19C: signal row centers y=-1.1; rear hold-down y=1.4. Ref is package center.
fpcpads=[pad(str(i+1),-2.75+i*.5,-1.1,.3,.8) for i in range(12)]
fpcpads += [pad('',x,1.4,.4,.8) for x in [-3.75,3.75]]
footprint('FH19C_12',fpcpads,(-4,-1.5,4,1.8),'FH19C_12')
hctl=[pad(str(i+1),-2.75+i*.5,1.405,.3,.65) for i in range(12)]
hctl += [pad('13',3.635,-1.405,.3,1.15),pad('14',-3.635,-1.405,.3,1.15)]
footprint('HCTL_FPC12',hctl,(-3.885,-2.18,3.885,1.73),'HCTL_FPC12')
footprint('TestPad',[pad('1',0,0,1,1,'"F.Cu" "F.Mask"')],(-.5,-.5,.5,.5),attr='exclude_from_pos_files exclude_from_bom')
footprint('Mount_1.8',['(pad "" np_thru_hole circle (at 0 0) (size 1.8 1.8) (drill 1.8) (layers "*.Cu" "*.Mask"))'],(-.9,-.9,.9,.9),extra='(fp_circle (center 0 0) (end 2 0) (stroke (width .05) (type default)) (fill none) (layer "F.CrtYd"))',attr='exclude_from_pos_files exclude_from_bom')
electrodes=json.loads((P/'output/electrodes.json').read_text());wheelpads=[]
for ch in electrodes['channels']:
    # A switch notch can clip a tiny tip off. Omit disconnected fragments;
    # no electrically floating islands are left on the board.
    def area(poly):
        pp=poly['points'];return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(pp,pp[1:]+pp[:1])))/2
    poly=max(ch['polygons'],key=area);ax,ay=poly['anchor'];pts=' '.join(f'(xy {ax-x:.6f} {y-ay:.6f})' for x,y in poly['points'])
    wheelpads.append(f'(pad "{ch["channel"]+1}" smd custom (at {22-ax:.6f} {ay-17:.6f}) (size .05 .05) (layers "F.Cu") (options (clearance outline) (anchor circle)) (primitives (gr_poly (pts {pts}) (width 0) (fill yes))))')
footprint('Wheel_D31',wheelpads,(-15.5,-15.5,15.5,15.5),attr='exclude_from_pos_files exclude_from_bom')

b=p.BOARD();b.GetDesignSettings().SetBoardThickness(p.FromMM(.8));b.SetCopperLayerCount(2)
netnames=sorted({n for c in components for n in c['nets'].values()});nets={}
for n in netnames:nets[n]=p.NETINFO_ITEM(b,'/'+n);b.Add(nets[n])
for c in components:
    print('ADD',c['ref'],flush=True)
    f=p.FootprintLoad(str(P/'Controls.pretty'),c['footprint']);b.Add(f);f.SetFPID(p.LIB_ID('Controls',c['footprint']))
    f.SetReference(c['ref']);f.SetValue(c['value']);f.SetPath(p.KIID_PATH('/'+rootid+'/'+c['symbol_uuid']))
    f.SetSheetfile('controls.kicad_sch');f.SetSheetname('')
    f.SetField('Description',c['description']);f.SetField('Datasheet',c['datasheet'])
    for index,a in enumerate(f.Pads()):
        name=c['nets'].get(a.GetNumber())
        if name:a.SetNet(nets[name])
        elif a.GetNumber() and c['ref']=='U1':
            nn='unconnected-(U1-'+pinout[int(a.GetNumber())]+'-Pad'+a.GetNumber()+')'
            if nn not in nets:nets[nn]=p.NETINFO_ITEM(b,nn);b.Add(nets[nn])
            a.SetNet(nets[nn])
        elif a.GetNumber() and c['ref']=='J1':
            nn='unconnected-(J1-Pad'+a.GetNumber()+')'
            if nn not in nets:nets[nn]=p.NETINFO_ITEM(b,nn);b.Add(nets[nn])
            a.SetNet(nets[nn])
    x,y,side,ang=c['pcb'];x=44-x;f.SetPosition(V(x,y))
    if side=='B':f.Flip(f.GetPosition(),p.FLIP_DIRECTION_LEFT_RIGHT)
    f.SetOrientationDegrees(ang);f.SetLocked(c['ref'].startswith(('SW','H','E')) or c['ref']=='J1')
    f.Reference().SetTextSize(V(.8,.8));f.Reference().SetTextThickness(p.FromMM(.1));f.Value().SetVisible(False)
    if c['ref'].startswith(('E','H','TP','R','C')):f.Reference().SetVisible(False)
    if c['ref'].startswith('U'):f.Reference().SetVisible(False)
    if c['ref']=='SW2':f.Reference().SetPosition(V(26,4))
def edge(a,z,mid=None):
    s=p.PCB_SHAPE();s.SetLayer(p.Edge_Cuts);s.SetWidth(p.FromMM(.05))
    if mid:s.SetShape(p.SHAPE_T_ARC);s.SetArcGeometry(V(*a),V(*mid),V(*z))
    else:s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(V(*a));s.SetEnd(V(*z))
    b.Add(s)
edge((10,0),(34,0));edge((34,0),(44,10),(41.071067812,2.928932188));edge((44,10),(44,24));edge((44,24),(34,34),(41.071067812,31.071067812))
edge((34,34),(10,34));edge((10,34),(0,24),(2.928932188,31.071067812));edge((0,24),(0,10));edge((0,10),(10,0),(2.928932188,2.928932188))
for txt,xy,size in [('Q2 CTRL B',(22,1),.8),('3V3 ONLY',(15,7),.8)]:
    t=p.PCB_TEXT(b);t.SetText(txt);t.SetPosition(V(*xy));t.SetTextSize(V(size,size));t.SetTextThickness(p.FromMM(.12));t.SetLayer(p.F_SilkS);b.Add(t)
p.SaveBoard(str(boardfile),b)
project={'meta':{'filename':'controls.kicad_pro','version':3},'board':{'design_settings':{'rules':{'min_clearance':.15,'min_track_width':.15,'min_via_diameter':.5,'min_through_hole_diameter':.3,'min_copper_edge_clearance':.25,'min_hole_clearance':.25,'min_silk_clearance':.1,'min_text_height':.8,'min_text_thickness':.1},'defaults':{'board_outline_line_width':.05},'rule_severities':{'lib_footprint_mismatch':'warning'}}},'net_settings':{'classes':[{'name':'Default','clearance':.15,'track_width':.2,'via_diameter':.6,'via_drill':.3,'microvia_diameter':.3,'microvia_drill':.1,'diff_pair_width':.2,'diff_pair_gap':.2,'diff_pair_via_gap':.2,'bus_width':12,'wire_width':6,'schematic_color':'rgba(0, 0, 0, 0.000)','pcb_color':'rgba(0, 0, 0, 0.000)'}],'meta':{'version':4}},'schematic':{'erc':{'rule_severities':{}}}}
project['board']['design_settings']['meta']={'version':2}
(P/'controls.kicad_pro').write_text(json.dumps(project,indent=2)+'\n')
(P/'output/design.json').write_text(json.dumps({'root_uuid':rootid,'components':components,'connector_pinout':jnet,'board_mm':[44,34,.8],'component_coordinates':'pcb fields list case-local X/Y; actual KiCad X = 44 - case-local X','case_transform':{'x':'47 - kicad_x','y':'kicad_y + 42.3','front_z':11.9,'back_z':11.1},'status':'GENERATED_UNROUTED'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
with (P/'output/bom.csv').open('w',newline='',encoding='utf-8-sig') as out:
    w=csv.writer(out);w.writerow(['Reference','Value','Footprint','Description','Datasheet'])
    for c in components:
        if c['kind'] not in ['TestPoint','MountingHole','Wheel']:w.writerow([c['ref'],c['value'],c['footprint'],c['description'],c['datasheet']])
print('CREATED',len(components),'components',len(nets),'nets')
