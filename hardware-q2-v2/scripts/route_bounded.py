"""Local headless legacy router, bounded per connection, checkpoints every 25 attempts.
No GUI/network; KiCad native DRC remains authoritative after importing SES.
"""
from pathlib import Path
import sys,time,json,math
P=Path(__file__).resolve().parents[1];R=P.parent;sys.path.insert(0,str(R/'tmp/v2-kicad-deps'))
import jpype as j
j.startJVM(str(R/'tmp/routing/jre/jdk-25.0.4.1+1-jre/bin/server/jvm.dll'),'-Xmx4g','-Djava.awt.headless=true','--enable-native-access=ALL-UNNAMED',classpath=[str(R/'tmp/routing/freerouting-1.9.0.jar')])
C=j.JClass;loc=C('java.util.Locale').ENGLISH
h=C('app.freerouting.interactive.BoardHandlingHeadless')(loc,False,.01)
stream=C('java.io.FileInputStream')(str(P/'output/routing.dsn'))
result=C('app.freerouting.designforms.specctra.DsnFile').read(stream,h,C('app.freerouting.board.BoardObserverAdaptor')(),C('app.freerouting.board.ItemIdNoGenerator')(),C('app.freerouting.board.TestLevel').RELEASE_VERSION);stream.close();print('LOAD',result,flush=True)
b=h.get_routing_board();settings=h.get_settings();aset=settings.autoroute_settings
for layer in [1,4]:aset.set_layer_active(layer,False)
stop=j.JProxy('app.freerouting.datastructures.Stoppable',dict(request_stop=lambda:None,is_stop_requested=lambda:False))
TimeLimit=C('app.freerouting.datastructures.TimeLimit');Control=C('app.freerouting.autoroute.AutorouteControl');Plane=C('app.freerouting.board.ConductionArea');Tree=C('java.util.TreeSet')
pins=list(b.get_pins());print('PINS',len(pins),flush=True)
def name(pin):return str(b.rules.nets.get(pin.get_net_no(0)).name) if pin.net_count() else ''
def rank(pin):
 n=name(pin)
 return (0 if n.startswith(('RF_','XTAL','MCU_XTAL')) else 1 if n.startswith(('FLASH_','MCU_FLASH')) else 2 if n.startswith(('LCD_','SD_')) else 3 if n=='GND' else 4, pin.get_center().to_float().x)
def count():
 total=0
 for i in range(1,b.rules.nets.max_net_no()+1):
  if str(b.rules.nets.get(i).name)!='GND':total+=max(0,len(b.get_connected_sets(i))-1)
 return total
def save(label):
 b.finish_autoroute();out=C('java.io.FileOutputStream')(str(P/'output/routed-bounded.ses'));ok=C('app.freerouting.designforms.specctra.SpecctraSesFileWriter').write(b,out,'q2-v2');out.close();print('SAVED',label,'gaps',count(),'ok',ok,flush=True)
print('INITIAL GAPS',count(),flush=True)
for passno,ms in enumerate([300,1000,1500],1):
 attempted=0;success=0;start=time.time();fail=[]
 for pin in sorted(pins,key=rank,reverse=passno%2==0):
  if not pin.net_count() or name(pin)=='GND':continue
  net=pin.get_net_no(0);conn=pin.get_connected_set(net);dest=pin.get_unconnected_set(net)
  if not dest or (b.rules.nets.get(net).contains_plane() and any(isinstance(a,Plane) for a in conn)):continue
  attempted+=1;n=name(pin)
  try:
   ctrl=Control(b,net,settings,aset.get_plane_via_costs() if n=='GND' else aset.get_via_costs(),aset.get_trace_cost_arr());ctrl.ripup_allowed=passno>1;ctrl.ripup_costs=200*passno;ctrl.remove_unconnected_vias=False
   eng=b.init_autoroute(net,ctrl.trace_clearance_class_no,stop,TimeLimit(ms),False)
   res=eng.autoroute_connection(conn,dest,ctrl,Tree())
   if str(res) in ['ROUTED','ALREADY_CONNECTED']:success+=1
   else:fail.append(n)
  except Exception as e:print('ERROR',n,str(e),flush=True)
  if attempted%25==0:save(f'pass {passno} try {attempted} success {success} {time.time()-start:.1f}s')
 save(f'pass {passno} done {attempted} success {success} {time.time()-start:.1f}s')
 (P/f'output/bounded-pass-{passno}.json').write_text(json.dumps({'pass':passno,'attempted':attempted,'success':success,'remaining':count(),'failed_nets':sorted(set(fail))},indent=2))
 if count()==0:break
j.shutdownJVM()
