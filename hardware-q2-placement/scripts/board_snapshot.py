"""Stable identity and mechanical snapshot for the unrouted placement handoff."""
import hashlib, json, re
import pcbnew as p

def tree(text):
    stack=[];root=None
    for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',text):
        if token=='(':
            node=[]
            if stack:stack[-1].append(node)
            stack.append(node)
        elif token==')':root=stack.pop()
        else:stack[-1].append(token)
    return root

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def snapshot(path):
    b=p.LoadBoard(str(path));t=tree(path.read_text(encoding='utf8'))
    def digest(nodes):return hashlib.sha256(json.dumps(nodes).encode()).hexdigest()
    def field(node,key):return next((x for x in node if isinstance(x,list) and x[0]==key),None)
    fps={}
    for f in b.GetFootprints():
        fps[f.GetReference()]={
            'uuid':f.m_Uuid.AsString(),'path':f.GetPath().AsString(),
            'value':f.GetValue(),'fpid':f.GetFPIDAsString(),'dnp':f.IsDNP(),
            'xy':[f.GetPosition().x/1e6,f.GetPosition().y/1e6],
            'angle':f.GetOrientationDegrees(),'side':'B' if f.IsFlipped() else 'F',
            'locked':f.IsLocked(),
            'pads':sorted([[a.m_Uuid.AsString(),a.GetNumber(),a.GetNetname()] for a in f.Pads()]),
        }
    return {'pcb_sha256':sha(path),'footprints':fps,
        'outline_sha256':digest([n for n in t if isinstance(n,list) and n[0].startswith('gr_') and field(n,'layer')==['layer','"Edge.Cuts"']]),
        'zones_sha256':digest([n for n in t if isinstance(n,list) and n[0]=='zone']),
        'layers_sha256':digest(field(t,'layers')),'stackup_sha256':digest(field(field(t,'setup'),'stackup')),
        'tracks_arcs_vias':len(b.GetTracks()),'copper_zones':sum(not z.GetIsRuleArea() for z in b.Zones()),
        'model_instances':sum(len([v for v in n if isinstance(v,list) and v[0]=='model']) for n in t if isinstance(n,list) and n[0]=='footprint')}
