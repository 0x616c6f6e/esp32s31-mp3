from pathlib import Path
from PySide6 import QtWidgets,QtSvg,QtGui,QtCore
P=Path(__file__).resolve().parents[1]/'output'
app=QtWidgets.QApplication([])
font_id=QtGui.QFontDatabase.addApplicationFont('C:/Windows/Fonts/arial.ttf')
overview=QtGui.QImage(1840,1567,QtGui.QImage.Format_ARGB32)
overview.fill(QtGui.QColor('#f5f6f8'))
op=QtGui.QPainter(overview);op.setPen(QtGui.QColor('#202630'))
font=QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(font_id)[0]);font.setPixelSize(27);op.setFont(font)
for i,side in enumerate(['front','back']):
 r=QtSvg.QSvgRenderer(str(P/(side+'-review.svg')))
 im=QtGui.QImage(900,1487,QtGui.QImage.Format_ARGB32);im.fill(QtCore.Qt.white)
 pa=QtGui.QPainter(im);r.render(pa);pa.end();im.save(str(P/(side+'-review.png')))
 op.drawImage(20+i*920,60,im);op.drawText(20+i*920,38,'Q2 V2 / '+side.upper())
op.end();overview.save(str(P/'pcb-overview.png'))
