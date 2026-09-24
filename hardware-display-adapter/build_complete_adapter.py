"""Build the OSPTEK reference-based passive AM213 adapter. KiCad 10 Python.
Sources: reference/osptek-official and main-fpc2-net-map.json.
Flexible tail geometry is an assembly candidate, not a supplier-approved flex stack.
"""
from pathlib import Path
import pcbnew as p
import json,uuid,shutil,csv,re,sys
ROOT=Path(__file__).resolve().parent;O=ROOT/'am213-fpc-adapter';LIB=O/'Adapter.pretty';LIB.mkdir(exist_ok=True)
OUT=O/'output';OUT.mkdir(exist_ok=True);K=Path('D:/KiCad/10.0/share/kicad')
sys.path.insert(0,str(ROOT.parent/'tmp'));from sexpr import parse,get,children,dump,S
uid=lambda s:str(uuid.uuid5(uuid.UUID('2bc04421-f71e-4b58-af1a-111296efbad9'),s))
q=lambda s:json.dumps(str(s),ensure_ascii=False)
name='am213-fpc-adapter';rootid=uid('root');defs={};pinouts={};instances=[];wires=[];labels=[];ncs=[];cs=[]

def sym(n,pins,halfwidth=10.16):
    h=max(5.08,(max(sum(x[2]==side for x in pins) for side in [-1,1])-1)*1.27+2.54)
    specs=[]
    for side in [-1,1]:
        row=[x for x in pins if x[2]==side]
        for i,(num,label,_,typ) in enumerate(row):specs.append((str(num),label,side*(halfwidth+2.54),(len(row)-1)*1.27-i*2.54,0 if side<0 else 180,typ))
    props=''.join(f'(property {q(k)} {q(v)} (at 0 {y} 0) (effects (font (size 1.27 1.27))))' for k,v,y in [('Reference','J' if n.startswith('J') else n[0],h+5.08),('Value',n,h+2.54)])
    body=f'(rectangle (start {-halfwidth} {h}) (end {halfwidth} {-h}) (stroke (width .254) (type default)) (fill (type background)))'
    if n=='R':body='(rectangle (start -2.54 1.016) (end 2.54 -1.016) (stroke (width .254) (type default)) (fill (type none)))'
    if n=='C':body=''.join(f'(polyline (pts (xy {x} -2) (xy {x} 2)) (stroke (width .254) (type default)) (fill (type none)))' for x in [-.508,.508])
    pp=''.join(f'(pin {ty} line (at {x} {y} {a}) (length {2.54 if n not in ["R","C"] else (2.54 if n=="R" else 4.572)}) (name {q(l)} (effects (font (size .9 .9)))) (number {q(num)} (effects (font (size .9 .9)))))' for num,l,x,y,a,ty in specs)
    defs[n]=f'(symbol "Adapter:{n}" (pin_names (offset .508)) (in_bom yes) (on_board yes) {props} (symbol "{n}_0_1" {body}) (symbol "{n}_1_1" {pp}))'
    pinouts[n]=(specs,h)

main={int(x['pin']):x['net'] for x in json.loads((ROOT/'main-fpc2-net-map.json').read_text())['pads'] if int(x['pin'])<=21}
host={3:'LCD_RST',4:'VCI_EN',5:'CLK_IN',7:'CS_IN',8:'D3_IN',9:'D2_IN',10:'D1_IN',11:'D0_IN',12:'GND',13:'VCC_3V3',14:'VCC_3V3',17:'GND',18:'TP_INT',19:'TP_SCL',20:'TP_SDA',21:'TP_RST'}
screen={1:'LCD_RST',2:'GND',3:'LCD_TE',4:'LCD_CS',5:'LCD_CLK',6:'LCD_D1',7:'LCD_D0',8:'GND',11:'VCC_3V3',12:'VCC_3V3',13:'GND',14:'GND',15:'LCD_VDD',16:'TP_VDD',17:'TP_INT',18:'TP_RST',19:'TP_SDA',20:'TP_SCL',21:'GND',22:'LCD_D3',23:'LCD_D2',24:'VCI_EN','MP':'GND'}
sym('J_HOST',[(i,main.get(i) or 'NC',-1 if i<=11 else 1,'passive') for i in range(1,22)])
spnames={**screen,9:'NC_IM1',10:'NC_MTP',11:'VBAT',12:'VBAT',15:'VDD',16:'TP_VDD'}
sym('J_LCD',[(i,spnames[i],-1 if i<=12 else 1,'passive') for i in range(1,25)]+[('MP','MOUNT_GND',1,'passive')])
for s in ['R','C']:sym(s,[(1,'',-1,'passive'),(2,'',1,'passive')],2.54)
sym('TP',[(1,'',-1,'passive')],1.27)

def component(ref,kind,value,nets,sch,fp,pcb,dnp=False,desc=''):
    nets={str(k):v for k,v in nets.items()};x,y=[round(round(z/1.27)*1.27,5) for z in sch];pp,h=pinouts[kind];sid=uid(ref)
    props=''.join(f'(property {q(k)} {q(v)} (at {x} {yy} 0) (effects (font (size 1.016 1.016)){hide}))' for k,v,yy,hide in [('Reference',ref,y-h-5.08,''),('Value',value,y-h-2.54,''),('Footprint','Adapter:'+fp,y,' hide'),('Description',desc,y,' hide')])
    instances.append(f'(symbol (lib_id "Adapter:{kind}") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp {"yes" if dnp else "no"}) (uuid "{sid}") {props}'+''.join(f'(pin {q(n)} (uuid "{uid(ref+"pin"+n)}"))' for n,*_ in pp)+f'(instances (project "{name}" (path "/{rootid}" (reference "{ref}") (unit 1)))))')
    for n,_,px,py,a,ty in pp:
        ax,ay=round(x+px,5),round(y-py,5)
        if n not in nets:ncs.append(f'(no_connect (at {ax} {ay}) (uuid "{uid(ref+n+"nc")}"))');continue
        ex=round(ax+(-5.08 if px<0 else 5.08),5)
        wires.append(f'(wire (pts (xy {ax} {ay}) (xy {ex} {ay})) (stroke (width 0) (type default)) (uuid "{uid(ref+n+"w")}"))')
        labels.append(f'(label {q(nets[n])} (at {ex} {ay} 0) (effects (font (size 1.016 1.016)) (justify {"right" if px<0 else "left"} bottom)) (uuid "{uid(ref+n+"l")}"))')
    cs.append(dict(ref=ref,kind=kind,value=value,nets=nets,footprint=fp,pcb=pcb,uuid=sid,dnp=dnp,description=desc))

tail=70.;cy=12.4005
component('J1','J_HOST','21P 0.3mm FPC fingers',host,(70,60),'FPC21_Fingers',(50-tail+1.4,50+cy,0),desc='AFE03 lower contact; 0.20+/-0.03mm finished tip; not a separate socket')
component('J2','J_LCD','OK-23GF024-04',screen,(220,60),'OK23GF024',(53,62,0),desc='Top view: 1 upper left, 12 lower left, 13 lower right, 24 upper right; OSPTEK board photo')
for i,(n,out,xy) in enumerate([('CLK_IN','LCD_CLK',(57,59)),('CS_IN','LCD_CS',(57,57)),('D0_IN','LCD_D0',(57,63)),('D1_IN','LCD_D1',(57,61)),('D2_IN','LCD_D2',(57,67)),('D3_IN','LCD_D3',(57,65))],1):
    component('R'+str(i),'R','22R' if i==1 else '0R',{1:n,2:out},(50+((i-1)%3)*95,125+((i-1)//3)*17.78),'R0402',(*xy,0),desc='QSPI series damping; initial conservative low clock, tune on scope')
component('R7','R','0R',{1:'VCC_3V3',2:'LCD_VDD'},(50,174),'R0402',(56,69.3,0),desc='Factory reference feeds pin15 at3.3V; removable isolation link')
component('R8','R','0R',{1:'VCC_3V3',2:'TP_VDD'},(145,174),'R0402',(56,70.8,0),desc='Factory reference feeds pin16 at3.3V; removable isolation link')
component('R9','R','100k',{1:'VCI_EN',2:'GND'},(240,174),'R0402',(56,54,0),desc='Default PMIC disable until ESP_IO46 asserts enable')
component('R10','R','4.7k',{1:'VCC_3V3',2:'TP_SDA'},(50,202),'R0402',(61,64,90),True,'Optional pull-up; host already has R46')
component('R11','R','4.7k',{1:'VCC_3V3',2:'TP_SCL'},(145,202),'R0402',(63,64,90),True,'Optional pull-up; host already has R45')
for ref,val,net,sch,xy,foot in [('C1','100nF','VCC_3V3',(50,230),(53,69.5),'C0402'),('C2','10uF','VCC_3V3',(145,230),(51.5,69.3),'C0603'),('C3','100nF','LCD_VDD',(240,230),(59,69.3),'C0402'),('C4','100nF','TP_VDD',(335,230),(59,70.8),'C0402')]:
    if ref=='C4':xy=(62,70.5)
    component(ref,'C',val,{1:net,2:'GND'},sch,foot,(*xy,90),desc='X5R/X7R 10V; C2 maximum assembled height <=0.8mm')
component('TP1','TP','TE 3V3',{1:'LCD_TE'},(335,125),'TP',(56,55.5,0),desc='No host GPIO allocated; TE unused in initial firmware')
note='OSPTEK AM213 reference: 3.3V direct QSPI/I2C; no level shifters.\nJ1.1/2 old backlight isolated; J1.6/15/16 unused.\nIO46 -> VCI_EN, IO47 -> LCD_RST, IO57 -> TP_RST.\nR10/R11 DNP: host I2C pull-ups R45/R46 present.\n70mm tail is mechanical candidate; confirm folding/stack with flex fabricator.\nNo TE to MCU; start QSPI <=10MHz and verify signal/power integrity.'
sch='(kicad_sch (version 20250114) (generator "eeschema") (uuid "'+rootid+'") (paper "A3") (title_block (title "AM213 / Existing ESP32-S31 mainboard FPC adapter") (date "2026-09-23") (rev "A - prototype") (company "alon")) (lib_symbols '+''.join(defs.values())+')'+''.join(instances+wires+labels+ncs)+f'(text {q(note)} (at 300 60 0) (effects (font (size 1.27 1.27)) (justify left)) (uuid "{uid("note")}")))'
(O/(name+'.kicad_sch')).write_text(sch,encoding='utf-8')
(O/'Adapter.kicad_sym').write_text('(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor")'+''.join(x.replace('"Adapter:','"') for x in defs.values())+')',encoding='utf-8')
(O/'sym-lib-table').write_text('(sym_lib_table (lib (name "Adapter") (type "KiCad") (uri "${KIPRJMOD}/Adapter.kicad_sym") (options "") (descr "AM213 local symbols")))')
(O/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "Adapter") (type "KiCad") (uri "${KIPRJMOD}/Adapter.pretty") (options "") (descr "AM213 adapter footprints")))')

def pad(n,x,y,w,h,layers='"F.Cu" "F.Paste" "F.Mask"'):
    return f'(pad "{n}" smd rect (at {x} {y}) (size {w} {h}) (layers {layers}) (solder_mask_margin 0.025))'
def fp(n,pads,box,extra='',attr='smd',model=None):
    x0,y0,x1,y1=box
    text=f'(footprint "{n}" (version 20250114) (generator "pcbnew") (layer "F.Cu") (attr {attr}) (property "Reference" "REF**" (at 0 {y0-1}) (layer "F.SilkS") (effects (font (size .65 .65) (thickness .1)))) (property "Value" "{n}" (at 0 {y1+1}) (layer "F.Fab") hide (effects (font (size .65 .65) (thickness .1)))) (fp_rect (start {x0} {y0}) (end {x1} {y1}) (stroke (width .1) (type default)) (fill none) (layer "F.Fab")) (fp_rect (start {x0-.15} {y0-.15}) (end {x1+.15} {y1+.15}) (stroke (width .05) (type default)) (fill none) (layer "F.CrtYd"))'+''.join(pads)+extra
    if model:text+=f'(model "${{KIPRJMOD}}/models3d/{model}.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))'
    (LIB/(n+'.kicad_mod')).write_text(text+')',encoding='utf-8')
bp=[]
for i in range(12):
    bp += [pad(i+1,-1.2,-2.2+i*.4,.5,.23),pad(24-i,1.2,-2.2+i*.4,.5,.23)]
for x in [-1.05,1.05]:
    for y in [-3.03,3.03]:bp.append(pad('MP',x,y,.8,.6))
fp('OK23GF024',bp,(-1.45,-3.66,1.45,3.66),extra='(fp_circle (center -1.65 -2.6) (end -1.5 -2.6) (stroke (width .1) (type default)) (fill solid) (layer "F.SilkS"))',model='OK-23GF024-04')
fp('FPC21_Fingers',[pad(i,0,3-(i-1)*.3,2.2,.2,'"F.Cu" "F.Mask"') for i in range(1,22)],(-1.4,-3.3,2.1,3.3),attr='smd exclude_from_bom exclude_from_pos_files')
fp('TP',[pad(1,0,0,.7,.7,'"F.Cu" "F.Mask"')],(-.35,-.35,.35,.35),attr='smd exclude_from_bom exclude_from_pos_files')
for dest,lib,src in [('R0402','Resistor_SMD','R_0402_1005Metric'),('C0402','Capacitor_SMD','C_0402_1005Metric'),('C0603','Capacitor_SMD','C_0603_1608Metric')]:
    s=(K/'footprints'/(lib+'.pretty')/(src+'.kicad_mod')).read_text().replace('(footprint "'+src+'"','(footprint "'+dest+'"',1)
    s=re.sub(r'\(model "[^"]+"',f'(model "${{KIPRJMOD}}/models3d/{dest}.step"',s)
    (LIB/(dest+'.kicad_mod')).write_text(s)
    m=K/'3dmodels'/(lib+'.3dshapes')/(src+'.step')
    if m.exists():shutil.copyfile(m,O/'models3d'/(dest+'.step'))

b=p.BOARD();b.SetCopperLayerCount(2);ds=b.GetDesignSettings();ds.SetBoardThickness(p.FromMM(.12));ds.SetAuxOrigin(p.VECTOR2I(p.FromMM(50),p.FromMM(50)))
v=lambda x,y:p.VECTOR2I(round(x*1e6),round(y*1e6))
ns=sorted({n for c in cs for n in c['nets'].values()});nets={}
for n in ns:nets[n]=p.NETINFO_ITEM(b,'/'+n);b.Add(nets[n])
for c in cs:
    f=p.FootprintLoad(str(LIB),c['footprint']);b.Add(f);f.SetFPID(p.LIB_ID('Adapter',c['footprint']));f.SetReference(c['ref']);f.SetValue(c['value']);f.SetPath(p.KIID_PATH('/'+rootid+'/'+c['uuid']));f.SetSheetfile(name+'.kicad_sch')
    for a in f.Pads():
        n=c['nets'].get(a.GetNumber())
        if n:a.SetNet(nets[n])
    f.SetPosition(v(*c['pcb'][:2]));f.SetOrientationDegrees(c['pcb'][2]);f.Reference().SetVisible(c['ref'] in ['J2','TP1']);f.Value().SetVisible(False)
    if c['dnp']:f.SetAttributes(f.GetAttributes() | p.FP_DNP)
    if c['ref']=='J2':f.Reference().SetPosition(v(52.5,57))
    if c['ref']=='TP1':f.Reference().SetPosition(v(57.5,55.5))
    f.Reference().SetTextSize(v(.8,.8));f.Reference().SetTextThickness(p.FromMM(.12))

# Left-exiting flexible ribbon. Root is chamfered to distribute strain; corner
# radiusing and coverlay tolerances remain fabricator review items.
y0=50+cy-3.3;y1=50+cy+3.3;tip=50-tail
outline=[(50,50),(67,50),(67,72),(50,72),(50,y1+1),(48,y1),(tip,y1),(tip,y0),(48,y0),(50,y0-1)]
for a,z in zip(outline,outline[1:]+outline[:1]):
    e=p.PCB_SHAPE();e.SetShape(p.SHAPE_T_SEGMENT);e.SetStart(v(*a));e.SetEnd(v(*z));e.SetWidth(p.FromMM(.05));e.SetLayer(p.Edge_Cuts);b.Add(e)

# Straight, single-layer tail traces; no vias or components in flex span.
# Every finger keeps its identity; unused/backlight fingers intentionally stop.
for i,n in host.items():
    y=50+cy+3-(i-1)*.3
    t=p.PCB_TRACK(b);t.SetStart(v(tip+2.5,y));t.SetEnd(v(50.3,y));t.SetWidth(p.FromMM(.14 if n in ['VCC_3V3','GND'] else .12));t.SetLayer(p.F_Cu);t.SetNet(nets[n]);b.Add(t)

def text(s,xy,layer=p.Dwgs_User,size=.7):
    t=p.PCB_TEXT(b);t.SetText(s);t.SetPosition(v(*xy));t.SetTextSize(v(size,size));t.SetTextThickness(p.FromMM(.1));t.SetLayer(layer);b.Add(t)
text('AM213 / 3V3', (58.5,51.5),p.F_SilkS,.8)
text('70 mm flex tail / NO VIAS / DO NOT CREASE', (15,62.4),size=1)
text('TIP t=0.20 +/-0.03; stiffener >=3.5 mm; contact face F.Cu',(1,68),size=.8)
text('17x22 component island; rear FR4 stiffener; total stack <=0.6mm',(58.5,75),size=.7)
text('1',(tip+3.3,y1-.7),p.F_SilkS,.8)
p.SaveBoard(str(O/(name+'.kicad_pcb')),b)

pro=json.loads((O/(name+'.kicad_pro')).read_text())
rules=pro.setdefault('board',{}).setdefault('design_settings',{}).setdefault('rules',{})
rules.update(min_clearance=.1,min_track_width=.1,min_via_diameter=.3,min_through_hole_diameter=.15,min_via_annular_width=.075,min_hole_clearance=.175,min_copper_edge_clearance=.15,min_silk_text_height=.6)
nc=pro.setdefault('net_settings',{});nc['classes']=[{'name':'Default','clearance':.1,'track_width':.12,'via_diameter':.4,'via_drill':.2,'microvia_diameter':.2,'microvia_drill':.1,'diff_pair_width':.12,'diff_pair_gap':.15,'diff_pair_via_gap':.25,'bus_width':12,'wire_width':6,'line_style':0,'pcb_color':'rgba(0, 0, 0, 0.000)','schematic_color':'rgba(0, 0, 0, 0.000)'}]
(O/(name+'.kicad_pro')).write_text(json.dumps(pro,indent=2))
(OUT/'design.json').write_text(json.dumps({'root_uuid':rootid,'components':cs,'tail_length_mm':tail,'tail_center_y_local_mm':cy,'host_nets':host,'screen_nets':screen},ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'bom.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['Reference','Value','Footprint','Populate','Description'])
    for c in cs:
        if c['ref'] not in ['J1','TP1']:w.writerow([c['ref'],c['value'],c['footprint'],'NO' if c['dnp'] else 'YES',c['description']])
print('Built',len(cs),'components;',len(ns),'nets; tail',tail,'mm')
