Q2 滑环按键小板 — 2026-09-22 无测试点版 / PCB prototype

生产参数 / Fabrication parameters
- 双层 FR-4，成品板厚 0.8 mm，外形 44 x 34 mm，四角 R10。
- 1 oz 铜厚，双面绝缘阻焊；表面处理按下单选项指定。
- 板框加工依据 Edge.Cuts 线中心；44.05 x 34.05 mm 是含 0.05 mm 画线宽度的图形包络，不是成品尺寸。
- controls-PTH.drl：52 个镀铜过孔，钻径 0.30 mm。
- controls-NPTH.drl：4 个非金属化安装孔，孔径 1.80 mm，不要改为镀铜孔。
- 顶层三个触摸电极必须保持阻焊覆盖，不开窗、不镀锡，不增添电极背面地铜。
- 保留设计中的双面地铜和触摸禁铺铜区域，不自行添加铜皮。
- F.Paste / B.Paste 为钢网层，不是额外铜层。
- 所有 Gerber 和钻孔采用相同的绝对原点，单位 mm；不镜像。
- 本包是裸板/钢网制造数据，不包含 SMT 贴装 BOM 和坐标。

Files: RS-274X Gerber with Protel extensions, Excellon PTH/NPTH drills.
F.Cu / B.Cu = top / bottom copper.
F.Mask / B.Mask = top / bottom solder mask openings.
F.Silkscreen / B.Silkscreen = top / bottom legend.
F.Paste / B.Paste = stencil data only.
Edge.Cuts = finished board outline centerline.

Source: hardware-controls/controls.kicad_pcb
PCB SHA-256: bf1cbd372979ea753bb2b9f4d9078b64513caa0bafdff4b06b10188c1d9859a5
KiCad 10.0.4: zones refilled before export.
Native DRC: 0 violations, 0 unconnected items, 0 schematic parity violations.

本版供原型打样；触摸灵敏度、覆盖层、按键行程和整机配合尚需实物验证。

TP1～TP11 已移除。请使用此 no-tp 版本，不要混用此前带测试点版。
