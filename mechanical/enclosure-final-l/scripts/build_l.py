"""AM213 screen assembly and mechanical adapter reservation; not an electrical release."""
from pathlib import Path
import FreeCAD as A,Part,json,math,hashlib
O=Path(__file__).resolve().parents[1];K=O.parent/'enclosure-final-k';V=A.Vector
d=A.openDocument(str(K/'Q2_K_Assembly_Access.FCStd'));d.Label='Q2 L / AM213 AMOLED / adapter development'
c=json.loads((O/'screen-contours.json').read_text())
assert hashlib.sha256((O.parents[1]/c['source']).read_bytes()).hexdigest()==c['sha256']
SCREEN_X=1.85
SCREEN_Y=.85  # Lower by 0.50 mm to balance the visible upper-corner border.
def box(x,y,z,w,h,t):return Part.makeBox(w,h,t,V(x,y,z))
def face(name,size=None):
 pts=c[name]
 if size:
  lo=[min(p[i] for p in pts) for i in [0,1]];hi=[max(p[i] for p in pts) for i in [0,1]]
  pts=[[(p[i]-(lo[i]+hi[i])/2)*size[i]/(hi[i]-lo[i])+(lo[i]+hi[i])/2 for i in [0,1]] for p in pts]
 if name in ['cover','panel']:
  # Replace quantized PDF polyline corners by tangent analytic arcs. These are
  # drawing-derived radii, not dimensioned supplier tolerances.
  x0=SCREEN_X+min(p[0] for p in pts);x1=SCREEN_X+max(p[0] for p in pts)
  y0=SCREEN_Y+min(p[1] for p in pts);y1=SCREEN_Y+max(p[1] for p in pts)
  rl,rr=(9.95,9.95) if name=='cover' else (9.0,8.42)
  ed=[]
  def pt(x,y):return V(x,y,0)
  def line(a,b):ed.append(Part.makeLine(pt(*a),pt(*b)))
  def arc(cx,cy,r,a,b):
   def p(t):return pt(cx+r*math.cos(math.radians(t)),cy+r*math.sin(math.radians(t)))
   ed.append(Part.Arc(p(a),p((a+b)/2),p(b)).toShape())
  line((x0+rl,y0),(x1-rr,y0));arc(x1-rr,y0+rr,rr,270,360)
  line((x1,y0+rr),(x1,y1-rr));arc(x1-rr,y1-rr,rr,0,90)
  line((x1-rr,y1),(x0+rl,y1));arc(x0+rl,y1-rl,rl,90,180)
  line((x0,y1-rl),(x0,y0+rl));arc(x0+rl,y0+rl,rl,180,270)
  return Part.Face(Part.Wire(ed))
 v=[V(SCREEN_X+p[0],SCREEN_Y+p[1],0) for p in pts]
 return Part.Face(Part.makePolygon(v+[v[0]]))
def ext(f,z,h):
 s=f.extrude(V(0,0,h));s.translate(V(0,0,z));return s
def offset(f,n):return Part.Face(f.OuterWire.makeOffset2D(n,join=0))
def add(n,s,group='AssemblyReferences',label=None):
 o=d.getObject(n) or d.addObject('PartDesign::Feature',n);o.Shape=s.removeSplitter();d.getObject(group).addObject(o)
 if label:o.Label=label
 return o
cg=face('cover');panel=face('panel',(43.14,34.79));va=face('viewing',(40.71,33.29));aa=face('viewing',(40.51,33.09))
s=d.HousingControlsA.Shape.copy()
# Fill the old aperture using its own outer top contour, retaining side ports.
top=[f for f in s.Faces if abs(f.BoundBox.ZMin-14.4)<1e-5 and abs(f.BoundBox.ZMax-14.4)<1e-5]
f=max(top,key=lambda f:f.Area)
fill=Part.Face(f.OuterWire).extrude(V(0,0,-2.9)).common(box(-3,-4,11.5,56,45,4))
s=s.fuse(fill)
# Full integrated glass fits from the front; support the black glass border.
cg_pocket=offset(cg,.25);panel_hole=offset(panel,.30)
s=s.cut(ext(cg_pocket,13.6,4)).cut(ext(panel_hole,10.85,3.0))
# Remove the former rear LCD rails; this screen mounts at its integral glass.
s=s.cut(box(13.9,1.49,11.49,22.2,2.52,1.06)).cut(box(13.9,36.99,11.49,22.2,2.52,1.06))
add('HousingControlsA',s,'PrintableParts','01 Housing L / AM213 integrated cover aperture')
add('LCDModule',ext(panel,12.82,.805),label='AM213 AMOLED panel / 43.14 x34.79 / stack excludes integral cover')
add('CoverLens',ext(cg,13.8,1.3),label='AM213 integral touch cover / 46.30 x37.50 x1.30 / NOT extra glass')
add('OLEDOpticalBond',ext(panel,13.625,.175),label='Factory OCA bond / 0.175 mm')
add('LCDActiveArea',ext(aa,15.095,.005),label='AM213 active area / landscape 40.51 x33.09 / 502x410 pixels')
add('LensBlackMask',ext(cg.cut(va),15.094,.006),label='Integral cover black mask / VA 40.71 x33.29')
adh=offset(cg,-.20).cut(offset(panel,.45))
add('LensAdhesive',ext(adh,13.6,.2),label='Mount integral cover black border / 0.20 mm adhesive')
for n in ['LCDMountTape','DisplayFPCRoute','DisplayChannelLiner']:
 if d.getObject(n):d.removeObject(n)
# The datasheet gives folded component heights but not a fully dimensioned FPC.
# Reserve its entire back-plane footprint rather than claiming an exact route.
reserve=ext(offset(panel,-.70),11.30,1.52)
add('ScreenRearFPCEnvelope',reserve,label='AM213 folded rear FPC/components KEEP-OUT / conservative 1.52 mm / contour TBD')
add('DisplayAdapterPCB',box(29,8,9.5,17,22,.6),label='Display adapter RESERVED / 17x22x0.6 / NOT routed PCB')
add('DisplayAdapterComponents',box(29.5,8.5,8.6,16,21,.9),label='Adapter underside component allowance / 0.9 mm')
add('DisplayAdapterConnectors',box(29.5,14,10.1,4,12,.8),label='Adapter connector allowance / mating drawings pending')
# Retain a clear separation between reservations and fabricated components.
for n in ['DisplayAdapterPCB','DisplayAdapterComponents','DisplayAdapterConnectors','ScreenRearFPCEnvelope']:
 o=d.getObject(n)
 if 'ValidationStatus' not in o.PropertiesList:o.addProperty('App::PropertyString','ValidationStatus')
 o.ValidationStatus='MECHANICAL RESERVATION ONLY; NOT AN ELECTRICALLY VALIDATED ASSEMBLY'
for o in d.PrintableParts.Group:assert o.Shape.isValid() and len(o.Shape.Solids)==1,(o.Name,len(o.Shape.Solids))
p=json.loads((K/'parameters.json').read_text())
for n in ['lcd_origin_mm','lcd_mount']:p.pop(n,None)
p.update(revision='L',display_model='AM213Q410502LK',display_size_inch=2.13,display_type='AMOLED with integral touch cover',
 display_resolution_portrait=[410,502],display_cover_landscape_mm=[46.3,37.5,1.3],display_total_stack_mm=2.28,
 display_stack_tolerance_mm=.2,display_total_stack_back_z_mm=12.82,display_panel_landscape_mm=[43.14,34.79],
 display_active_landscape_mm=[40.51,33.09],display_cover_xy_mm=[SCREEN_X,SCREEN_Y],
 display_straight_edge_margins_mm={'left':1.85,'right':1.85,'top':2.35},display_downward_adjustment_mm=.5,
 display_alignment_note='Upper corner visual border balanced against side border; straight top margin intentionally 0.5 mm larger.',
 display_cover_pocket_clearance_per_side_mm=.25,display_border_mount_adhesive_mm=.2,
 adapter_reserved_case_xyz_mm=[29,8,9.5],adapter_reserved_pcb_mm=[17,22,.6],
 display_connection='24-pin OK-23GM024-04 cannot mate existing 21-pin FPC2. Active adapter, cable and power source required; NOT released.',
 status='MECHANICAL_SCREEN_UPDATE_WITH_ADAPTER_RESERVATION; NOT COMPLETE_ASSEMBLY_RELEASE')
(O/'parameters.json').write_text(json.dumps(p,indent=2));(O/'source.json').write_bytes((K/'source.json').read_bytes())
d.DesignParameters.clearAll()
for i,(k,v) in enumerate(p.items(),1):d.DesignParameters.set('A'+str(i),k);d.DesignParameters.set('B'+str(i),str(v))
d.recompute();d.saveAs(str(O/'Q2_L_AM213_Adapter_Study.FCStd'))
print('L_BUILT',s.isValid(),s.Volume,flush=True)
