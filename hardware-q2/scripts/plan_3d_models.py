"""Match package models by numbered pad positions, without changing PCB geometry."""
from pathlib import Path
import sys,json,math,shutil,hashlib
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'tmp'));from sexpr import *
K=Path('D:/KiCad/10.0/share/kicad');OUT=P/'models3d';OUT.mkdir(exist_ok=True);(OUT/'vendor').mkdir(exist_ok=True)
mapping={
'SOT-23-5_L3.0-W1.7-P0.95-LS2.8-BR':'Package_TO_SOT_SMD:SOT-23-5',
'SOT-23-5_L3.0-W1.7-P0.95-LS2.8-BR_1':'Package_TO_SOT_SMD:SOT-23-5',
'SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL':'Package_TO_SOT_SMD:SOT-23-6',
'SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL-2':'Package_TO_SOT_SMD:SOT-23-6',
'SOD-123_L2.8-W1.8-LS3.7-RD':'Diode_SMD:D_SOD-123',
'MSOP-10_L3.0-W3.0-P0.50-LS4.9-BL':'Package_SO:MSOP-10_3x3mm_P0.5mm',
'VSSOP-10_L3.0-W3.0-P0.50-LS4.9-BL':'Package_SO:MSOP-10_3x3mm_P0.5mm',
'QFN-40_L5.0-W5.0-P0.40-TL-EP3.6_1':'Package_DFN_QFN:QFN-40-1EP_5x5mm_P0.4mm_EP3.6x3.6mm',
'TQFN-16_L3.0-W3.0-P0.50-BL-EP1.7':'Package_DFN_QFN:QFN-16-1EP_3x3mm_P0.5mm_EP1.7x1.7mm',
'WQFN-24_L4.0-W4.0-P0.50-TL-EP2.7':'Package_DFN_QFN:Texas_RTW_WQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm',
'LGA-14_L3.0-W2.5-P0.50-TL':'Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y',
'CRYSTAL-SMD_4P-L3.2-W2.5-BL_1':'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm',
'L0603':'Inductor_SMD:L_0603_1608Metric',
}
custom={
'CONN-SMD_ESP32-S31-WROOM-3':{'kind':'esp32s31','bounds':[-11,-18,11,12],'height':3.5,'quality':'datasheet-derived simplified model','source':'hardware/reference/esp32-s31-wroom-3.pdf p64; PCB1.0, overall3.5, shield21x23; antenna metal pattern omitted'},
'CONN-TH-21P_AFE03-S21FMA-1H':{'kind':'fpc','bounds':[-3.95,-1.2,3.95,2],'height':1.0,'quality':'drawing-derived simplified model','source':'mechanical/display-fit/reference/AFE03-S21FMA-1H.pdf; 21pin,7.9x3.2x1.0; internal slot not dimensionally validated'},
'AUDIO-SMD_PJ-342B-TX-SMT':{'kind':'jack','bounds':[-8.835,-3.12,5.165,3.28],'height':4.5,'quality':'approximate connector model','source':'source footprint Fab and missing EasyEDA model filename; height4.5 unverified'},
'USB-C-SMD_TYPE-C-16PIN-2MD-073':{'kind':'usb','bounds':[-4.5,-.597,4.572,4.975],'height':3.2,'quality':'approximate connector model','source':'source footprint Fab; height3.2 and socket details assumed; 16pin footprint, not the old6pin model reference'},
'TF-SMD_TF-PUSH':{'kind':'tf','bounds':[-7.24,-4.8,8,9.7],'height':1.8,'quality':'approximate connector model','source':'source footprint Fab; height1.8 assumed; no exact manufacturer model'},
'HDR-TH_2P-P2.54-V-F':{'kind':'socket','bounds':[-2.74,-1.25,2.74,1.25],'height':5.5,'quality':'approximate low-profile connector model','source':'source footprint; socket height5.5 assumed to match existing mechanical reservation, actual part not selected'},
'HDR-TH_3P-P2.54-V-M':{'kind':'header','bounds':[-3.81,-1.25,3.81,1.25],'height':5.5,'quality':'approximate short-pin connector model','source':'source footprint; pin protrusion chosen within5.5 reservation, actual part not selected'},
'IND-SMD_L2.0-W1.6':{'kind':'chip','bounds':[-1,-.8,1,.8],'height':1.1,'quality':'generic package model','source':'source footprint Fab and missing EasyEDA model filename; manufacturer height unverified'},
'RTC-SMD_L3.2-W2.5-P0.7-RX8130CE':{'kind':'rtc','bounds':[-1.25,-1.6,1.25,1.6],'height':1.0,'quality':'generic package model','source':'source footprint Fab; height1.0 assumed'},
'DFN-10_L3.0-W2.0-P0.50-BL':{'kind':'ic','bounds':[-1.5,-1,1.5,1],'height':.6,'quality':'generic package model','source':'source footprint Fab and pad layout; height0.6 assumed; no exposed pad invented'},
'VQFN-14_L3.5-W3.5-P0.50-BL-EP':{'kind':'ic','bounds':[-1.75,-1.75,1.75,1.75],'height':1.0,'quality':'generic package model','source':'source footprint Fab and pad layout; height from old missing model filename'},
'X2SON-8_L1.4-W1.0-P0.35-BL':{'kind':'ic','bounds':[-.7,-.5,.7,.5],'height':.4,'quality':'generic package model','source':'source footprint Fab and pad layout; height from old missing model filename'},
}
def pads(t):return {a[1]:tuple(map(float,get(a,'at')[1:3])) for a in children(t,'pad') if a[1]}
board=parse((P/'hardware.kicad_pcb').read_text(encoding='utf8'));refs={}
for f in children(board,'footprint'):refs.setdefault(str(f[1]).split(':')[-1],[]).append(prop(f,'Reference')[2])
plan=[]
for path in sorted((P/'MP3_Source.pretty').glob('*.kicad_mod')):
    name=path.stem;t=parse(path.read_text(encoding='utf8'))
    if name.startswith('MountingHole'):continue
    std=mapping.get(name)
    for prefix,package,lib in [('R0402','R_0402_1005Metric','Resistor_SMD'),('R1206','R_1206_3216Metric','Resistor_SMD'),('C0402','C_0402_1005Metric','Capacitor_SMD'),('C0603','C_0603_1608Metric','Capacitor_SMD'),('C0805','C_0805_2012Metric','Capacitor_SMD')]:
        if name.startswith(prefix):std=lib+':'+package
    entry={'footprint':name,'references':sorted(refs[name]),'file':name+'.step','pads':[{'number':a[1],'position':list(map(float,get(a,'at')[1:3])),'size':list(map(float,get(a,'size')[1:3])),'angle':float(get(a,'at')[3]) if len(get(a,'at'))>3 else 0,'type':a[2]} for a in children(t,'pad')]}
    if std:
        lib,stem=std.split(':');s=parse((K/'footprints'/(lib+'.pretty')/(stem+'.kicad_mod')).read_text(encoding='utf8'));a,b=pads(t),pads(s);keys=set(a)&set(b)
        best=None
        for deg in [0,90,180,270]:
            r=math.radians(deg);rot=lambda q:(q[0]*math.cos(r)-q[1]*math.sin(r),q[0]*math.sin(r)+q[1]*math.cos(r));bb={k:rot(b[k]) for k in keys};off=[sum(a[k][j]-bb[k][j] for k in keys)/len(keys) for j in range(2)];err=max(math.dist(a[k],[bb[k][j]+off[j] for j in range(2)]) for k in keys)
            if best is None or err<best[0]-1e-9:best=(err,deg,off)
        model=children(s,'model')[0];rel=str(model[1]).split('}/',1)[1];src=K/'3dmodels'/rel;dest=OUT/'vendor'/src.name
        shutil.copyfile(src,dest)
        entry.update(kind='standard',source_model='vendor/'+src.name,source_library_footprint=std,source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),rotation_z_physical_deg=-best[1],offset_xyz=[best[2][0],-best[2][1],0],pad_centroid_fit_max_error_mm=round(best[0],6),quality='KiCad generic package model; physical height must match ordered part')
        print(name,std,'rotation',-best[1],'pad residual',round(best[0],4))
    else:entry.update(custom[name])
    plan.append(entry)
(OUT/'model-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf8')
print('MODEL_PLAN',len(plan),'FOOTPRINTS',sum(len(e['references']) for e in plan))
