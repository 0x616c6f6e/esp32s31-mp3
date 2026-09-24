from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

O=Path(__file__).resolve().parent
im=Image.new('RGB',(1800,1530),'#f5f7fb'); d=ImageDraw.Draw(im)
font_path='C:/Windows/Fonts/msyh.ttc'
def f(n): return ImageFont.truetype(font_path,n)
def text(x,y,s,n=26,c='#23344b'): d.text((x,y),s,font=f(n),fill=c)
def center(box,lines,n=23):
 x0,y0,x1,y1=box; h=len(lines)*(n+9)
 for i,s in enumerate(lines):
  w=d.textbbox((0,0),s,font=f(n))[2]
  text((x0+x1-w)/2,(y0+y1-h)/2+i*(n+9),s,n)
text(65,38,'AM213 屏幕 · FPC 转接布局草案',44)
text(65,108,'17 × 22 mm 元件区＋局部补强＋21P 柔性尾巴  |  功能分区，不是生产封装',25,'#596a80')
d.rounded_rectangle((55,175,865,1415),radius=20,fill='white')
d.rounded_rectangle((900,175,1745,1415),radius=20,fill='white')
text(88,200,'01  元件面朝屏幕',29)
text(88,244,'左上角 (0,0)，X →，Y ↓；单位 mm',23,'#596a80')
ox,oy,sc=130,345,39
def xy(x,y):return ox+x*sc,oy+y*sc
box=(*xy(0,0),*xy(17,22))
d.rectangle(box,fill='#fff5d5',outline='#bc8a23',width=4)
for x in range(1,17):d.line((*xy(x,0),*xy(x,22)),fill='#f0e6c8')
for y in range(1,22):d.line((*xy(0,y),*xy(17,y)),fill='#f0e6c8')
d.line((ox,317,ox+17*sc,317),fill='#52647b',width=2)
for x in (ox,ox+17*sc):d.line((x,307,x,330),fill='#52647b',width=2)
text(ox+245,281,'17 mm',24)
text(76,745,'22',24);text(68,780,'mm',20)
def zone(x,y,w,h,lines,color):
 b=(*xy(x,y),*xy(x+w,y+h));d.rounded_rectangle(b,10,fill=color,outline='#60748e',width=2);center(b,lines)
zone(.5,.5,11,3,['阻尼 / 去耦余量','去耦实际紧贴 IC'], '#e8edf5')
zone(.5,6,4,12,['J2','24P BTB','母座','4 × 12','操作区','方向待定'],'#c5e5ee')
zone(6,4,6,4,['U1 · 4 路','CLK / CS','D0 / D1'],'#cbe0fc')
zone(6,9,6,4,['U2 · 4 路','D2 / D3','LCD / TP RST'],'#cbe0fc')
zone(6,14,6,4,['U3 · 返回','TP_INT','TE 测试预留'],'#d9d3f4')
zone(12.5,.5,4,7,['PWR','逻辑稳压','供电选择','去耦','方案待定'],'#f8d9c5')
zone(12.5,9,4,5,['U4','I²C 转换','两侧上拉'],'#ceeadc')
zone(.5,19,16,2,['P_IN / GND 焊盘 · 测试 · 尾巴过渡'],'#e8edf5')
# Tail is deliberately illustrative; no connector lands are fabricated here.
tb=(*xy(5.2,22),*xy(11.8,25))
d.rectangle(tb,fill='#ffe3a0',outline='#bc8a23',width=3)
center(tb,['21P / 0.3 mm','柔性尾巴示意'],21)
text(100,1342,'出边、长度、接触面与金手指尺寸待实物定',23,'#916319')
text(935,202,'02  连接路径',29)
def card(y,title,lines,fill):
 d.rounded_rectangle((935,y,1710,y+155),14,fill=fill)
 text(960,y+15,title,27)
 for i,line in enumerate(lines):text(960,y+57+i*34,line,23)
card(255,'主板 FPC2 → 柔性尾巴 → 元件岛',['原接口 21P / 0.3 mm；末端补强按插座图','1/2 背光输出隔离，22/23 是插座机械焊盘'],'#fff1d2')
card(435,'U1 / U2 / U3 → J2 → 新屏',['8 路输出＋1 路中断返回；预留电平转换','J2 需与 OK-23GM024-04 屏端公座匹配'],'#e6f0fd')
card(615,'U4 单独处理触摸 I²C',['SDA：主板20 → 屏19；SCL：主板19 → 屏20','开漏双向转换，不与 QSPI 推挽转换混用'],'#e5f3eb')
text(935,803,'03  FPC 叠层起稿目标',29)
for i,s in enumerate(['所有元件先放同面，背面作补强及绝缘固定。','FPC＋补强＋胶层总厚目标 ≤ 0.6 mm。','朝屏幕器件高目标 ≤ 0.8 mm；必须复核装配。','弯曲区不放器件、过孔、焊盘；不硬折死角。']):text(935,860+i*43,s,24)
text(935,1062,'04  画板前保留的未定项',29)
for i,s in enumerate(['屏针15 / 16供电、PMIC供电及负载电流；','BTB正式焊盘与合高、两端 Pin 1 / 接触面；','D0读回方向、OE使能与屏幕上电时序；','尾巴绕主板边缘到背面的展开形状与长度。']):text(935,1120+i*43,s,24)
text(65,1451,'布局起稿参考 · 未布线、未完成电源设计、未确认实际 FPC 装配 · 2026-09-23',25,'#68788b')
im.save(O/'fpc-layout-concept.png')
print(O/'fpc-layout-concept.png')
