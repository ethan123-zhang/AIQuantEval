---
type: project
topic: 环境与工具链
last_updated: 2026-10-11
---

# 环境与工具链（实测事实）

## WSL 侧

| 项 | 值 |
|---|---|
| 发行版 | Ubuntu 22.04 |
| Python | 3.10.12 |
| rknn-toolkit2 | **2.3.2** |
| numpy | **2.2.6** |
| torch | 2.4.0+cpu |
| onnx | 1.15.0 |
| onnxruntime | 1.23.2 |
| opencv-python | 5.0.0.93 |
| 工作区 | `/home/ethan/rknn_workspace` |
| 虚拟环境 | `/home/ethan/rknn-venv`（另有 `~/.local` 下的 rknn） |

> **版本约束更正**：早期文档常写 rknn-toolkit2 "依赖 `numpy<=1.26.4`"，
> 实测 numpy **2.2.6** 下 config/load_onnx/build/hybrid/推理全流程正常，
> **无需降级**。真正需留意的是 `torch<=2.4.0`。

## Windows 侧

| 项 | 值 |
|---|---|
| 摄像头 | 真实设备在 **MSMF index 1**（不是 DSHOW index 0） |
| 推流端口 | TCP **8899** |
| 依赖 | 仅需 opencv-python（无 rknn） |

## 硬件

- **无 RK3588 开发板**。一切"连板"能力均不可用（见 `04-pitfalls.md`）。

## 数据集

| 用途 | 位置 | 规模 |
|---|---|---|
| 源图 | `E:\AIQuantEval\coco_val2017_500\images\val2017` | 500 张 |
| 标注 | `...\annotations\instances_val2017_sub500.json` | 500 图 / 3842 框 / 80 类 |
| 校准集（WSL） | `/home/ethan/rknn_workspace/calib_images/` | **500 张**（2026-10-11 起） |
| 校准清单 | `/home/ethan/rknn_workspace/dataset.txt` | 绝对路径，**前 200 张** |
| 评估集（WSL） | `precision_analysis/data/images` + `data/labels` | **494 张 / 3799 框** |

**为什么是 494 而不是 500**：另 6 张仅含 `iscrowd` 标注，按 COCO 惯例剔除
（`prepare_coco.py` 的处理是正确的，不是漏图）。

## 环境陷阱

- `wsl.exe` 每次调用都会向 stderr 输出一行 localhost 代理警告，**属正常噪声**，
  不是错误，过滤掉即可。

## 相关记忆

- 坑清单 → `04-pitfalls.md`
- RKNN 工具链的限制与参数细节（知识正文）→ **aiVault**：
  `E:\Document\Ethan'vault\aiVault\wiki\entities\RKNN_Toolkit2.qmd`
- 量化结论 → `03-quantization-findings.md`（指针页）
