"""Same-width comparison of the saved E/F front renders, preserving proportions."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
canvas=Image.new('RGB',(1260,1250),'white');draw=ImageDraw.Draw(canvas)
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n)
draw.text((50,25),'屏幕三边等距 · 操作区整体上移',font=font(30),fill='#193146')
for x,path,title,note in [(70,HERE.parent/'enclosure-q2-e/exports/front-E.png','调整前 · E','顶部 0.5 mm / 左右 2 mm'),(690,HERE/'exports/front-F.png','调整后 · F','顶部 / 左右均为 2 mm')]:
    im=Image.open(path).convert('RGB')
    mask=im.convert('L').point(lambda v:255 if v<230 else 0)
    crop=im.crop(mask.getbbox());crop=crop.resize((500,round(crop.height*500/crop.width)),Image.Resampling.LANCZOS)
    canvas.paste(crop,(x,190))
    draw.text((x,95),title,font=font(25),fill='#193146')
    draw.text((x,140),note,font=font(20),fill='#546c80')
draw.text((70,1080),'机身：50 × 80 × 13.5 mm',font=font(22),fill='#546c80')
draw.text((690,1080),'机身：50 × 81.5 × 13.5 mm',font=font(22),fill='#193146')
draw.text((70,1130),'屏幕到圆环：4.3 mm',font=font(22),fill='#546c80')
draw.text((690,1130),'屏幕到圆环：2.3 mm',font=font(22),fill='#193146')
draw.text((70,1200),'边距按可见屏幕保护盖板计算；右图圆环、按键与触摸小板整体上移 2 mm。',font=font(20),fill='#546c80')
canvas.save(HERE/'exports/comparison-E-F.png')
