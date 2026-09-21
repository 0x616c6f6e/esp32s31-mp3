# Q2 外壳修订 E · 实际新 PCB 装配

打开 `ESP32S31_MP3_Q2_E.FCStd`。默认显示完整外观，实际板为 `MainPCB`，可编辑尺寸在 `Parameters`。本版使用 `../../hardware-q2/hardware.kicad_pcb` 导出的真实板体；旧 C/D 版仍保留用于追溯。

机身 50 × 80 × 13.5 mm，盖板突出后最大厚度 14.2 mm。主板 46 × 76 mm、R10，壳壁 1.2 mm，名义侧边间隙 0.8 mm；上下螺柱通过 PCB 板边缺口避让。后盖增加与四个实际 NPTH 孔对应的支撑柱。主控朝向屏幕，背面 FPC 座通过左侧绕行的屏幕排线连接；操作小板使用另一条独立 FPC 通道。

屏幕上移 1.5 mm 后，FPC2 同步对齐到装配 Y=20.400 mm。排线中心路径长度为 46.14 mm。只确认路径和 XY 对齐，尚未确认尾部厚度、触点面、插入深度、端子 pinout 或折弯应变；连接器以外形实体表示，图中相交的插入包络不代表已经验证插接。

电池占位调整为 **24 × 34 × 3 mm**，位置 `(8.3, 37, 7.8)`，以避让操作板螺钉头和耳机座。具体电池型号、容量及膨胀余量待确定。滑环和五键板保留 44 × 34 × 0.8 mm 的机械外形、孔位、开关和连接座占位，没有电路或铜层实现。

`exports/validation.json` 记录实体有效性、零件相交体积、板体和元件占位干涉、外包络和源 PCB 哈希。当前所有列出的非预期干涉检查通过。元件高度部分是假设，不能替代完整器件 STEP 和实物试装；PCB 安装螺钉头、电池引线、插接操作空间及装配公差还需确认。

## 预览与导出

- `exports/exterior-E.png`：完整外观。
- `exports/new-PCB-installed.png`：透明壳体内的实际新 PCB。
- `exports/front-E.png`：正视图。
- `exports/assembly-E-new-PCB.step`：整机装配参考。
- `exports/q2-e-housing`、`q2-e-rear-cover`、`q2-e-wheel-rocker`、`q2-e-center-button`：各零件 STEP / STL。
- `exports/control-board-mechanical.step`、`control-board-outline.dxf`、`control-board-features.csv`：后续设计操作小板的结构输入。
- `exports/mainboard-reference-envelope.step`：简化空间包络；实际带缺口主板以 `MainPCB` 和 hardware-q2 的 STEP 为准。

## 更新方法

只修改结构参数时，保存并关闭本版文档，编辑 `parameters.json`，再运行 `Rebuild.FCMacro`。若改了 PCB，先使用 KiCad 重新检查、导出 board-only STEP 并运行 `hardware-q2/scripts/export_geometry.py`，再用 FreeCAD 解释器运行 `freeze_mechanical.py` 更新冻结参考。源文件哈希不一致时重建会停止，避免混用旧板。
