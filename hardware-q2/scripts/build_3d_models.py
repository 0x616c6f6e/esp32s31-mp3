"""Run in FreeCAD GUI: generate colored, footprint-local STEP models."""
import FreeCAD as App, Part, Import, ImportGui, math, json, shutil,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];OUT=P/'models3d';plan=json.loads((OUT/'model-plan.json').read_text(encoding='utf8'));V=App.Vector
black=(.085,.09,.10);metal=(.73,.75,.77);gold=(.78,.61,.24);fr4=(.12,.23,.18)
report=[]
for entry in plan:
    dest=OUT/entry['file'];doc=App.newDocument('ModelBuild');parts=[]
    def obj(name,shape,color):
        o=doc.addObject('PartDesign::Feature',name);o.Shape=shape;o.ViewObject.ShapeColor=color;parts.append(o);return o
    def box(x0,y0,x1,y1,z0,z1):return Part.makeBox(x1-x0,y1-y0,z1-z0,V(x0,-y1,z0))
    if entry['kind']=='standard':
        ImportGui.insert(str(OUT/entry['source_model']),doc.Name)
        parts=[o for o in doc.Objects if hasattr(o,'Shape') and not o.Shape.isNull() and not o.OutList]
        # Source package Fab outlines are centered. Pad lengths differ between
        # libraries, so do not translate the body using biased pad centroids.
        entry['offset_xyz']=[0,0,0]
        transform=App.Placement(V(),App.Rotation(V(0,0,1),entry['rotation_z_physical_deg']))
        for o in parts:o.Placement=transform.multiply(o.Placement)
        doc.recompute()
        if entry['rotation_z_physical_deg']==0:shutil.copyfile(OUT/entry['source_model'],dest)
        else:ImportGui.export(parts,str(dest))
    else:
        x0,y0,x1,y1=entry['bounds'];h=entry['height'];kind=entry['kind'];pins=[]
        if kind=='esp32s31':
            obj('ModulePCB',box(x0,y0,x1,y1,.04,1),fr4)
            shield=box(-10.5,-11.5,10.5,11.5,1,3.5)
            obj('Shield',shield,metal)
            obj('Pin1Marker',Part.makeCylinder(.25,.015,V(-10,11,3.5)),black)
        elif kind=='usb':
            hood=box(x0,y0,x1,y1,0,h).cut(box(x0+.3,y0+.3,x1-.3,y1+.1,.3,h-.3))
            obj('MetalShell',hood,metal);obj('ContactTongue',box(-3,y0+.5,3,y1-.55,1.25,1.75),black)
        elif kind=='jack':
            body=box(x0,y0,x1,y1,0,h).cut(Part.makeCylinder(1.75,12.5,V(x0-.01,-(y0+y1)/2,h/2),V(1,0,0)))
            obj('SocketBody',body,black)
            ring=Part.makeCylinder(2.12,.15,V(x0,-(y0+y1)/2,h/2),V(1,0,0)).cut(Part.makeCylinder(1.75,.17,V(x0-.01,-(y0+y1)/2,h/2),V(1,0,0)))
            obj('MouthRim',ring,metal)
        elif kind=='tf':
            obj('Insulator',box(x0+.3,y0+.3,x1-.3,y1-.3,0,.35),black)
            shell=box(x0,y0,x1,y1,.35,h).cut(box(x0+.25,y0+.25,x1-.25,y1+.1,.35,h-.2))
            obj('CardShell',shell,metal)
        elif kind=='fpc':
            obj('ConnectorHousing',box(x0,y0,x1,y1,.08,h),(.23,.24,.25))
            obj('Latch',box(-3.32,.8,3.32,1.96,.73,1),black)
        elif kind in ['socket','header']:
            body=box(x0,y0,x1,y1,0,h if kind=='socket' else 2.0)
            for p in entry['pads']:
                if not p['number']:continue
                x,y=p['position']
                if kind=='socket':body=body.cut(box(x-.38,y-.38,x+.38,y+.38,1,h+.1))
                pins.append(box(x-.3,y-.3,x+.3,y+.3,-2.8,.5 if kind=='socket' else h))
            obj('HeaderBody',body,black)
        else:
            body=box(x0,y0,x1,y1,.07,h)
            obj('Body',body,(.23,.24,.25) if kind=='chip' else black)
            if kind in ['ic','rtc']:
                pin1=next(p for p in entry['pads'] if p['number']=='1');x,y=pin1['position'];x=max(x0+.17,min(x1-.17,x));y=max(y0+.17,min(y1-.17,y))
                obj('Pin1Marker',Part.makeCylinder(min(.13,(x1-x0)/12),.012,V(x,-y,h)),(.62,.64,.65))
        if kind not in ['socket','header']:
            for p in entry['pads']:
                if not p['number'] or p['type']=='np_thru_hole':continue
                x,y=p['position'];sx,sy=p['size'];scale=.72 if kind!='esp32s31' else .9
                # Terminal geometry follows the pad orientation; no slot, latch
                # or solder-fillet dimensions are inferred from these pads.
                pin=Part.makeBox(sx*scale,sy*scale,.075,V(-sx*scale/2,-sy*scale/2,0));pin.rotate(V(),V(0,0,1),p['angle']);pin.translate(V(x,-y,0));pins.append(pin)
        if pins:obj('Terminals',Part.makeCompound(pins),gold if kind in ['esp32s31','header','socket','fpc'] else metal)
        doc.recompute();ImportGui.export(parts,str(dest))
    combined=Part.makeCompound([o.Shape for o in parts]);bb=combined.BoundBox
    assert combined.isValid(),entry['footprint']
    entry['model_bounds_xyz_mm']=[bb.XMin,bb.YMin,bb.ZMin,bb.XMax,bb.YMax,bb.ZMax]
    entry['model_sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();report.append(entry)
    App.closeDocument(doc.Name)
(OUT/'model-manifest.json').write_text(json.dumps({'units':'mm','coordinate_system':'footprint local X, negative footprint Y, Z up; transforms baked into STEP','models':report},ensure_ascii=False,indent=2),encoding='utf8')
print('MODELS_CREATED',len(report),'COMPONENT_INSTANCES',sum(len(e['references']) for e in report))
