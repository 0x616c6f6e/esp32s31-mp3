import FreeCAD as App, Part, json, hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;OUT=HERE/'exports'
flat=App.openDocument(str(HERE/'LCD209_dimensioned.FCStd'))
module=Part.makeCompound([flat.BacklightBody.Shape,flat.LCDGlass.Shape])
bb=module.BoundBox
assert all(abs(a-b)<1e-6 for a,b in zip([bb.XLength,bb.YLength,bb.ZLength],[36.33,43.45,1.46]))
assert flat.Contact01.Shape.CenterOfMass.x>flat.Contact21.Shape.CenterOfMass.x
assert abs(flat.FlatFPC.Shape.BoundBox.YLength-46.14)<1e-6
reimport={}
for name in ['lcd209-flat-reference.step','lcd209-module-only.step','AFE03-21-envelope.step','current-assembly-NOT-MATED.step']:
    s=Part.Shape();s.read(str(OUT/name));assert s.isValid()
    reimport[name]={'valid':True,'solids':len(s.Solids),'bounds_mm':[s.BoundBox.XLength,s.BoundBox.YLength,s.BoundBox.ZLength]}
assert reimport['AFE03-21-envelope.step']['bounds_mm'][2]==1.0
audit=json.loads((OUT/'fit-audit.json').read_text(encoding='utf8'))
sha=hashlib.sha256((HERE.parents[1]/'hardware/hardware.kicad_pcb').read_bytes()).hexdigest()
assert sha==audit['board_sha256']
result={'board_unchanged':True,'lcd_native_size_verified':True,'pin1_right_in_source_front_view':True,'step_reimport':reimport,'assembly_mates':False}
(OUT/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print('VERIFICATION_COMPLETE',json.dumps(result))
