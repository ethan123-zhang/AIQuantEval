---
type: project
topic: 项目地图
last_updated: 2026-10-11
---

# 项目地图

## 仓库定位

AIQuantEval = **模型量化与边缘部署的评测工程**。包含 E 盘（Windows 侧）与
WSL 侧两块，两者是**同一件事的两半**，不是两个独立项目。

## 两侧分工

| 位置 | 角色 | 说明 |
|---|---|---|
| `E:\AIQuantEval` | **本仓库**（git 管理） | 评测数据、Windows 侧推流、本记忆库 |
| `/home/ethan/rknn_workspace`（WSL） | **实际工作区** | rknn-toolkit2 跑量化/推理；**未纳入本 git 仓库** |

> **关键事实**：WSL 侧 `rknn_workspace` **不在本仓库里**，也**不在 git 版本管理下**。
> 它体量大（含模型与数据集）且需 Linux 工具链。因此：
> **WSL 侧的重要结论必须回写进本记忆库**，否则换机/重装即丢失。

## 目录

| 路径 | 内容 |
|---|---|
| `MEMORY.md` + `memory/` | 本记忆库 |
| `RK3588_Sim/` | Windows 原生摄像头采集 + TCP 推流给 WSL（详见其 README） |
| `coco_val2017_500/` | COCO val2017 的 500 张子集 + 标注 + 下载脚本 |
| `push_ai.bat` | 推送脚本（**当前 0 字节，未实现**） |

## 数据流（评测链路）

```
E:\AIQuantEval\coco_val2017_500\images\val2017   (500 张源图)
        │
        ├──► WSL: /home/ethan/rknn_workspace/calib_images/   (校准集，已替换为全 500 张)
        │            └── dataset.txt (取前 200 张为绝对路径)
        │
        └──► WSL: precision_analysis/data/images + data/labels  (评估集，494 张/3799 框)
                     └── prepare_coco.py 由 instances_val2017_sub500.json 转换
```

> **风险提示**：校准集与评估集**源自同一批 val2017 图像、高度重叠**。
> 这违反"校准集与测试集必须分开"的原则，会让量化后指标虚高。
> 详见 `05-open-questions.md`。

## 相关记忆

- 环境细节 → `02-environment.md`
- 量化结论 → `03-quantization-findings.md`
- 已知坑 → `04-pitfalls.md`
