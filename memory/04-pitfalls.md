---
type: project
topic: 踩坑清单
last_updated: 2026-10-11
---

# 踩坑清单（已踩过，别重踩）

## 1. `accuracy_analysis` 必须有开发板——模拟器下无解

`rknn.accuracy_analysis(inputs, output_dir, target, device_id)` 的 `target`
**不是"编译目标"，而是"一块通过 adb 连接的物理开发板"**。内部路径：
`rknn_base._runtime_dump` → `init_runtime(target=...)` → `get_board_info`。

- 无板时 `target='rk3588'` 必报 `RuntimeError: no devices/emulators found`。
- `target=None` 只能拿最终输出，**无法逐层**。
- 该接口**没有"模拟器逐层"模式**（`simulator_error` 也是相对板端 golden 而言）。

**无板替代方案**：
1. `hybrid_quantization_step1`（**不带 `proposal=True`**）产出
   `*.quantization.cfg`，含逐层 `ori_min/ori_max/scale/zero_point`。
2. ONNX Runtime 抓逐层中间张量，用该层实际 int8 参数做量化-反量化，
   算 cosine / 归一化欧氏距离 / SNR。

## 2. `hybrid_quantization_step1(proposal=True)` 在 YOLOv8 上崩溃

抛 `KeyError: '/model.22/dfl/Softmax_output_0_sw'`
（`hybrid_proposal.py` 内部映射缺失）。**去掉 `proposal` 参数即可正常产出配置。**

## 3. `load_rknn()` 加载的模型无法在模拟器推理

```
E init_runtime: RKNN model that loaded by 'load_rknn' not support inference
on the simulator, please set 'target' first!
```

→ 混合量化/量化模型**必须在同一进程内**完成
`hybrid_quantization_step2`（或 `build`） → `init_runtime` → `inference`，
不能先导出 `.rknn` 再另开进程加载推理。

## 4. `custom_quantize_layers` 里不能写 Constant 节点

```
E hybrid_quantization_step2: Invalid operands name
  '/model.22/Constant_12_output_0' in custom_quantize_layers!
```

→ 过滤掉名字含 `Constant` 的层再写入。

## 5. 逐层 cosine/SNR 会误导修复方向 ⚠️

**本项目最重要的一条教训。** 逐层指标把检测头 `cv3.*` 标为最敏感，
但保检测头**完全无效**；真正关键的只有输出层 2 层。
**别用逐层误差直接推导"该保哪层"，要用消融实验验证。**

## 6. 中间产物会污染 `scale` 统计

跑 `hybrid_quantization_step1` 生成的 cfg 中，空列表 `[]` 若被朴素解析会变成
字符串 `'[]'`，导致 `float('[]')` 崩溃。解析时要特判空列表。

## 7. Windows 侧：端口 8899 必须只被一个进程占用

Windows 上 `SO_REUSEADDR` 允许**两个进程同时 bind 同一端口**，
旧推流进程不退会导致 WSL 连到旧进程（看到陈旧画面）。

```powershell
netstat -ano | findstr :8899
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
```

## 8. Windows 侧：MSMF 下不要 set FOURCC / FPS

MSMF 自行协商格式并直接输出 BGR，对它 `set(CAP_PROP_FOURCC)` 读回值无意义，
强行 `set(CAP_PROP_FPS)` 可能让流降级成"能读帧但全黑"。**只有 DSHOW 才需显式协商 MJPG。**

（摄像头相关细节详见 `RK3588_Sim/README.md`，此处不重复。）

## 9. 工具/环境类

- `wsl.exe` 的 localhost 代理警告走 stderr，**是噪声不是错误**。
- 本机 PowerShell 工具在**工作区为 WSL UNC 路径**时可能报
  `GetNamedSecurityInfoW failed (Win32 1)` 而无法启动；改用
  `wsl.exe -d Ubuntu-22.04 -- bash -lc "..."` 即可绕开。
- 复杂嵌套引号经 PowerShell → wsl → bash 极易被吞，**改用脚本文件传递**。
