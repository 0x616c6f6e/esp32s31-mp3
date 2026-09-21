from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
HERE=Path(__file__).resolve().parent;OUT=HERE/'exports'
im=Image.new('RGB',(1560,1120),'#f1f4f8');d=ImageDraw.Draw(im)
font='C:/Windows/Fonts/msyh.ttc'
def text(x,y,s,size=23,color='#253447'):
    d.text((x,y),s,font=ImageFont.truetype(font,size),fill=color)
def line(a,b,color='#7d8b9c',w=2):d.line([a,b],fill=color,width=w)
def dash(a,b,color):
    x1,y1=a;x2,y2=b
    for x in range(int(x1),int(x2),13):line((x,y1),(min(x+7,x2),y2),color,2)
d.rounded_rectangle((24,24,1536,125),20,fill='#15283e')
text(50,42,'2.09″ 屏幕模型与主板背面 FPC2 对齐检查',32,'white')
text(51,89,'结论：标称尾端尺寸相符；当前装配不能确认直接插接。',20,'#cbd9e9')
d.rounded_rectangle((24,145,595,1088),18,fill='white')
d.rounded_rectangle((615,145,1536,620),18,fill='white')
d.rounded_rectangle((615,640,1536,1088),18,fill='white')
text(47,163,'按用户图建立的尺寸模型',26)
s=6.4;ox=163;oy=267
def pt(x,y):return (ox+x*s,oy+y*s)
def rr(x,y,w,h,r,fill):d.rounded_rectangle((*pt(x,y),*pt(x+w,y+h)),r*s,fill=fill)
rr(0,0,36.33,43.45,10,'#272c34');rr(1.075,1.05,34.18,40.05,9,'#111d27')
text(195,366,'320 × 375',22,'#c0d7e6');text(184,402,'AA 34.18 × 40.05',16,'#c0d7e6')
rr((36.33-18)/2,43.45,18,12.8,1,'#cf8b30')
rr((36.33-6.6)/2,43.45+12.3,6.6,46.14-12.3,0,'#cf8b30')
for i in range(21):
    x=(36.33-6)/2+i*.3
    d.rectangle((*pt(x-.09,87.09),*pt(x+.09,89.59)),fill='#fbe3a0')
text(221,817,'21',15);text(294,817,'1',15)
for a,b in [((163,230),(395.5,230)),((127,267),(127,545)),((443,545),(443,840))]:
    line(a,b);line((a[0]-4,a[1]-4),(a[0]+4,a[1]+4));line((b[0]-4,b[1]-4),(b[0]+4,b[1]+4))
text(205,200,'36.33 ±0.1',21)
text(42,346,'43.45',21);text(43,373,'±0.1',19)
text(451,660,'46.14',21);text(451,690,'±0.5',19)
text(56,868,'模块总厚 1.46±0.1 mm',23)
text(56,906,'尾宽 6.6±0.05；触点跨度 6 mm',21)
text(56,944,'外形圆角、排线颈部与本体厚度为估计。',19,'#687789')
text(56,976,'金手指按接触区包络表示；端部补强厚度未知。',18,'#687789')
text(56,1033,'单位：mm  /  可编辑 FCStd + STEP',21)
text(642,162,'背面投影：中心线偏差 3.866 mm',26)
ax=666;ay=222;k=17
def ap(x,y):return (ax+x*k,ay+(y-10)*k)
def rect(x,y,w,h,fill=None,outline=None,width=2):d.rectangle((*ap(x,y),*ap(x+w,y+h)),fill=fill,outline=outline,width=width)
rect(7.652,14.084,3.2,7.9,'#dc665c')
rect(8.352,18.6,14,6.6,'#e5b55d')
rect(8.352,18.6,2.5,6.6,'#f1d393')
rect(7.652,17.95,3.2,7.9,outline='#267bc4',width=3)
for yy,col in [(18.034,'#d44a47'),(21.9,'#bc830e')]:dash(ap(0,yy),ap(29,yy),col)
x=ap(27,0)[0];y1=ap(0,18.034)[1];y2=ap(0,21.9)[1]
line((x,y1),(x,y2),'#253447');line((x-6,y1),(x+6,y1));line((x-6,y2),(x+6,y2))
text(x+12,(y1+y2)/2-14,'3.866',23)
text(1135,239,'红：当前 FPC2',22,'#b8463e')
text(1135,279,'金：未横向偏折的屏幕尾端',22,'#9c701c')
text(1135,319,'蓝框：移位候选，仅供布局',21,'#236aa7')
text(650,533,'连接座轴线 Y=18.034；屏幕排线轴线 Y=21.900。',21)
text(650,570,'候选移动仅解决横向对齐；插入高度、折弯与避让仍需验证。',20,'#687789')
text(642,657,'FreeCAD 实际检查视图 · 从主板背面观察',25)
native=Image.open(OUT/'current-fit-rear-isometric.png').convert('RGB')
native=native.crop((45,185,1050,865));native.thumbnail((590,365))
im.paste(native,(631,705))
text(1230,753,'橙色：46.14 mm',19)
text(1230,785,'无横向剪切的折弯示意',19)
text(1230,837,'红色：当前连接座',19)
text(1230,869,'及几何干涉区域',19)
text(1230,924,'主板和屏幕半透明',19,'#687789')
text(1230,956,'折弯半径尚未确认',19,'#687789')
im.save(OUT/'display-fit-review.png')
print(OUT/'display-fit-review.png')
