"""Generate a reviewable pin proposal. Does not change schematic/PCB nets."""
from pathlib import Path
import json,csv,hashlib,re
from sexpr import parse,children,prop,get
P=Path(__file__).resolve().parents[1];R=P.parent
layout=json.loads((P/'placement.json').read_text(encoding='utf8'));fps={a['ref']:a for a in layout['components']}
names=('ANT VDDA3 VDDA4 CHIP_PU XTAL_32K_N/GPIO0 XTAL_32K_P/GPIO1 GPIO2 GPIO3 GPIO4 GPIO5 VDDPST_1 GPIO6 GPIO7 GPIO8 GPIO9 GPIO10 GPIO11 VREF_TOUCH GPIO12 GPIO13 GPIO14 GPIO15 GPIO16 GPIO17 GPIO18 GPIO19 SDIO_DATA0 SDIO_DATA1 SDIO_DATA2 VDD_PSRAM_1P8_1 SDIO_DATA3 SDIO_CLK SDIO_CMD VDD_PSRAM_1P8_2 VDD_LDO_1P8 SPICS SPIQ SPIWP VDD_SPI SPIHD SPICLK SPID VCCA/VDDPST_2 USB_DP USB_DM GPIO33 GPIO34 GPIO35 GPIO36 GPIO37 GPIO38 GPIO39 GPIO40 VDDPST_3 GPIO42 GPIO43 GPIO44 GPIO45 GPIO46 GPIO47 GPIO48 GPIO49 VREF_ADC VDDPST_4 GPIO50 GPIO51 GPIO52 GPIO53 MTDO MTCK MTDI MTMS GPIO58 GPIO59 GPIO60 GPIO61 VDDA1 XTAL_N XTAL_P VDDA2 GND').split()
assert len(names)==81
gpio_to_pin={0:5,1:6,**{i:i+5 for i in range(2,6)},6:12,7:13,8:14,9:15,10:16,11:17,**{i:i+7 for i in range(12,19)},19:26,20:27,21:28,22:29,23:31,24:32,25:33,26:36,27:37,28:38,30:40,31:41,32:42,33:46,34:47,35:48,36:49,37:50,38:51,39:52,40:53,**{i:i+13 for i in range(42,48)},48:61,49:62,50:65,51:66,52:67,53:68,54:69,55:70,56:71,57:72,58:73,59:74,60:75,61:76}
assert len(gpio_to_pin)==60 and len(set(gpio_to_pin.values()))==60
rows={i:dict(pin=i,pin_name=n,gpio=next((g for g,p in gpio_to_pin.items() if p==i),None),group='未分配',signal='',old_net='',direction='',target='',reset_requirement='',notes='') for i,n in enumerate(names,1)}
def assign(g,group,signal,old,direction,target,reset,notes=''):
 r=rows[gpio_to_pin[g]];assert r['group']=='未分配'
 r.update(group=group,signal=signal,old_net=old,direction=direction,target=target,reset_requirement=reset,notes=notes)
def fixed(pin,group,signal,target,reset,notes=''):
 r=rows[pin];assert r['group']=='未分配';r.update(group=group,signal=signal,target=target,reset_requirement=reset,notes=notes,direction='专用')

# LP GPIOs remain available for wake inputs; GPIO0 here is not an ESP32-S31 boot strap.
for g,s,old,target in [(0,'KEY_POWER_SENSE_N','ESP_IO42','FPC1.11 / U6.1，经3.3V隔离检测'),(1,'CTRL_INT_N','ESP_IO43','FPC1.5'),(2,'RTC_INT_N','ESP_IO34','U1.6'),(3,'IMU_INT1','ESP_IO1','U15.4'),(4,'BAT_ALERT_N','ESP_IO35','U14.1'),(5,'CHG_INT_N','BQ25895_INT','U3.7')]:
 assign(g,'唤醒/中断',s,old,'输入',target,'输入；上拉仅接3.3V；GPIO3极性由IMU配置','LP GPIO；唤醒需要固件配置。KEY必须隔离GEK供电域；不得原样直连。' if g==0 else 'LP GPIO；可按需要配置唤醒，保持供电时才有效。')
assign(6,'系统LP I2C','SYS_I2C_SCL','BQ25895_I2C_CLK','开漏双向','U3.5 U14.3 U1.2 U11.2 FPC1.4','外部上拉3.3V','LP I2C，F2；100kHz起步；不是I2C_NUM_2')
assign(7,'系统LP I2C','SYS_I2C_SDA','BQ25895_I2C_SDA','开漏双向','U3.6 U14.2 U1.3 U11.3 FPC1.3','外部上拉3.3V','LP I2C，F2；LP核访问须与主核通过命令/共享内存协调')
for g,s,old,di,t,reset,note in [
 (9,'POWER_OFF_REQ','GEK100_RST','输出','U6.3，经断电防反灌电路','外部下拉；上电低','新增软件关机请求；高有效，需保证掉电后复位脉冲时长'),
 (10,'CTRL_RESET_N','ESP_IO44','开漏输出','FPC1.6','释放，由小板RC上拉','CH32V006 PD7配置硬件复位后才生效'),
 (11,'USB_PATH_SEL','ESP_IO33','输出','U17.2','外部电阻固定默认路径','避开GPIO33复位USB功能；0/1对应哪路须核对U17真值表'),
 (12,'MOTOR_EN','ESP_IO40','输出','U11.5','外部下拉；默认关闭','保留现有R44下拉；PWM/触发使用需按马达驱动配置'),
 (13,'CHG_OTG_EN','BQ25895_OTG_EN','输出','U3.8','外部下拉；默认关闭','保留R12下拉；不得上电即打开OTG'),
 (19,'SD_CARD_DETECT_N','ESP_IO19','输入','CARD2.CD','新增/核对3.3V上拉','检测触点极性以实物卡座导通确认')]:
 assign(g,'系统控制',s,old,di,t,reset,note)
for g,s,old,t in [(14,'AUDIO_I2C_SCL','DAC_I2C_SCL','U7.6 U15.13'),(15,'AUDIO_I2C_SDA','DAC_I2C_SDA','U7.5 U15.14')]:
 assign(g,'音频HP I2C0',s,old,'开漏双向',t,'保留3.3V侧上拉','HP I2C0经GPIO Matrix；U7后为1.8V DAC总线')
for g,s,old,t in [(20,'SD_D0','ESP_TF_DAT0','CARD2.7'),(21,'SD_D1','ESP_TF_DAT1','CARD2.8'),(22,'SD_D2','ESP_TF_DAT2','CARD2.1'),(23,'SD_D3','ESP_TF_DAT3','CARD2.2'),(24,'SD_CLK','ESP_TF_CLK','CARD2.5'),(25,'SD_CMD','ESP_TF_CMD','CARD2.3')]:
 assign(g,'SDMMC',s,old,'输出' if g==24 else '双向',t,'CMD/D0-D3上拉3.3V；CLK不随意加上拉','原生SDIO F0；本板卡接口先用3.3V，不直接改1.8V模式')
for g,s,old,t in [(26,'FLASH_CS_N','ESP_FLASH_CS','U10.1'),(27,'FLASH_D1','ESP_FLASH_DO','U10.2'),(28,'FLASH_D2','ESP_FLASH_WP','U10.3'),(30,'FLASH_D3','ESP_FLASH_HOLD','U10.7'),(31,'FLASH_CLK','ESP_FLASH_CLK','U10.6'),(32,'FLASH_D0','ESP_FLASH_DI','U10.5')]:
 assign(g,'启动Flash',s,old,'输出' if g in [26,31] else '双向',t,'按启动Flash参考电路','固定MSPI引脚；不分给应用GPIO；U10容量待选，建议与原模组16MB目标一致')
fixed(44,'USB HS','USB_HS_DP','U17.7','专用差分','旧网ESP_USB_DP；不是GPIO44')
fixed(45,'USB HS','USB_HS_DM','U17.6','专用差分','旧网ESP_USB_DN；不是GPIO45')
assign(33,'调试预留','USB_DEBUG_DM','','专用差分','新增调试焊盘/连接器','保留USB Serial/JTAG功能','不再接USB切换SEL；与HS USB不是同一对线，不可并接')
assign(34,'调试预留','USB_DEBUG_DP','','专用差分','新增调试焊盘/连接器','保留USB Serial/JTAG功能','不再接RTC中断；量产无调试连接器时可不装引出件')
for g,s,old,t in [(35,'DAC_I2S_DOUT','DAC_I2S_SDIN','U8.2'),(38,'DAC_I2S_LRCK','DAC_I2S_LRCK','U8.5'),(39,'DAC_RESET_N','DAC_RST#','U8.12'),(40,'DAC_I2S_BCLK','DAC_I2S_SCLK','U8.9')]:
 assign(g,'音频I2S',s,old,'输出',t,'RESET默认低；时钟初始化前静止','GPIO Matrix；保留U8到1.8V域转换；DOUT是ESP输出，旧网SDIN按DAC视角命名')
for g,s,old,t in [(42,'TP_I2C_SCL','ESP_I2C2_SCL','JDISP1.20'),(43,'TP_I2C_SDA','ESP_I2C2_SDA','JDISP1.19')]:
 assign(g,'触屏HP I2C1',s,old,'开漏双向',t,'3.3V上拉，屏幕断电时防反灌','HP I2C1；与系统/音频总线隔离，无需假定触控IC地址')
for g,s,old,di,t,reset in [(44,'LCD_RESET_N','ESP_IO47','输出','JDISP1.1','默认低；电源稳定后释放'),(45,'LCD_VCI_EN','ESP_IO46','输出','JDISP1.24','默认低；按屏幕电源时序使能'),(46,'LCD_TE','AM213_TE_RESERVED','输入','JDISP1.3','输入，禁止驱动屏幕TE'),(47,'TP_INT_N','ESP_IO54','输入','JDISP1.17','按触控规格配置中断/上拉'),(48,'TP_RESET_N','ESP_IO57','输出','JDISP1.18','默认低；按触控规格释放')]:
 assign(g,'屏幕控制',s,old,di,t,reset,'3.3V沿用本项目屏幕方案；供电域和上下电次序仍须验证')
for g,s,old,t,native in [(52,'LCD_CS_N','ESP_SPI2_CS','JDISP1.4','SPI2_CS'),(53,'LCD_CLK','ESP_SPI2_CLK','JDISP1.5','SPI2_CK'),(54,'LCD_D0','ESP_SPI2_D0','JDISP1.7','SPI2_D'),(55,'LCD_D1','ESP_SPI2_D1','JDISP1.6','SPI2_Q'),(56,'LCD_D3','ESP_SPI2_D3','JDISP1.22','SPI2_HOLD'),(57,'LCD_D2','ESP_SPI2_D2','JDISP1.23','SPI2_WP')]:
 assign(g,'屏幕QSPI',s,old,'输出/总线',t,'CS上拉、CLK低；解除传统JTAG复用',f'手册F2={native}；SPI2_HOST；SDK IOMUX路径待验证，先按GPIO Matrix <=40MHz调试')
assign(58,'下载UART0','UART0_TX','CH343P_UART_RX','输出','U12.5 RXD','UART0默认输出','ESP TX接CH343 RX，勿按旧网络后缀反接')
assign(59,'下载UART0','UART0_RX','CH343P_UART_TX','输入','U12.4 TXD','UART0输入','ESP RX接CH343 TX')
for g,s,old,reset,note in [(36,'STRAP_FLASH_3V3','','10k候选上拉3.3V','默认eFuse下高选择3.3V；不得悬空/接外部中断'),(37,'STRAP_USB_JTAG','','10k候选上拉3.3V','无内部上下拉；当JTAG_SEL_ENABLE启用时高选USB JTAG；不为此烧eFuse'),(60,'BOOT_MODE_H','ESP_BOOT2','10k候选上拉3.3V','下载时必须高；不复用普通外设'),(61,'BOOT_DOWNLOAD_N','ESP_BOOT1','10k候选上拉3.3V','正常高；下载时拉低，同时GPIO60高；通过下载控制电路')]:
 assign(g,'启动配置',s,old,'启动采样','启动上拉/下载电路',reset,note)
fixed(4,'复位','CHIP_PU','RC及CH343下载控制电路','10k上拉/RC按参考设计','旧网ESP32S31_EN；必须核对自动下载握手，不能误当普通GPIO')
rows[4]['old_net']='ESP32S31_EN';rows[44]['old_net']='ESP_USB_DP';rows[45]['old_net']='ESP_USB_DN'
fixed(1,'射频','ANT','RF匹配/天线','按RF参考设计','专用射频端口')
for pin in [2,3,11,43,54,64,77,80]:
 if rows[pin]['group']=='未分配':fixed(pin,'电源','3V3_'+names[pin-1],'3.3V域，局部滤波/去耦','按每个电源脚放去耦','VDDA模拟电源滤波不可省略')
for pin in [30,34]:fixed(pin,'电源',names[pin-1],'VDD_LDO_1P8，按参考电路','1.8V PSRAM供电','不是3.3V输入')
fixed(35,'电源','VDD_LDO_1P8','PSRAM 1.8V供电和去耦','芯片电源输出','不能接外部3.3V')
fixed(39,'电源','VDD_SPI','外接Flash供电/去耦','按3.3V Flash参考电路','结合GPIO36配置；不是任意与外部电源并接')
fixed(78,'晶振','XTAL_N','40MHz晶振/匹配','专用时钟','按乐鑫参考设计，不能随意加长/过孔')
fixed(79,'晶振','XTAL_P','40MHz晶振/匹配','专用时钟','需要参考设计指定的串联电感/负载网络')
fixed(81,'地','GND_EP','连续GND/散热过孔','可靠接地','封装中央裸露焊盘，不是GPIO81')
for pin in [18,63]:fixed(pin,'模拟预留','NC_'+names[pin-1],'本方案不用触摸/ADC则按手册处理','不作为GPIO','后续启用相关功能须补参考电容')
for r in rows.values():
 if r['group']=='未分配':r.update(group='空闲GPIO',signal=f"SPARE_GPIO{r['gpio']}",direction='预留',reset_requirement='不接外设，固件避免悬空',notes='供后续扩展；不得替代电源/USB专用脚')
 # Documentation pad centers based on nominal terminal length 0.4mm. Not a land pattern.
 n=r['pin']
 if n<=20:x,y=-3.8,-3.325+(n-1)*.35
 elif n<=40:x,y=-3.325+(n-21)*.35,3.8
 elif n<=60:x,y=3.8,3.325-(n-41)*.35
 elif n<=80:x,y=3.325-(n-61)*.35,-3.8
 else:x,y=0,0
 r['board_local_nominal_terminal_xy']=[round(30-y,3),round(17+x,3)]
 r['board_side_at_minus90']='上' if n<=20 else '左' if n<=40 else '下' if n<=60 else '右' if n<=80 else '中央'
plan=list(rows.values())
assert all(r['signal'] for r in plan)
assert len({r['signal'] for r in plan})==81
assert all(rows[gpio_to_pin[g]]['group']=='启动配置' for g in [36,37,60,61])
assert [rows[gpio_to_pin[g]]['signal'] for g in [52,53,54,55,56,57]]==['LCD_CS_N','LCD_CLK','LCD_D0','LCD_D1','LCD_D3','LCD_D2']
used_nets={a['old_net'] for a in plan if a['old_net']}
source_path=R/'hardware-q2/ProPrj_esp32s31-mp4_2026-09-22.kicad_pcb'
source=parse(source_path.read_text(encoding='utf8'));old_u9=next(f for f in children(source,'footprint') if prop(f,'Reference')[2]=='U9')
old_nets={get(a,'net')[1] for a in children(old_u9,'pad') if get(a,'net') and get(a,'net')[1] not in ['', 'GND','VCC_3V3']}
excluded={'ESP_IO4':'旧板无外围连接，改作电池告警','ESP_IO5':'旧板无外围连接，改作充电中断','ESP_IO45':'旧TFT背光控制删除；新GPIO45用于AMOLED使能'}
assert old_nets-used_nets==set(excluded),(old_nets-used_nets)
audit={'status':'PIN_PROPOSAL_CONSISTENT_NOT_WIRED_OR_FIRMWARE_VALIDATED','physical_pins':81,'gpio_count':60,'spare_gpios':[r['gpio'] for r in plan if r['group']=='空闲GPIO'],'duplicate_gpio_assignments':0,'old_mcu_nets_accounted_for':True,'removed_or_unused_legacy_nets':excluded,'bus_resources':{'HP_I2C0':[14,15],'HP_I2C1':[42,43],'LP_I2C':[6,7],'SPI2':[52,53,54,55,56,57]},'no_board_or_schematic_net_changes':True,'pcb_sha256':hashlib.sha256((P/'q2-v2-placement.kicad_pcb').read_bytes()).hexdigest()}
audit['source_mainboard_sha256']=hashlib.sha256(source_path.read_bytes()).hexdigest()
pad_nets={}
for board in [source,parse((P/'q2-v2-placement.kicad_pcb').read_text(encoding='utf8'))]:
 for footprint in children(board,'footprint'):
  ref=prop(footprint,'Reference')[2]
  for pad in children(footprint,'pad'):
   net=get(pad,'net');pad_nets[(ref,pad[1])]=net[1] if net else ''
target_checks=[]
for r in plan:
 if not r['old_net']:continue
 for ref,pad in re.findall(r'\b([A-Z]+\d+)\.([A-Z]*\d*|CD)\b',r['target']):
  actual=pad_nets.get((ref,pad),'MISSING')
  assert actual==r['old_net'],(ref,pad,r['old_net'],actual)
  target_checks.append({'reference':ref,'pad':pad,'old_net':actual})
audit['existing_target_pad_checks']=len(target_checks)
audit['existing_target_pad_mismatches']=0
(P/'pin-assignment.json').write_text(json.dumps({'status':audit['status'],'chip_candidate':'ESP32-S31NRV16','source':'esp32-s31_datasheet_en.pdf v0.5','rows':plan,'validation':audit},ensure_ascii=False,indent=2),encoding='utf8')
cols=['pin','pin_name','gpio','group','signal','old_net','direction','target','reset_requirement','notes','board_side_at_minus90']
with (P/'pin-assignment.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(plan)
header=['/* Q2 V2 pin PROPOSAL only. Not an initialized or board-tested BSP. */','#pragma once','/* Numbers ending GPIO are GPIO indices, not QFN physical pin numbers. */']
for a in plan:
 if a['gpio'] is not None and a['group'] not in ['启动Flash','启动配置','调试预留','空闲GPIO']:
  header.extend([f"/* QFN pin {a['pin']}; {a['target']} */",f"#define Q2_{a['signal']}_GPIO {a['gpio']}"])
header+=['/* LP I2C is NOT a third HP I2C controller. Initialize through LP APIs. */','#define Q2_SYS_I2C_INITIAL_HZ 100000','#define Q2_AUDIO_I2C_HP_PORT 0','#define Q2_TP_I2C_HP_PORT 1','#define Q2_LCD_SPI_INITIAL_HZ 20000000','/* Native USB HS uses dedicated QFN pins 44/45, never GPIO44/45. */']
(P/'q2_v2_pin_plan.h').write_text('\n'.join(header)+'\n',encoding='utf8')
table=['# 第二版引脚分配完整表','', '候选方案：ESP32-S31NRV16；KiCad −90°。GPIO编号与QFN物理脚号分别列出。尚未写入原理图/PCB。','', '| 物理脚 | 芯片脚名 | GPIO | 功能分组 | 建议网络名 | 旧网络 | 目标 |','|---:|---|---:|---|---|---|---|']
for a in plan:table.append('| '+' | '.join(str(a[k]) if a[k] is not None else '—' for k in ['pin','pin_name','gpio','group','signal','old_net','target'])+' |')
(P/'pin-assignment-all-pins.md').write_text('\n'.join(table)+'\n',encoding='utf8')
print(json.dumps(audit,ensure_ascii=False,indent=2))
