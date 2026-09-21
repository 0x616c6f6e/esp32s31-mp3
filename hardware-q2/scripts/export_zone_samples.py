import pcbnew as p,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'hardware-q2';b=p.LoadBoard(str(P/'hardware.kicad_pcb'))
vias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA)]
pads=[a for f in b.GetFootprints() for a in f.Pads()]
groundplanes=[z.GetFilledPolysList(l) for z in b.Zones() if z.GetNetname()=='GND' for l in z.GetLayerSet().CuStack() if l in [p.In1_Cu,p.In4_Cu]]
result=[]
for z in b.Zones():
    if z.GetIsRuleArea() or z.GetNetname() not in ['GND','VBUS_5V','Net-(D2-A)','VCC_LCD_BG']:continue
    for l in z.GetLayerSet().CuStack():
        poly=z.GetFilledPolysList(l)
        for i in range(poly.OutlineCount()):
            c=poly.COutline(i);bb=c.BBox();x0,y0,x1,y1=bb.GetX()/1e6,bb.GetY()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6
            step=.2 if (x1-x0)*(y1-y0)<50 else .6
            pts=[]
            for ix in range(math.ceil(x0/step),math.floor(x1/step)+1):
                for iy in range(math.ceil(y0/step),math.floor(y1/step)+1):
                    x,y=round(ix*step,6),round(iy*step,6)
                    pos=p.VECTOR2I(round(x*1e6),round(y*1e6))
                    if poly.Contains(pos,i) and (z.GetNetname()!='GND' or any(q.Contains(pos) for q in groundplanes)):pts.append([x,y])
            present=[{'id':v.m_Uuid.AsString(),'pos':[v.GetPosition().x/1e6,v.GetPosition().y/1e6]} for v in vias if v.GetNetname()==z.GetNetname() and poly.Contains(v.GetPosition(),i)]
            pp=[{'id':a.m_Uuid.AsString(),'ref':a.GetParentFootprint().GetReference(),'num':a.GetNumber(),'pos':[a.GetPosition().x/1e6,a.GetPosition().y/1e6]} for a in pads if a.GetNetname()==z.GetNetname() and a.IsOnLayer(l) and poly.Contains(a.GetPosition(),i)]
            result.append({'net':z.GetNetname(),'zone':z.m_Uuid.AsString(),'layer':l,'index':i,'bounds':[x0,y0,x1,y1],'points':pts,'existing_vias':present,'pads':pp})
(P/'output/zone-samples.json').write_text(json.dumps(result),encoding='utf8')
print('ZONE_POLYGONS',len(result))
