"""Pin-specific distances and signal-net MST estimates; not routed lengths."""
import math,collections
import pcbnew as p

PAIRS=[('bootstrap','U3','21','C11'),('charger_SW','U3','19','L2'),
 ('charger_diode','U3','19','D2'),('REGN_bypass','U3','22','C9'),
 ('PMID_bypass','U3','23','C16'),('battery_bypass','U3','13','C10'),
 ('buck_VIN','U4','4','C1'),('buck_FB_top','U4','5','R4'),('buck_FB_bottom','U4','5','R3'),
 ('DAC_VD','U2','4','C28'),('DAC_VL','U2','31','C27'),
 ('DAC_VA','U2','7','C17'),('DAC_VCP','U2','25','C23'),
 ('DAC_FILT_plus','U2','5','C8'),('DAC_FILT_minus','U2','6','C18'),
 ('DAC_XTO','U2','36','X1'),('DAC_XTI','U2','37','X1'),
 ('motor_REG','U11','1','C4'),('motor_output_plus','U11','7','H1'),('motor_output_minus','U11','9','H1'),
 ('battery_shunt','H2','3','R1'),('USB_ESD_DP','USB1','A6','D1'),('USB_ESD_DM','USB1','A7','D1'),
 ('USB_mux_input_DP','U17','3','D1'),('USB_mux_input_DM','U17','4','D1'),
 ('USB_mux_ESP_DP','U17','7','U9'),('USB_mux_ESP_DM','U17','6','U9'),
 ('USB_mux_UART_DP','U17','9','U12'),('USB_mux_UART_DM','U17','8','U12'),
 ('RTC_IRQ','U9','44','U1')]
POWER={'GND','GBAT','VBAT','VCC','VCC_3V3','VCC_1V8','VCC_LCD_BG','LCD_LEDA','LCD_LEDK'}
def xy(pad):return (pad.GetPosition().x/1e6,pad.GetPosition().y/1e6)
def mst(points):
 if not points:return 0
 reached=[points[0]];left=points[1:];value=0
 while left:
  distance,index=min((math.dist(a,v),i) for a in reached for i,v in enumerate(left))
  value+=distance;reached.append(left.pop(index))
 return value
def measure(board):
 fs={f.GetReference():f for f in board.GetFootprints()};pairs={};nets=collections.defaultdict(list)
 for label,ref,pin,target in PAIRS:
  pad=next(a for a in fs[ref].Pads() if a.GetNumber()==pin)
  dist=min(math.dist(xy(pad),xy(a)) for a in fs[target].Pads() if a.GetNetname()==pad.GetNetname())
  pairs[label]={'source':ref+'.'+pin,'target':target,'net':pad.GetNetname(),'mm':round(dist,4),
                'opposite_sides':fs[ref].IsFlipped()!=fs[target].IsFlipped()}
 for f in fs.values():
  for pad in f.Pads():
   net=pad.GetNetname()
   if net and net not in POWER and not net.startswith('unconnected-'):nets[net].append(xy(pad))
 return {'selected_connections':pairs,'signal_net_mst_mm':{n:round(mst(pp),4) for n,pp in nets.items()}}
def compare(before,after):
 a=measure(before);b=measure(after)
 rows=[{'connection':label,'before':a['selected_connections'][label],'after':b['selected_connections'][label],
        'change_mm':round(b['selected_connections'][label]['mm']-a['selected_connections'][label]['mm'],4)} for label in a['selected_connections']]
 return {'definition':'Straight-line pin distances and 2D Euclidean signal-net MST. Excludes listed power rails, GND and explicit NC; includes DNP pads. Not routing, via count, impedance or SI simulation.',
         'excluded_power_nets':sorted(POWER),'selected_connections':rows,
         'signal_mst_total_before_mm':round(sum(a['signal_net_mst_mm'].values()),4),
         'signal_mst_total_after_mm':round(sum(b['signal_net_mst_mm'].values()),4),
         'signal_nets_before_mm':a['signal_net_mst_mm'],'signal_nets_after_mm':b['signal_net_mst_mm']}
if __name__=='__main__':
 import argparse,json
 from pathlib import Path
 cli=argparse.ArgumentParser();cli.add_argument('before');cli.add_argument('after');cli.add_argument('output',type=Path)
 args=cli.parse_args();before=p.LoadBoard(args.before);after=p.LoadBoard(args.after)
 report=compare(before,after);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(report['signal_mst_total_before_mm'],report['signal_mst_total_after_mm'])
 for row in report['selected_connections']:print(row['connection'],row['before']['mm'],'->',row['after']['mm'])
