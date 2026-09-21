"""Replace missing model references; assert all electrical/placement data unchanged."""
from pathlib import Path
import sys,json,copy,hashlib,re
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'tmp'));from sexpr import *
manifest=json.loads((P/'models3d/model-manifest.json').read_text(encoding='utf8'));models={m['footprint']:m for m in manifest['models']}
path=P/'hardware.kicad_pcb';board=parse(path.read_text(encoding='utf8'));before=copy.deepcopy(board)
def stripped(tree):
    tree=copy.deepcopy(tree)
    for f in children(tree,'footprint'):f[:]=[n for n in f if not(isinstance(n,list) and n[0]=='model')]
    return tree
def attach(f,name):
    f[:]=[n for n in f if not(isinstance(n,list) and n[0]=='model')]
    if name not in models:return
    m=models[name];assert (P/'models3d'/m['file']).is_file()
    f.append(['model',S('${KIPRJMOD}/models3d/'+m['file']),['offset',['xyz','0','0','0']],['scale',['xyz','1','1','1']],['rotate',['xyz','0','0','0']]])
for f in children(board,'footprint'):attach(f,str(f[1]).split(':')[-1])
assert stripped(board)==stripped(before)
for pathlib in (P/'MP3_Source.pretty').glob('*.kicad_mod'):
    t=parse(pathlib.read_text(encoding='utf8'));attach(t,pathlib.stem);pathlib.write_text(dump(t)+'\n',encoding='utf8')
def end_expr(text,start):
    depth=0;quoted=False;escaped=False
    for i in range(start,len(text)):
        c=text[i]
        if quoted:
            if escaped:escaped=False
            elif c=='\\':escaped=True
            elif c=='"':quoted=False
        elif c=='"':quoted=True
        elif c=='(':depth+=1
        elif c==')':
            depth-=1
            if depth==0:return i+1
    raise ValueError('Unbalanced PCB expression')
# Preserve native KiCad copper polygon formatting; only edit model blocks.
raw=path.read_text(encoding='utf8')
for match in reversed(list(re.finditer(r'(?m)^([ \t]*)\(footprint ',raw))):
    start=raw.index('(',match.start());end=end_expr(raw,start);chunk=raw[start:end]
    fp=parse(chunk);name=str(fp[1]).split(':')[-1]
    for modelmatch in reversed(list(re.finditer(r'(?m)^[ \t]*\(model ',chunk))):
        ms=chunk.index('(',modelmatch.start());me=end_expr(chunk,ms)
        if me<len(chunk) and chunk[me]=='\n':me+=1
        chunk=chunk[:modelmatch.start()]+chunk[me:]
    if name in models:
        indent=match.group(1);body=chunk[:chunk.rfind('\n')+1]
        node='(model "${KIPRJMOD}/models3d/'+models[name]['file']+'"\n'+indent+'\t(offset (xyz 0 0 0))\n'+indent+'\t(scale (xyz 1 1 1))\n'+indent+'\t(rotate (xyz 0 0 0))\n'+indent+'\t)'
        chunk=body+indent+'\t'+node+'\n'+indent+')'
    raw=raw[:start]+chunk+raw[end:]
assert parse(raw)==board
path.write_text(raw,encoding='utf8')
result={'footprints':len(children(board,'footprint')),'models_attached':sum(len(children(f,'model')) for f in children(board,'footprint')),'model_only_change_verified':True,'unchanged_without_model_nodes_sha256':hashlib.sha256(dump(stripped(board)).encode()).hexdigest(),'excluded_mounting_holes':4}
(P/'models3d/attachment-validation.json').write_text(json.dumps(result,indent=2),encoding='utf8');print('MODELS_ATTACHED',result)
