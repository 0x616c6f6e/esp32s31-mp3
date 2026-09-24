"""Update only J2's mechanical footprint, preserving board placement and other work."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent/'am213-fpc-adapter'
if (ROOT/'am213-fpc-adapter.kicad_sch').exists():
    raise SystemExit('Legacy placement generator disabled: completed electrical project exists.')
NAME='OK-23GF024-04_MechanicalOnly'
FP='''(footprint "OK-23GF024-04_MechanicalOnly"
  (version 20260206) (generator "pcbnew")
  (layer "F.Cu")
  (descr "OCN socket: 7.32x2.59x0.79mm, 24 contacts, 0.4mm pitch. MECHANICAL ONLY; no copper pads; Pin 1 unresolved.")
  (attr board_only exclude_from_pos_files exclude_from_bom)
  (property "Reference" "J2" (at 0 -4.5) (layer "F.Fab")
    (effects (font (size 0.8 0.8) (thickness 0.12))))
  (property "Value" "OK-23GF024-04" (at 0 4.5) (layer "F.Fab") hide
    (effects (font (size 0.6 0.6) (thickness 0.1))))
  (fp_rect (start -1.295 -3.66) (end 1.295 3.66)
    (stroke (width 0.12) (type default)) (fill none) (layer "F.Fab"))
  (fp_rect (start -2 -6) (end 2 6)
    (stroke (width 0.08) (type dash)) (fill none) (layer "Dwgs.User"))
  (fp_line (start -0.45 0) (end 0.45 0) (stroke (width 0.1) (type default)) (layer "F.Fab"))
  (fp_line (start 0 -0.45) (end 0 0.45) (stroke (width 0.1) (type default)) (layer "F.Fab"))
  (model "${KIPRJMOD}/models3d/OK-23GF024-04.step"
    (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))
)
'''

def update_board():
    import re
    p=ROOT/'am213-fpc-adapter.kicad_pcb';s=p.read_text(encoding='utf-8')
    match=re.search(r'\(footprint "Adapter_Placement:(?:BTB_24P_Placement_Only|OK-23GF024-04_MechanicalOnly)"',s)
    assert match,'Expected J2 mechanical footprint missing; refusing to replace other content'
    start=match.start();depth=0;quoted=False;escape=False
    for i in range(start,len(s)):
        c=s[i]
        if escape:escape=False;continue
        if quoted and c=='\\':escape=True;continue
        if c=='"':quoted=not quoted
        if not quoted:
            if c=='(':depth+=1
            if c==')':
                depth-=1
                if not depth:end=i+1;break
    old=s[start:end]
    at=re.search(r'\(at [^)]+\)',old).group(0)
    assert not re.search(r'\(pad\s',old),'Existing copper requires manual review'
    fp=FP.replace(f'"{NAME}"',f'"Adapter_Placement:{NAME}"',1).replace('(version 20260206) (generator "pcbnew")','',1).replace('(layer "F.Cu")',f'(layer "F.Cu") {at}',1)
    s=s[:start]+fp+s[end:]
    s=s.replace('J2: 24P BTB\\nPAD / PIN 1 TBD','J2: OK-23GF024-04\\nPAD / PIN 1 TBD')
    p.write_text(s,encoding='utf-8')
    (ROOT/'Adapter_Placement.pretty'/f'{NAME}.kicad_mod').write_text(FP,encoding='utf-8')
    print('J2 model attached; preserved placement',at)
if __name__=='__main__':update_board()
