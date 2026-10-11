---
type: project
topic: 会话记录 — 文件改动与测试结果
last_updated: 2026-10-11
---

# 文件改动与测试结果（2026-10-11）

> 进度与结论 → `06-session-log.md` · 决策依据 → `07-decisions-and-failures.md`

## 一、修改的关键文件

### WSL 侧（`/home/ethan/rknn_workspace/precision_analysis/`，**无 git**）

| 文件 | 说明 |
| :--- | :--- |
| `final_verify.py` | **定论验证**：float / int8 / 仅保输出层 |
| `hybrid_eval.py` | 四方对比 |
| `layer_precision.py` | 逐层量化误差（解析式 + 真实激活 qdq） |
| `hybrid_build.py` | 混合量化构建 |
| `make_report.py` / `hybrid_report.py` | 报告生成 |
| `run_compare.py` | **修了 bug**：`mAP50_95` 原被误赋值为 `mAP50` |

产物：`results/final_verify/final_report.json`、`results/HYBRID_REPORT.md`、
`results/FINAL_REPORT.md`、`results/layer_analysis/layer_table.csv`。

### 数据与环境

| 路径 | 改动 |
| :--- | :--- |
| `/home/ethan/rknn_workspace/calib_images/` | **182 → 500 张**（val2017，md5 校验一致）；旧数据**已覆盖删除** |
| `/home/ethan/rknn_workspace/dataset.txt` | 重建为绝对路径，取前 200 张 |
| `E:\AIQuantEval\push_ai.bat` | 0 字节 → 补上内容（106 B），现已可推送 |

### aiVault（`E:\Document\Ethan'vault\aiVault`）

| 文件 | 改动 |
| :--- | :--- |
| `wiki/concepts/YOLO_Head_Quantization_Collapse.md` | 新建并**两轮更正**（因果：检测头→主干→输出层） |
| `wiki/comparisons/RKNN_Quantization_Strategy_vs.qmd` | 新建（按 §4.4 模板） |
| `raw/20261011-local/yolov8n_rknn_int8_collapse.md` | 新建（按 §4.1 模板） |
| `wiki/concepts/Dual_Store_Knowledge_vs_Project_Memory.md` | 新建（**跨项目通用**双库分工约定） |
| `wiki/entities/RKNN_Toolkit2.qmd` | 更正 2 处事实错误 + 新增 §4.1 |
| `INDEX.md` / `LOG.md` | 同步更新 |

## 二、当前测试结果

评估集：COCO val2017 子集 **494 张 / 3799 框**，conf=0.001，
rknn-toolkit2 2.3.2，`target_platform=rk3588`，**模拟器（无板）**。

| 配置 | mAP@0.5 | mAP@0.5:0.95 | 检测数 | 模型大小 |
| :--- | :--- | :--- | :--- | :--- |
| float（基准） | 0.4332 | 0.3162 | 10948 | — |
| INT8 全量化 | 0.0000 | 0.0000 | 0 | 4.82 MB |
| 敏感 14 层 float16 | 0.0000 | 0.0000 | 0 | 5.21 MB |
| 主干 132 层 float16 | 0.4269 | 0.2790 | 9995 | 7.26 MB |
| **仅输出层 2 层 float16** | **0.4387** | 0.2878 | 9462 | **4.89 MB** |

> ⚠️ **这些数字目前不可对外引用** —— 评估集与校准集同源（见 §四风险 1）。

## 三、尚未解决的风险与问题

| # | 风险 | 严重度 | 说明 |
| :--- | :--- | :--- | :--- |
| 1 | **校准集与评估集同源** | 🔴 高 | 均为 val2017（500/494 张），违反"必须分开"。**0.4387 有虚高风险，不可外引** |
| 2 | **"换校准集无效"仅 5 张图证据** | 🟡 中 | 未在全量算 mAP |
| 3 | **全部结论来自模拟器** | 🟡 中 | 无真机验证；且模拟器耗时≠真机 |
| 4 | **WSL 工作区无 git** | 🟡 中 | 全部实验脚本与模型无版本管理，换机即丢 |
| 5 | **未实测推理耗时** | 🟡 中 | "仅保输出层省算力"只是理论推断 |
| 6 | **旧校准集已删除** | 🟢 低 | 直接覆盖未备份，做 B 组对照需从 git 恢复 |
| 7 | **切尾巴未实测** | 🟢 低 | 仅机理分析 |
