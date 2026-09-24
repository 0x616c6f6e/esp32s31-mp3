# 滑环与按键小板 C：CH32V006

采用 **CH32V006F8U6** 替换 AT42QT2120-MMHR 和 TCA6408A，由一颗 MCU 处理三电极滑环、四个机械按键，并作为 I²C 从机向主板报告。POWER 保持独立、10 kΩ 上拉、按下接地。

这是需要配套固件和实物调参的新硬件版本，不能直接沿用旧 AT42 的驱动或生产文件。

KiCad 10.0.4 检查结果：ERC 0、DRC 0、未连接项 0、原理图一致性问题 0。板上共有 439 段走线和 62 个过孔。双面 GND 铺铜避开触摸电极及其背面（外扩约 0.8 mm），并避开三路采样走线（铜边外扩约 0.5 mm）；这些余量仍需实物验证。

新版文件：[Gerber 生产包](output/controls-ch32v006-jlcpcb-20260922-101316-gerbers.zip)、[BOM](output/controls-ch32v006-bom.csv)、[装配 STEP](output/controls-ch32v006.step)、[背面预览](output/ch32v006-review/back.png)。BOM 由当前原理图导出，共 10 类、23 个装配元件，尚未匹配嘉立创 SMT 料号。

## 工程与机械接口

- KiCad 工程：`controls.kicad_pro`，原理图、PCB、本地符号库、封装库与模型一起使用。
- 双层 FR-4，板厚 0.8 mm，44 × 34 mm，原 R10 板框。
- 五个按键、四个安装孔、三电极滑环 E1、FPC J1 的位置与方向保持原样。
- 电极仍为三组插值电极，外径 31 mm、内径 15 mm；不改变前面板外观。
- 新 MCU 及阻容位于背面。J2 为四个裸焊盘，不安装插针，不增加连接器高度。
- 已添加名义尺寸的 CH32V006 QFN20 STEP 模型。本版 23 个元件已导入 [I 版装配优化工程](../mechanical/enclosure-final-i/README.md)，最新工程为 `mechanical/enclosure-final-i/Q2_I_Serviceable_Assembly.FCStd`。小板采用三颗 M1.6 × 2 mm（头下长度）薄头螺钉、三片 0.3 mm 平垫及右侧限位台；右上原固定柱封闭不装螺钉，避开 FFC。G/H 复合实体检查曾漏报该处干涉，使用 I 版检查和打印文件。

J1：1 GND、2 +3V3、3 SDA、4 SCL、5 INT_N、6 RESET_N、7～10 NC、11 KEY_POWER、12 GND；固定焊盘 13、14 接地。供电与信号电平为 3.3 V。

## 采购与装配变化

| 位号 | C 版器件/数值 | 数量 | 说明 |
|---|---|---:|---|
| U1 | CH32V006F8U6 | 1 | QFN20，3×3 mm，0.4 mm 脚距，EP 1.9×1.9 mm |
| J1 | HC-FPC-05-10-12RLTAG | 1 | 原 12 pin、0.5 mm FPC 连接器 |
| SW1～SW5 | SKSWCEE010 | 5 | 原机械开关 |
| R1～R3 | 1 kΩ，0402 | 3 | 触摸采样串阻，需实物调参 |
| R4、R5 | 4.7 kΩ，0402 | 2 | I²C 上拉 |
| R6、R7、R14 | 10 kΩ，0402 | 3 | INT、RESET、POWER 上拉 |
| R8 | 0 Ω，0402 | 1 | MCU 电源连接，不能装旧 22 Ω |
| R9～R12 | 47 kΩ，0402 | 4 | 四个普通键的 GPIO 上拉 |
| C1、C3 | 100 nF，0402，X7R，≥10 V | 2 | MCU 去耦、复位 RC |
| C2 | 1 µF，0402，X5R/X7R，≥10 V | 1 | MCU 电源去耦 |

单板 23 个采购/装配元件。J2、E1、H1～H4 为 PCB 自带焊盘、电极及安装孔，不采购。U2、R13、C4 已移除；C3 现在用于复位，不能按旧版位置和功能装配。型号后缀及封装必须核对，TSSOP20 的 CH32V006F8P6 不能替代此 QFN20 焊盘。

## 固件

见 [CH32V006-interface.md](CH32V006-interface.md)：完整引脚分配、SDI 下载、PD7 硬件复位配置，以及拟定的 I²C 寄存器协议。地址暂定 0x1C，寄存器与 AT42QT2120 不兼容。本次没有交付可烧录固件；官方 TouchKey 示例也不能原样烧录到此板。

打样后要在最终盖板下标定三路触摸基线、阈值、零位、转动方向与跨零连续性，并验证充电/音频干扰、按键消抖、待机电流、复位和再次下载能力。

## 检查与历史文件

本次备份、原生 ERC/DRC 报告、机械接口比较和预览位于 `output/ch32v006-review/`，以其中的 final 报告和 `validation.json` 为准。历史生成脚本可能仍包含 B 版芯片和旧镜像坐标，不要直接运行旧 `build_design.py` 或 `build_fit.py` 覆盖当前工程。

2026-09-22 10:13:16 批次已从用户调整走线后的 C 版导出 Gerber 生产包（源 PCB 保存时间为 10:13:08），包含九个图层、独立 PTH/NPTH 钻孔、Gerber Job 和加工说明。下单参数：双层 FR-4、44 × 34 mm、板厚 0.8 mm、外层铜厚 1 oz。62 个 Ø0.30 mm 镀铜过孔及四个 Ø1.80 mm 非金属化安装孔已与 PCB 核对；顶面触摸电极保留阻焊覆盖。导出前原生 DRC、未连接项和原理图一致性问题均为 0；文件校验和及检查记录见 `output/ch32v006-gerber-review-20260922-101316/manifest.json`。

**旧 `controls-jlcpcb-20260922-no-tp-gerbers.zip`、旧 BOM、`fabrication/` 和历史 STEP 是 AT42/TCA 版本，全部不适用于 C 版。** 旧 README 与原始工程在 `output/ch32v006-review/before/` 保留。
