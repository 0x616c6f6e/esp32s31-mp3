"""Readable enclosure-coordinate plan from the checked component/cable data."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[2];O=P/'mechanical/connector-layout'
r=json.loads((O/'fit-check.json').read_text());layout=json.loads((P/'hardware-q2-placement/output/placement.json').read_text(encoding='utf8'))
im=Image.new('RGB',(1140,1020),'#f5f7fa');d=ImageDraw.Draw(im);S=10
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
def point(x,y):return (65+x*S,120+y*S)
def box(a,b,c,e):return (*point(a,b),*point(c,e))
d.text((45,30),'H1 马达 / H2 电池 · 内部位置规划',font=font(30),fill='#142638')
d.text((45,76),'尺寸单位 mm · 外壳坐标示意 · 主板正面 / 屏幕侧',font=font(18),fill='#52677b')
d.rounded_rectangle(box(0,0,50,80),radius=120,fill='#d2d7dd',outline='#4b5b6b',width=3)
d.rounded_rectangle(box(2,2,48,78),radius=100,fill='#e2eee6',outline='#708b79',width=2)
for f in layout['footprints']:
    if f['side']!='F' or f['reference'].startswith('SCREW') or f['reference'] in ['H1','H2']:continue
    x0,y0,x1,y1=f['bounds'];d.rectangle(box(149-x1,y0-49,149-x0,y1-49),fill='#c1cfc6',outline='#9eafa4')
d.rounded_rectangle(box(3.275,2.235,46.725,38.565),radius=55,outline='#7c8c9b',width=2)
d.text(point(8,6),'屏幕所在区域',font=font(18),fill='#6e7f8c')
d.rectangle(box(8.3,37,32.3,71),fill='#b5cce0',outline='#527b9d',width=2)
d.text(point(14,43),'电池预留',font=font(20),fill='#284b68')
d.text(point(14,47),'24 × 34 × 3',font=font(18),fill='#284b68')
d.text(point(14,51),'成品型号待定',font=font(16),fill='#284b68')
for name,route in r['wire_centerlines_case_mm'].items():
    color='#d88c2d' if name.startswith('Motor') else {'BatteryWire1':'#c04747','BatteryWire2':'#b19420','BatteryWire3':'#465466'}[name]
    d.line([point(x,y) for x,y,z in route],fill=color,width=3)
d.ellipse(box(34.4,52.4,43.6,61.6),fill='#b98442',outline='#7b542a',width=2)
d.ellipse(box(35,53,43,61),fill='#f0c46b',outline='#885e21',width=2)
d.text(point(39,57),'LRA',font=font(16),anchor='mm',fill='#674717')
for ref,n in [('H1',2),('H2',3)]:
    c=layout['connector_revision'][ref];x,y=c['case_xy_mm'];hw=(4.2 if n==2 else 5.4)/2
    d.rectangle(box(x-2,y-hw,x+2.3,y+hw),fill='#fffdf1',outline='#725e37',width=2)
    d.text(point(x,y),ref,font=font(18),anchor='mm',fill='#42361c')
notes=[('H1 · 两芯马达端子','JST BM02B-ACHSS-GAN-ETF','PCB (130, 113) / F.Cu / −90°'),('H2 · 三芯电池端子','JST BM03B-ACHSS-GAN-ETF','PCB (142, 109) / F.Cu / −90°'),('马达候选 · C08-005','中心 (39, 57)，底面 Z = 7.1','最大包络 Ø8.1 × 3.45'),('装配关系','线束先插好，再装电池和操作小板','马达距小板 0.55，距电池 2.65'),('当前状态','无新增 PCB 走线；网络保持','端子 / 马达 / 线束相交检查通过')]
for i,(title,a,b) in enumerate(notes):
    yy=150+i*145;d.text((625,yy),title,font=font(23),fill='#20364b');d.text((625,yy+42),a,font=font(18),fill='#516477');d.text((625,yy+75),b,font=font(17),fill='#516477')
d.text((50,955),'规划模型：线束画出的是通道；电池性能、公差与实物装配仍需确认。',font=font(18),fill='#52677b')
im.save(O/'connector-plan.png')
