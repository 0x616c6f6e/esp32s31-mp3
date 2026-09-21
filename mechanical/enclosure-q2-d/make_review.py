from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
HERE=Path(__file__).resolve().parent;OUT=HERE/'exports'
im=Image.new('RGB',(1500,1140),'#eef2f6');d=ImageDraw.Draw(im)
def text(x,y,s,size=23,color='#20344a'):d.text((x,y),s,fill=color,font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',size))
d.rounded_rectangle((24,24,1476,136),18,fill='#172c43')
text(50,42,'Q2 修订 D · 屏幕及屏窗上移 1.5 mm',34,'white')
text(51,93,'完整外壳恢复默认显示；原主板适配仍有明确冲突，见右图。',23,'#d0dfed')
for x,filename in [(24,'exterior-D.png'),(760,'current-PCB-conflicts.png')]:
    d.rounded_rectangle((x,155,x+716,991),15,fill='white')
    src=Image.open(OUT/filename).convert('RGB').crop((40,245,1180,1240));src.thumbnail((686,685))
    im.paste(src,(x+15,251))
text(48,177,'完整外观方案',28)
text(49,219,'50 × 80 mm；顶部盖板名义余量 0.5 mm',20)
text(786,177,'现有 PCB 与外壳的真实干涉',28)
text(787,219,'红色区域：板边、板角和器件包络撞壳',20,'#b7473c')
text(49,936,'上移后的屏幕、开窗、盖板已同步更新。',21)
text(787,936,'这块原PCB还不能装入左侧外观方案。',21,'#b7473c')
text(48,1020,'原因：旧板 48 × 76 / R1.2；机身采用 Q2 风格大圆角 R12，板角尚未重新布局。',23)
text(48,1065,'FPC 中心线仍偏差 2.366 mm；改板时需同时处理连接座位置和排线绕行空间。',23)
im.save(OUT/'revision-D-review.png')
