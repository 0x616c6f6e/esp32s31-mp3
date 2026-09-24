"""SCREW3 support: 0.5 mm left in KiCad, +X in case coordinates."""
import math

def apply(source_doc):
    outer = source_doc.getObject('MainPCBPostOuter2')
    pilot = source_doc.getObject('MainPCBPostPilot2')
    assert abs(outer.Placement.Base.y - 43.5) < .002
    assert outer.Radius.Value == 1.9 and pilot.Radius.Value == .8
    for obj in (outer, pilot):
        placement = obj.Placement
        placement.Base.x = 4.0
        obj.Placement = placement
    source_doc.recompute()
    return {'reference': 'SCREW3', 'old_case_center_mm': [3.5, 43.5],
            'new_case_center_mm': [4.0, 43.5], 'case_delta_mm': [.5, 0],
            'kicad_direction': 'left / -X', 'kicad_delta_mm': [-.5, 0],
            'pilot_diameter_mm': 1.6, 'support_diameter_mm': 3.8,
            'pcb_modified': False}
