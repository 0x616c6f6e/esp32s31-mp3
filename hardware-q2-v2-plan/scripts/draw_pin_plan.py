"""Documentation pin map; no CAD geometry or copper is changed."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont
P=Path(__file__).resolve().parents[1]
rows=json.loads((P/'pin-assignment.json').read_text(encoding='utf8'))['rows']
im=Image.new('RGB',(2300,2290),'#f6f8fc'); d=ImageDraw.Draw(im)
def font(n):return ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
f=font(21)
colors={'屏幕QSPI':'#7253b4','屏幕控制':'#7253b4','触屏HP I2C1':'#7253b4','音频I2S':'#c47a17','音频HP I2C0':'#c47a17','启动Flash':'#157e9e','SDMMC':'#157e9e','系统LP I2C':'#078479','唤醒/中断':'#078479','系统控制':'#078479','启动配置':'#bd4556','调试预留':'#466cb0','下载UART0':'#466cb0','USB HS':'#466cb0','空闲GPIO':'#97a2b2'}
d.text((90,55),'Q2 V2 · ESP32-S31 引脚规划 A',font=font(48),fill='#172b46')
d.text((90,130),'KiCad 顶视图 · 芯片 −90° · 1脚位于右上 · GPIO号与物理脚号分别标注',font=font(28),fill='#445a70')
d.text((90,180),'仅供原理图和布局规划；不是封装焊盘图，未完成电气连接。',font=font(26),fill='#687b90')
cx,cy=1150,1140;scale=100
d.rounded_rectangle((cx-400,cy-400,cx+400,cy+400),radius=18,fill='#24384d')
for r in rows:
 if r['pin']==81:continue
 x,y=r['board_local_nominal_terminal_xy']; x=cx+(x-30)*scale;y=cy+(y-17)*scale
 col=colors.get(r['group'],'#667687');side=r['board_side_at_minus90']
 label=f"{r['pin']:02d}  "+(f"G{r['gpio']}  " if r['gpio'] is not None else '')+r['signal']
 if side in ['左','右']:
  d.rectangle((x-20,y-10,x+20,y+10),fill=col)
  if side=='左': d.text((cx-425,y),label,font=f,fill=col,anchor='rm')
  else:d.text((cx+425,y),label,font=f,fill=col,anchor='lm')
 else:
  d.rectangle((x-10,y-20,x+10,y+20),fill=col)
  box=f.getbbox(label);tile=Image.new('RGBA',(int(d.textlength(label,font=f))+8,32))
  ImageDraw.Draw(tile).text((3,-box[1]),label,font=f,fill=col)
  tile=tile.rotate(90 if side=='上' else -90,expand=True)
  yy=cy-425-tile.height if side=='上' else cy+425
  im.paste(tile,(int(x-tile.width/2),int(yy)),tile)
d.ellipse((cx+290,cy-350,cx+326,cy-314),fill='#ffffff')
d.text((cx,cy-180),'ESP32-S31',font=font(55),fill='white',anchor='mm')
d.text((cx,cy-105),'QFN80 + EP81 · 8 × 8 mm',font=font(30),fill='#d4e0ee',anchor='mm')
d.text((cx,cy-48),'1脚角 → 右上',font=font(30),fill='#d4e0ee',anchor='mm')
d.rectangle((cx-145,cy+5,cx+145,cy+160),outline='#8b9dae',width=3)
d.text((cx,cy+82),'81 · GND / EP',font=font(32),fill='#d4e0ee',anchor='mm')
d.text((cx,cy+235),'中心：板框相对 (30, 17) mm',font=font(27),fill='#d4e0ee',anchor='mm')
legend=[('屏幕 / 触控','#7253b4'),('音频','#c47a17'),('Flash / TF','#157e9e'),('控制 / LP总线','#078479'),('启动配置','#bd4556'),('USB / UART','#466cb0'),('备用','#97a2b2')]
for i,(label,col) in enumerate(legend):
 xx=90+i*305;d.rectangle((xx,2080,xx+22,2102),fill=col);d.text((xx+33,2074),label,font=font(24),fill='#263c52')
d.text((90,2140),'屏幕 D2 = GPIO57，D3 = GPIO56。USB HS 使用物理44/45脚，不是GPIO44/45。',font=font(27),fill='#263c52')
d.text((90,2190),'系统GPIO6/7属于 LP I²C；POWER GPIO0需隔离GEK电源域。详细约束见 pin-assignment.md。',font=font(27),fill='#263c52')
im.save(P/'pin-assignment-overview.png')
print(P/'pin-assignment-overview.png')
