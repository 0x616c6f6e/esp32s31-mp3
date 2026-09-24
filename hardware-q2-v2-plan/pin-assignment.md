# Q2第二版引脚规划 A · 2026-09-24

按当前裸芯片候选位置 `(30,17) mm / −90° / 正面` 分配，优先固定高速接口、启动配置和唤醒，再安排低速控制。对象为ESP32-S31NRV16，参考本地手册v0.5。**这是原理图设计输入，尚未把这些新GPIO写入原理图或PCB；旧板网络名不能代表新GPIO号。**

## 推荐分配

下表GPIO栏是软件GPIO编号。完整81脚表另列QFN物理脚号、电源、启动电平、旧网络、目标器件和连接注意事项。

| 功能 | GPIO分配 | QFN物理脚 |
|---|---|---|
| 启动Flash CS/D1/D2/D3/CLK/D0 | 26 / 27 / 28 / 30 / 31 / 32 | 36 / 37 / 38 / 40 / 41 / 42 |
| TF D0/D1/D2/D3/CLK/CMD | 20 / 21 / 22 / 23 / 24 / 25 | 27 / 28 / 29 / 31 / 32 / 33 |
| TF卡检测 | 19 | 26 |
| 屏幕CS/CLK/D0/D1/D2/D3 | **52 / 53 / 54 / 55 / 57 / 56** | 67 / 68 / 69 / 70 / 72 / 71 |
| 屏幕RST_N / VCI_EN / TE | 44 / 45 / 46 | 57 / 58 / 59 |
| 触屏SCL / SDA / INT_N / RST_N | 42 / 43 / 47 / 48 | 55 / 56 / 60 / 61 |
| 音频BCLK / LRCK / ESP_DOUT / RST_N | **40 / 38 / 35 / 39** | 53 / 51 / 48 / 52 |
| DAC＋IMU I²C：SCL/SDA | 14 / 15 | 21 / 22 |
| 系统LP I²C：SCL/SDA | **6 / 7** | 12 / 13 |
| POWER独立检测 / 按键板INT_N / RTC_INT_N | **0 / 1 / 2** | 5 / 6 / 7 |
| IMU_INT1 / 电量计ALERT_N / 充电INT_N | 3 / 4 / 5 | 8 / 9 / 10 |
| 按键板RESET_N | 10 | 16 |
| USB切换SEL / 马达EN / OTG_EN | 11 / 12 / 13 | 17 / 19 / 20 |
| 软件关机请求 | 9 | 15 |
| UART0 TX / RX | 58 / 59 | 73 / 74 |
| USB Serial/JTAG D− / D+预留 | 33 / 34 | 46 / 47 |
| USB HS D+ / D− | **专用脚，不是GPIO44/45** | **44 / 45** |

另有GPIO8、16、17、18、49、50、51共 **7个普通GPIO空闲**。GPIO36、37、60、61专门留给启动配置，不计入可随意使用的空闲脚。GPIO29、GPIO41没有对应的封装GPIO引出，不能按连续序号补进去。

## 为什么这样分配

- Flash和TF使用固定接口，分别从芯片左下和左侧出线。U10在芯片左下；保留物理焊盘对应关系，但正式启动Flash容量仍待选，原W25Q16JV只有2 MB。
- 屏幕QSPI使用手册第24页的SPI2 F2功能组，位于旋转后芯片右侧。**D2是GPIO57、D3是GPIO56，不能按数字递增接反。** GPIO54–57同时是传统JTAG脚，本方案将它们用于屏幕。
- I²S从芯片底部输出，朝下方U8/DAC；保持四路1.8 V电平转换。`DAC_I2S_SDIN`是以DAC为视角命名的旧网，新名称为`DAC_I2S_DOUT`，方向是ESP输出。DAC保留本地X1时钟，本方案不新增MCU MCLK。
- POWER、按键INT、RTC中断分配到LP GPIO0–2。ESP32-S31的GPIO0不是本芯片BOOT脚；它与GPIO1在本方案中也不再接外部32.768 kHz晶振。低功耗唤醒仍要配置固件，并保持相应电源域供电；整机断电时依赖GEK硬件开机，不依赖ESP GPIO唤醒。
- 主板原GPIO33接USB切换、GPIO34接RTC中断，会占用芯片默认USB Serial/JTAG功能。这版迁出两项功能，保留这对调试信号。

## 三组I²C的实现选择

| 总线资源 | SCL / SDA | 现有网络和器件 | 初始速率建议 |
|---|---|---|---|
| HP I²C0 | GPIO14 / 15 | DAC_I2C：U7→DAC，U15 IMU | 100 kHz，验证后400 kHz |
| HP I²C1 | GPIO42 / 43 | 原ESP_I2C2：屏幕触控 | 100 kHz，按屏幕触控规格调整 |
| **LP I²C** | GPIO6 / 7 | 原BQ25895_I2C：充电U3、电量计U14、RTCU1、马达U11、CH32按键板FPC1 | **100 kHz** |

芯片有2路HP I²C和1路LP I²C，**不能在普通I²C驱动里创建虚构的`I2C_NUM_2`来使用第三路**。系统总线需要LP驱动/LP核程序，主CPU通过请求队列或共享内存协调，不能两个核同时驱动同一总线。GPIO6/7也不能同时用于LP UART。

这样保留了原三组网络，不需要先假设屏幕触控的I²C地址，也不需要把不同总线的上拉直接并接。CH32小板规划地址0x1C，协议尚须固件实现；系统其他器件地址仍以实际型号核对。上拉总值、并联上拉及总线电容需在原理图阶段检查。

若后续决定不编写LP核固件，可在确认屏幕触控地址、电平、供电和上拉后，把触屏并入系统HP总线，以2路HP实现；**那是另一版总线拓扑，不是这份分配表的既成连接。**

## 屏幕接口对照

| BTB脚 | 信号 | MCU GPIO |
|---:|---|---:|
| 1 | LCD_RESET_N | 44 |
| 3 | TE | 46 |
| 4 | CS_N | 52 |
| 5 | CLK | 53 |
| 6 | D1 | 55 |
| 7 | D0 | 54 |
| 17 | TP_INT_N | 47 |
| 18 | TP_RESET_N | 48 |
| 19 | TP_SDA | 43 |
| 20 | TP_SCL | 42 |
| 22 | D3 | 56 |
| 23 | D2 | 57 |
| 24 | VCI_EN | 45 |

2/8/13/14/21及固定焊盘接GND，9/10 NC；11/12/15/16按此前商定的3.3 V方案供电。此表保持BTB电气脚号，连接器90°或270°仍由屏幕排线实物决定，不能靠旋转封装交换信号编号。

手册列出了这组SPI2复用，但当前ESP-IDF S31在线SPI驱动文档的IOMUX表仍显示N/A。因此这里只确认**芯片有此复用候选**，不宣称当前SDK自动走原生IOMUX或可直接跑80 MHz。先用GPIO Matrix、20 MHz起步，40 MHz以内调通；进一步提速必须检查实际SDK引脚路由、显示驱动和示波器时序。[ESP-IDF SPI Master说明](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s31/api-reference/peripherals/spi_master.html)

## 按键FPC保持原针序

FPC1：1=GND，2=3.3V，3=GPIO7/SDA，4=GPIO6/SCL，5=GPIO1/INT_N，6=GPIO10/RESET_N，7–10=NC，11=POWER机械按键信号，12=GND，13/14固定焊盘=GND。POWER继续按下拉低，其他按键和滑环通过CH32＋I²C读取。

**第11脚不能未经电源域处理直接接GPIO0。** 现有U6 GEK100由VCC供电，其KEY内部上拉到自身电源；同时小板R14上拉到小板3.3V。VCC可能高于3.3V，关机时小板3.3V还可能断电。因此原来的共网直连关系需要在第二版加入隔离/合适的常供电与检测电路，避免ESP过压、通过小板上拉回灌或KEY不能释放。GPIO0分配给处理后的`KEY_POWER_SENSE_N`，不是声明原网已经可以安全直连。

GPIO9为新增软件关机请求，目标为GEK的RST（高有效）。上电默认低；关机前先停音频、保存状态/卸载TF，再发请求。GEK厂家说明RST需要持续足够时间，高电平触发；掉电后的保持时间、防反灌和默认下拉需由电路保证。GPIO9不是直接驱动3.3V稳压器的EN。[GEK100厂家手册](https://gsctek.com/uploads/allimg/20251225/1-251225110HM63.pdf)

## 启动、调试和电源约束

| 项目 | 分配与默认状态 |
|---|---|
| GPIO36 / QFN49 | 候选10k上拉3.3V，配合默认eFuse选择3.3V Flash；不接普通外设 |
| GPIO37 / QFN50 | 候选10k上拉3.3V，避免悬空；参与JTAG源选择，不为本设计烧eFuse |
| GPIO60 / QFN75 | 候选10k上拉；下载时必须为高 |
| GPIO61 / QFN76 | BOOT：正常上拉，进入下载时拉低 |
| CHIP_PU / QFN4 | EN/复位RC；与CH343下载控制电路联动 |
| UART0 GPIO58 TX | 接CH343 RXD/U12.5，旧网名CH343P_UART_RX |
| UART0 GPIO59 RX | 接CH343 TXD/U12.4，旧网名CH343P_UART_TX |

GPIO61低且GPIO60低是无效启动组合。自动下载电路要按裸芯片参考电路重新核对，不能仅搬运旧模组焊盘编号。

GPIO33/34保留给USB Serial/JTAG；它们不与当前USB-C上的HS D+/D−并接。若要使用，需后续设计独立调试接点/选路。传统四线JTAG被屏幕占用，UART0作为基础恢复下载路径。

VDD_PSRAM_1P8_1/2（QFN30/34）、VDD_LDO_1P8（35）、VDD_SPI（39）、各VDDA/VDDPST及EP81都已列入完整表；它们不能分配普通GPIO。未启用片内ADC和触摸时，VREF_ADC/VREF_TOUCH按手册处理，不因原理图空白就接3.3V。

## 交付与校验

- `pin-assignment-all-pins.md`：全部81个物理引脚的可读表。
- `pin-assignment.csv`：UTF-8 BOM表格，可导入Excel。
- `pin-assignment.json`：机器可读映射及校验结果。
- `q2_v2_pin_plan.h`：固件引脚常量草案；没有初始化驱动，不表示固件已支持/测试。
- `pin-assignment-overview.png`：−90°顶视分配图；端子位置为说明示意，不是PCB焊盘图。

校验覆盖：81个物理脚、60个GPIO无重复分配；启动脚未被普通功能占用；原U9所有非电源网络都被分配或明确列为删除/空闲；三路I²C控制器资源分别明确。没有修改PCB、原理图和已生产的小板。

资料：本地`esp32-s31_datasheet_en.pdf`第17–26、29–40、68–69页；[ESP-IDF GPIO说明](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s31/api-reference/peripherals/gpio.html)；[LP核及LP I²C接口](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s31/api-reference/system/ulp-lp-core.html)。芯片手册为预发布版本，最终电路和SDK实现还需联调。
