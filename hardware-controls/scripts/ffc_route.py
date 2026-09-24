"""Constant-width, developable 40 mm FFC route in the X/Z plane.
No lateral shear, pin-order reversal, or cable stretching is modeled.
Bend radius, body thickness and connector mating elevation are assumptions.
"""
import math
import FreeCAD as A, Part
V=A.Vector

def build(add,parts,models,obstacles,volume):
 y=51.711;width=6.5;thick=.15;r=1.1
 y0=y-width/2;shapes=[];length=0.;segments=[]
 def point(x,z):return V(x,y0,z)
 def straight(a,b,t=thick,count=True):
  nonlocal length
  dx,dz=b[0]-a[0],b[1]-a[1];l=math.hypot(dx,dz);nx,nz=-dz/l*t/2,dx/l*t/2
  pp=[point(a[0]+nx,a[1]+nz),point(b[0]+nx,b[1]+nz),point(b[0]-nx,b[1]-nz),point(a[0]-nx,a[1]-nz)]
  shapes.append(Part.Face(Part.makePolygon(pp+[pp[0]])).extrude(V(0,width,0)))
  if count:length+=l;segments.append({'line':[a,b],'length_mm':l})
 def arc(c,a,b):
  nonlocal length
  def pt(rr,deg):
   th=math.radians(deg);return point(c[0]+rr*math.cos(th),c[1]+rr*math.sin(th))
  ro,ri=r+thick/2,r-thick/2
  edges=[Part.Arc(pt(ro,a),pt(ro,(a+b)/2),pt(ro,b)).toShape(),Part.makeLine(pt(ro,b),pt(ri,b)),Part.Arc(pt(ri,b),pt(ri,(a+b)/2),pt(ri,a)).toShape(),Part.makeLine(pt(ri,a),pt(ro,a))]
  shapes.append(Part.Face(Part.Wire(edges)).extrude(V(0,width,0)))
  l=r*abs(math.radians(b-a));length+=l;segments.append({'arc_center':c,'angles_deg':[a,b],'radius_mm':r,'length_mm':l})
 main_tip=27.799;control_tip=38.7
 straight((main_tip,3.8),(34.5,3.8))
 arc((34.5,2.7),90,0);arc((36.7,2.7),180,270)
 straight((36.7,1.6),(47.443748,1.6))
 arc((47.443748,2.7),270,360)
 straight((48.543748,2.7),(48.543748,9.6))
 arc((47.443748,9.6),0,90)
 straight((47.443748,10.7),(control_tip,10.7))
 # Terminal reinforcement, 4 mm minimum, 0.30 mm total insertion thickness.
 straight((main_tip,3.8),(main_tip+4,3.8),.3,False)
 straight((control_tip+4,10.7),(control_tip,10.7),.3,False)
 cable=add('ControlFFC40mm',Part.makeCompound(shapes),'References',(.88,.57,.17),'FFC 12P / 0.5 / 40 mm / B opposite contacts / nominal R1.1')
 conflicts=[];clearances=[]
 targets={**obstacles,**{n:o.Shape for n,o in models.items()}}
 for name,sh in targets.items():
  if name in ['PCB_FPC1','J1']:continue # Intended mating regions.
  v=volume(cable.Shape,sh)
  if v>1e-5:conflicts.append({'against':name,'volume_mm3':round(v,6)})
  if name in ['MainPCB','HousingControlsA','RearCoverWithPCBPosts','MotorMaximumEnvelope','BatteryReference']:
   clearances.append({'against':name,'distance_mm':round(cable.Shape.distToShape(sh)[0],4)})
 report={'nominal_centerline_length_mm':round(length,6),'target_stock_length_mm':40,'width_mm':width,'body_thickness_assumed_mm':thick,'terminal_thickness_mm':.3,'terminal_reinforcement_mm':4,'bend_radius_assumed_mm':r,'connector_slot_height_and_insertion_depth_assumed':True,'no_in_plane_bending_or_twist':True,'contact_type':'B / opposite exposed faces','pin_mapping':{str(i):i for i in range(1,13)},'center_axis_case_y_mm':y,'segments':segments,'conflicts':conflicts,'clearances':clearances,'nominal_route_pass':not conflicts and abs(length-40)<.02,'physical_sample_validation_required':True}
 return report
