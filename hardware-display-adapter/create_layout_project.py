"""Create a placement-only KiCad project; no electrical pads or routing."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'am213-fpc-adapter'
OUT.mkdir(exist_ok=True)
if (OUT/'am213-fpc-adapter.kicad_sch').exists():
    raise SystemExit('Legacy placement generator disabled: completed electrical project exists.')
NAME='am213-fpc-adapter'
LIB=OUT/'Adapter_Placement.pretty'
LIB.mkdir(exist_ok=True)

def footprint(name, reference, value, w, h, note):
    # F.Fab outlines are reserved work areas, deliberately NOT copper lands.
    s=f'''(footprint "{name}"
      (version 20260206) (generator "pcbnew")
      (layer "F.Cu")
      (descr "{note}")
      (attr board_only exclude_from_pos_files exclude_from_bom)
      (property "Reference" "{reference}" (at 0 {-h/2-0.8}) (layer "F.Fab")
        (effects (font (size 0.8 0.8) (thickness 0.12))))
      (property "Value" "{value}" (at 0 {h/2+1.0}) (layer "F.Fab") hide
        (effects (font (size 0.6 0.6) (thickness 0.1))))
      (fp_rect (start {-w/2} {-h/2}) (end {w/2} {h/2})
        (stroke (width 0.12) (type default)) (fill none) (layer "F.Fab"))
      (fp_line (start -0.45 0) (end 0.45 0)
        (stroke (width 0.1) (type default)) (layer "F.Fab"))
      (fp_line (start 0 -0.45) (end 0 0.45)
        (stroke (width 0.1) (type default)) (layer "F.Fab"))
    )'''
    (LIB/(name+'.kicad_mod')).write_text(s,encoding='utf-8')

footprint('BTB_24P_Placement_Only','J2','24P_BTB_MATE_TBD',4,12,
          'PLACEMENT ONLY: 4x12 mm operation envelope; no pads. Mating footprint and Pin 1 TBD.')
footprint('FPC_21P_Exit_Placement_Only','J1','21P_0.3mm_TAIL_EXIT',6.6,3.5,
          'TAIL EXIT ONLY: 21P 0.3mm; width 6.6mm reference. NOT a socket or finished finger footprint. Tail endpoint TBD.')

template=(ROOT/'adapter-outline.kicad_pcb').read_text()
items=[template[:template.index('\t(gr_line')].replace('(pad_to_mask_clearance 0)', '(aux_axis_origin 50 50)\n\t\t(pad_to_mask_clearance 0)')]

def line(a,z,layer='Edge.Cuts',width=.05):
    items.append(f'(gr_line (start {a[0]} {a[1]}) (end {z[0]} {z[1]}) (stroke (width {width}) (type default)) (layer "{layer}"))')

def label(s,x,y,size=.7):
    items.append(f'(gr_text {json.dumps(s)} (at {x} {y}) (layer "Dwgs.User") (effects (font (size {size} {size}) (thickness 0.1))))')

corners=[(50,50),(67,50),(67,72),(50,72)]
for i in range(4):line(corners[i],corners[(i+1)%4])
for name,ref,at in [('BTB_24P_Placement_Only','J2',(52.5,62)),('FPC_21P_Exit_Placement_Only','J1',(58.5,70.25))]:
    fp=(LIB/(name+'.kicad_mod')).read_text()
    fp=fp.replace(f'(footprint "{name}"',f'(footprint "Adapter_Placement:{name}"',1)
    fp=fp.replace('(version 20260206) (generator "pcbnew")','',1)
    fp=fp.replace('(layer "F.Cu")',f'(layer "F.Cu") (at {at[0]} {at[1]})',1)
    items.append(fp)

label('AM213 FPC ADAPTER - PLACEMENT ONLY',58.5,46,.8)
label('17 x 22 mm component island',58.5,48,.7)
label('J2: 24P BTB\nPAD / PIN 1 TBD',60.5,57,.65)
label('No components\nNo copper / no nets\nNo routing',60.5,62,.7)
label('J1: FLEX TAIL EXIT',58.5,74,.65)
line((58.5,75),(58.5,77),'Dwgs.User',.12)
line((58.5,77),(58.1,76.5),'Dwgs.User',.12)
line((58.5,77),(58.9,76.5),'Dwgs.User',.12)
label('UNFOLDED TAIL LENGTH / CONTACT SIDE TBD\nTail is NOT included in Edge.Cuts',58.5,79,.6)
items.append('(embedded_fonts no)\n)')
(OUT/(NAME+'.kicad_pcb')).write_text('\n'.join(items)+'\n')

pro=json.loads((ROOT/'adapter-outline.kicad_pro').read_text())
pro['meta']['filename']=NAME+'.kicad_pro'
(OUT/(NAME+'.kicad_pro')).write_text(json.dumps(pro,indent=2)+'\n')
(OUT/'fp-lib-table').write_text('''(fp_lib_table
  (version 7)
  (lib (name "Adapter_Placement")(type "KiCad")(uri "${KIPRJMOD}/Adapter_Placement.pretty")(options "")(descr "Placement envelopes only - no electrical pads"))
)
''')
(OUT/'README.md').write_text('''# AM213 FPC 转接板定位工程

打开 `am213-fpc-adapter.kicad_pro`，再进入 PCB 编辑器。本工程只有板框及接口定位，没有原理图、电气焊盘、网络、元件电路或走线。

板框：17×22 mm 元件区，KiCad 左上角 (50,50) mm；局部坐标原点在这里，X向右、Y向下。模型对应 X29～46、Y8～30 mm。

| 对象 | KiCad中心 (mm) | 局部中心 (mm) | 含义 |
|---|---|---|---|
| J2 | (52.5,62) | (2.5,12) | 4×12 mm屏幕24P BTB母座操作区占位，长轴沿Y |
| J1 | (58.5,70.25) | (8.5,20.25) | 6.6×3.5 mm尾巴出口参考区，下沿位于板框Y=22；不是插座或尾端金手指 |

两个封装在 F.Fab 层，均可移动，排除在BOM和贴片坐标外；**没有真实焊盘**。J2待取得正式母座图再换封装并核对Pin 1。J1代表从此处引出21P/0.3 mm柔性尾巴，末端位置、实际展开长度和接触面未确定，因此尾巴未画入Edge.Cuts。

工程沿用0.6 mm基板预留厚度，仅为FPC＋补强＋胶层的机械预算，并非生产FPC叠层。局部补强区、弯折半径及金手指最终厚度需随后定义。原板框工程、已生产主板和外壳均未修改。
''',encoding='utf-8')

print('CREATED',OUT)
print('17x22 mm island; J2=(52.5,62); J1 exit=(58.5,70.25); no electrical pads/tracks/zones')

# Apply the verified mechanical model if it has already been built.
if (OUT/'models3d'/'OK-23GF024-04.step').exists():
    from attach_btb_model import update_board
    update_board()
