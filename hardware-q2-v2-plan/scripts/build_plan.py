"""Placement study only. Run with KiCad 10 Python; production sources are read-only."""
from pathlib import Path
import sys,json,hashlib,shutil,math,csv
import pcbnew as p
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'hardware-q2-v2-plan'
sys.path.insert(0,str(Path(__file__).resolve().parent))
from sexpr import parse,dump,children,get,prop,S
SRC=ROOT/'hardware-q2/ProPrj_esp32s31-mp4_2026-09-22.kicad_pcb'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
source_hash=sha(SRC)
origin=(128.868,67.647)
removed={'U9':'Module replaced by bare-chip design reserve', 'FPC2':'Replaced by front BTB candidate',
 'U16':'Old TFT backlight boost is not used by AMOLED','L4':'Old TFT backlight boost',
 'C42':'Old TFT backlight boost','C55':'Old TFT backlight boost','C56':'Old TFT backlight boost',
 'C57':'Old TFT backlight boost','R40':'Old TFT backlight current sense','R41':'Old TFT boost enable pull-down'}
tree=parse(SRC.read_text(encoding='utf8'))
tree[:]=[n for n in tree if not (isinstance(n,list) and n and (n[0] in ['segment','arc','via','zone','group'] or (n[0]=='footprint' and prop(n,'Reference')[2] in removed) or (n[0].startswith('gr_') and (get(n,'layer') or [0,0])[1]!='Edge.Cuts')))]
base=OUT/'q2-v2-placement.kicad_pcb'
base.write_text(dump(tree),encoding='utf8')
b=p.LoadBoard(str(base));fs={f.GetReference():f for f in b.GetFootprints()}
original=p.LoadBoard(str(SRC))
before={}
for f in original.GetFootprints():
 r=f.GetReference()
 before[r]=dict(ref=r,x=p.ToMM(f.GetPosition().x)-origin[0],y=p.ToMM(f.GetPosition().y)-origin[1],
  angle=f.GetOrientationDegrees(),side=original.GetLayerName(f.GetLayer()),
  pads=[dict(n=a.GetNumber(),net=a.GetNetname(),x=p.ToMM(a.GetPosition().x),y=p.ToMM(a.GetPosition().y)) for a in f.Pads()])
values={}
for sch in (ROOT/'hardware-q2').glob('*.kicad_sch'):
 for s in children(parse(sch.read_text(encoding='utf8')),'symbol'):
  r=prop(s,'Reference');v=prop(s,'Value')
  if r and v:values[str(r[2])]=str(v[2])
reasons={r:'Existing relative placement retained' for r in fs}
def put(ref,x,y,angle=None,side=None,reason=''):
 f=fs[ref]
 if side and (f.GetLayer()==p.F_Cu)!=(side=='F'):f.Flip(f.GetPosition(),p.FLIP_DIRECTION_LEFT_RIGHT)
 if angle is not None:f.SetOrientationDegrees(angle)
 f.SetPosition(p.VECTOR2I(p.FromMM(x+origin[0]),p.FromMM(y+origin[1])))
 if reason:reasons[ref]=reason
def translate(refs,dx,dy,reason):
 for r in refs.split():
  a=before[r];put(r,a['x']+dx,a['y']+dy,reason=reason)

# Translate sensitive local circuits as groups, preserving their pad relationships.
translate('U2 X1 C8 C17 C18 C19 C20 C21 C22 C23 C24 C25 C26 C27 C28 C29 C32 C33',0,0,
          'DAC local circuit retained: moving downward conflicts with motor carrier')
translate('U7 R17 R18 R19 C34',0,3,'Level translator between MCU corridor and DAC')
translate('U8 C35',0,3,'I2S translator between MCU corridor and DAC')
translate('U5 C30 C31',-9.818,.543,'1.8V audio LDO adjacent to DAC, separated from switching regulator')
translate('U12 C44 C37 C38 C51 R27 R28',-3.848,14.044,
          'USB-UART bridge beside USB mux; avoids long differential pair branch')
# SD pullups stay beneath the fixed socket. Existing external data Flash is not
# silently treated as the module internal boot flash (its value is only 16 Mbit).
put('U10',18.6,28.2,270,'F','Flash below-left of S31; clock pins toward core; boot flash capacity selection remains open')
put('C13',22,24.6,0,'F','Local Flash decoupling near pin 8; not a completed bare-chip VDD_SPI circuit')
for r,x,y in [('R29',22,11),('C39',23.5,11),('C40',24,15),('C41',26,15),
              ('C45',32,23),('C46',34,23),('R20',34,20),('R25',36,20)]:
 put(r,x,y,side='B',reason='Provisional core support on back; reassess after bare-chip pinout')
for r,x,y in [('R45',34,33.5),('R46',36,33.5),('R26',20,34),('R30',22,34),
              ('R22',28,36),('R10',29.5,36),('R42',34,38),('R6',36,38),
              ('R43',38,38),('R7',39.5,40),('R8',41,40),('R44',39,57.5)]:
 put(r,x,y,side='B',reason='Pullups/pulldowns grouped by destination bus')
translate('U14 C61 R2 C43 R33 R34',0,4,'Battery gauge and local network closer to battery pads')
translate('U1 C53 C54',-4,0,'RTC separate from switching power; I2C bus corridor')
for r,x,y in [('U11',38,62),('C4',33.5,62),('C5',42,59.8),('C58',40.5,59.8),('L3',42,57.8)]:
 put(r,x,y,reason='Motor driver grouped close to motor wire pads')
for r,x,y in [('R27',28.7,51.2),('R28',28.7,52.5),('C38',23.5,52.1),('C37',28.7,54.4),
              ('C53',30.2,43.3),('C54',31.3,45.3),('C58',39.5,59.1),('C11',32,58.5),('C31',17.8,53.5)]:
 put(r,x,y,reason='Local clearance refinement while keeping destination circuit close')
put('D1',34.45,66,180,'B','USB ESD behind connector input pads; short paired vias before protected bus to mux')

# Mechanical anchors remain at source locations, including FPC1 and solder-wire pads.
anchors=['SCREW1','SCREW2','SCREW3','SCREW5','USB1','CN1','CARD2','FPC1','CN2','CN3']
for r in anchors:fs[r].SetLocked(True);reasons[r]='Locked enclosure/interface anchor'

# Add the real BTB land pattern, with explicitly provisional 90-degree orientation.
lib=ROOT/'hardware-display-adapter/am213-fpc-adapter/Adapter.pretty'
f=p.FootprintLoad(str(lib),'OK23GF024');f.SetReference('JDISP1');f.SetValue('OK-23GF024-04');b.Add(f);fs['JDISP1']=f
put('JDISP1',30,29.2,90,'F','Front BTB candidate; verify native screen tail folding and pin 1 before freeze')
f.SetFPID(p.LIB_ID('V2_Plan','OK23GF024'))
mapping={1:'ESP_IO47',2:'GND',3:'AM213_TE_RESERVED',4:'ESP_SPI2_CS',5:'ESP_SPI2_CLK',6:'ESP_SPI2_D1',7:'ESP_SPI2_D0',8:'GND',
 11:'VCC_3V3',12:'VCC_3V3',13:'GND',14:'GND',15:'VCC_3V3',16:'VCC_3V3',17:'ESP_IO54',18:'ESP_IO57',19:'ESP_I2C2_SDA',20:'ESP_I2C2_SCL',21:'GND',22:'ESP_SPI2_D3',23:'ESP_SPI2_D2',24:'ESP_IO46'}
nets={str(n.GetNetname()):n for n in b.GetNetsByNetcode().values()}
for name in set(mapping.values())-set(nets):
 n=p.NETINFO_ITEM(b,name);b.Add(n);nets[name]=n
for pad in f.Pads():
 name='GND' if pad.GetNumber()=='MP' else mapping.get(int(pad.GetNumber()))
 if name:pad.SetNet(nets[name])

reserves=[
 dict(id='CORE',box=[21,8,38,25],side='F',label='ESP32-S31 + XTAL + DECOUPLING / DESIGN RESERVE'),
 dict(id='RF',box=[27,2,40,7],side='FB',label='RF / ANTENNA OPTIONS - NOT FINAL KEEPOUT'),
 dict(id='BTB',box=[24.5,26.2,35.5,32.2],side='F',label='BTB + MATING / 90 OR 270 DEG TBD'),
 dict(id='BUS',box=[24,33,29,49],side='F',label='DIGITAL ROUTING CORRIDOR'),
 dict(id='FFC',box=[0,46.15,18,53.3],side='B',label='CONTROL FFC ACCESS - NO NEW COMPONENTS'),
 dict(id='XTAL',box=[35.5,10,42.5,15],side='F',label='40MHz crystal + matching reservation; not actual components'),
]
core=dict(part_candidate='ESP32-S31NRV16',body_mm=[8,8],height_mm=[.8,.85,.9],pitch_mm=.35,ep_nominal_mm=[6.5,6.5],
 center_local_mm=[30,17],kicad_angle_deg=-90,pin1_corner='upper-right',body_box=[26,13,34,21],
 status='DOCUMENTATION_GEOMETRY_ONLY_NO_ELECTRICAL_FOOTPRINT',source='esp32-s31_datasheet_en.pdf',source_pages=[16,17,35,104],
 source_sha256=sha(ROOT/'esp32-s31_datasheet_en.pdf'))
def line(a,z,layer=p.Dwgs_User):
 sh=p.PCB_SHAPE();sh.SetShape(p.SHAPE_T_SEGMENT);sh.SetStart(p.VECTOR2I(*[p.FromMM(v) for v in a]));sh.SetEnd(p.VECTOR2I(*[p.FromMM(v) for v in z]));sh.SetLayer(layer);sh.SetWidth(p.FromMM(.1));b.Add(sh)
def label(s,x,y,size=.7):
 t=p.PCB_TEXT(b);t.SetText(s);t.SetPosition(p.VECTOR2I(p.FromMM(x+origin[0]),p.FromMM(y+origin[1])));t.SetLayer(p.Dwgs_User);t.SetTextSize(p.VECTOR2I(p.FromMM(size),p.FromMM(size)));t.SetTextThickness(p.FromMM(.1));b.Add(t)
for r in reserves:
 x1,y1,x2,y2=r['box'];pts=[(x1,y1),(x2,y1),(x2,y2),(x1,y2)]
 for i in range(4):line(tuple(pts[i][j]+origin[j] for j in range(2)),tuple(pts[(i+1)%4][j]+origin[j] for j in range(2)),p.Cmts_User if r['side']=='B' else p.Dwgs_User)
 label(r['id'],(x1+x2)/2,(y1+y2)/2,1)
pts=[(26,13),(34,13),(34,21),(26,21)]
for i in range(4):line(tuple(pts[i][j]+origin[j] for j in range(2)),tuple(pts[(i+1)%4][j]+origin[j] for j in range(2)))
label('S31 QFN80 8x8\n-90deg / BODY ONLY',30,17,.55)
label('1',33.4,13.6,.55)
label('V2 PLACEMENT STUDY - UNROUTED / CORE SCHEMATIC MISSING',23,-4,1)
label('46 x 76 mm / DATUM upper-left Edge.Cuts / TOP VIEW',23,79,.8)
b.GetDesignSettings().SetAuxOrigin(p.VECTOR2I(*[p.FromMM(v) for v in origin]))
b.GetDesignSettings().SetGridOrigin(p.VECTOR2I(*[p.FromMM(v) for v in origin]))

# Reuse available nominal local STEP models instead of source's broken EASYEDA paths.
modelref={q['ref']:q for q in json.loads((ROOT/'mechanical/final-board-review/mainboard-reference.json').read_text())['footprints']}
for r,f in fs.items():
 f.SetValue(values.get(r,f.GetValue()))
 if r in ['CN2','CN3']:
  f.SetValue('SOLDER_WIRES_3P' if r=='CN2' else 'SOLDER_WIRES_2P')
  for g in list(f.GraphicalItems()):f.Remove(g)
  reasons[r]='Locked original solder-pad positions; omit tall header, use insulated wires'
 f.Value().SetVisible(False);f.Reference().SetVisible(True)
 models=f.Models();models.clear()
 model=modelref.get(r,{}).get('model')
 if r=='JDISP1':model='hardware-display-adapter/am213-fpc-adapter/models3d/OK-23GF024-04.step'
 if model:
  m=p.FP_3DMODEL();m.m_Filename='${KIPRJMOD}/../'+model;m.m_Scale=p.VECTOR3D(1,1,1)
  if r=='U10':m.m_Rotation=p.VECTOR3D(0,0,90) # Existing nominal model has lead span on X, footprint zero-degree span is on Y.
  models.push_back(m)
 f.Reference().SetTextSize(p.VECTOR2I(p.FromMM(.65),p.FromMM(.65)));f.Reference().SetTextThickness(p.FromMM(.1))
 f.Reference().SetLayer(p.F_Fab if f.GetLayer()==p.F_Cu else p.B_Fab)
 # Avoid legacy references floating far from moved packages.
 f.Reference().SetPosition(f.GetPosition());f.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
(OUT/'V2_Plan.pretty').mkdir(exist_ok=True)
for r,f in fs.items():
 f.SetFPID(p.LIB_ID('V2_Plan','Plan_'+r))
 p.FootprintSave(str(OUT/'V2_Plan.pretty'),f)
p.SaveBoard(str(base),b)
# Copy board-only project settings; no misleading old module schematic is copied.
shutil.copy2(SRC.with_suffix('.kicad_pro'),base.with_suffix('.kicad_pro'))
(OUT/'V2_Plan.pretty').mkdir(exist_ok=True)
shutil.copy2(lib/'OK23GF024.kicad_mod',OUT/'V2_Plan.pretty/OK23GF024.kicad_mod')
(OUT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "V2_Plan")(type "KiCad")(uri "${KIPRJMOD}/V2_Plan.pretty")(options "")(descr "V2 planning footprint")))\n')

def bbbox(bb):return [round(p.ToMM(bb.GetX())-origin[0],4),round(p.ToMM(bb.GetY())-origin[1],4),round(p.ToMM(bb.GetRight())-origin[0],4),round(p.ToMM(bb.GetBottom())-origin[1],4)]
data=[]
for r,f in fs.items():
 xy=[round(p.ToMM(f.GetPosition()[i])-origin[i],4) for i in range(2)]
 pads=[dict(number=a.GetNumber(),net=a.GetNetname(),xy=[round(p.ToMM(a.GetPosition()[i])-origin[i],4) for i in range(2)],box=bbbox(a.GetBoundingBox())) for a in f.Pads()]
 data.append(dict(ref=r,value=f.GetValue(),xy=xy,angle=f.GetOrientationDegrees(),side='F' if f.GetLayer()==p.F_Cu else 'B',box=bbbox(f.GetBoundingBox(False,False)),pads=pads,reason=reasons.get(r),before=before.get(r)))
report=dict(status='PLACEMENT_PLANNING_ONLY_NOT_FOR_FABRICATION',source=str(SRC.relative_to(ROOT)),source_sha256=source_hash,board_sha256=sha(base),datum=list(origin),outline_mm=[46,76],removed=removed,anchors=anchors,reserves=reserves,core_package_plan=core,components=data)
(OUT/'placement.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
with (OUT/'placement-coordinates.csv').open('w',newline='',encoding='utf-8-sig') as h:
 w=csv.writer(h);w.writerow(['Ref','Value','Side','X_from_outline_mm','Y_from_outline_mm','Angle_deg','KiCad_X_mm','KiCad_Y_mm','Reason'])
 for a in sorted(data,key=lambda a:a['ref']):w.writerow([a['ref'],a['value'],a['side'],*a['xy'],a['angle'],round(a['xy'][0]+origin[0],4),round(a['xy'][1]+origin[1],4),a['reason']])
assert sha(SRC)==source_hash
assert len(b.GetTracks())==0 and len(b.Zones())==0
for r in anchors:
 a=next(a for a in data if a['ref']==r);old=before[r]
 assert math.hypot(a['xy'][0]-old['x'],a['xy'][1]-old['y'])<.001,r
print('BUILD',len(data),'components; source unchanged; copper removed in planning copy only')

