"""One-shot migration of the unrouted placement to low-profile harness connectors.

Run with KiCad Python. Preserves footprint/signal-pad identities and all nets.
Refuses to run after migration or if the board has been routed.
"""
from pathlib import Path
import sys, copy, shutil, uuid, json, hashlib
import pcbnew as pcb
P=Path(__file__).resolve().parents[1]; ROOT=P.parent
sys.path.insert(0,str(ROOT/'tmp'))
from sexpr import parse,dump,get,children,prop,S
K=Path('D:/KiCad/10.0/share/kicad')
boardpath=P/'hardware.kicad_pcb'
tree=parse(boardpath.read_text(encoding='utf8'))
assert not any(children(tree,k) for k in ['segment','arc','via'])
specs={'H1':(2,'5_MOTOR',130,113,-90,'LRA motor; pin 1 OUT_N, pin 2 OUT_P'),
       'H2':(3,'2_POWER',142,109,-90,'Battery; pin 1 VBAT, pin 2 BAT_TS, pin 3 GBAT')}
manifest=json.loads((P/'models3d/model-manifest.json').read_text(encoding='utf8'))
for ref,(n,sheet,x,y,angle,description) in specs.items():
    old=next(f for f in children(tree,'footprint') if prop(f,'Reference')[2]==ref)
    assert 'HDR-TH' in old[1], 'Migration already applied; do not overwrite manual changes.'
    name=f'JST_ACH_BM0{n}B-ACHSS-GAN-ETF_1x0{n}-1MP_P1.20mm_Vertical'
    mpn=f'BM0{n}B-ACHSS-GAN-ETF'
    fp=parse((K/'footprints/Connector_JST.pretty'/f'{name}.kicad_mod').read_text(encoding='utf8'))
    get(fp,'model')[1]=S('${KIPRJMOD}/models3d/'+name+'.step')
    (P/'MP3_Source.pretty'/f'{name}.kicad_mod').write_text(dump(fp)+'\n',encoding='utf8')
    modeldst=P/'models3d'/f'{name}.step'
    assert modeldst.exists(), 'Run build_ach_models.py with FreeCAD first.'
    fp[1]=S('MP3_Source:'+name)
    fp[:]=[a for a in fp if not isinstance(a,list) or a[0] not in ['version','generator']]
    fp.extend([copy.deepcopy(get(old,k)) for k in ['uuid','path']])
    fp.append(['at','0','0','0']);fp.append(['locked','yes'])
    values={'Reference':ref,'Value':mpn,'Datasheet':'https://www.jst-mfg.com/product/pdf/eng/eACH.pdf','Description':description}
    for key,value in values.items():
        field=prop(fp,key)
        if field is None:
            field=copy.deepcopy(prop(old,key));fp.append(field)
        field[2]=S(value)
        if key!='Reference' and get(field,'hide') is None:field.append(['hide','yes'])
    # Reference on Fab avoids unreviewed silk crowding; pin-1 triangle stays on silk.
    get(prop(fp,'Reference'),'layer')[1]=S('F.Fab')
    field=copy.deepcopy(prop(old,'Supplier Part'));field[2]=S('');fp.append(field)
    oldpads={str(a[1]):a for a in children(old,'pad')}
    for pad in children(fp,'pad'):
        if str(pad[1]) in oldpads:
            for key in ['uuid','net','pinfunction','pintype']:
                src=get(oldpads[str(pad[1])],key)
                if src:pad.append(copy.deepcopy(src))
        else:pad.append(['uuid',S(str(uuid.uuid4()))])
    tree[tree.index(old)]=fp
    schpath=P/(sheet+'.kicad_sch');sch=parse(schpath.read_text(encoding='utf8'))
    sym=next(a for a in children(sch,'symbol') if prop(a,'Reference') and prop(a,'Reference')[2]==ref)
    for key,value in {**values,'Footprint':'MP3_Source:'+name,'Supplier Part':''}.items():
        prop(sym,key)[2]=S(value)
    # Keep original generic connector graphic/pin coordinates so wires and UUIDs do not change.
    # Long ordering code is hidden on sheet, available in properties/BOM.
    if get(prop(sym,'Value'),'hide') is None:prop(sym,'Value').append(['hide','yes'])
    schpath.write_text(dump(sch)+'\n',encoding='utf8')
    manifest['models']=[m for m in manifest['models'] if ref not in m['references']]
    manifest['models'].append({'footprint':name,'references':[ref],'file':modeldst.name,
        'kind':'connector','quality':'Conservative nominal mated envelope; not vendor CAD',
        'source':'JST eACH.pdf overall dimensions; scripts/build_ach_models.py',
        'datasheet':values['Datasheet'],'height':1.4,
        'model_sha256':hashlib.sha256(modeldst.read_bytes()).hexdigest()})
boardpath.write_text(dump(tree)+'\n',encoding='utf8')
b=pcb.LoadBoard(str(boardpath));fps={f.GetReference():f for f in b.GetFootprints()}
for ref,(_,_,x,y,angle,_) in specs.items():
    f=fps[ref];f.SetPosition(pcb.VECTOR2I(round(x*1e6),round(y*1e6)));f.SetOrientationDegrees(angle);f.SetLocked(True)
pcb.SaveBoard(str(boardpath),b)
(P/'models3d/model-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
layout=json.loads((P/'output/placement.json').read_text(encoding='utf8'))
xy=lambda v:[v.x/1e6,v.y/1e6]
state=lambda f:{'xy':xy(f.GetPosition()),'angle':f.GetOrientationDegrees(),'side':'B' if f.IsFlipped() else 'F'}
for ref in specs:
    layout['fixed_mechanical_references'].remove(ref)
    old=next(f for f in layout['footprints'] if f['reference']==ref)
    layout['changes'].append({'ref':ref,'old':{k:old[k] for k in ['xy','angle','side']},'new':state(fps[ref])})
layout['connector_revision']={ref:{**state(fps[ref]),'value':fps[ref].GetValue(),'case_xy_mm':[149-v[2],v[3]-49],'wire_exit_case':'+X','pin_nets':{a.GetNumber():a.GetNetname() for a in fps[ref].Pads() if a.GetNumber()!='MP'}} for ref,v in specs.items()}
layout['pcb_sha256']=hashlib.sha256(boardpath.read_bytes()).hexdigest()
layout['footprints']=[]
for ref,f in fps.items():
    bb=f.GetBoundingBox(False,False)
    layout['footprints'].append({'reference':ref,'value':f.GetValue(),**state(f),'bounds':xy(bb.GetOrigin())+xy(bb.GetEnd()),'pads':[{'num':a.GetNumber(),'net':a.GetNetname(),'xy':xy(a.GetPosition())} for a in f.Pads()]})
(P/'output/placement.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2),encoding='utf8')
print('CONNECTORS_MIGRATED',json.dumps(layout['connector_revision']))
