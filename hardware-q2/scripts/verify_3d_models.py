"""Verify portable model attachments and preserve the pre-model mechanical baseline."""
from pathlib import Path
import sys, json, hashlib, subprocess, copy
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'tmp'))
from sexpr import parse, dump, children, prop

def nonmodel_digest(text):
    tree=parse(text)
    for f in children(tree,'footprint'):
        f[:]=[n for n in f if not(isinstance(n,list) and n[0]=='model')]
    return hashlib.sha256(dump(tree).encode()).hexdigest()

def verify_mechanical_baseline(root, baseline_hash):
    board=root/'hardware-q2/hardware.kicad_pcb'
    if hashlib.sha256(board.read_bytes()).hexdigest()==baseline_hash:return
    record=json.loads((root/'hardware-q2/models3d/attachment-validation.json').read_text(encoding='utf8'))
    assert record['baseline_pcb_sha256']==baseline_hash
    assert nonmodel_digest(board.read_text(encoding='utf8'))==record['unchanged_without_model_nodes_sha256'], 'PCB geometry changed; refresh mechanical sources.'

def main():
    path=P/'hardware.kicad_pcb'
    # This immutable revision is the electrically and mechanically checked board
    # immediately before adding 3D associations. Never compare with mutable HEAD.
    baseline=subprocess.check_output(['git','show','4bef85f:hardware-q2/hardware.kicad_pcb'],cwd=P.parent)
    baseline_hash=hashlib.sha256(baseline).hexdigest()
    assert baseline_hash=='ce984be8cd00eccfb9ba1c35203b1fd6431c1c1a723471e4444699da7df6e87b'
    digest=nonmodel_digest(path.read_text(encoding='utf8'))
    assert digest==nonmodel_digest(baseline.decode('utf8'))
    tree=parse(path.read_text(encoding='utf8'))
    manifest=json.loads((P/'models3d/model-manifest.json').read_text(encoding='utf8'))
    models={m['footprint']:m for m in manifest['models']}
    refs=[];excluded=[]
    for f in children(tree,'footprint'):
        ref=prop(f,'Reference')[2];mm=children(f,'model')
        if str(ref).startswith('SCREW'):
            assert not mm;excluded.append(ref);continue
        m=models[str(f[1]).split(':')[-1]]
        assert len(mm)==1 and str(mm[0][1])=='${KIPRJMOD}/models3d/'+m['file']
        assert hashlib.sha256((P/'models3d'/m['file']).read_bytes()).hexdigest()==m['model_sha256']
        refs.append(ref)
    for f in (P/'MP3_Source.pretty').glob('*.kicad_mod'):
        t=parse(f.read_text(encoding='utf8'))
        if f.stem in models:assert len(children(t,'model'))==1
    assert len(refs)==122 and len(excluded)==4 and len(models)==41
    record={'models_attached':len(refs),'unique_models':len(models),'excluded_mounting_holes':excluded,'model_only_change_verified':True,'baseline_git_revision':'4bef85f','baseline_pcb_sha256':baseline_hash,'pcb_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'unchanged_without_model_nodes_sha256':digest,'all_model_files_resolve':True,'all_model_sha256_match':True,'mechanical_component_model_interference_revalidated':False,'mechanical_note':'Existing E assembly uses frozen approximate envelopes, including U9 height3.2. New U9 STEP uses datasheet nominal3.5. A model-only PCB change does not validate enclosure fit against the new STEP assembly.'}
    (P/'models3d/attachment-validation.json').write_text(json.dumps(record,indent=2),encoding='utf8')
    print('3D_MODELS_VERIFIED',json.dumps(record))

if __name__=='__main__':main()
