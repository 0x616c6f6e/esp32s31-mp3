# CH32V006 C 版迁移检查

源电路为 AT42QT2120 + TCA6408A；目标为单颗 CH32V006F8U6。`before/` 是本次操作前的原文件备份；`candidate/` 是工作候选文件。以 hardware-controls 根目录中的最终工程为准，不要从这里的中间 PCB 导出生产文件。

`design.json` 记录本版原理图 UUID、元件、实际 KiCad 顶视坐标、MCU 引脚与 FPC 接口。这里的坐标是实际 PCB 坐标，不能直接交给历史脚本中采用 `44-x` 镜像约定的机械生成器。

检查报告以 `final-erc.json`、`final-drc.json`、`validation.json` 为准；带 pre-route / routed / fanout / grid 字样的文件仅用于迁移过程诊断。模型预览用于检查元件体积与布局，不代替整机 FreeCAD 装配的干涉验证。

C 版需要新固件，详见 `../../CH32V006-interface.md`。本次没有生成可直接烧录的固件；旧 AT42 版本的 Gerber 和 BOM 不适用于 C 版。后续已于 2026-09-22 导出新版生产包 `../controls-ch32v006-jlcpcb-20260922-gerbers.zip`，导出检查记录见 `../ch32v006-gerber-review/manifest.json`。

最终检查：KiCad 10.0.4 ERC、DRC、未连接项、原理图一致性问题均为 0。新版 BOM 为 `../controls-ch32v006-bom.csv`，装配 STEP 为 `../controls-ch32v006.step`。J1、E1、SW1～SW5、H1～H4 和板框通过前后几何一致性检查。不要将这些电气与几何检查解释为固件或整机实测通过。
