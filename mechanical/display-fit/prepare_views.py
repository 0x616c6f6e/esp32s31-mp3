from pathlib import Path
import FreeCAD as App, FreeCADGui as Gui, json
from PySide import QtCore
HERE=Path(__file__).resolve().parent;OUT=HERE/'exports'
def settle():
    loop=QtCore.QEventLoop();QtCore.QTimer.singleShot(450,loop.quit);loop.exec_()
def op(path):
    d=next((d for d in App.listDocuments().values() if d.FileName==str(path).replace('\\','/')),None)
    return d or App.openDocument(str(path))
flat=op(HERE/'LCD209_dimensioned.FCStd')
for o in flat.Objects:
    if hasattr(o,'ViewObject'):o.ViewObject.Visibility=False
colors=json.loads((OUT/'display-model-colors.json').read_text(encoding='utf8'))
for name,col in colors.items():
    o=flat.getObject(name);o.ViewObject.Visibility=True;o.ViewObject.ShapeColor=tuple(col);o.ViewObject.DisplayMode='Shaded'
App.setActiveDocument(flat.Name);Gui.activeDocument().activeView().viewAxonometric();settle();Gui.activeDocument().activeView().fitAll();settle()
Gui.activeDocument().activeView().saveImage(str(OUT/'lcd-native-isometric.png'),900,1100,'White')
flat.save()
doc=op(HERE/'LCD_FPC2_fit_audit.FCStd');App.setActiveDocument(doc.Name)
colors=json.loads((OUT/'audit-colors.json').read_text(encoding='utf8'))
for o in doc.Objects:
    if hasattr(o,'Shape'):
        o.ViewObject.ShapeColor=tuple(float(v) for v in colors.get(o.Name,[.5,.5,.5]));o.ViewObject.DisplayMode='Shaded';o.ViewObject.Visibility=True
doc.ProposedFPC2_Yplus3p866.ViewObject.Visibility=False
doc.InstalledLCD.ViewObject.Transparency=80
doc.CurrentMainPCB.ViewObject.Transparency=75
doc.ActualSolderPadCenters.ViewObject.Visibility=False
v=Gui.activeDocument().activeView()
z=App.Vector(-1,1,-1.2);x=App.Vector(0,0,1).cross(z);y=z.cross(x)
v.setCameraOrientation(App.Rotation(x,y,z,'ZXY').Q);settle();v.fitAll();settle()
v.saveImage(str(OUT/'current-fit-rear-isometric.png'),1100,1000,'White')
doc.save()
print('VIEWS_SAVED')
