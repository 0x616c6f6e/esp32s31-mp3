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

def circle(x,y,r,color=ink,width=2,fill='none'):
    svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{color}" stroke-width="{width}"/>')
    draw.ellipse((x-r,y-r,x+r,y+r),outline=color,width=width,fill=None if fill=='none' else fill)
text(58,56,'独立滑环 + 五键操作板 / 机械外形 C',31)
text(58,94,'单位 mm   |   板框、孔位和器件空间预留；电路、电极铜箔与布线尚未实施',19,blue)
line(58,112,1540,112,'#b7c6cf',2)
x,y,S=210,242,16
rect(x,y,44*S,34*S,10*S,'#e9f2ec','#277151',2)
hdim(x,x+44*S,181,y,'44.0')
vdim(y,y+34*S,150,x,'34.0')
for hx,hy in [(3,8.7),(41,8.7),(3,24.7),(41,24.7)]:circle(x+hx*S,y+hy*S,.9*S,ink,2,'white')
for r in [15.5,10.5]:circle(x+22*S,y+17*S,r*S,orange,2)
keys=[('返回',22,4),('电源',22,17),('下一曲',9,17),('上一曲',35,17),('播放/暂停',22,30)]
for name,kx,ky in keys:
    rect(x+(kx-1.5)*S,y+(ky-1.5)*S,3*S,3*S,2,'#d5dde2',ink,1)
    text(x+kx*S,y+(ky+1.5)*S+25,name,17,ink,'middle')
rect(x+34*S,y+4.2*S,7.5*S,3*S,2,'#d4e8f3',blue,1)
text(x+37.75*S,y+4.2*S-13,'背面 FPC 座',16,blue,'middle')
line(x+15*S,y+33*S,620,858,orange);text(530,891,'圆角 R10；板厚 0.8',22,orange)
text(x,211,'局部原点 (0,0)，+X 向右，+Y 向下',17,blue)
rect(984,158,556,770,12,'#f4f7f9','#d8e1e7',1)
text(1010,204,'后续 PCB 设计约束',25)
rows=['4 × D1.8 安装孔：',
      '(3,8.7)、(41,8.7)',
      '(3,24.7)、(41,24.7)',
      '滑环中心：(22,17)',
      '感应带示意：外径 31 / 内径 21',
      '五个开关：3 × 3 × 0.55 占位',
      'FPC 座在小板背面，中心 (37.75,5.7)',
      '连接器占位：7.5 × 3 × 1',
      '孔与按键坐标同时提供 CSV。',
      'DXF 板边闭合，STEP 可用于装配。',
      'FPC 引脚数、接触方向及开关型号待定。',
      '机身坐标中的小板原点：(3,44.3,11.1)',
      '从机身正面观察时，左右与此坐标相反。']
for i,s in enumerate(rows):text(1010,253+i*46,s,18,orange if i>=10 else ink)
line(58,1003,1540,1003,'#b7c6cf',2)
text(58,1042,'ESP32-S31 MP3 / 独立操作板机械预留    •    当前不作为生产 PCB 文件',19)
svg.append('</svg>');(OUT/'control-board-dimensions.svg').write_text('\n'.join(svg),encoding='utf8');im.save(OUT/'control-board-dimensions.png')

# Labeled montage uses actual FreeCAD renders, not a substitute for CAD geometry.
from PIL import ImageChops
canvas=Image.new('RGB',(1680,1180),'white');d=ImageDraw.Draw(canvas)
font=lambda n:ImageFont.truetype(fontpath,n)
d.text((50,24),'修订 C：主板方向修正 + 独立滑环 / 按键板',font=font(31),fill=ink)
d.text((50,77),'ESP32 朝屏幕  ·  屏幕 FPC2 朝后盖  ·  橙色：屏幕排线通道  ·  蓝色：操作板 FPC 通道',font=font(19),fill=blue)
def paste_render(name,box):
    pic=Image.open(OUT/name).convert('RGB');bb=ImageChops.difference(pic,Image.new('RGB',pic.size,'white')).getbbox();pic=pic.crop(bb);pic.thumbnail((box[2],box[3]),Image.Resampling.LANCZOS)
    canvas.paste(pic,(box[0]+(box[2]-pic.width)//2,box[1]+(box[3]-pic.height)//2))
d.text((55,135),'屏幕移去后：ESP32 与操作板均位于正面',font=font(22),fill=ink)
paste_render('internal-front.png',(30,188,955,875))
d.text((1020,135),'背面：排线绕板边连接原 FPC2',font=font(21),fill=ink)
paste_render('screen-fpc-rear.png',(1020,183,620,405))
d.text((1020,630),'独立小板：44 × 34 × 0.8 mm',font=font(22),fill=ink)
paste_render('control-board-front.png',(1035,676,590,360))
d.text((55,1110),'操作小板仅机械预留；现有主板边缘与屏幕排线通道的冲突仍需改板解决。',font=font(21),fill=orange)
canvas.save(OUT/'assembly-review.png')
print('C_DRAWINGS_SAVED')
