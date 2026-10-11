---
type: reference
topic: 量化结论（指针 → aiVault）
last_updated: 2026-10-11
---

# 量化结论 —— 指针页

> ⚠️ **知识真源在 aiVault，本页不复制正文。**
> 需要细节请直接打开下列页面；本页只放结论摘要与入口，避免两处内容分叉。

## 真源位置

**`E:\Document\Ethan'vault\aiVault`**（独立 git 仓库，remote `ethan123-zhang/Ethan-s-aiVault`）

| 需要什么 | 去哪看 |
|---|---|
| 塌陷机理、消融实验、修复方案 | `wiki/concepts/YOLO_Head_Quantization_Collapse.md` |
| 四种量化策略的精度/体积选型对比 | `wiki/comparisons/RKNN_Quantization_Strategy_vs.qmd` |
| 完整实验条件与 6 组原始数据 | `raw/20261011-local/yolov8n_rknn_int8_collapse.md` |
| RKNN 工具链限制（连板/参数） | `wiki/entities/RKNN_Toolkit2.qmd` |

## 结论摘要（仅供快速回忆，细节以 aiVault 为准）

- **INT8 全量化会把 YOLOv8n 打崩**：494 张图 0 检测，mAP@0.5 = 0.0000（float 基准 0.4332）。
- **根因**：输出张量 `output0` 形状 `(1,84,8400)`，把框坐标（0~640）与类别概率（0~1）
  混在同一 int8 张量，一个 `scale` 覆盖不了相差 3 个数量级的范围，概率被抹成 0。
- **不是主干、也不是检测头的问题**（消融实验 T1–T5 已证）。
- **修复**：把 `output0-rs`、`output0_int8` 两层设为非量化即可 → mAP@0.5 = 0.4387，
  模型 4.82 → 4.89 MB，主干保持 int8。
- **换校准集无效**（但此结论仅 5 张图验证，属弱证据）。

## 本仓库内的脚本入口

实验脚本在 **WSL 侧**，不在本仓库：

```
/home/ethan/rknn_workspace/precision_analysis/
├── final_verify.py      # 定论验证（float / int8 / 仅保输出层）
├── hybrid_eval.py       # 四方对比
├── layer_precision.py   # 逐层误差
└── run_compare.py       # float vs int8
```

产物：`results/final_verify/final_report.json`、`results/HYBRID_REPORT.md`、
`results/FINAL_REPORT.md`。

## 相关记忆

- 待办与风险 → `05-open-questions.md`
- 踩坑 → `04-pitfalls.md`
