# Q2 外壳 F：屏幕三边等距、操作区上移

打开 `ESP32S31_MP3_Q2_F.FCStd`，默认显示完整外观。本版接续 E 版外壳，并装入当前 `hardware-q2-placement` 的真实主板元件模型以及 H1/H2 端子、马达和线束规划。

| 调整 | E 版 | F 版 |
| --- | --- | --- |
| 外壳宽 × 长 × 厚 | 50 × 80 × 13.5 mm | 50 × 81.5 × 13.5 mm |
| 可见屏幕盖板上边距 | 0.5 mm | 2 mm |
| 可见屏幕盖板左右边距 | 各 2 mm | 各 2 mm |
| 外壳平面圆角 | R12 | R12.5 |
| 圆环中心 Y | 61.3 mm | 59.3 mm |
| 触摸/五键小板起始 Y | 44.3 mm | 42.3 mm |
| 屏幕盖板至圆环间距 | 4.3 mm | 2.3 mm |

边距以外观看到的 **46 × 40 mm 黑色保护盖板轮廓** 为基准，不是 LCD 有效显示区。盖板 R10.5 与机身 R12.5 的顶部圆角中心重合，使直边和顶部圆角处均保持 2 mm 名义边距。机身顶部沿原坐标负 Y 延伸 1.5 mm，新的壳体 Y 范围为 −1.5～80 mm。盖板及屏幕在装配中的位置不变，屏幕 FPC 与主板连接座的原对齐关系保持。

触摸小板、圆环、中心键、五个开关、按键图标、四个安装孔及支柱、螺钉、板端 FPC 座整体上移 2 mm；小板局部孔坐标不变。操作板 FPC 的起点和转折点同步调整，主板端点保持原位。延伸顶部后，为原螺钉柱增加上部连接筋，让螺柱保持单一实体连接且不改变 PCB 缺口和螺钉轴线。

本次按新增顶部高度的要求将机身长度加至 81.5 mm；主板继续保持 46 × 76 mm，外壳厚度不变，含屏幕盖板最大厚度仍为 14.2 mm。KiCad 文件及走线状态未改变。

## 文件与验证

- `exports/comparison-E-F.png`：同宽比例的修改前后对比。
- `exports/front-F.png`、`exterior-F.png`：正视图和立体外观。
- `exports/new-PCB-installed.png`：内部装配预览。
- `exports/q2-f-housing.step/.stl`、`q2-f-rear-cover.step/.stl`：机身和后盖。
- `exports/q2-f-wheel-rocker.step/.stl`、`q2-f-center-button.step/.stl`：圆环和中心键。
- `exports/control-board-mechanical.step`、`control-board-outline.dxf`、`control-board-features.csv`：小板结构资料。
- `exports/assembly-F-current-PCB.step`：包含当前主板、操作小板、候选马达和线束的装配参考。
- `exports/validation.json`：实体有效性、三边距、元件/排线/马达/线束间隙与源 PCB 哈希检查。

外观零件和小板检查为有效单一实体；当前模型未发现非预期相交，马达最大包络距操作小板 0.55 mm；STEP 回读体积核对和 STL 封闭性检查通过，见 `export-verification.json`。完整检查结果以生成的 `validation.json` 为准。电池、操作板连接器、线材弯曲半径和部分器件模型仍为规划数据，未完成实物公差与插接验证。操作小板尚未设计电路和铜层。

修改结构时请保存并关闭本版文档，修改 `parameters.json`，再运行 `Rebuild.FCMacro`，使硬件包络、图标、FPC 通道与导出文件一起重建。若调整操作区，`ControlShiftY`、`WheelY`、`ControlBoardY` 必须保持同一位移关系，脚本会检查。`build_enclosure.py` 可用 FreeCAD 命令行生成模型；`prepare_views.py` 需要 FreeCAD 图形界面。E 版和上一版连接器规划装配保留作比较。
