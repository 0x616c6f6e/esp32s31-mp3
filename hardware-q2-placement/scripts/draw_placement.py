"""Annotated front/back component placement, using the verified native coordinates."""
from pathlib import Path
import json,argparse
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1]
cli=argparse.ArgumentParser();cli.add_argument('--data',type=Path,default=P/'output/placement.json');cli.add_argument('--output',type=Path,default=P/'output/placement-front-back.png')
args=cli.parse_args();data=json.loads(args.data.read_text(encoding='utf8'))
scale=15;W=860;H=1370
im=Image.new('RGB',(W*2,H),'#f5f6f8');d=ImageDraw.Draw(im)
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
title=font(28);small=font(16);tiny=font(10)
palette={'dac':'#a3d1be','clock':'#a3d1be','i2c_level':'#afd6ce','i2s_level':'#afd6ce','analog_ldo':'#afd6ce','charger':'#f4c39b','buck':'#f4c39b','fuel_gauge':'#f4c39b','power_key':'#f4c39b','usb_uart':'#a8c8ec','usb_mux':'#a8c8ec','usb_esd':'#a8c8ec','display':'#d4b6e2','rtc':'#d4b6e2','imu':'#d4b6e2'}
colors={r:palette.get(g,'#cbd3df') for g,gg in data['groups'].items() for r in [gg['anchor']]+gg['support']}
for panel,side in enumerate(['F','B']):
    ox=panel*W+80;oy=140
    def pt(x,y):return (ox+((x-101) if side=='F' else (147-x))*scale,oy+(y-51)*scale)
    def box(b):
        a=pt(b[0],b[1]);c=pt(b[2],b[3]);return (min(a[0],c[0]),min(a[1],c[1]),max(a[0],c[0]),max(a[1],c[1]))
    d.text((panel*W+60,24),'正面 · 屏幕侧' if side=='F' else '背面 · 后盖侧（已镜像）',font=title,fill='#152338')
    d.text((panel*W+60,68),'46 × 76 mm / R10 · 仅元件摆放，无走线',font=small,fill='#526477')
    d.rounded_rectangle(box((101,51,147,127)),radius=10*scale,fill='#e4e9e5',outline='#315347',width=3)
    for yy in [52,126]:d.ellipse(box((121.2,yy-2.8,126.8,yy+2.8)),fill='#f5f6f8',outline='#315347',width=2)
    rf=box((122.592,51.2,144.846,60.669));d.rectangle(rf,outline='#c48038',width=2);d.text((rf[0]+5,rf[1]+10),'天线禁布区',font=small,fill='#a46222')
    for f in data['footprints']:
        r=f['reference']
        if r.startswith('SCREW'):
            x,y=f['xy'];d.ellipse(box((x-1.1,y-1.1,x+1.1,y+1.1)),fill='#f5f6f8',outline='#60746d',width=2);continue
        if f['side']!=side:continue
        bb=box(f['bounds']);d.rectangle(bb,fill=colors.get(r,'#b9c7ce'),outline='#596c78',width=1)
        for pad in f['pads']:
            x,y=pt(*pad['xy']);d.ellipse((x-1.4,y-1.4,x+1.4,y+1.4),fill='#926e2b')
        x=(bb[0]+bb[2])/2;y=(bb[1]+bb[3])/2
        label_font=small if r.startswith(('U','X','H','FPC','CARD','USB','CN')) else tiny
        d.text((x,y),r,font=label_font,fill='#102334',anchor='mm',stroke_width=1,stroke_fill=colors.get(r,'#b9c7ce'))
    d.text((panel*W+60,1300),'绿色：音频　橙色：电源　蓝色：USB　紫色：显示/传感器',font=small,fill='#526477')
im.save(args.output)
print('ANNOTATED_PLACEMENT_SAVED')
