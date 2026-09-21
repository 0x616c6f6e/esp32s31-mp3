from pathlib import Path
import pcbnew as p,json,math
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'hardware-q2';b=p.LoadBoard(str(P/'hardware.kicad_pcb'))
xy=lambda v:[round(v.x/1e6,6),round(v.y/1e6,6)]
box=lambda bb:[xy(bb.GetOrigin()),xy(bb.GetEnd())]
layers=list(b.GetEnabledLayers().CuStack());out={'layers':layers,'items':[],'footprints':[],'outline_mm':[101,51,147,127],'outline_size_mm':[46,76],'corner_radius_mm':10}
for f in b.GetFootprints():
    fp={'reference':f.GetReference(),'value':f.GetValue(),'side':'bottom' if f.IsFlipped() else 'top','position_mm':xy(f.GetPosition()),'rotation_deg':f.GetOrientationDegrees(),'bounds_mm':box(f.GetBoundingBox(False,False)),'pads':[]}
    for a in f.Pads():
        ob={'id':a.m_Uuid.AsString(),'net':a.GetNetname(),'pos':xy(a.GetPosition()),'layers':[l for l in layers if a.IsOnLayer(l)],'kind':'pad','size':xy(a.GetSize()),'angle':a.GetOrientationDegrees(),'shape':int(a.GetShape()),'hole':xy(a.GetDrillSize()),'ref':f.GetReference(),'num':a.GetNumber(),'npth':a.GetAttribute()==p.PAD_ATTRIB_NPTH,'box':box(a.GetBoundingBox())}
        out['items'].append(ob);fp['pads'].append(ob)
    out['footprints'].append(fp)
for t in b.GetTracks():
    ob={'id':t.m_Uuid.AsString(),'net':t.GetNetname(),'pos':xy(t.GetStart()),'layers':[l for l in layers if t.IsOnLayer(l)],'width':(t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth())/1e6}
    if isinstance(t,p.PCB_VIA):ob.update(kind='via',hole=t.GetDrillValue()/1e6)
    elif isinstance(t,p.PCB_ARC):ob.update(kind='arc',end=xy(t.GetEnd()),mid=xy(t.GetMid()),box=box(t.GetBoundingBox()))
    else:ob.update(kind='track',end=xy(t.GetEnd()))
    out['items'].append(ob)
out['keepouts']=[]
for z in b.Zones():
    if z.GetIsRuleArea():
        c=z.Outline().COutline(0);out['keepouts'].append([xy(c.CPoint(i)) for i in range(c.PointCount())])
(P/'output/geometry.json').write_text(json.dumps(out,ensure_ascii=False),encoding='utf8')
print('GEOMETRY',len(out['items']),len(out['footprints']))
