# AM213 屏幕转接板 A — 电气样板

2026-09-23：已完成原理图、双层 FPC PCB、布线、3D 模型及 L 版装配检查副本。按用户选择采用 **3.3 V 供电和直接连接逻辑**，没有修改已生产主板和按键板。

## 当前文件

- 打开工程：[am213-fpc-adapter.kicad_pro](am213-fpc-adapter/am213-fpc-adapter.kicad_pro)。同目录有原理图、PCB 和自带符号、封装、STEP 库。
- 最新装配副本：[Q2_L_AM213_Completed_Adapter.FCStd](am213-fpc-adapter/models3d/Q2_L_AM213_Completed_Adapter.FCStd)。原始 L 外壳没有覆盖。
- [元件面预览](am213-fpc-adapter/output/pcb-top.png)、[折弯预览](am213-fpc-adapter/output/adapter-folded.png)、[装配预览](am213-fpc-adapter/output/adapter-in-enclosure.png)。
- [BOM](am213-fpc-adapter/output/bom.csv)、[接线及坐标](fpc-layout-guide.md)、[制造说明](am213-fpc-adapter/FABRICATION.md)。
- `am213-fpc-adapter/output/AM213-adapter-A-fabricator-review.zip`：Gerber、钻孔与工艺说明，供 **FPC 工厂审核及小批样板**；不是普通刚性 PCB 下单包。

旧 `adapter-outline.kicad_pcb`、`fpc-layout-concept.png`、`Adapter_Placement.pretty` 和机械占位预览仅作历史参考。旧 1.8 V 电平转换方案已被本版取代。

## 电气依据

屏厂 OSPTEK 官方 AM213 参考原理图明确把 11/12 脚 VBAT、15 脚 VDD、16 脚 TP_VDD 接到 3.3 V，QSPI/I²C 直接连接 ESP32。采用该参考，取消早期预留的电平转换电路。

- 官方仓库：https://github.com/osptek/amoled-2.13-410x502-qspi-co5300
- 原理图与实板照片：[PCB-2.13&1.96AMOLED-qspi转接板.pdf](reference/osptek-official/PCB-2.13&1.96AMOLED-qspi转接板.pdf)。第 1 页左侧为 AM213，第 2 页实板照片用于母座针号核对。
- 原厂连接器图：[OK-23GF024-04.pdf](reference/osptek-official/OK-23GF024-04.pdf)，母座第 3 页。
- 下载来源和 blob 标识：`reference/osptek-official/sources.json`。

旧屏幕规格书第 6 页仍有 VBAT 下限 3.4 V、VDDIO 1.8 V 等与参考板不一致的文字。本版选择有屏厂参考电路支持，但没有实屏点亮、最大负载及主板电源余量测试，不等于供应商对所有批次的保证。

## 检查与限制

KiCad 10 原生 ERC **0**、DRC 违规 **0**、未连接 **0**、原理图/PCB 一致性问题 **0**。报告在 `output/erc.json`、`output/drc.json`。工艺下限见制造说明，不能代替板厂 DFM。

FreeCAD 按 R0.8 mm 折弯 70 mm 排线，检查元件岛、补强、元件和母座最大包络。排线及插头补强进入简化实体 `PCB_FPC2` 是预期配合重叠；除此之外未发现体积干涉。屏幕原生尾巴、公母插合公差、锁扣和触点仍需实物试装。

`build_complete_adapter.py` 会覆盖 PCB 布线，不要对手改后的工程直接运行。其余脚本是本次构建和修复记录；当前交付以已保存 KiCad 文件为准。旧机械占位生成器已加覆盖保护。
