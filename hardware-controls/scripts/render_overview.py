"""Compose a review image from native KiCad top/bottom renders (Pillow)."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
P=Path(__file__).resolve().parents[1];O=P/'output'
canvas=Image.new('RGB',(2000,1010),'#f5f6f8');draw=ImageDraw.Draw(canvas)
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
draw.text((35,20),'Q2 操作小板 B  |  I²C 滑环 + 四键，POWER 独立',font=font(34),fill='#183238')
draw.text((35,78),'正面 · 滑环电极与五个机械开关',font=font(24),fill='#34515b')
draw.text((1035,78),'背面 · AT42QT2120 + TCA6408A',font=font(24),fill='#34515b')
for name,x in [('3d-front.png',25),('3d-back.png',1025)]:
    im=Image.open(O/name).convert('RGBA');im=im.crop(im.getbbox());im=ImageOps.contain(im,(950,790))
    canvas.paste(im,(x+(950-im.width)//2,135+(790-im.height)//2),im)
draw.text((35,952),'44 × 34 × 0.8 mm  |  0x1C 滑环 / 0x20 四键  |  共享 INT  |  主板暂未连接',font=font(24),fill='#34515b')
canvas.save(O/'controls-overview.png')
