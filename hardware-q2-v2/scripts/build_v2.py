"""Build an independent V2 electrical candidate; never changes the source boards.
Use KiCad 10 Python. Routing is a separate stage; refuse to overwrite routed work.
"""
from pathlib import Path
import sys,json,uuid,math,shutil,hashlib,xml.etree.ElementTree as ET,re
import pcbnew as p
P=Path(__file__).resolve().parents[1];ROOT=P.parent;PLAN=ROOT/'hardware-q2-v2-plan'
sys.path.insert(0,str(PLAN/'scripts'));from sexpr import parse,dump,children,get,prop,S
LIB=Path('D:/KiCad/10.0/share/kicad/footprints')
for d in ['V2.pretty','output','models3d']:(P/d).mkdir(exist_ok=True)
outfile=P/'q2-v2.kicad_pcb'
if outfile.exists():assert not p.LoadBoard(str(outfile)).GetTracks(),'Refusing to replace routed board'
origin=(128.868,67.647);V=lambda x,y:p.VECTOR2I(round(x*1e6),round(y*1e6))
def layers(*ids):
 s=p.LSET()
 for i in ids:s.AddLayer(i)
 return s
uid=lambda s:str(uuid.uuid5(uuid.UUID('cc5bc37c-570c-4cf3-a1df-87f9ea47032e'),s))
tree=parse((PLAN/'q2-v2-placement.kicad_pcb').read_text(encoding='utf8'))
tree[:]=[a for a in tree if not (isinstance(a,list) and a and ((a[0].startswith('gr_') and (get(a,'layer') or [None,None])[1]!='Edge.Cuts') or (a[0]=='footprint' and prop(a,'Reference')[2] in ['C40','C41','C45','C46','R27','R28','U10'])))]
(P/'output/base.kicad_pcb').write_text(dump(tree),encoding='utf8')
b=p.LoadBoard(str(P/'output/base.kicad_pcb'));refboard=p.LoadBoard(str(P/'reference/core-reference.kicad_pcb'))
pinplan=json.loads((PLAN/'pin-assignment.json').read_text(encoding='utf8'))['rows']
rename={r['old_net']:r['signal'] for r in pinplan if r['old_net']}
rename.update({'ESP_IO42':'KEY_RAW_N','GEK100_RST':'GEK_RST','VCC_LCD_BG':'VCC_PMID'})
def nname(n):return rename.get(n,n.replace('$','N_'))
netmap={}
def net(n):
 if not n:return None
 if n not in netmap:
  a=p.NETINFO_ITEM(b,n);b.Add(a);netmap[n]=a
 return netmap[n]
def wirepad(a,n):
 if n:a.SetNet(net(n))
 else:a.SetNetCode(0)
sourcexml=ET.parse(P/'reference/source-netlist.xml').getroot()
xc={x.attrib['ref']:x for x in sourcexml.find('components')}
libparts={(x.attrib['lib'],x.attrib['part']):x for x in sourcexml.find('libparts')}
components={};changes=[]
def pinmeta(ref,f):
 c=xc.get(ref);lp=libparts.get((c.find('libsource').attrib['lib'],c.find('libsource').attrib['part'])) if c is not None else None
 names={a.attrib['num']:{'name':a.attrib.get('name',''),'type':a.attrib.get('type','passive')} for a in lp.find('pins')} if lp is not None and lp.find('pins') is not None else {}
 return {a.GetNumber():names.get(a.GetNumber(),{'name':a.GetNumber(),'type':'passive'}) for a in f.Pads() if a.GetNumber()}
for f in b.GetFootprints():
 ref=f.GetReference();c=xc.get(ref)
 value=c.findtext('value') if c is not None else f.GetValue();f.SetValue(value)
 for a in f.Pads():wirepad(a,nname(a.GetNetname()))
 page=c.find('sheetpath').attrib['names'].strip('/') if c is not None else 'DISPLAY'
 components[ref]={'ref':ref,'value':value,'group':page,'pins':pinmeta(ref,f),'source':'V1 PCB connectivity / original schematic pin names'}
def assign(ref,pad,n):
 f=b.FindFootprintByReference(ref);found=False
 for a in f.Pads():
  if a.GetNumber()==str(pad):wirepad(a,n);found=True
 assert found,(ref,pad)
def add(ref,value,path,nets,x,y,angle=0,side='F',group='CORE',pins=None,source='New V2 circuit'):
 lib,name=path.split('/',1);f=p.FootprintLoad(str(LIB/(lib+'.pretty')),name);assert f,path
 b.Add(f);f.SetReference(ref);f.SetValue(value);f.SetPosition(V(origin[0]+x,origin[1]+y));f.SetOrientationDegrees(angle)
 if side=='B':f.Flip(f.GetPosition(),p.FLIP_DIRECTION_LEFT_RIGHT)
 for a in f.Pads():wirepad(a,nets.get(a.GetNumber(),''))
 components[ref]={'ref':ref,'value':value,'group':group,'pins':{a.GetNumber():(pins or {}).get(a.GetNumber(),{'name':a.GetNumber(),'type':'passive'}) for a in f.Pads() if a.GetNumber()},'source':source}
 return f
def passive(ref,value,n1,n2,x,y,angle=0,side='F',size='0402',group='CORE'):
 kind='Capacitor' if ref.startswith('C') else 'Inductor' if ref.startswith('L') else 'Resistor';pre=ref[0]
 metric={'0201':'0603','0402':'1005','0603':'1608'}[size]
 return add(ref,value,f'{kind}_SMD/{pre}_{size}_{metric}Metric',{'1':n1,'2':n2},x,y,angle,side,group)
# Transform the official core's local placement; preserve the silicon pin order.
core=refboard.FindFootprintByReference('U1');delta=-90-core.GetOrientationDegrees();center=core.GetPosition();dest=V(origin[0]+30,origin[1]+17)
byphysical={str(r['pin']):r for r in pinplan};refnets={}
for a in core.Pads():
 r=byphysical[a.GetNumber()];old=a.GetNetname()
 if r['group']=='空闲GPIO':new=''
 elif r['pin'] in [18,63]:new=''
 elif r['pin'] in [2,3]:new='MCU_VDDA34'
 elif r['pin'] in [11,43,54,64,77,80]:new='VCC_3V3'
 elif r['pin'] in [30,34,35]:new='MCU_1V8'
 elif r['pin']==39:new='MCU_VDD_SPI'
 elif r['pin']==81:new='GND'
 elif r['pin']==73:new='MCU_UART0_TX'
 elif r['pin'] in [37,38,40,41,42,44,45]:new='MCU_'+r['signal']
 elif r['pin']==79:new='MCU_XTAL_P'
 elif r['pin']==78:new='XTAL_N'
 elif r['pin']==1:new='RF_CHIP'
 else:new=r['signal']
 refnets[old]=new
refnets.update({'VDD33':'VCC_3V3','GND':'GND','XTAL_P':'XTAL_P','SPIQ':'FLASH_D1','SPIWP':'FLASH_D2','SPIHD':'FLASH_D3','SPICLK':'FLASH_CLK','SPID':'FLASH_D0','TX0':'UART0_TX','USB_DP':'USB_HS_DP','USB_DM':'USB_HS_DM','RF':'RF_STAGE1','RF1':'RF_STAGE2','RF_ANT':'RF_ANT'})
vals={**{'C'+str(i):'100nF' for i in [12,14,17,18,19,20,22,23,24,25]},**{'C'+str(i):'1uF' for i in [5,13,16,21]},'C1':'24pF','C2':'27pF','C3':'1.5pF','C4':'1.5pF','C6':'10nF','C7':'1.3pF','C8':'DNP','C9':'DNP','C10':'10uF','C15':'10uF','L1':'2.4nH','L2':'3.9nH','L3':'24nH LQP03TN24NH02D','L4':'2nH LQP03TN2N0B02D','L5':'0R','R6':'499R','R7':'10k','R10':'10k','Y1':'40MHz 15pF 10ppm MDH 2.3.3.400001552EL','U1':'ESP32-S31NRV16'}
core_refs={}
for source in refboard.GetFootprints():
 old=source.GetReference()
 if old in ['U2','U3','ANT1','D1','C11','C12','R11']:continue
 new='U9' if old=='U1' else 'Y101' if old=='Y1' else old[0]+str(100+int(old[1:]))
 f=p.FOOTPRINT(source);b.Add(f);f.Rotate(center,p.EDA_ANGLE(delta,p.DEGREES_T));f.Move(dest-center);f.SetReference(new);f.SetValue(vals.get(old,'0R'))
 for a in f.Pads():wirepad(a,refnets.get(a.GetNetname(),a.GetNetname()))
 if old=='U1':
  # PADS importer retains only one paste island as pad 81. Replace it with
  # the datasheet 6.5 mm copper EP and a separately windowed paste layer.
  ep=next(a for a in f.Pads() if a.GetNumber()=='81');ep.SetShape(p.PAD_SHAPE_RECT);ep.SetSize(V(6.5,6.5));ep.SetPosition(f.GetPosition());ep.SetOrientationDegrees(0)
  ep.SetLayerSet(layers(p.F_Cu,p.F_Mask));ep.SetLocalSolderMaskMargin(p.FromMM(.025))
  for xx in [-2.5,-1.25,0,1.25,2.5]:
   for yy in [-2.5,-1.25,0,1.25,2.5]:
    pa=p.PAD(f);pa.SetAttribute(p.PAD_ATTRIB_SMD);pa.SetShape(p.PAD_SHAPE_RECT);pa.SetSize(V(1,1));pa.SetPosition(f.GetPosition()+V(xx,yy));pa.SetLayerSet(layers(p.F_Paste));f.Add(pa)
  pins={str(r['pin']):{'name':r['pin_name'],'type':'power_in' if r['group'] in ['电源','地'] else 'bidirectional'} for r in pinplan}
 else:pins={a.GetNumber():{'name':a.GetNumber(),'type':'passive'} for a in f.Pads() if a.GetNumber()}
 if old=='Y1':pins={str(i):{'name':n,'type':'passive'} for i,n in enumerate(['XIN','GND','XOUT','GND'],1)}
 components[new]={'ref':new,'value':f.GetValue(),'group':'CORE_RF' if old in ['C3','C4','C7','C8','C9','L1','L2','L5'] else 'CORE','pins':pins,'source':'Espressif WROOM-3 V1.2 reference '+old}
 if vals.get(old)=='DNP':f.SetDNP(True)
 core_refs[old]=new
# Flash: replace 2 MB data flash with a 16 MB boot-flash candidate.
add('U10','W25Q128JVSIQ','Package_SO/SOIC-8_5.3x5.3mm_P1.27mm',{'1':'FLASH_CS_N','2':'FLASH_D1','3':'FLASH_D2','4':'GND','5':'FLASH_D0','6':'FLASH_CLK','7':'FLASH_D3','8':'MCU_VDD_SPI'},18.6,28.2,270,group='CORE',pins={str(i):{'name':n,'type':'power_in' if i in [4,8] else 'bidirectional'} for i,n in enumerate(['CS_N','D1','D2','GND','D0','CLK','D3','VCC'],1)})
assign('C13','1','MCU_VDD_SPI')
# Correct module-era strap/reset labels; add explicit GPIO37 strap.
passive('R120','10k','VCC_3V3','STRAP_USB_JTAG',33.2,22.7,90,side='B')
# Default states for LCD/USB/independent detection.
for ref,value,n1,n2,x,y in [('R121','10k','VCC_3V3','LCD_CS_N',35.5,28),('R122','100k','LCD_RESET_N','GND',36,30),('R123','100k','LCD_VCI_EN','GND',36,31.5),('R124','100k','USB_PATH_SEL','GND',28,58),('R125','10k','VCC_3V3','SD_CARD_DETECT_N',18,15),('R126','10k','VCC_3V3','KEY_POWER_SENSE_N',25,12),('R127','100k','DAC_RESET_N','GND',24,40)]:passive(ref,value,n1,n2,x,y,side='B')
# Stock antenna connector; matching values require RF measurement on this PCB.
add('JRF1','Hirose U.FL-R-SMT-1','Connector_Coaxial/U.FL_Hirose_U.FL-R-SMT-1_Vertical',{'1':'RF_ANT','2':'GND'},30,5,0,group='CORE_RF')
# Always-on 3.3 V supplies the existing controls board and GEK. Five MOSFET
# channels isolate the switched MCU domain, preserving the finished FPC pinout.
add('U20','TLV75533PDBVR','Package_TO_SOT_SMD/SOT-23-5',{'1':'VCC','2':'GND','3':'VCC','5':'VCC_3V3_AON'},23,39,0,'B','POWER_AON',pins={str(i):{'name':n,'type':t} for i,n,t in [(1,'IN','power_in'),(2,'GND','power_in'),(3,'EN','input'),(4,'NC','no_connect'),(5,'OUT','power_out')]})
passive('C130','2.2uF','VCC','GND',20.5,39,90,'B',group='POWER_AON');passive('C131','2.2uF','VCC_3V3_AON','GND',25.5,39,90,'B',group='POWER_AON')
assign('U6','6','VCC_3V3_AON');assign('FPC1','2','VCC_3V3_AON')
for i,(src,dst,pad) in enumerate([('SYS_I2C_SDA','CTRL_SDA_AON','3'),('SYS_I2C_SCL','CTRL_SCL_AON','4'),('CTRL_INT_N','CTRL_INT_AON_N','5'),('CTRL_RESET_N','CTRL_RESET_AON_N','6'),('KEY_POWER_SENSE_N','KEY_RAW_N','11')]):
 add('Q'+str(101+i),'BSS138','Package_TO_SOT_SMD/SOT-23',{'1':'VCC_3V3','2':src,'3':dst},20+i*4,44,90,'B','POWER_AON',pins={'1':{'name':'G','type':'input'},'2':{'name':'S','type':'passive'},'3':{'name':'D','type':'passive'}})
 assign('FPC1',pad,dst)
 # Existing small board carries AON-side pullups; host-side pullups are retained.
passive('R128','10k','VCC_3V3','CTRL_RESET_N',36,42,0,'B',group='POWER_AON')
passive('C132','100nF','VCC_3V3_AON','GND',23,41,0,'B',group='POWER_AON')
# AON one-shot holds GEK RST after the switched MCU loses power.
add('U21','SN74LVC1G123DCUR','Package_SO/VSSOP-8_2.3x2mm_P0.5mm',{'1':'GND','2':'POWER_OFF_REQ','3':'OFF_CLEAR_N','4':'GND','5':'GEK_RST','6':'OFF_CEXT','7':'OFF_RC','8':'VCC_3V3_AON'},27,46.5,0,'B','POWER_AON',pins={str(i):{'name':n,'type':t} for i,n,t in [(1,'A_N','input'),(2,'B','input'),(3,'CLR_N','input'),(4,'GND','power_in'),(5,'Q','output'),(6,'CEXT','passive'),(7,'REXT_CEXT','passive'),(8,'VCC','power_in')]})
for ref,val,n1,n2,x,y in [('R129','100k','POWER_OFF_REQ','GND',24,46),('R130','200k','VCC_3V3_AON','OFF_RC',29.5,46),('C133','1uF','OFF_CEXT','OFF_RC',29.5,47.5),('R131','100k','VCC_3V3_AON','OFF_CLEAR_N',25,49),('C134','100nF','OFF_CLEAR_N','GND',27,49),('C135','100nF','VCC_3V3_AON','GND',29,49)]:passive(ref,val,n1,n2,x,y,side='B',group='POWER_AON')
# Proper two-transistor UART auto-download; remove original direct 0R links.
add('Q106','MMBT3904','Package_TO_SOT_SMD/SOT-23',{'1':'AUTO_EN_B','2':'CH343P_UART_RTS','3':'CHIP_PU'},31.5,52,0,'B','DOWNLOAD',pins={str(i):{'name':n,'type':'passive'} for i,n in enumerate(['B','E','C'],1)})
add('Q107','MMBT3904','Package_TO_SOT_SMD/SOT-23',{'1':'AUTO_BOOT_B','2':'CH343P_UART_DTR','3':'BOOT_DOWNLOAD_N'},35.5,52,0,'B','DOWNLOAD',pins={str(i):{'name':n,'type':'passive'} for i,n in enumerate(['B','E','C'],1)})
passive('R132','10k','CH343P_UART_DTR','AUTO_EN_B',31.5,54.5,0,'B',group='DOWNLOAD');passive('R133','10k','CH343P_UART_RTS','AUTO_BOOT_B',35.5,54.5,0,'B',group='DOWNLOAD')
# Recovery pads use exposed copper, no paste or pin-header volume.
for i,(name,x,y) in enumerate([('GND',38,23),('CHIP_PU',40,23),('BOOT_DOWNLOAD_N',42,23),('USB_DEBUG_DM',38,25),('USB_DEBUG_DP',40,25),('VCC_3V3',42,25)]):add('TP'+str(101+i),name,'TestPoint/TestPoint_Pad_D1.0mm',{'1':name},x,y,0,'B','DOWNLOAD')
# Provide local BTB decoupling. Screen supply remains the user's chosen 3.3 V.
passive('C136','100nF','VCC_3V3','GND',33,31.5,0,'B',group='DISPLAY');passive('C137','4.7uF','VCC_3V3','GND',31,31.5,0,'B',group='DISPLAY')
# Low-profile battery/motor solder pads remain at the established mechanical positions.
for ref in ['CN2','CN3']:components[ref]['value']='Solder wire pads';b.FindFootprintByReference(ref).SetValue('Solder wire pads')
# Rebuild a portable, footprint-per-reference library and deterministic linkage.
for f in b.GetFootprints():
 ref=f.GetReference();c=components[ref];fp='FP_'+ref
 c['nets']={a.GetNumber():a.GetNetname() for a in f.Pads() if a.GetNumber()}
 c['x']=round(p.ToMM(f.GetPosition().x)-origin[0],6);c['y']=round(p.ToMM(f.GetPosition().y)-origin[1],6)
 c['angle']=f.GetOrientationDegrees();c['side']='B' if f.IsFlipped() else 'F';c['footprint']=fp;c['dnp']=f.IsDNP()
 c['uuid']=uid(ref);f.SetFPID(p.LIB_ID('V2',fp))
 for field in f.GetFields():
  field.SetLayer(p.B_Fab if f.IsFlipped() else p.F_Fab);field.SetVisible(field.GetName()=='Reference')
 for a in f.Pads():
  if a.GetNumber():a.SetPinFunction(c['pins'].get(a.GetNumber(),{}).get('name',a.GetNumber()))
 # Copy reachable pre-existing models; discard absent importer paths.
 for model in list(f.Models()):
  raw=str(model.m_Filename)
  if raw.startswith('${KIPRJMOD}'):
   source=(PLAN/raw.replace('${KIPRJMOD}/','')).resolve()
   if source.is_file():
    target=P/'models3d'/source.name
    if not target.exists():shutil.copy2(source,target)
    model.m_Filename='${KIPRJMOD}/models3d/'+target.name
 f.SetLibDescription(c['source'])
 p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(P/'V2.pretty'),f)
b.SetCopperLayerCount(6)
p.SaveBoard(str(outfile),b)
project=json.loads((PLAN/'q2-v2-placement.kicad_pro').read_text(encoding='utf8'))
project['board']['design_settings']['rules'].update({'min_clearance':.1,'min_track_width':.1,'min_via_diameter':.45,'min_through_hole_diameter':.2,'min_hole_clearance':.25,'min_copper_edge_clearance':.25})
project['net_settings']['classes']=[{'name':'Default','description':'V2 signal 0.15mm, 0.1mm clearance','clearance':.1,'track_width':.15,'via_diameter':.45,'via_drill':.2,'diff_pair_width':.15,'diff_pair_gap':.15,'diff_pair_via_gap':.25,'microvia_diameter':.3,'microvia_drill':.1,'wire_width':6,'bus_width':12,'line_style':0,'pcb_color':'rgba(0, 0, 0, 0.000)','schematic_color':'rgba(0, 0, 0, 0.000)'}]
(P/'q2-v2.kicad_pro').write_text(json.dumps(project,indent=2),encoding='utf8')
(P/'fp-lib-table').write_text('(fp_lib_table (lib (name "V2") (type "KiCad") (uri "${KIPRJMOD}/V2.pretty") (options "") (descr "Project-local V2 footprints")))\n')
(P/'output/design-contract.json').write_text(json.dumps({'status':'ELECTRICAL_CANDIDATE_UNROUTED','origin':origin,'components':components,'core_reference_map':core_refs,'sources':{'source_pcb_sha256':hashlib.sha256((ROOT/'hardware-q2/ProPrj_esp32s31-mp4_2026-09-22.kicad_pcb').read_bytes()).hexdigest()}},ensure_ascii=False,indent=2),encoding='utf8')
print('Saved V2 candidate:',len(components),'components',len(netmap),'nets',flush=True)





