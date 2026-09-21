"""Dimensioned SVG + matching PNG, derived from the same CAD parameter file."""
from pathlib import Path
import json, html, math
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent;OUT=HERE/'exports';p=json.loads((HERE/'parameters.json').read_text())
W,H=1600,1080;im=Image.new('RGB',(W,H),'white');draw=ImageDraw.Draw(im)
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="white"/>']
ink='#263642';blue='#25638c';orange='#af6726';light='#edf2f5'
fontpath='C:/Windows/Fonts/msyh.ttc'
def text(x,y,s,size=20,color=ink,anchor='start',rotate=0):
    font=ImageFont.truetype(fontpath,size)
    attrs=f'text-anchor="{anchor}"'
    if rotate:attrs+=f' transform="rotate({rotate} {x} {y})"'
    svg.append(f'<text x="{x}" y="{y}" font-family="Microsoft YaHei, Arial, sans-serif" font-size="{size}" fill="{color}" {attrs}>{html.escape(s)}</text>')
    if rotate:
        b=font.getbbox(s);tile=Image.new('RGBA',(b[2]+8,size*2),(255,255,255,0));ImageDraw.Draw(tile).text((4,0),s,font=font,fill=color);tile=tile.rotate(-rotate,expand=True)
        im.paste(tile,(int(x-tile.width/2),int(y-tile.height/2)),tile)
    else:
        draw.text((x,y),s,font=font,fill=color,anchor={'start':'ls','middle':'ms','end':'rs'}[anchor])
def line(x1,y1,x2,y2,color=ink,width=1):
    svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>');draw.line((x1,y1,x2,y2),fill=color,width=width)
def rect(x,y,w,h,r=0,fill='white',stroke=ink,width=2):
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
    draw.rounded_rectangle((x,y,x+w,y+h),radius=r,fill=fill,outline=stroke,width=width)
def arrow(x,y,dx,dy):
    pts=[(x,y),(x+dx*8-dy*3,y+dy*8+dx*3),(x+dx*8+dy*3,y+dy*8-dx*3)]
    svg.append('<polygon points="'+' '.join(f'{a},{b}' for a,b in pts)+f'" fill="{blue}"/>');draw.polygon(pts,fill=blue)
def hdim(x1,x2,y,edge,label):
    line(x1,edge,x1,y,blue);line(x2,edge,x2,y,blue);line(x1,y,x2,y,blue);arrow(x1,y,1,0);arrow(x2,y,-1,0);text((x1+x2)/2,y-8,label,20,blue,'middle')
def vdim(y1,y2,x,edge,label):
    line(edge,y1,x,y1,blue);line(edge,y2,x,y2,blue);line(x,y1,x,y2,blue);arrow(x,y1,0,1);arrow(x,y2,0,-1);text(x-14,(y1+y2)/2,label,20,blue,'middle',-90)
text(58,56,'2.09" LCD — 按用户尺寸图建模',31)
text(58,88,'单位 mm   /   蓝色：图纸标注尺寸   /   橙色：未标注、估算项   /   示意比例，勿量图',18,blue)
line(58,106,1540,106,'#b7c6cf',2)
S=7;x,y=270,230;bw,bh=p['LCDWidth']*S,p['LCDLength']*S
rect(x,y,bw,bh,10*S,light)
rect(x+.1*S,y+.1*S,36.13*S,43.25*S,9.9*S,'#f8fafb','#8598a4',1)
ax=x+(36.33-34.18)/2*S;ay=y+1.05*S
rect(ax,ay,34.18*S,40.05*S,9*S,'#dfe9ed','#68808e',1)
text(x+bw/2,y+bh/2-8,'A.A. 34.18 × 40.05',20,ink,'middle')
text(x+bw/2,y+bh/2+24,'320 RGB × 375 / QSPI',17,ink,'middle')
hdim(x,x+bw,155,y,'BL 36.33 ±0.1')
hdim(x+.1*S,x+bw-.1*S,200,y,'LCD 36.13')
vdim(y,y+bh,154,x,'BL 43.45 ±0.1')
vdim(y+.1*S,y+bh-.1*S,207,x,'LCD 43.25')
vdim(ay,ay+40.05*S,610,x+bw,'A.A. 40.05')
neckx=x+(36.33-18)/2*S;necky=y+bh
rect(neckx,necky,18*S,12.8*S,0,'#f5d5a3',orange,1)
tx=x+(36.33-6.6)/2*S;ty=necky+12.8*S
rect(tx,ty,6.6*S,(46.14-12.8)*S,0,'#f5d5a3',orange,1)
end=necky+46.14*S
for i in range(21):
    px=x+(36.33-6)/2*S+i*.3*S-.09*S
    rect(px,end-2.5*S,.18*S,2.5*S,0,'#cf9a3c','#cf9a3c',1)
vdim(necky,end,700,x+bw/2,'FPC 46.14 ±0.5')
hdim(tx,tx+6.6*S,end+52,end,'6.6 ±0.05')
line(x+50,y+25,102,240,orange);text(65,217,'R10 估算',18,orange)
text(300,end+98,'展开视图：宽颈与过渡轮廓为示意',18,orange,'middle')
# Side view: overall LCM dimension, exaggerated lateral dimension line for legibility.
rect(785,y,1.46*S,bh,.8,'#445460',ink,1)
line(770,200,815,200,blue);line(785,200,785,y,blue);line(785+1.46*S,200,785+1.46*S,y,blue)
text(788,169,'LCM 1.46 ±0.1',20,blue,'middle')
text(788,y+bh+28,'侧视',18,ink,'middle')
rect(903,139,637,330,12,'#f4f7f9','#d8e1e7',1)
text(930,179,'尺寸来源与模型边界',23)
notes=['模组：36.33 × 43.45 × 1.46；LCD：36.13 × 43.25',
       '显示区：34.18 × 40.05；顶部内缩 1.05',
       '黑色单面胶 t = 0.03；是否计入总厚需供应商确认',
       'TP：无。外壳盖板为另行设计，并非自带触摸屏。',
       '连接器标注：OK-F302-21115；接触面/引脚方向待核对',
       '圆角、FPC 宽颈、膜厚与折弯半径均非标注尺寸。']
for i,s in enumerate(notes):text(930,220+i*39,s,17,orange if i==5 else ink)
text(931,527,'排线端部放大 / 21 触点示意',22)
dx,dy,sc=1060,625,48
rect(dx,dy,6.6*sc,2.5*sc,0,'#f5d5a3',orange,1)
for i in range(21):rect(dx+(.3+i*.3-.09)*sc,dy,.18*sc,2.5*sc,0,'#cf9a3c','#916829',1)
hdim(dx+.3*sc,dx+6.3*sc,584,dy,'触点中心跨度 6 ±0.03')
hdim(dx,dx+6.6*sc,dy+2.5*sc+47,dy+2.5*sc,'端部宽 6.6 ±0.05')
vdim(dy,dy+2.5*sc,1475,dx+6.6*sc,'露铜 2.5 ±0.3')
text(930,847,'间距 0.3 ±0.03；单个触点宽 0.18 为估算。',19,orange)
text(930,889,'机内安装旋转 90°：43.45 横向 × 36.33 纵向。',19)
text(930,927,'折叠排线仅用于空间研究，尚未与现有 FPC2 对接。',18,orange)
line(58,1003,1540,1003,'#b7c6cf',2)
text(58,1042,'ESP32-S31 MP3 / Q2 外观修订 B    |    原生尺寸：parameters.json → FreeCAD Spreadsheet',18)
svg.append('</svg>');(OUT/'lcd-dimensions.svg').write_text('\n'.join(svg),encoding='utf8');im.save(OUT/'lcd-dimensions.png')
print('DIMENSION_DRAWING_SAVED')
