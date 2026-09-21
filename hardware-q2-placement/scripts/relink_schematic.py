"""Restore UUID associations from a freshly exported KiCad XML netlist.

Run with KiCad's Python. References are used only to repair missing links; every
pin/net, value and footprint ID is checked before saving. Net updates require
the explicit --sync-nets option and are recorded in the repair report.
"""
from pathlib import Path
import argparse, collections, hashlib, json, re, xml.etree.ElementTree as ET
import pcbnew as pcb

P = Path(__file__).resolve().parents[1]

def normalized_net(name):
    return name.replace('{slash}', '/').replace('{backslash}', '\\')

def run(netlist, apply=False, remove=(), sync_nets=False):
    xml = ET.parse(netlist).getroot()
    root_uuid = re.search(r'\(uuid "([^"]+)"\)', (P/'hardware.kicad_sch').read_text(encoding='utf8')).group(1)
    components = {c.get('ref'): c for c in xml.findall('./components/comp')
                  if not any(p.get('name') == 'exclude_from_board' for p in c.findall('property'))}
    nets = {(n.get('ref'), n.get('pin')): normalized_net(net.get('name'))
            for net in xml.findall('./nets/net') for n in net.findall('node')}
    board_path = P/'hardware.kicad_pcb'
    before = hashlib.sha256(board_path.read_bytes()).hexdigest()
    board = pcb.LoadBoard(str(board_path))
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    assert len(fps) == len(board.GetFootprints()), 'Duplicate PCB references'
    assert len(components) == len(xml.findall('./components/comp')) - sum(
        any(p.get('name') == 'exclude_from_board' for p in c.findall('property'))
        for c in xml.findall('./components/comp')), 'Duplicate schematic references'
    obsolete = set(fps)-set(components)
    assert obsolete <= set(remove) and not set(components)-set(fps), (obsolete, set(components)-set(fps))
    assert not board.GetTracks(), 'This repair is for an unrouted board'
    removed_objects = [fps.pop(ref) for ref in obsolete]
    for footprint in removed_objects:
        board.Remove(footprint)
    changes = []
    net_changes = []
    for ref, f in sorted(fps.items()):
        c = components[ref]
        assert f.GetValue() == c.findtext('value'), (ref, 'value mismatch')
        assert f.GetFPIDAsString() == c.findtext('footprint'), (ref, 'footprint mismatch')
        for pad in f.Pads():
            actual = normalized_net(pad.GetNetname())
            expected = nets.get((ref, pad.GetNumber()), '')
            if actual != expected:
                assert sync_nets, (ref, pad.GetNumber(), actual, expected)
                target = next((v for v in board.GetNetsByNetcode().values() if normalized_net(v.GetNetname()) == expected), None)
                assert target is not None, (ref, 'New net requires explicit creation', expected)
                net_changes.append({'reference': ref, 'pad': pad.GetNumber(), 'before': actual, 'after': expected})
                pad.SetNet(target)
        props = {v.get('name'): v.get('value', '') for v in c.findall('property')}
        assert f.IsDNP() == ('dnp' in props), (ref, 'DNP mismatch')
        stamps = c.findtext('tstamps').split()
        assert len(stamps) == 1, (ref, 'Multi-unit symbol requires explicit mapping')
        path = '/' + root_uuid + c.find('sheetpath').get('tstamps') + stamps[0]
        old = f.GetPath().AsString()
        assert not old or old == path, (ref, 'Existing association conflicts')
        changes.append({'reference': ref, 'old_path': old, 'path': path,
                        'sheetfile': props['Sheetfile'], 'sheetname': props['Sheetname']})
        if apply:
            f.SetPath(pcb.KIID_PATH(path))
            f.SetSheetfile(props['Sheetfile'])
            f.SetSheetname(props['Sheetname'])
    if apply:
        assert before == hashlib.sha256(board_path.read_bytes()).hexdigest(), 'PCB changed during operation'
        pcb.SaveBoard(str(board_path), board)
    report = {'action': 'apply' if apply else 'check', 'source_netlist': str(netlist),
              'input_pcb_sha256': before,
              'pcb_sha256': hashlib.sha256(board_path.read_bytes()).hexdigest(),
              'footprints': len(fps), 'missing_before': sum(not x['old_path'] for x in changes),
              'pad_nets_values_footprints_dnp_verified': True, 'removed_obsolete': sorted(obsolete),
              'synchronized_pads': net_changes, 'links': changes}
    if apply:
        out = P/'output/reassociation.json'
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k != 'links'}, ensure_ascii=False))

if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('netlist', type=Path)
    args.add_argument('--apply', action='store_true')
    args.add_argument('--remove', nargs='*', default=[])
    args.add_argument('--sync-nets', action='store_true')
    options = args.parse_args()
    run(options.netlist, options.apply, options.remove, options.sync_nets)
