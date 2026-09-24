Q2 controls C / CH32V006F8U6 — 嘉立创裸板打样数据 — 2026-09-22

双层 FR-4，成品板厚 0.8 mm，外形 44 × 34 mm，四角 R10，外层铜厚 1 oz。
板框以 controls-Edge_Cuts.gm1 的线中心加工。
Gerber Job 的 44.05 × 34.05 mm 包含 0.05 mm 画线宽度，不是成品尺寸。
所有 Gerber 和 Excellon 钻孔为 mm、绝对原点、不镜像。
controls-PTH.drl：61 个 Ø0.30 mm 镀铜过孔。
controls-NPTH.drl：4 个 Ø1.80 mm 非金属化安装孔，不能改为镀铜孔。
顶部三组触摸电极保留阻焊覆盖，不开窗、不上锡；不要在电极背面额外增加铜皮。
保留设计中的 GND 覆铜和禁铺铜区域。表面处理及阻焊颜色按订单选项选择。

.gtl/.gbl：顶/底铜层；.gts/.gbs：顶/底阻焊开窗；.gto/.gbo：顶/底丝印。
.gtp/.gbp：顶/底钢网层，不是额外铜层；.gm1：板框。
本 ZIP 供裸板及钢网制造，不含贴片 BOM、坐标或固件。
新版 BOM 单独见 controls-ch32v006-bom.csv；不要混用 AT42/TCA 版生产文件。

来源：hardware-controls/controls.kicad_pcb
PCB SHA-256：d4d2037be103225b9a990941eed6e9a067a849ac06b961e922cb0380ecad46a2
KiCad 10.0.4 导出，重铺铜检查后 DRC 0、未连接 0、原理图一致性问题 0。
CH32 固件尚未实现；触摸参数、盖板与整机装配需实物验证。
