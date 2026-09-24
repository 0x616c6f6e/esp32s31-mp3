from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,math,collections
P=Path(__file__).resolve().parents[1];j=json.loads((P/'placement.json').read_text(encoding='utf8'));parts={a['ref']:a for a in j['components']}
im=Image.new('RGB',(1580,1470),'#eef2f7');d=ImageDraw.Draw(im)
def font(n):return ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
def text(x,y,s,n=23,color='#23394d'):d.text((x,y),s,font=font(n),fill=color)
text(66,30,'Q2 第二版 · 优先布线的元件布局规划',38)
text(68,92,'46 × 76 mm / 六层 / 正面 BTB / 裸芯片电路尚未设计 / 不可直接生产',23,'#62758c')
sc=12.6;y0=207;outline=json.loads((P/'outline.json').read_text())[0]
key={'CARD2':'TF 卡座','U10':'数据 Flash','JDISP1':'屏幕 BTB','U2':'DAC','U5':'1.8 V','U7':'I²C','U8':'I²S','U12':'USB-UART','U17':'USB切换','U3':'充电','U4':'3.3 V','FPC1':'按键 FPC','U14':'电量计','U1':'RTC','U11':'马达','USB1':'USB-C','CN1':'耳机座','U15':'IMU','D1':'USB ESD','CN2':'电池线','CN3':'马达线'}
for side,x0,title in [('F',105,'正面 F.Cu · 面向屏幕'),('B',870,'背面 B.Cu · 从正面透视，坐标不镜像')]:
 text(x0-20,151,title,23)
 def xy(x,y):return(x0+x*sc,y0+y*sc)
 def box(a):return(*xy(a[0],a[1]),*xy(a[2],a[3]))
 d.polygon([xy(*q) for q in outline],fill='#fcfdfb',outline='#45655e',width=3)
 for x in range(0,47,5):
  text(x0+x*sc-6,y0-27,str(x),14,'#71869b')
 for y in range(0,77,5):text(x0-29,y0+y*sc-10,str(y),14,'#71869b')
 for r in j['reserves']:
  if side not in r['side']:continue
  colors={'CORE':'#dbe8fc','RF':'#fbe8c9','BTB':'#d9efeb','BUS':'#e7edf7','FFC':'#f3dce8','XTAL':'#e5ddf5'}
  d.rectangle(box(r['box']),fill=colors[r['id']],outline='#8095a7',width=2)
  labels={'CORE':'','RF':'RF / 天线方案预留','BTB':'','BUS':'数\n字\n走\n线\n通\n道','FFC':'按键排线通道\n禁止新增器件','XTAL':'晶振及匹配'}
  xx,yy=xy((r['box'][0]+r['box'][2])/2,(r['box'][1]+r['box'][3])/2)
  for k,s in enumerate(labels[r['id']].split('\n')):
   w=d.textlength(s,font=font(17));text(xx-w/2,yy-29+k*25,s,17,'#3d6580')
 if side=='F':
  d.rectangle(box(j['core_package_plan']['body_box']),fill='#406783',outline='#1c3d53',width=2)
  for i,s in enumerate(['S31','8 × 8','−90°']):
   w=d.textlength(s,font=font(19));x,y=xy(30,15+i*1.55);text(x-w/2,y-10,s,19,'white')
  x,y=xy(33.4,13.6);d.ellipse((x-3,y-3,x+3,y+3),fill='#ffe890')
  text(*xy(21.8,22.1),'芯片外形 / 无焊盘',16,'#3d6580')
 for a in j['components']:
  r=a['ref']
  if r.startswith('SCREW'):
   x,y=xy(*a['xy']);d.ellipse((x-15,y-15,x+15,y+15),fill='#eef2f7',outline='#75868e',width=2);continue
  if a['side']!=side:continue
  bb=a['box'];d.rectangle(box(bb),fill='#d5e2e0' if r in key else '#e8eeee',outline='#94a5a8',width=1)
  for p in a['pads']:
   d.rectangle(box(p['box']),fill='#c3ac79',outline='#917c4f')
  if r not in key and r not in ['X1','L1','L2','L3','U6']:continue
  x,y=xy(*a['xy']);s=r if r not in key else r+' '+key[r];n=13 if r not in key else 16
  w=d.textlength(s,font=font(n));d.rectangle((x-w/2-2,y-10,x+w/2+2,y+12),fill='#fcfdfbe0'[:7]);text(x-w/2,y-10,s,n)
 text(x0+150,y0+980,'X →  /  Y ↓  /  单位 mm',19,'#62758c')
text(69,1265,'BTB 候选中心：X=30.00，Y=29.20 mm；90° / 270° 朝向仍需实物排线确认。',23)
text(69,1309,'安装孔、USB、耳机座、TF 卡座及按键 FPC 固定；电池 / 马达沿用低矮焊接线束。',22)
text(69,1353,'蓝色区域仅为规划空间；U10 仅 2 MB，不能直接等同原模组内的 16 MB 启动 Flash。',20,'#785b35')
text(69,1396,'元件矩形为封装边界示意；具体焊盘和层面以 KiCad 工程为准。',19,'#687b90')
im.save(P/'placement-overview.png')

# Compare only unchanged peripheral nets. There is no honest global wirelength
# comparison while the MCU terminals are missing from the new schematic.
metrics=[]
for a,b,net in [('USB1','D1','TYPEC_USB_DP_IN'),('USB1','D1','TYPEC_USB_DN_IN'),('U12','U17','CH343P_USB_DP'),('U12','U17','CH343P_USB_DN'),('U5','U2','VCC_1V8'),('U8','U2','CS43131_I2S_SCLK'),('U8','U2','CS43131_I2S_SDIN'),('U8','U2','CS43131_I2S_LRCK')]:
 vals=[]
 for old in [True,False]:
  def pads(r):
   if old:return[(p['x'],p['y']) for p in parts[r]['before']['pads'] if p['net']==net]
   return [p['xy'] for p in parts[r]['pads'] if p['net']==net]
  vals.append(min(math.dist(x,y) for x in pads(a) for y in pads(b)))
 metrics.append(dict(a=a,b=b,net=net,before_mm=round(vals[0],3),after_mm=round(vals[1],3),reduction_percent=round(100*(1-vals[1]/vals[0]),1)))
(P/'connection-distance-check.json').write_text(json.dumps(dict(method='Minimum straight-line pad-to-pad distance for selected unchanged nets; NOT routed length or whole-board optimization score',metrics=metrics),indent=2))
print(json.dumps(metrics,indent=2))
