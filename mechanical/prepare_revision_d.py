"""Create revision D from C; preserve the previous deliverable."""
from pathlib import Path
import json, shutil
HERE=Path(__file__).resolve().parent
src=HERE/'enclosure-q2-c';dst=HERE/'enclosure-q2-d'
dst.mkdir(exist_ok=True);(dst/'exports').mkdir(exist_ok=True)
shutil.copytree(src/'reference',dst/'reference',dirs_exist_ok=True)
p=json.loads((src/'parameters.json').read_text(encoding='utf8'))
p['LCDInstalledY']-=1.5;p['LensY']-=1.5
p['FPCServiceRadius']=.675
(dst/'parameters.json').write_text(json.dumps(p,indent=2),encoding='utf8')
for name in ['build_enclosure.py','assembly_layout.py','validate_and_export.py']:
    s=(src/name).read_text(encoding='utf8')
    s=s.replace('Q2_Enclosure_C','Q2_Enclosure_D').replace('ESP32S31_MP3_Q2_C','ESP32S31_MP3_Q2_D')
    s=s.replace('Q2 C / corrected mainboard orientation + control daughterboard','Q2 D / screen raised 1.5 mm / full housing visible')
    s=s.replace("'revision':'C'","'revision':'D'").replace('q2-c-','q2-d-').replace('assembly-C-with-current-PCB','assembly-D-current-PCB-CONFLICTS').replace('ASSEMBLY_C_COMPLETE','ASSEMBLY_D_COMPLETE')
    if name=='assembly_layout.py':
        start=s.index('fpc2_shape=')
        end=s.index('\ntarget=',start)
        s=s[:start]+'''fpc2_shape=Part.makeBox(3.2,7.9,1.0,V(7.652,14.084,main_z-1.0))
fpc2=ref('ScreenConnectorFPC2','FPC2 / rear / verified 1.0 mm height',fpc2_shape,(.70,.22,.18),'AFE03 drawing:7.9 x3.2 x1.0, lower contact, FPC0.20 +/-0.03. Internal slot Z and screen tail thickness unconfirmed. Solid outer envelope, no fictional slot.')
''' +s[end:]
        s=s.replace('tipx=8.352;tipy=18.034','tipx=8.352;tipy=cy')
        s=s.replace("'屏幕 FPC / 正面绕左板边至背面 FPC2'","'屏幕 FPC / 上移1.5 mm后的自然轴线，尚未插接'")
        s=s.replace('Centerline route nominal46.14 mm. Side jog is a routing envelope, not a proven developable fold. R0.65/R0.45 and contact slot are assumed. Do not fabricate from this folded ribbon.','Centerline46.14 mm; no lateral shear. Natural axisY20.400 vs socketY18.034, mismatch2.366. R0.65/R0.675 and tip X/Z are assumptions; not mated or fabrication-ready.')
        s=s.replace("'LCD front -> LEFT edge wrap -> rear service loop -> existing FPC2 (under ESP32)'","'LCD front -> LEFT edge wrap -> rear loop; UNMATED, Y offset2.366 mm'")
    if name=='validate_and_export.py':
        # Outer solid is not a connector slot; report overlap separately from the shell checks.
        s=s.replace("pairs += [(control_screws,battery),(control_screws,control),(fpc,fpc2)]","pairs += [(control_screws,battery),(control_screws,control)]\nchecks['unmated_fpc_vs_socket_envelope_mm3']=round(fpc.Shape.common(fpc2.Shape).Volume,6)\nchecks['screen_shift_up_mm']=1.5\nchecks['screen_fpc_axis_offset_mm']=round(tipy-18.034,6)\nchecks['screen_fpc']['mated']=False")
    (dst/name).write_text(s,encoding='utf8')
print(dst)
