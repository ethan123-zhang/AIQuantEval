# RK3588 摄像头仿真 — Windows 侧推流

用 Windows 原生读摄像头，JPEG 压缩后经 TCP 推给 WSL，WSL 用 rknn-toolkit2
模拟 RK3588 跑 YOLOv8n 推理并显示。

## 为什么不用 usbip 透传

usbip 把 UVC 摄像头透传进 WSL 时，isochronous 流在 vhci 上不可靠，
表现为绿屏/黑帧。改为 Windows 原生采集 + TCP 推流后问题消失。

## 文件

| 文件 | 说明 |
|---|---|
| `stream_cam_fixed.py` | **主程序**。在 Windows 上运行，推流服务端 |
| `cam_probe.py` | 设备探测工具，列出所有摄像头并判断是否有真实画面 |
| `archive/stream_cam_v1.py` | 初版，保留作对照。**有已知 bug，勿用** |
| `archive/scripts_backup/` | 原 scripts 目录全部 20 个文件的完整备份，见下方说明 |

## 已归档 / 已删除的文件

原目录 `C:\Users\hp\Doubao\chats\2026-10-09\new-chat-1\scripts` 已清理，
现只保留 `stream_cam_fixed.py`。其余文件的完整副本存于
`archive/scripts_backup/`（20 个文件，38.7 KB），确认不再需要后可直接删除。

归档中的文件按用途分三类：

- **一次性探测脚本**（结论已写入本 README，无保留价值）：
  `probe_all.py`、`probe_cams.py`、`scan_win_cam.py`、`scan_formats.py`、
  `fmt_test.py`、`yuyv_diag.py`、`cam_test.py`、`check_env.py`
- **WSL 侧脚本**（在 Windows 上跑不了，真正在用的是
  `/home/ethan/rknn_workspace` 里那份）：`rknn_cam_tcp.py`、`yolo_common.py`、
  `rknn_cam_demo.py`、`rknn_build_infer.py`、`rknn_offline_test.py`、
  `diag_quant.py`、`cam_demo_onnx.py`、`onnx_test.py`、`inspect_model.py`、
  `check_rknn.py`
- **废弃版本**：`stream_cam.py`（即 `archive/stream_cam_v1.py`）

> 注意：`rknn_cam_tcp.py` 与 `yolo_common.py` 在删除前未经版本比对。
> 若 WSL 侧那份不是最新，可从 `archive/scripts_backup/` 取回。

## 用法

先探测设备，确认哪个 index 是真实摄像头：

```powershell
python cam_probe.py
```

再启动推流（**必须先启动它，再在 WSL 跑推理**）：

```powershell
python stream_cam_fixed.py --backend msmf --index 1
```

其他模式：

```powershell
python stream_cam_fixed.py --list       # 只探测，不开 TCP
python stream_cam_fixed.py --preview    # 本地预览，不开 TCP
python stream_cam_fixed.py --dump out.jpg   # 存一帧看数据
```

然后进 WSL：

```bash
cd /home/ethan/rknn_workspace
python3 rknn_cam_tcp.py
```

## 排查过的坑（重要，别重复踩）

**1. 本机真实摄像头在 MSMF index 1，不是 DSHOW index 0**

DSHOW 的低 index 会命中"能成功打开但只返回黑帧"的设备，或 Intel 虚拟摄像头
（返回一张 Intel logo 图）。所以自动探测必须 MSMF 优先，并且要跳过空帧
（判据：帧的 `std < 3.0` 视为无内容）。

**2. MSMF 下不要 set(CAP_PROP_FOURCC) 和 CAP_PROP_FPS**

MSMF 走 Media Foundation 自行协商格式，并直接输出解码好的 BGR 帧，
`imencode` 压 JPEG 即可。对它 `set(FOURCC)` 的读回值是无意义的
（实测返回 `0x16`），强行 `set(FPS)` 还可能让流降级成"能读帧但内容全黑"。

**只有 DSHOW 才需要显式协商 MJPG。**

**3. 端口 8899 必须只被一个进程占用**

原版用了 `SO_REUSEADDR`，在 Windows 上它的语义允许**两个进程同时 bind 同一端口**。
结果：旧的推流进程没退出，新的启动后 WSL 连上的其实是旧进程，
于是看到旧进程推的 Intel logo 画面，而新进程的画面完全没被用到。

排查方法：

```powershell
netstat -ano | findstr :8899
taskkill /F /PID <PID>
```

或者一次清干净：

```powershell
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
```

**4. 判断黑屏出在哪一环**

`stream_cam_fixed.py` 推流时每 30 帧打印一次实际画面数据：

```
[stream_cam] 发送第 30 帧: shape=(480, 640, 3) mean=87.3 std=41.2
```

- `mean` 正常（几十到一百多）但 WSL 是黑的 → 问题在 WSL 侧
- `mean=0.0` → 采集侧就是黑的
- 先用 `--preview` 确认 Windows 本地正常，可以一步排除掉一半排查面

## 协议

TCP 8899，客户端连 Windows 默认网关地址。

```
4 字节大端长度 + JPEG 字节流
```

支持客户端断开后重连。

## 另一侧

WSL 侧代码在 `/home/ethan/rknn_workspace`，**未随本目录一起整理**，
因为 `rknn_cam_tcp.py` 里写死了该绝对路径：

```python
ONNX = "/home/ethan/rknn_workspace/model/yolov8n.onnx"
DATASET = "/home/ethan/rknn_workspace/dataset.txt"
```

它依赖 `rknn-toolkit2`，只能在 WSL 里运行。
