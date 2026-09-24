# ESP32-S31 MP3 / Q2 风格播放器

当前工程：

- **[V2 裸芯片主板 PCB](hardware-q2-v2/README.md)**：打开 `hardware-q2-v2/q2-v2.kicad_pro`。ESP32-S31NRV16、正面 AM213 BTB、46 × 76 mm 六层板，0201 阻容已改为 0402。当前仅保留电源布线与铺铜，信号待手动布线；几何 DRC、电源未连接及原理图一致性均为 0，174 项信号飞线为有意保留，不能直接投产。[双面预览](hardware-q2-v2/output/pcb-overview.png)。
- [V2 布局及管脚规划依据](hardware-q2-v2-plan/README.md)：保留方案来源；实际已布线管脚以 [V2 当前引脚表](hardware-q2-v2/pin-assignment.md) 为准。

**当前开发外壳为 L 版：适配新的 2.13 英寸 AM213 AMOLED。** 已修改屏幕总成、面壳开孔和固定台，整机仍为50×81.5×15.1 mm。新屏24针BTB不能直接连接已生产主板的21针FPC2，已完成独立双层FPC转接板的3.3 V参考电路和布线；ERC/DRC及原理图一致性检查通过。L版已有完整转接板装配检查副本，仍待FPC工艺审核、实物插合和点亮测试。

- **[最新外壳 L：2.13英寸屏幕适配](mechanical/enclosure-final-l/README.md)**：`Q2_L_AM213_Adapter_Study.FCStd`，直接使用新屏自带触摸盖板，预留17×22 mm转接板空间。[转接板接线规划](hardware-display-adapter/README.md)。

- **[历史外壳 K：旧2.09英寸屏幕](mechanical/enclosure-final-k/README.md)**：`Q2_K_Assembly_Access.FCStd`。已修复J版装入路径与薄壁，但不适用新AM213屏幕；保留作历史参考。

- **[历史外壳 J：后盖胶粘铜螺母版](mechanical/enclosure-final-j/README.md)**：打样复查暂缓，见 [J 版问题记录](mechanical/enclosure-final-j/PREFLIGHT-REVIEW.md)。已由 K 版取代。

- **[历史外壳 I：装配优化版](mechanical/enclosure-final-i/README.md)**：`Q2_I_Serviceable_Assembly.FCStd`。小板采用三颗带限长垫片的螺钉＋侧边限位台，避开 FFC；加厚按键止脱边、增加排线槽与绝缘护边。修正 G/H 版复合实体干涉漏报，使用 I 版完整四件打印包。

- **[历史外壳 H：小板固定加强版](mechanical/enclosure-final-h/README.md)**：`Q2_H_Reinforced_Assembly.FCStd`。加粗四个小板螺柱、加宽根部并增加侧壁加强筋，小板螺钉改为头下长 2 mm 的 M1.6；外形及两板位置沿用 G 版。使用 H 版打印包，G 版保留为历史。

- **[历史外壳 G：薄型树脂装机样件](mechanical/enclosure-final-g/README.md)**：`Q2_G_Thin_Assembly.FCStd`，适配最终主板与 CH32V006 小板，50 × 81.5 × 14.2 mm（含盖板）。CN2/CN3 改为直接焊线装配；修正支柱、马达托座、屏幕排线和按键避让。附四件打印文件。电池成品厚度仍待供方确认，装机约束见说明。

- [最终主板与按键板 FreeCAD 检查](mechanical/final-board-review/README.md)：采用 `hardware-q2/ProPrj_esp32s31-mp4_2026-09-22.kicad_pro` 为最终主板；两板已导入 `Q2_Final_Mainboard_Assembly.FCStd`。四个主板安装孔与原柱对齐，但发现马达/耳机座、C13/屏幕排线干涉，详见检查报告。

- [独立滑环与按键小板 C](hardware-controls/README.md)：打开 `hardware-controls/controls.kicad_pro`；44 × 34 × 0.8 mm，CH32V006F8U6 读取触摸环与四个机械键，通过 I²C 上报，POWER 独立上拉、按下为低；使用 12P / 0.5 mm / 40 mm 异面 FFC。当前整机机械装配见 K 版外壳，需另行完成小板固件及实物触摸标定。
- [已生产的模组版主板](hardware-q2/ProPrj_esp32s31-mp4_2026-09-22.kicad_pro)：当前保存工程为 `ProPrj_esp32s31-mp4_2026-09-22`；原始生产 Gerber 的审查记录见 [打板检查](hardware-q2/gerber-review-20260922/README.md)。
- [H1/H2 端子、马达和电池规划](mechanical/connector-layout/README.md)：当前摆放版使用 JST ACH 两芯/三芯端子，新增 FreeCAD 装配及线束通道检查。
- [历史外壳 F](mechanical/enclosure-q2-f/README.md)：保留早期外观方案；当前装配应参考 L 版。

旧 `hardware/`、`hardware-q2-placement/` 和旧主板导出文件已从当前目录移除，可从 Git 历史查找。根目录的 PDF、嘉立创 `.epro2` / `.epro` 及 Gerber 压缩包是原始资料。

历史摆放版已有主板与外壳适配；用户新布局 `hardware-q2-layout` 已用于最新小板/排线装配，其最终版本的四个主板安装孔已确认与原柱对齐；完整复查以最新报告为准。屏幕 FPC 插接细节、完整器件高度、具体电池型号仍需确认。独立滑环及五键小板见 `hardware-controls/`；两板接口针序已核对，排线插接、小板触摸与摇摆按键仍需实物验证。[排线采购与装配说明](hardware-controls/mechanical/FFC-INTERCONNECT.md)。详细尺寸、检查范围和后续事项见上述工程说明。
