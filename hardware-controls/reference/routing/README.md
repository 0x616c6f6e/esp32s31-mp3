# 布线交换记录

最终文件是上两级的 `controls.kicad_pcb`，此目录仅记录布线交换输入，不应直接作为主工程编辑。

当前记录对应 B 版。`controls-sensors-base.kicad_pcb` 已连接三个 WHEEL 网络，并预布 U2 到 R4 的 SDA 出线。`controls-route.dsn` 将真实的触摸铜面边界表示为正面避让区，冻结这些已有连接，然后由 Freerouting 2.4.1 完成其他网络；`controls-route.ses` 为回传记录。

这是有意采用的交换方式：KiCad 的 DSN 导出会把凹形自定义焊盘近似为凸包；普通信号层铜面在该布线工具中也不默认阻挡其他网络。直接使用这两种表示会得到错误候选。因此本记录在 DSN 中省略 E1 引脚，使用真实边界的避让区。布线器的交换格式提示不能代替原生 KiCad DRC；本项目不设置实际 PCB 的错误豁免。

回传后运行 `scripts/finalize_board.py`：将 C3/C4 向 KiCad X 负方向平移 0.2 mm，连同相接走线一起调整，消除与 U2 的 courtyard 重叠；将相邻 UNUSED_INPUTS 过孔向 X 负方向移 0.15 mm；规范 J1 未连接脚的网络名称；补齐测试点位号、J1 的 1 脚标记及工程规则。此脚本可重复执行，不会重复平移。

最终检查结果为 0 违规、0 未连接、0 原理图一致性问题；没有通过屏蔽 KiCad 错误实现通过。以项目 `output/drc.json` 和主 PCB 为交付依据，不能直接使用此处的预布线基板打样。

2026-09-21 接口换脚：J1 第 3 脚改为 SDA、第 4 脚改为 SCL。`controls-pin-swap-base.kicad_pcb`、`controls-pin-swap.dsn`、`controls-pin-swap.ses` 记录本次局部重连；保留原有 RESET_N、触摸采样走线及接口区域之外的连接，释放接口附近其他走线后重新布线。此前的 `controls-route.*` 保留作初次布线记录，其 J1 脚位不代表最终版本。本次回传并运行 finalize_board.py 后，原生 KiCad DRC、未连接检查和原理图一致性检查均为零。

2026-09-21 最终接口及 POWER 上拉：按用户确认，接口恢复为 1/12 GND、2 +3V3、3 SDA、4 SCL、5 INT_N、6 RESET_N、7…10 NC、11 KEY_POWER。新增 R14 = 10 kΩ，将 KEY_POWER 上拉至 +3V3，按下 SW1 时接地。R14 位于背面 KiCad (12, 1.4) mm、-90°，靠近接口并避开电池。`controls-power-pullup-base.kicad_pcb`、`controls-power-pullup.dsn` 和 `controls-power-pullup.ses` 记录最终增量连接：保留原已验证布线，预接 POWER 支路后补接 R14 电源侧。此版本经过原生 KiCad 检查，0 违规、0 未连接、0 原理图一致性问题；DSN 中的连接提示仍以原生检查为准。中途的接口反序方案未用于交付。

2026-09-21 新主板 FPC1 对齐：J1 更换为 HCTL 并移动到 B.Cu (8.130, 9.411) mm、−90°；U1 向 KiCad −X 移 0.6 mm。`controls-fpc-aligned*` 和 `controls-fpc-u1*` 记录接口及芯片局部重连；最后以双层避障补齐 R4 的 +3V3 支路，路径节点见 `power-bridge-path.json`（层 0=F.Cu、1=B.Cu，栅格 0.025 mm）。最终 PCB 是权威文件，交换中间文件不能直接打样。最终原生 DRC、未连接、原理图一致性和 ERC 均为零。
