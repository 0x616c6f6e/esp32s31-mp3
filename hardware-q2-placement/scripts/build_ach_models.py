"""FreeCAD: nominal mated ACH envelope, not manufacturer-certified CAD.

Source: JST eACH.pdf. Overall mated height 1.4, depth 4.3; body widths 4.2/5.4.
Pads locate terminals; internal latch/contact details intentionally omitted.
Local model frame: footprint X, negative footprint Y, Z above PCB.
"""
from pathlib import Path
import FreeCAD as App,Part
P=Path(__file__).resolve().parents[1]
for n,width in [(2,4.2),(3,5.4)]:
    name=f'JST_ACH_BM0{n}B-ACHSS-GAN-ETF_1x0{n}-1MP_P1.20mm_Vertical'
    body=Part.makeBox(width,4.3,1.3,App.Vector(-width/2,-2.3,.1))
    # Conservative solid mated envelope includes plug, but not wires.
    pins=[Part.makeBox(.6,.85,.15,App.Vector((i-(n-1)/2)*1.2-.3,1.45,0)) for i in range(n)]
    for xx in [-width/2+.35,width/2-.35]:
        pins.append(Part.makeBox(.7,.8,.15,App.Vector(xx-.35,-2.3,0)))
    shape=Part.makeCompound([body]+pins)
    shape.exportStep(str(P/'models3d'/f'{name}.step'))
print('ACH_ENVELOPE_MODELS_SAVED')
