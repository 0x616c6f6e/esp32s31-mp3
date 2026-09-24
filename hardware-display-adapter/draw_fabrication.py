from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor,black
R=Path(__file__).resolve().parent;O=R/'am213-fpc-adapter/output';F=O/'fabricator-review'
c=canvas.Canvas(str(F/'AM213-A-fabrication-drawing.pdf'),pagesize=landscape(A4));c.setTitle('AM213 A - FPC fabricator review drawing')
W,H=landscape(A4)
def txt(x,y,s,size=9,bold=False):c.setFillColor(black);c.setFont('Helvetica-Bold' if bold else 'Helvetica',size);c.drawString(x*mm,y*mm,s)
txt(15,195,'AM213 A / FLEX ADAPTER',18,True);txt(15,187,'Fabricator review / first prototype - NOT an approved flex stack',10)
txt(205,195,'2026-09-23 | units: mm',9);txt(205,188,'TOP / component & contact face',9)
scale=2.6;X=lambda x:(25+(x+70)*scale)*mm;Y=lambda y:(167-y*scale)*mm
def rect(x,y,w,h,color,stroke=1):c.setFillColor(HexColor(color));c.rect(X(x),Y(y+h),w*scale*mm,h*scale*mm,stroke=stroke,fill=1)
outline=[(0,0),(17,0),(17,22),(0,22),(0,16.7005),(-2,15.7005),(-70,15.7005),(-70,9.1005),(-2,9.1005),(0,8.1005)]
p=c.beginPath();p.moveTo(X(outline[0][0]),Y(outline[0][1]))
for x,y in outline[1:]:p.lineTo(X(x),Y(y))
p.close();c.setFillColor(HexColor('#fff1d6'));c.setStrokeColor(black);c.setLineWidth(.7);c.drawPath(p,stroke=1,fill=1)
rect(-70,9.1005,3.5,6.6,'#d9e5ee');rect(0,0,17,22,'#dae9db')
for i in range(1,22):rect(-69.7,15.4005-(i-1)*.3-.1,2.2,.2,'#bf8c28',0)
rect(3-1.295,12-3.66,2.59,7.32,'#6f7681')
c.setFillColor(HexColor('#c33c33'));c.circle(X(1.65),Y(9.6),.6*mm,fill=1,stroke=0)
txt(222,126,'J2 (3,12)',8,True)
txt(80,131,'6.60 wide flex ribbon / no vias in free span',9)
txt(16,111,'J1 pin 1: lower finger',8);txt(16,106,'21P / 0.30 pitch / F.Cu',8)
txt(208,102,'1 upper-left; 24 upper-right',8);txt(208,97,'12 lower-left; 13 lower-right',8)
def dim(x1,x2,y,label):
 c.setStrokeColor(black);c.setLineWidth(.4);yy=Y(y);c.line(X(x1),yy,X(x2),yy)
 for x in [x1,x2]:c.line(X(x),yy-2*mm,X(x),yy+2*mm)
 c.setFont('Helvetica',9);c.drawCentredString((X(x1)+X(x2))/2,yy+1.2*mm,label)
dim(-70,0,-3,'70.00 tail to island edge');dim(0,17,-3,'17.00');dim(-70,-66.5,18.3,'3.50 min stiffener')
c.line(X(19),Y(0),X(19),Y(22));c.line(X(18),Y(0),X(20),Y(0));c.line(X(18),Y(22),X(20),Y(22));txt(260,137,'22.00',8)
txt(15,89,'BACK-SIDE STIFFENERS (colored overlays; copper shown from top)',10,True)
txt(15,82,'Blue: tip, x=-70 to -66.5; finished tip 0.20 +/-0.03; contact surface F.Cu.',9)
txt(15,76,'Green: component island, x=0..17, y=0..22; flex + FR4 stiffener + adhesive <=0.60.',9)
txt(15,70,'Flex body target 0.12; bending model R0.8. Fabricator must approve actual laminate and static bend.',9)
txt(15,59,'FAB REQUIREMENTS',10,True)
for i,line in enumerate([
 '2 copper layers; minimum trace/space 0.10/0.10; nominal signal trace 0.12; supply stripe 0.44.',
 '39 PTH: pad 0.40 / drill 0.20; 3 GND PTH: pad 0.30 / drill 0.15; min annular ring 0.075.',
 'Min drill-to-other-copper 0.175; copper-to-edge 0.15. No blind/buried vias.',
 'Review pad-adjacent / via-in-pad solder loss; agree plugging/covering process before production.',
 'Confirm coverlay windows, connector finger drawing, plating and edge tolerances with AFE03 datasheet.',
 'Root uses chamfered flare. Return any proposed fillet/teardrop changes for electrical/mechanical review.',
 'Gerber + drill origin: island upper-left (KiCad 50,50). Do not clip negative-X ribbon.',
 'See FABRICATION.md and BOM; R10/R11 DNP. Electrical ERC/DRC pass does not establish physical fit.'
]):txt(15,52-i*5.1,line,8.5)
txt(234,8,'Sheet 1 / 1',8);c.save();print(F/'AM213-A-fabrication-drawing.pdf')
