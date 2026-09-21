from pathlib import Path
import subprocess,json,sys,collections
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'hardware-q2';sys.path.insert(0,str(ROOT/'tmp'))
from sexpr import *
cli='D:/KiCad/10.0/bin/kicad-cli.exe'
report=Path(sys.argv[1]) if len(sys.argv)>1 else P/'output/routed2-drc.json'
for iteration in range(30):
    data=json.loads(report.read_text(encoding='utf8'))
    bad={i['uuid'] for v in data['violations'] if v['type'] in ['track_dangling','via_dangling'] for i in v['items']}
    print(iteration,dict(collections.Counter(v['type'] for v in data['violations'])),'unconnected',len(data['unconnected_items']),flush=True)
    if not bad:break
    tree=parse((P/'hardware.kicad_pcb').read_text(encoding='utf8'))
    tree[:]=[n for n in tree if not(isinstance(n,list) and n[0] in ['segment','arc','via'] and get(n,'uuid')[1] in bad)]
    (P/'hardware.kicad_pcb').write_text(dump(tree)+'\n',encoding='utf8')
    report=P/'output/clean-drc.json'
    r=subprocess.run([cli,'pcb','drc','--refill-zones','--save-board','--schematic-parity','--format','json','-o',str(report),str(P/'hardware.kicad_pcb')],capture_output=True)
    if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace'))
print('STUB_CLEANUP_COMPLETE',flush=True)
