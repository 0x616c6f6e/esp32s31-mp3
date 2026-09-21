# KiCad 元件 3D 模型

122 个实体元件全部关联本地 STEP；4 个安装孔不添加虚构元件。41 个封装模型同时写入 `../hardware.kicad_pcb` 和 `../MP3_Source.pretty`。路径使用 `${KIPRJMOD}/models3d/`，不依赖系统模型库或失效的 EASYEDA_MODELS 目录。

从 KiCad 打开 `../hardware.kicad_pro`，进入 PCB 编辑器的 3D 查看器。若编辑器中仍加载旧 PCB，请先关闭旧窗口，再从磁盘打开，避免旧窗口保存覆盖新模型引用。

## 模型精度

| 类别 | 来源与范围 |
| --- | --- |
| 29 种标准封装 | KiCad 10 安装库：电阻、电容、电感、二极管、SOT、MSOP、QFN、LGA、晶振。按源封装编号焊盘匹配方向；这是通用封装，不等同于订购型号的厂商 CAD。 |
| ESP32-S31-WROOM-3 | 本项目 Espressif 数据手册第 64 页尺寸，22 × 30 × 3.5 mm，模块 PCB 1.0 mm，屏蔽罩 21 × 23 mm；省略天线铜图形及内部元件。没有使用 ESP32-S3 模型代替。 |
| AFE03-S21FMA-1H | 本项目连接器图纸，7.9 × 3.2 × 1.0 mm；简化锁扣和端子。插槽高度、插入深度、屏幕尾部厚度及触点面未验证。 |
| USB、耳机座、TF、排针/排母 | 按现有封装 Fab 外形生成近似模型；高度、内部细节和实际采购型号仍需确认。排针突出长度也是假设。 |
| 其余 5 种小型封装 | 源封装轮廓及焊盘派生的简化模型；高度来源和假设逐项记录于 model-manifest.json。 |

**现有 E 版 FreeCAD 装配仍使用之前的简化元件包络，不会自动替换成这些 STEP。** 例如 U9 旧包络为 3.2 mm，新模型为资料标称 3.5 mm。现有外壳通过的是旧包络检查，不能据此声称本次完整 STEP 装配已通过干涉验证。屏幕排线也仍未完成插接兼容确认。

## 文件与检查

- `pcb-populated.step`：KiCad 原生导出的带元件板卡，可在 FreeCAD 中导入。
- `pcb-3d-front.png`、`pcb-3d-back.png`、`pcb-3d-isometric.png`：KiCad 原生 3D 渲染。
- `model-manifest.json`：41 种模型的元件位号、来源、假设、尺寸边界和 SHA-256。
- `attachment-validation.json`：122 个关联路径和文件哈希检查；与原提交 `4bef85f` 比较，剔除 model 节点后的 PCB 数据完全一致。
- `vendor/`：未经修改的 KiCad 模型源文件；根目录中的模型已按本工程封装方向定向。
- `LICENSE-NOTICE.md`：模型来源、署名及许可说明。

PCB 的元件位置、焊盘、走线、铜区、孔槽和设计规则未改动。添加模型后重新运行 KiCad DRC：0 违规、0 未连接、0 原理图一致性问题。3D 外观检查不替代尺寸公差、电气或制造验证。

## 重建

仅查看工程不需要重建或安装 FreeCAD。需修改模型时：`plan_3d_models.py` 读取 KiCad 标准库路径（可在脚本中配置），`build_3d_models.py` 在 FreeCAD GUI Python 环境生成彩色 STEP，`attach_3d_models.py` 添加引用，`verify_3d_models.py` 检查关联及 PCB 未改动。最后使用 KiCad CLI 重渲染、导出 STEP 并运行 `final_audit.py`、`check_delivery.py`。

外壳重建的源检查允许经验证的纯模型引用变化，但保留旧机械源哈希和旧包络检查范围；任何非模型 PCB 变化仍会阻止重建，直到重新冻结机械来源。
