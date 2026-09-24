from pathlib import Path
import FreeCAD as A,Part
out=Path(__file__).resolve().parents[1]/'models3d/U10-nominal-envelope.step'
# Missing vendor model: conservative package envelope from referenced filename.
# Body 5.3x5.3x1.9, total lead span 7.9; no claim of vendor tolerance coverage.
s=Part.makeBox(7.9,5.3,1.9,A.Vector(-3.95,-2.65,0))
s.exportStep(str(out))
print('U10 nominal envelope exported')
