import FreeCAD as A,Part,math
V=A.Vector
def build():
 y=20.4005;t=.12;r=.8;sh=[];segs=[];length=0.
 def pt(x,z,width):return V(x,y-width/2,z)
 def line(a,b,width):
  nonlocal length
  dx,dz=b[0]-a[0],b[1]-a[1];l=math.hypot(dx,dz);nx,nz=-dz/l*t/2,dx/l*t/2
  ps=[pt(a[0]+nx,a[1]+nz,width),pt(b[0]+nx,b[1]+nz,width),pt(b[0]-nx,b[1]-nz,width),pt(a[0]-nx,a[1]-nz,width)]
  sh.append(Part.Face(Part.makePolygon(ps+[ps[0]])).extrude(V(0,width,0)));length+=l
  segs.append({'line':[a,b],'width':width,'length':l})
 def arc(cx,cz,rad,a,b,width):
  nonlocal length
  def p(rr,deg):return pt(cx+rr*math.cos(math.radians(deg)),cz+rr*math.sin(math.radians(deg)),width)
  ro,ri=rad+t/2,rad-t/2
  es=[Part.Arc(p(ro,a),p(ro,(a+b)/2),p(ro,b)).toShape(),Part.makeLine(p(ro,b),p(ri,b)),Part.Arc(p(ri,b),p(ri,(a+b)/2),p(ri,a)).toShape(),Part.makeLine(p(ri,a),p(ro,a))]
  sh.append(Part.Face(Part.Wire(es)).extrude(V(0,width,0)))
  l=rad*abs(math.radians(b-a));length+=l;segs.append({'arc_center':[cx,cz],'radius':rad,'angles':[a,b],'width':width,'length':l})
 edge=29.;tx=2.2;top=10.04;run=1.75;ret=3.35;tip=8.352
 prefix=edge-tx+math.pi*r+(top-r-(run+r));neck=.5
 nx=tx+neck;rise=.35;theta=math.acos(1-rise/(2*r));dx=2*r*math.sin(theta)
 ramp_end=12.2;ramp_start=ramp_end+dx
 # Uniform 6.6 mm ribbon; a separate 2 mm root flare joins the island.
 constant=prefix+neck-nx+math.pi*r-ramp_start+2*r*theta+ramp_end-tip
 turn=(70.0-constant)/2
 line((edge,top),(tx,top),6.6);arc(tx,top-r,r,90,180,6.6)
 line((tx-r,top-r),(tx-r,run+r),6.6);arc(tx,run+r,r,180,270,6.6)
 line((tx,run),(nx,run),6.6);line((nx,run),(turn,run),6.6)
 arc(turn,run+r,r,270,450,6.6);line((turn,ret),(ramp_start,ret),6.6)
 arc(ramp_start,ret+r,r,270,270-math.degrees(theta),6.6)
 arc(ramp_end,3.7-r,r,90-math.degrees(theta),90,6.6)
 line((ramp_end,3.7),(tip,3.7),6.6)
 assert abs(length-70.0)<1e-7,length
 return Part.makeCompound(sh),{'centerline_length_mm':length,'body_thickness_assumed_mm':t,'bend_radius_assumed_mm':r,'ribbon_width_mm':6.6,'root_flare_length_mm':2.0,'tip_case_mm':[tip,y,3.7],'return_z_mm':ret,'segments':segs,'note':'No in-plane shear. Actual FPC contour, allowable bend radius, contact thickness and insertion depth still require supplier/sample confirmation.'}

