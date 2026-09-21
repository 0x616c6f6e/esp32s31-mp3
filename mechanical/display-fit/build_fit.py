"""FreeCAD geometry audit. Current board is read-only. No forced lateral FPC shear."""
import FreeCAD as App, Part, math, json, csv
from pathlib import Path
HERE=Path(__file__).resolve().parent
OUT=HERE/'exports'; OUT.mkdir(exist_ok=True)
V=App.Vector
board=json.loads((HERE/'reference/current-fpc2.json').read_text(encoding='utf8'))
source=HERE.parent/'enclosure-q2-c'
flat=App.openDocument(str(HERE/'LCD209_dimensioned.FCStd'))
doc=App.newDocument('LCD_FPC2_Fit_Audit')
colors={}
def obj(name,shape,col,note):
    o=doc.addObject('Part::Feature',name);o.Shape=shape
    o.addProperty('App::PropertyString','Evidence','Audit').Evidence=note
    colors[name]=col
    if App.GuiUp:o.ViewObject.ShapeColor=tuple(float(v) for v in col);o.ViewObject.DisplayMode='Shaded'
    return o
def bx(a,b,c,x,y,z):return Part.makeBox(a,b,c,V(x,y,z))
pcb=Part.Shape();pcb.read(str(source/'reference/source-PCB.brep'))
pcb.rotate(V(25,0,0),V(0,1,0),180);pcb.translate(V(0,0,12.3))
main=obj('CurrentMainPCB',pcb,(.12,.43,.31),'Current board body at C rigid transform. Connector coordinates freshly read from hardware.kicad_pcb.')
cs=Part.Shape();cs.read(str(source/'reference/source-ComponentEnvelopes.brep'))
cs.rotate(V(25,0,0),V(0,1,0),180);cs.translate(V(0,0,12.3))
layout=json.loads((HERE.parents[1]/'hardware/output/layout-data.json').read_text(encoding='utf8'))
names=[f['reference'] for f in layout['footprints'] if not f['reference'].startswith('SCREW')]
shapes=dict(zip(names,cs.Solids))
esp=obj('ESP32Envelope',shapes['U9'],(.6,.63,.68),'Original footprint XY; component height3.2 assumed, retained for clearance audit.')
screen=Part.makeCompound([flat.getObject(n).Shape for n in ['BacklightBody','LCDGlass','ActiveArea']])
screen.rotate(V(0,0,0),V(0,0,1),90);screen.translate(V(46.725,3.735,11.84))
lcd=obj('InstalledLCD',screen,(.12,.15,.19),'User BL36.33 x43.45 x1.46; landscape C placement. Corner radius estimated.')
# JUSHUO drawing proves closed height1.0 and 7.9 x3.2 nominal outer body.
# Slot location/height NOT dimensioned: show solid envelope, never a fictitious fitted slot.
conn=obj('ActualFPC2Envelope',bx(3.2,7.9,1,7.652,14.084,3.2),(.83,.18,.16),'AFE03-S21FMA-1H: body7.9 x3.2 x1.0. No modeled mating slot: insertion Z and stop need supplier confirmation. FPC lower contacts, t0.20 +/-0.03, stiffened length3.5min.')
padsh=[]
for p in board['pads']:
    if int(p['pin'])<=21:
        x,y=p['case_xy'];padsh.append(bx(.7,.18,.04,x-.35,y-.09,4.16))
pads=obj('ActualSolderPadCenters',Part.makeCompound(padsh),(.92,.7,.28),'Actual KiCad solder-pad centers. These are NOT internal mating-contact positions.')
# Translation-only candidate, hidden by default: no copper change and no clearance claim.
candidate=conn.Shape.copy();candidate.translate(V(0,3.866,0))
prop=obj('ProposedFPC2_Yplus3p866',candidate,(.16,.49,.86),'XY alignment candidate only: board(140.148,70.900),90deg,B.Cu. Placement/routing and adjacent components NOT validated.')
# Developable cylindrical bends, no XY shear or stretch. Radii and Z are assumptions.
cy=21.9;t=.12;edge=3.275;wrapx=1.4;r=.65;ztop=12.09
zrun=2.35;zreturn=3.70;ru=(zreturn-zrun)/2;tx=wrapx+r
topcenter=ztop-r;bottomcenter=zrun+r
prefix=edge-tx+math.pi*r+topcenter-bottomcenter
neckremain=12.8-prefix;nx=tx+neckremain;tipx=8.352
turnx=(46.14-12.8+nx-math.pi*ru+tipx)/2
assert neckremain>0 and turnx>tipx
def arc(cx,cz,rad,width,clip):
    ring=Part.makeCylinder(rad+t/2,width,V(cx,cy-width/2,cz),V(0,1,0)).cut(Part.makeCylinder(rad-t/2,width+2,V(cx,cy-width/2-1,cz),V(0,1,0)))
    return ring.common(clip)
upper=arc(tx,topcenter,r,18,bx(r+t,20,r+t,tx-r-t,cy-10,topcenter))
lower=arc(tx,bottomcenter,r,18,bx(r+t,20,r+t,tx-r-t,cy-10,bottomcenter-r-t))
loop=arc(turnx,(zrun+zreturn)/2,ru,6.6,bx(ru+t,8,2*ru+2*t,turnx,cy-4,zrun-t))
segments=[bx(edge-tx,18,t,tx,cy-9,ztop-t/2),upper,bx(t,18,topcenter-bottomcenter,wrapx-t/2,cy-9,bottomcenter),lower,bx(neckremain,18,t,tx,cy-9,zrun-t/2),bx(turnx-nx,6.6,t,nx,cy-3.3,zrun-t/2),loop,bx(turnx-tipx,6.6,t,tipx,cy-3.3,zreturn-t/2)]
route=obj('Unjogged46p14mmFPC',Part.makeCompound(segments),(.92,.54,.12),'Constant-width cylindrical-fold candidate preserves nominal centerline length. No sideways displacement. FPC body t0.12, R0.65/R0.675, neck18x12.8, terminalZ3.70 and tipX8.352 are assumptions; NOT a validated installation.')
tip=obj('UnjoggedTerminalEnvelope',bx(2.5,6.6,.04,tipx,cy-3.3,zreturn+t/2),(.97,.77,.23),'2.5 mm exposed-contact envelope; centered Y21.9, actual socket axisY18.034. Not inserted or electrically mated.')
axis=obj('NaturalTailAxis',Part.makeLine(V(0,cy,3.75),V(25,cy,3.75)),(.85,.47,.09),'Natural tail centerline Y21.900')
sockaxis=obj('ActualSocketAxis',Part.makeLine(V(0,18.034,3.76),V(25,18.034,3.76)),(.85,.16,.18),'Actual socket contact-row transverse centerY18.034')
clashes={}
for name,s in [('PCB',pcb),('ESP32_assumed_envelope',shapes['U9'])]:
    common=s.common(route.Shape);clashes[name]=round(common.Volume,6)
    if common.Volume>1e-6:obj('Interference_'+name,common,(1,.05,.12),'Interference of this illustrative cylindrical-fold route with current source geometry; component heights provisional.')
length=prefix+neckremain+(turnx-nx)+math.pi*ru+(turnx-tipx)
physical=[main,esp,lcd,conn,pads,route,tip]
checks={o.Name:{'valid':o.Shape.isValid(),'solids':len(o.Shape.Solids)} for o in physical}
assert all(v['valid'] for v in checks.values()) and abs(length-46.14)<1e-7
pins=[p for p in board['pads'] if int(p['pin'])<=21]
socket_y=sum(p['case_xy'][1] for p in pins)/21
assert abs(socket_y-18.034)<1e-6
audit={'status':'NOT_CONFIRMED_MATABLE_IN_CURRENT_ASSEMBLY','board_sha256':board['sha256'],'lcd_nominal_mm':[36.33,43.45,1.46],'lcd_tolerance_mm':[.1,.1,.1],'tail_width_mm':6.6,'tail_width_tolerance_mm':.05,'tail_extension_mm':46.14,'tail_extension_tolerance_mm':.5,'terminal_span_mm':6,'derived_pitch_mm':.3,'terminal_pitch_tolerance':'not specified; drawing0.3 +/-0.03 is edge offset','fpc2_case_axis_y_mm':socket_y,'lcd_tail_case_axis_y_mm':cy,'transverse_offset_mm':round(cy-socket_y,6),'connector_body_mm':[7.9,3.2,1],'required_insertion_thickness_mm':.2,'required_insertion_thickness_tolerance_mm':.03,'required_stiffened_length_min_mm':3.5,'lcd_insertion_thickness':'unknown','lcd_pin_functions':'unknown','connector_slot_z':'not specified in source drawing; NOT asserted by this model','candidate_kicad_xy_mm':[140.148,70.900],'candidate_is_applied':False,'un_jogged_candidate_centerline_length_mm':length,'candidate_radii_mm':[r,ru],'candidate_intersections_mm3':clashes,'geometry':checks,'source_pdf':'https://datasheet.lcsc.com/datasheet/pdf/a3fef74488a86aba9513d2bb0e2e596c.pdf?productCode=C262542'}
(OUT/'fit-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
with (OUT/'pin-comparison.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['pin','mainboard_net','screen_function','socket_case_y_mm','unshifted_screen_pin_y_mm','offset_mm'])
    for p in sorted(pins,key=lambda p:int(p['pin'])):
        n=int(p['pin']);natural=cy+3-(n-1)*.3
        w.writerow([n,p['net'],'UNKNOWN',p['case_xy'][1],round(natural,6),round(natural-p['case_xy'][1],6)])
doc.recompute()
if App.GuiUp:
    prop.ViewObject.Visibility=False;main.ViewObject.Transparency=70;lcd.ViewObject.Transparency=75
doc.saveAs(str(HERE/'LCD_FPC2_fit_audit.FCStd'))
Part.makeCompound([o.Shape for o in physical]).exportStep(str(OUT/'current-assembly-NOT-MATED.step'))
conn.Shape.exportStep(str(OUT/'AFE03-21-envelope.step'))
(OUT/'audit-colors.json').write_text(json.dumps(colors),encoding='utf8')
print('FIT_AUDIT_COMPLETE',json.dumps(audit))
