from pathlib import Path
import pcbnew as p,shutil,sys
P=Path(__file__).resolve().parents[1];ses=Path(sys.argv[1]);suffix=sys.argv[2] if len(sys.argv)>2 else '-route-review'
target=P/('q2-v2'+suffix+'.kicad_pcb');pro=(P/'q2-v2.kicad_pro').read_bytes()
b=p.LoadBoard(str(P/'q2-v2.kicad_pcb'));assert p.ImportSpecctraSES(b,str(ses))
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(target),b);target.with_suffix('.kicad_pro').write_bytes(pro)
print('Saved',target.name,len(b.GetTracks()),'tracks/vias')
