# ESP32-S31 MP3 / Q2 风格播放器

当前工程：

- [KiCad 主板](hardware-q2/README.md)：46 × 76 mm、R10、六层，打开 `hardware-q2/hardware.kicad_pro`。
- [FreeCAD 外壳与装配](mechanical/enclosure-q2-e/README.md)：打开 `mechanical/enclosure-q2-e/ESP32S31_MP3_Q2_E.FCStd`。
- [最终检查摘要](hardware-q2/output/validation-summary.json)：DRC 无违规、无未连接，原理图一致性检查通过；ERC 保留原有 9 条警告。

`hardware/` 与其他机械修订保留作历史参考。根目录的 PDF、嘉立创 `.epro2` 及 Gerber 压缩包是用户提供的原始资料。

当前版本完成主板与外壳的结构适配；屏幕 FPC 插接细节、完整器件高度、具体电池型号仍需确认。滑环及五键小板目前仅完成机械方案，未实现电路。详细尺寸、检查范围和后续事项见上述工程说明。
