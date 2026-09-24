# AM213 转接板 A

打开 `am213-fpc-adapter.kicad_pro`。现为已完成原理图和布线的电气工程，取代旧机械占位版本。

- 原理图、PCB：同名 `.kicad_sch`、`.kicad_pcb`
- 自带库：`Adapter.kicad_sym`、`Adapter.pretty`、`models3d`
- 最新装配副本：`models3d/Q2_L_AM213_Completed_Adapter.FCStd`
- 检查、BOM、预览及制造审核包：`output/`

采用屏厂 3.3 V 直接接线参考；17×22 mm 元件岛、70 mm 左出尾巴；J2 局部 **(3,12)**、1 脚左上。R10/R11 不装。ERC/DRC、未连接和原理图一致性问题均为 0。

详见[接线与坐标](../fpc-layout-guide.md)、[电气依据](../README.md)、[制造说明](FABRICATION.md)。先审核柔性叠层、补强、0.15 mm 小孔及金手指工艺，再做样板；尚未实物插合和点亮。

`Adapter_Placement.pretty`、旧 `placement-preview.*` 及 `models3d/Q2_L_BTB_Fit_Review.FCStd` 为历史阶段文件。
