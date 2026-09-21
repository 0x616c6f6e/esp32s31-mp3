from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
source=HERE.parent/'enclosure-q2'
params=json.loads((source/'parameters.json').read_text(encoding='utf8'))
(HERE/'parameters.json').write_text(json.dumps(params,indent=2),encoding='utf8')
s=(source/'build_display.py').read_text(encoding='utf8')
s=s.replace("DOCNAME='LCD209_Dimensioned'", "DOCNAME='LCD209_FitReview'")
s=s.replace("[DOCNAME,'LCD209_36x43']", "[DOCNAME,'LCD209_dimensioned']")
s=s.replace("HERE/'LCD209_36x43.FCStd'", "HERE/'LCD209_dimensioned.FCStd'")
s=s.replace("'Contact%02d'%(i+1)", "'Contact%02d'%(21-i)")
s=s.replace("Pin1 handedness/contact face must be checked.", "Pin1 at right in supplied front-view drawing; other pins inferred sequentially. This contact geometry is an envelope, not a terminal phototool. FPC insertion thickness, stiffener and physical contact face need confirmation. The drawing 0.3 +/-0.03 is an edge offset, NOT a pitch tolerance; pitch0.3 is inferred from21 contacts over6 mm.")
s=s.replace("parts.Label='外壳零件 / export these'", "parts.Label='LCD final parts'")
s=s.replace("refs.Label='PCB and ASSUMED component envelopes / 不打印'", "refs.Label='LCD / dimensioned outline and illustrative FPC'")
(HERE/'build_display.py').write_text(s,encoding='utf8')
