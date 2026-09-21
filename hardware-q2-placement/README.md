# Q2 主板 · 双面摆放 / 手动布线版

打开本目录的 **hardware.kicad_pro**，从同一个工程进入原理图和 PCB 编辑器。本版供手动布线使用，已于 2026-09-21 恢复原理图关联并重新规划功能区摆放。

125 个封装（121 个实体元件和 4 个安装孔）均已关联原理图；正面 59 个、背面 62 个实体元件。本次调整 60 个元件的位置、方向或板面。板框仍为 46 × 76 mm、R10、六层，走线／过孔／铺铜均为 0。

## 本次修复与摆放

- 从当前原理图恢复根页／子页／符号 UUID 路径。按用户已保存的原理图删除 PCB 中过时的 R10，并将 U3.TS 同步到 BAT_TS；原理图内容未被改写。
- USB：D1 靠近 USB1，U17 公共端朝向 USB，输出朝向 ESP32／CH343；U12 在背面侧方分支，RTC 移到正面释放背面 USB 通道。
- 音频：按 DAC 的供电、充电泵与滤波引脚聚拢电容，调整晶振方向。C28 位于背面，手动布线时需通过短电源过孔及就近地过孔完成去耦回路。
- 电源：保留原充电、降压芯片的紧凑开关回路。电池采样电阻 R1 移近 H2 的 GBAT，电量计及外围同步靠近。
- 马达：U11 输出朝向 H1，缩短两条输出连接；H1/H2 端子保持既定位置和线束出口。

U9、CARD2、CN1、USB1、FPC2、H1、H2 和 4 个安装孔已锁定；屏幕 FPC 绕板通道、操作小板接口预留和天线禁布区保留。H1/H2 为低矮 JST ACH 两芯／三芯端子，见 [线束与器件规划](../mechanical/connector-layout/README.md)。操作小板及主板连接器电路尚未实现，当前仅有机械预留。

详细问题、尺寸比较、取舍和手动布线顺序见 [PCB 布局审查](review/pcb-layout-review.md)。比较指标是焊盘之间的平面直线距离，不是实际布线长度或信号完整性结果；部分低速连接有意变长，以改善 USB 和音频布局。

## 验证

- KiCad DRC：0 违规、0 原理图一致性问题；385 条未连接是尚未布线的状态。
- ERC：0 错误、9 条既有警告。电路功能审查中尚未处理的事项仍需解决，不能据此直接生产。
- 125 个封装／557 个焊盘的身份、网络、值和 DNP 与关联修复后的基线一致；用户原理图保存内容、板框、机械锚点、天线区和叠层均保持不变。
- FreeCAD：121 个元件的名义实体与 F 版外壳、屏幕、操作小板、电池、马达、排线和线束未发现非预期相交；元件之间也无实体相交。
- 新装配为 `output/placement-F-fit.FCStd`。F 版外壳源文件未改写，其原内嵌 PCB 仍是历史摆放。
- 几何检查基于当前占位和近似模型，不涵盖实物公差、焊锡、散热或 FPC 弯折；最终选型与手动布线完成后应重新检查。

## 文件

- `output/placement-front-back.png`：带位号的双面摆放图，背面已镜像；对比图为 `review/placement-before.png`。
- `output/3d-front.png`、`output/3d-back.png`：最新 KiCad 3D 预览。
- `output/placement-populated.step`：最新带元件板卡；`output/placement-F-fit.FCStd`：与 F 版结构匹配的检查装配。
- `output/component-placement.csv`：坐标／方向／板面／锁定清单，未经生产审核。
- `output/placement.json`、`placement-metrics.json`：摆放变化、功能分组和连接距离。
- `output/reassociation.json`：关联修复和网络同步记录；其输出哈希对应移动元件之前的修复阶段。
- `output/placement-drc.json`、`placement-erc.json`、`validation.json`、`mechanical-check.json`：本次验证结果。
- `review/placement-baseline.json`：关联修复后的身份、网络与机械基线；`output/current-netlist.xml`：本次原理图导出的网络表。
- `models3d/`、`MP3_Source.pretty/`：工程本地模型和封装库。

从同一工程打开原理图与 PCB 后，可交叉选择元件，并用 F8 正常更新 PCB，无需重新按位号关联。如果编辑器仍显示旧文件，应重新载入磁盘文件，避免用旧会话覆盖当前结果。

`scripts/relink_schematic.py` 负责明确校验后的关联恢复；`refine_routing_placement.py` 是本次候选布局生成记录，必须使用修复后的输入快照，不应在开始手动布线后重新生成。`scripts/validate_placement.py` 校验当前板与本次基线，运行前需重新导出网络表、DRC、ERC、STEP 并执行 FreeCAD 机械检查。历史生成器 `place_components.py`、`plan_connectors.py` 和旧模型报告不代表当前布局。
