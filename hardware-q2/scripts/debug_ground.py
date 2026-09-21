from pathlib import Path
HERE=Path(__file__).resolve().parent;s=HERE/'route_repair.py'
exec(compile(s.read_text(encoding='utf8').split('results=[];new=[]')[0],str(s),'exec'))
from PIL import ImageFont
mask,via=masks('GND',.127)
canvas=Image.new('RGB',(1000,600),'white');dd=ImageDraw.Draw(canvas)
for idx,(ref,num) in enumerate([('U9','26'),('C49','1')]):
    a=next(o for o in items if o.get('ref')==ref and o.get('num')==num);x,y=a['pos'];px,py=pix(a['pos']);l=LS.index(a['layers'][0]);scale=5
    for j,arr in enumerate([mask[l],via]):
        im=Image.fromarray((~arr[py-50:py+51,px-50:px+51]*255).astype('uint8')).convert('RGB').resize((505,505))
        dr=ImageDraw.Draw(im);dr.ellipse((248,248,256,256),fill='red')
        canvas.paste(im,(idx*500,j*0)) if j==0 else None
    dd.text((idx*500,515),f'{ref}.{num} layer {a["layers"][0]} 5x5mm red=pad center',fill='black')
canvas.save(P/'output/ground-mask.png')
for ref,num in [('U9','26'),('C49','1')]:
    a=next(o for o in items if o.get('ref')==ref and o.get('num')==num)
    print(ref,[{k:o.get(k) for k in ['id','net','kind','pos','end','layers','ref','num']} for o in items if o['net']!='GND' and any(l in o['layers'] for l in a['layers']) and (math.dist(o['pos'],a['pos'])<1.6 or ('end' in o and math.dist(o['end'],a['pos'])<1.6))])
