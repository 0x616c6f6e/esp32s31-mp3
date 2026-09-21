# ESP32-S31 MP3 / Q2 风格播放器

当前工程：

- [双面元件摆放 / 手动布线版](hardware-q2-placement/README.md)：打开 `hardware-q2-placement/hardware.kicad_pro`；正面 52 个、背面 70 个元件，旧走线/过孔/铺铜已清除，保留网络供手动布线。
- [KiCad 已布线参考板](hardware-q2/README.md)：46 × 76 mm、R10、六层，打开 `hardware-q2/hardware.kicad_pro`。
- [FreeCAD 外壳与装配](mechanical/enclosure-q2-e/README.md)：打开 `mechanical/enclosure-q2-e/ESP32S31_MP3_Q2_E.FCStd`。
- [已布线参考板检查摘要](hardware-q2/output/validation-summary.json)：该参考板 DRC 无违规、无未连接，原理图一致性检查通过；ERC 保留原有 9 条警告。新的手动布线版检查见其独立目录。

`hardware/` 与其他机械修订保留作历史参考。根目录的 PDF、嘉立创 `.epro2` 及 Gerber 压缩包是用户提供的原始资料。

当前版本完成主板与外壳的结构适配；屏幕 FPC 插接细节、完整器件高度、具体电池型号仍需确认。滑环及五键小板目前仅完成机械方案，未实现电路。详细尺寸、检查范围和后续事项见上述工程说明。
