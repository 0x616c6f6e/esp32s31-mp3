"""Generate linked, editable functional sheets from the explicit V2 net contract.
Labels are global across sheets. ERC and exported netlist are checked separately.
"""
from pathlib import Path
import sys,json,uuid,math,re
P=Path(__file__).resolve().parents[1];ROOT=P.parent
sys.path.insert(0,str(ROOT/'hardware-q2-v2-plan/scripts'));from sexpr import parse,dump,children,get,prop,S
data=json.loads((P/'output/design-contract.json').read_text(encoding='utf8'));components=data['components']
uid=lambda s:str(uuid.uuid5(uuid.UUID('cc5bc37c-570c-4cf3-a1df-87f9ea47032e'),s));q=lambda s:json.dumps(str(s),ensure_ascii=False)
rootid=uid('root');defs={};pageids={};instances={};pinlocations={}
def define(c):
 ref=c['ref'];numbers=sorted(c['pins'],key=lambda s:(0,int(s)) if s.isdigit() else (1,s))
 ispassive=len(numbers)==2 and ref[0] in 'RCL'; half=math.ceil(len(numbers)/2);h=max(2.54,(half+1)*1.27);w=2.54 if ispassive else 17.78
 if ref=='U9':w=27.94
 if ispassive:
  pins=[(numbers[0],-5.08,0,0),(numbers[1],5.08,0,180)]
  if ref[0]=='C':body=''.join(f'(polyline (pts (xy {x} -2.54) (xy {x} 2.54)) (stroke (width .254) (type default)) (fill (type none)))' for x in [-.508,.508])
  elif ref[0]=='L':body='(polyline (pts (xy -2.54 0) (xy -1.27 1.27) (xy 0 -1.27) (xy 1.27 1.27) (xy 2.54 0)) (stroke (width .254) (type default)) (fill (type none)))'
  else:body='(rectangle (start -2.54 1.016) (end 2.54 -1.016) (stroke (width .254) (type default)) (fill (type none)))'
 else:
  body=f'(rectangle (start {-w} {h}) (end {w} {-h}) (stroke (width .254) (type default)) (fill (type background)))'
  pins=[]
  for i,num in enumerate(numbers):
   side=-1 if i<half else 1;j=i if i<half else i-half
   pins.append((num,side*(w+2.54),h-2.54-j*2.54,0 if side<0 else 180))
 props=''.join(f'(property {q(k)} {q(v)} (at 0 {yy} 0) (effects (font (size 1.27 1.27)){hide}))' for k,v,yy,hide in [('Reference',ref,h+5.08,''),('Value',c['value'],h+2.54,''),('Footprint','V2:'+c['footprint'],0,' hide'),('Datasheet','',0,' hide')])
 pp=''
 allowed={'input','output','bidirectional','tri_state','passive','free','unspecified','power_in','power_out','open_collector','open_emitter','no_connect'}
 for num,x,y,angle in pins:
  meta=c['pins'][num];typ=meta['type'];typ={'bidi':'bidirectional','power_in':'power_in'}.get(typ,typ)
  if typ not in allowed:typ='passive'
  # Imported EasyEDA passives/connectors have incorrect input/output pin types.
  if re.match(r'^(R|C|L|D|X|Y|CN|USB|CARD|FPC|J|TP|SCREW)\d',ref) or ref=='JDISP1':typ='passive'
  if ref=='U9':
   if num in ['35','39']:typ='power_out'
   elif num in ['1','18','63','78','79']:typ='passive'
  if ref=='U3' and num=='16':typ='passive' # Same SYS output as pin 15, internally common.
  name='' if ispassive else meta['name']
  pp+=f'(pin {typ} line (at {x} {y} {angle}) (length {4.572 if ispassive and ref[0]=="C" else 2.54}) (name {q(name)} (effects (font (size .9 .9)))) (number {q(num)} (effects (font (size .9 .9)))))'
 name='SYM_'+ref;defs[ref]=f'(symbol "V2:{name}" (pin_names (offset .4)) (in_bom yes) (on_board yes) {props} (symbol "{name}_0_1" {body}) (symbol "{name}_1_1" {pp}))'
 pinlocations[ref]=(pins,h)
for c in components.values():define(c)
groups={}
for c in components.values():groups.setdefault('MCU_CORE' if c['ref']=='U9' else re.sub(r'[^A-Za-z0-9_-]','_',c['group']),[]).append(c)
pages=[]
for group,cs in sorted(groups.items(),key=lambda z:(z[0]!='MCU_CORE',z[0])):
 cs.sort(key=lambda c:(-len(c['pins']),c['ref']))
 # Conservative row heights allow large imported ICs to remain legible.
 cells=[];xcol=0;y=35;rowheight=0;chunk=1
 for c in cs:
  h=pinlocations[c['ref']][1];height=max(30,2*h+22)
  if xcol==3:y+=rowheight;xcol=0;rowheight=0
  if y+height>270 and cells:
   pages.append((group+f'_{chunk}',cells));chunk+=1;cells=[];y=35;xcol=0;rowheight=0
  xx=115 if c['ref']=='U9' else 65+xcol*130
  cells.append((c,xx,y+h+8));xcol+=1;rowheight=max(rowheight,height)
 if cells:pages.append((group+f'_{chunk}',cells))
rootitems=[]
for index,(name,cells) in enumerate(pages):
 pageid=uid('sheet-'+name);fileid=uid('file-'+name);pageids[name]=pageid
 rootitems.append(f'(sheet (at {25+(index%3)*125} {35+(index//3)*30}) (size 110 20) (stroke (width .254) (type default)) (fill (color 0 0 0 0)) (uuid "{pageid}") (property "Sheetname" {q(name)} (at {25+(index%3)*125} {33+(index//3)*30} 0) (effects (font (size 1.27 1.27)) (justify left bottom))) (property "Sheetfile" {q(name+".kicad_sch")} (at {25+(index%3)*125} {56+(index//3)*30} 0) (effects (font (size 1.27 1.27)) (justify left top))) (instances (project "q2-v2" (path "/{rootid}" (page "{index+2}")))))')
 items=[];used=[]
 for c,x,y in cells:
  x=round(round(x/1.27)*1.27,4);y=round(round(y/1.27)*1.27,4)
  ref=c['ref'];used.append(ref);sid=c['uuid'];pins,h=pinlocations[ref];instances[ref]='/'+rootid+'/'+pageid+'/'+sid
  props=''.join(f'(property {q(k)} {q(v)} (at {x} {yy} 0) (effects (font (size {sz} {sz})){hide}))' for k,v,yy,sz,hide in [('Reference',ref,y-h-5.08,1.27,''),('Value',c['value'],y-h-2.54,.9,''),('Footprint','V2:'+c['footprint'],y,1.27,' hide'),('Datasheet','',y,1.27,' hide')])
  items.append(f'(symbol (lib_id "V2:SYM_{ref}") (at {x} {y} 0) (unit 1) (in_bom {"no" if ref.startswith("TP") else "yes"}) (on_board yes) (dnp {"yes" if c["dnp"] else "no"}) (uuid "{sid}") {props} '+''.join(f'(pin {q(n)} (uuid "{uid(ref+"-pin-"+n)}"))' for n,px,py,a in pins)+f'(instances (project "q2-v2" (path "/{rootid}/{pageid}" (reference {q(ref)}) (unit 1)))))')
  for num,px,py,ang in pins:
   ax,ay=round(x+px,6),round(y-py,6);n=c['nets'].get(num,'')
   if not n:
    items.append(f'(no_connect (at {ax} {ay}) (uuid "{uid(ref+num+"nc")}"))');continue
   ex=round(ax+(-5.08 if px<0 else 5.08),6)
   items.append(f'(wire (pts (xy {ax} {ay}) (xy {ex} {ay})) (stroke (width 0) (type default)) (uuid "{uid(ref+num+"wire")}"))')
   # Global label orientation points toward the symbol and extends away.
   la=0 if px<0 else 180;just='right' if px<0 else 'left'
   items.append(f'(global_label {q(n)} (shape bidirectional) (at {ex} {ay} {la}) (effects (font (size .85 .85)) (justify {just})) (uuid "{uid(ref+num+"label")}") (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {ex} {ay} {la}) (effects (font (size 1.27 1.27)) hide)))')
  # Keep the exact target symbol sheet name in the PCB for cross-probing.
  c['sheet']=name;c['path']=instances[ref]
 title=f'Q2 V2 / {name} / electrical candidate'
 text=f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{fileid}") (paper "A3") (title_block (title {q(title)}) (rev "V2-A") (date "2026-09-24")) (lib_symbols '+''.join(defs[r] for r in used)+')'+''.join(items)+')\n'
 (P/(name+'.kicad_sch')).write_text(text,encoding='utf8')
flagdef='(symbol "V2:SUPPLY_SOURCE" (power) (pin_names (offset 0)) (in_bom no) (on_board no) (property "Reference" "#FLG" (at 0 0 0) (effects (font (size 1.27 1.27)) hide)) (property "Value" "PWR_FLAG" (at 0 2.54 0) (effects (font (size 1.27 1.27)))) (symbol "SUPPLY_SOURCE_0_1" (polyline (pts (xy 0 0) (xy -1.27 1.27) (xy 0 2.54) (xy 1.27 1.27) (xy 0 0)) (stroke (width .254) (type default)) (fill (type none)))) (symbol "SUPPLY_SOURCE_1_1" (pin power_out line (at 0 0 90) (length 0) (name "pwr" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))))'
for i,n in enumerate(['GND','VBAT','VBUS_5V','VCC_3V3','MCU_VDDA34','N_5N15']):
 x=25.4+i*60.96;y=254;ref='#FLG'+str(101+i)
 rootitems.append(f'(symbol (lib_id "V2:SUPPLY_SOURCE") (at {x} {y} 0) (unit 1) (in_bom no) (on_board no) (dnp no) (uuid "{uid(ref)}") (property "Reference" "{ref}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide)) (property "Value" "PWR_FLAG" (at {x} {y-4} 0) (effects (font (size 1.27 1.27)))) (pin "1" (uuid "{uid(ref+"pin")}")) (instances (project "q2-v2" (path "/{rootid}" (reference "{ref}") (unit 1)))))')
 rootitems.append(f'(global_label {q(n)} (shape bidirectional) (at {x} {y} 0) (effects (font (size .85 .85)) (justify right)) (uuid "{uid(ref+"label")}") (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide)))')
root=f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{rootid}") (paper "A3") (title_block (title "Q2 V2 ESP32-S31NRV16 mainboard") (rev "V2-A") (date "2026-09-24")) (lib_symbols {flagdef}) '+''.join(rootitems)+')\n'
(P/'q2-v2.kicad_sch').write_text(root,encoding='utf8')
(P/'V2.kicad_sym').write_text('(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor") '+''.join(s.replace('(symbol "V2:','(symbol "',1) for s in list(defs.values())+[flagdef])+')',encoding='utf8')
(P/'sym-lib-table').write_text('(sym_lib_table (lib (name "V2") (type "KiCad") (uri "${KIPRJMOD}/V2.kicad_sym") (options "") (descr "Explicit V2 pin contracts")))')
# Relink every footprint to its real hierarchical symbol instance.
board=parse((P/'q2-v2.kicad_pcb').read_text(encoding='utf8'))
for f in children(board,'footprint'):
 c=components[prop(f,'Reference')[2]]
 for key in ['path','sheetname','sheetfile']:
  f[:]=[a for a in f if not(isinstance(a,list) and a and a[0]==key)]
 f += [['path',S(c['path'])],['sheetname',S(c['sheet'])],['sheetfile',S(c['sheet']+'.kicad_sch')]]
(P/'q2-v2.kicad_pcb').write_text(dump(board),encoding='utf8')
(P/'output/design-contract.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
print('Generated',len(pages),'functional sheets;',len(components),'linked components')
