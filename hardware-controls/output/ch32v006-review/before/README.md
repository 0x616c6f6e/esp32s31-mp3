# 滑环与按键小板 B：I²C 四键＋独立 POWER

## 当前生产版本：2026-09-22，无测试点

已同步移除原理图和 PCB 中 TP1～TP11，清理 70 段分支走线及 5 个冗余过孔。当前为 31 个封装对象（26 个装配元件、1 个触摸电极、4 个安装孔）、442 段走线、52 个过孔。其余封装位置、接口针序和功能网络保持不变；ERC、DRC、未连接项和原理图一致性问题均为 0。

最新生产包：[controls-jlcpcb-20260922-no-tp-gerbers.zip](output/controls-jlcpcb-20260922-no-tp-gerbers.zip)。双层 FR-4、44 × 34 mm、0.8 mm 板厚，52 个 Ø0.30 mm 镀铜过孔、4 个 Ø1.80 mm 非金属化安装孔。请使用此包，旧带测试点版仅保留作历史记录。最新 BOM 为 [controls-jlcpcb-20260922-bom.csv](output/controls-jlcpcb-20260922-bom.csv)，10 类、单板 26 个元件，LCSC 料号尚待匹配。

检查报告、前后对比图及修改前备份位于 [output/remove-testpoints](output/remove-testpoints/README.md)。旧 STEP / FreeCAD 装配未重新导出。

## 2026-09-22 GND 铺铜优化

当前 `controls.kicad_pcb` 已增加双面 GND 铺铜，GND 走线从 99 段减至 75 段（减少约 26.59 mm），保留 12 个必要的 GND 过孔。E1 触摸电极及其背面设置禁铺铜区，轮廓外扩约 0.8 mm；三路 WHEEL/SENSE 走线按铜边再外扩约 0.5 mm 避让。这些是本版设计余量，触摸灵敏度仍需结合覆盖层实测调参。

铺铜间距 0.20 mm、最小铜宽 0.25 mm、热焊盘间隙/辐条宽 0.20 mm，移除孤立铜岛。所有封装定义、元件位置、原理图、信号走线和板框均保持不变。KiCad 10.0.4 原生重铺铜后的 DRC 为 0 违规、0 未连接、0 原理图一致性问题。

此次铺铜阶段报告、前后对比图及备份位于 [output/ground-plane-review](output/ground-plane-review/README.md)。对应的 `controls-jlcpcb-20260922-gerbers.zip` 带有测试点，已被上面的无测试点版替代。下文旧 `fabrication/`、Gerber ZIP 以及历史 STEP 和 validation/fit 报告均为历史版本。

打开 **controls.kicad_pro**。这是独立工程，已按用户完成布局的 `hardware-q2-layout` 主板设计 FFC 对接，主板文件未修改；原理图与 PCB 的符号路径和网络已对应。配套装配为 `mechanical/Q2_Controls_Assembly.FCStd`。

## 电路与布局

- 44 × 34 × 0.8 mm、R10、双层板；沿用 F 版外壳的四个 Ø1.8 安装孔和五个按键中心。
- 正面 E1 为三个相互插值的电容触摸电极，外径 31 mm、内径 15 mm，留出四个开关窗口。电极覆盖阻焊，无锡膏；不使用旧机械模型里的十二个示意扇区。
- U1：AT42QT2120-MMHR，3.3 V，I²C 地址 0x1C。三路 10 kΩ 采样串阻、22 Ω 电源滤波、100 nF / 1 µF 去耦；SDA/SCL 各 4.7 kΩ 上拉，共享 INT_N / RESET_N 各 10 kΩ 上拉。
- U2：TCA6408ARGTR，RGT VQFN-16，3 × 3 mm，0.5 mm 脚距，最大高 1 mm。ADDR 接地，7 位地址 0x20；VCCI、VCCP 共用 +3V3，各有 100 nF 去耦。散热焊盘接地。封装焊盘和本地包络模型依据 TI RGT0016A 图。
- 五个 ALPS SKSWCEE010，3 × 2 mm、标称高 0.6 ±0.05 mm、1.8 N、行程 0.13 mm。BACK / PREV / NEXT / PLAY 分别接 U2 P0 / P1 / P2 / P3，R9…R12 各 47 kΩ 上拉，按下为低；只通过 I²C 向外部主机报告这四键。
- POWER 独立引出：SW1.1 → J1.11，R14 = 10 kΩ 上拉至小板 +3V3；上电后松开为高、按下接地为低。不接 U1/U2，按下时上拉支路电流约 0.33 mA。高电平依赖小板供电，本版未实现整机开关机；若需要关机唤醒，须在主板设计中确认上拉电源为常供电域。
- U2 未用的 P4…P7 共接 UNUSED_INPUTS，由 R13 = 10 kΩ 下拉，避免上电浮空。这四脚必须一直配置为输入；不要用作输出或连接外设。
- U1 CHANGE 和 U2 INT 均为开漏输出，共接 INT_N；RESET_N 也由两芯片共用。主控轮询仅需 SDA/SCL，有中断通知时合计 3 个 IO；RESET_N 是可选调试/恢复信号，不接时由上拉保持高。
- 芯片及无源件在背面、避开电池和马达占位。新增 U2 与无源件布置在电池下方区域，正面五键及板框不变。J1 改为与主板 FPC1 相同的 HC-FPC-05-10-12RLTAG，12 芯、0.5 mm 间距、下接点，适配 0.30 ±0.03 mm 端部厚度。KiCad 坐标 (8.130, 9.411) mm、B.Cu、−90°；它不是屏幕接口。
- 已完成新主板 FPC1 与小板 J1 的针序对照和 40 mm 成品 FFC 名义装配路线；详见 [FFC 对接与采购说明](mechanical/FFC-INTERCONNECT.md)。整机开关机逻辑与实物连接尚未验证。

## J1 引脚

按 **焊盘编号** 接线，不能根据排线同面／反面的外观直接推断另一端编号。

| 引脚 | 信号 | 用途 |
|---|---|---|
| 1 | GND | 地 |
| 2 | +3V3 | 稳压 3.3 V 输入 |
| 3 | SDA | I²C 数据 |
| 4 | SCL | I²C 时钟 |
| 5 | INT_N | 滑环＋四键共享低有效开漏中断 |
| 6 | RESET_N | 两芯片共享低有效复位；可不接 |
| 7…10 | NC | 不连接；不再引出四个普通按键 |
| 11 | KEY_POWER | 独立电源键，10 kΩ 上拉；按下为低 |
| 12 | GND | 地 |
| 13、14 | GND | 金属固定脚，不计入 12 芯排线 |

TP1～TP11 已移除。调试电源、I²C、中断、复位和 POWER 可从 J1 对应引脚测量，四个机械键输入可从 U2 或开关焊盘测量。

## 独立上电与调试

1. 用限流的稳压 3.3 V 给 J1.2/J1.1 供电。不得输入电池原始电压。主机逻辑电平也使用 3.3 V。
2. 先以 100 kHz I²C 访问 7 位地址 0x1C，读寄存器 0x00，预期芯片 ID 为 0x3E。
3. 寄存器 0x0E 写 0xC0，启用 KEY0…KEY2 的环形模式；KEY0…KEY2 的控制寄存器保持触摸输入配置。
4. 未使用的 KEY3…KEY11 不应浮空扫描：对应十进制地址 31…39 的控制寄存器写 0x01，配置为输出低电平，焊盘不接外部网络。配置后按数据手册执行重新校准，并等待校准完成。
5. 读取检测状态和滑环位置，检查一整圈的连续性、零点回绕、方向及按压时的误触。阈值、脉冲数、积分、低功耗周期须结合成品覆盖层实测设定；本项目没有凭空填入“已验证”的灵敏度参数。
6. 初始化 U2，访问 7 位地址 0x20：先向输出寄存器 0x01 写 0x00（设安全的输出锁存值，不改变方向），向极性寄存器 0x02 写 0x00，向方向寄存器 0x03 写 0xFF，保持所有端口为输入。读回 0x02 / 0x03 核对配置。不要把共接的 P4…P7 配成输出。
7. 读取 U2 输入寄存器 0x00。正常未按时低四位为 0x0F，高四位为 0；`pressed = (~input) & 0x0F`。bit0=BACK，bit1=PREV，bit2=NEXT，bit3=PLAY，可识别同时按下。建议每 5 ms 采样并连续稳定 20 ms 后确认变化；长按/连击由主控处理。
8. INT_N 触发时，分别读取 U1 的状态字节和 U2 的输入寄存器，清除两边的中断来源；只读取其中一颗可能让中断一直为低。初始化后主动读一次两颗芯片，正常服务中应持续处理到 INT_N 释放，并设置有界重试、周期补读及总线错误恢复，不能仅等待下一个下降沿。即使中断已释放，也继续定时采样直到机械键消抖完成；U2 不会为静止的按键反复触发中断。
9. 小板上电后测试 POWER：J1.11 松开时约 3.3 V，按下时约 0 V；确认不影响 U2 低四位。R14 已提供上拉，主机端按 3.3 V 逻辑输入读取并进行消抖。未来接入整机电源管理时确认其电源域和关机唤醒要求。

若测试主机已有 I²C 上拉，应计算并联后的总阻值，必要时不装 R4/R5。RESET_N 未连接时由 R7 保持高电平；外部拉低至少 10 ms 并释放后须重新初始化两颗 IC，等待触摸校准完成。J1 输入电源应与主机 I²C 电平同步，不能在小板断电时持续用信号线反向供电。小板掉电重启后也必须重新初始化。

## 外壳适配

`mechanical/` 单独保存适配版本，没有覆盖 F 版外壳源文件。

- 保持整机外观、按键中心、板框和安装高度。小板下表面 Z=11.1、上表面 Z=11.9 mm。
- 修正原键帽的内部压柱、限位环和壳体内部环槽；旧键帽直接套用会在开关触发前碰到 PCB。
- 新压柱底面 Z=12.65 mm。考虑开关高度公差，静态间隙为 0.10…0.20 mm；名义触发行程 0.28 mm，按高度下限计算为 0.33 mm。
- `fit-check.json` 检查小板和 26 个元件、电池／移位后的马达／新主板已建模元件与外壳的名义实体相交（不包含未重布的电池和马达线束），检查 0.33 mm 轴向下压，以及四个方向的约 ±0.727° 倾斜加 0.165 mm 下移姿态。U2 包络使用最大 1 mm 高度；其他尺寸仍为名义尺寸。这些姿态只证明有可用运动空间，不等同于受力、回弹、摇摆手感或寿命验证，需打印实物确认。
- 电池仍为 24 × 34 × 3 mm 占位，板底到电池名义间隙仅 0.3 mm；实际电池厚度、膨胀余量及绝缘层需要重新核对，不能据此选用更厚电池。
- 滑环上方存在约 1.05 mm 空气间隙及 0.6 mm 键帽。键帽使用非导电塑料，不做导电镀层。空气间隙与按压运动会影响触摸，需要整机调试；本版是待验证的原型设计。

FreeCAD 文件包含可重算的内部圆柱、切除与融合特征；`HousingControlsA`、`WheelControlsA`、`CenterButtonControlsA` 分别提供 STEP / STL，后盖增加局部内部 FFC 避让槽并导出 `RearCoverWithPCBPosts.step/.stl`，外表面保持不变。马达中心从壳体 (39, 57) 移到 (39, 62) mm，电池不变；U1 向壳体 +X 平移 0.6 mm 以避让新主板耳机座。新主板 1.6 mm 厚；2026-09-22 完整复查确认最终主板四个安装孔与原固定柱对齐；同时发现马达/耳机座及 C13/屏幕排线干涉，不能将旧的局部通过报告视为整机装配通过。最新装配与报告见 `../mechanical/final-board-review/`。打开装配默认显示外观，可展开 `ControlsPCB`、`References` 查看内部。

## 文件与检查

- `controls.kicad_sch` / `controls.kicad_pcb`：实际独立小板设计；本地 `Controls.pretty`、`Controls.kicad_sym`、`models3d` 随工程携带。
- `output/bom.csv`：26 个装配元件的型号与数据手册。
- `output/erc.json`、`output/drc.json`、`output/validation.json`：最终原生 KiCad 检查与保存文件的校验摘要。
- `fabrication/`：双面 Gerber、钢网层及分开的 PTH / NPTH 钻孔；`output/controls-B-prototype-gerbers.zip` 为 B 版原型打样包。制造参数见包内说明。
- `output/schematic.png` / `output/schematic/controls.svg`：可直接查看的原理图。
- `output/controls-populated.step`：小板 STEP；FreeCAD 检查将 KiCad 导出的介质厚度扩展为 0.8 mm 成品板包络。
- `mechanical/fit-check.json`：名义装配与轴向行程检查，包含源文件校验值。

本版尚未经过实物焊接、触摸调参、ESD、按键寿命或整机验证。DRC/ERC 与名义几何通过只证明相应的设计规则和包络检查通过。

## 设计依据与重建

原厂资料保存在 `reference/`，来源：[Microchip AT42QT2120](https://ww1.microchip.com/downloads/en/devicedoc/doc9634.pdf)、[Microchip QTAN0079](https://ww1.microchip.com/downloads/aemDocuments/documents/OTH/ApplicationNotes/ApplicationNotes/doc10752.pdf)、[ALPS SKSW](https://tech.alpsalpine.com/cms.media/product_catalog_ta_02_sksw_en_ee3e98d509.pdf)、[Hirose FH19C](https://www.hirose.com/en/product/p/CL0580-0413-0-10)。电极窗口和形状是本项目的实现，并非厂家验证过的参考 PCB。

B 版新增 [TI TCA6408A 数据手册](https://www.ti.com/lit/ds/symlink/tca6408a.pdf)：§5 核对 RGT 引脚；§8.3.3 开漏中断；§8.6 寄存器/0x20 地址；RGT0016A 图核对 3 × 3 mm / EP 1.45 × 1.45 mm 封装。A 版机械零件内部名称 `HousingControlsA` 等保留，保留历史名称；本次新增后盖内部排线避让，不改变外观和按键中心。

`make_electrodes.py` 需要 Python + Shapely；`build_design.py`、`finalize_board.py`、`validate.py` 使用 KiCad 10 的 Python/pcbnew；`build_models.py`、`build_fit.py` 使用 FreeCAD 1.1。生成脚本是本版设计记录，不应在手工修改后直接重跑覆盖。`build_design.py` 只生成初始原理图和摆放，会拒绝覆盖已有走线的板，不会重建最终布线。最终布线直接保存在 PCB；对应交换记录及说明在 `reference/routing/`。原生 KiCad DRC、连通性和原理图一致性是交付检查依据。

本次连接器依据 [HCTL HC-FPC-05-10 原厂图纸](https://atta.szlcsc.com/upload/public/pdf/source/20221027/B2DE489DA152049D1F105170189CFB4E.pdf)，本地副本为 `reference/HCTL-HC-FPC-05-10.pdf`。旧 Hirose 资料仅保留为历史参考，不能按其 0.2 mm 排线规格采购新 J1 的排线。
