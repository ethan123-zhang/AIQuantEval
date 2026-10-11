#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rknn_cam_tcp.py  (WSL 侧运行)
从 Windows 主机 TCP 接收摄像头帧(JPEG) -> RKNN(YOLOv8n, 模拟鲁班猫 RK3588) 推理 -> 窗口显示。

原因: usbip 透传 UVC 摄像头时 isochronous 流不可靠(vhci 限制, 画面绿屏/黑帧),
      因此改为 Windows 原生读摄像头 + TCP 推流, WSL 只做推理与显示。
协议: 4字节大端长度 + JPEG, 连 Windows 主机(默认网关) 8899 端口。
按 q 或 ESC 退出。
"""
import os
import socket
import struct
import subprocess
import time

import cv2
import numpy as np
from rknn.api import RKNN

from yolo_common import (CONF_THRES, INPUT_SIZE, NMS_THRES, COCO_NAMES,
                         letterbox, postprocess)

ONNX = "/home/ethan/rknn_workspace/model/yolov8n.onnx"
DATASET = "/home/ethan/rknn_workspace/dataset.txt"
TARGET = "rk3588"
PORT = 8899


def win_ip():
    out = subprocess.check_output(
        "ip route | awk '/default/ {print $3; exit}'", shell=True, text=True)
    return out.strip()


def build_rknn():
    print(f"构建 RKNN 模型 (模拟 鲁班猫 RK3588 板卡环境: target_platform={TARGET}, 由 rknn-toolkit2 模拟器执行)...")
    rknn = RKNN(verbose=False)
    ret = rknn.config(mean_values=[[0, 0, 0]], std_values=[[255, 255, 255]],
                      target_platform=TARGET)
    if ret != 0:
        raise RuntimeError("config 失败")
    ret = rknn.load_onnx(model=ONNX)
    if ret != 0:
        raise RuntimeError("load_onnx 失败")

    quant = os.environ.get("RKNN_QUANT", "0") == "1"  # 默认 float: INT8 会量化检测头输出导致检测失效
    if quant:
        print("INT8 量化构建中 (使用校准集 dataset.txt), 可能需要几分钟...")
        ret = rknn.build(do_quantization=True, dataset=DATASET)
    else:
        print("float 构建中...")
        ret = rknn.build(do_quantization=False)
    if ret != 0:
        raise RuntimeError("build 失败")

    ret = rknn.init_runtime()
    if ret != 0:
        raise RuntimeError("init_runtime 失败")
    print("RKNN 模型就绪 (模拟器)")
    return rknn


def recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("连接断开")
        buf += chunk
    return buf


def main():
    rknn = build_rknn()
    host = win_ip()
    print(f"连接 Windows 推流端 {host}:{PORT} ...")
    while True:
        try:
            sock = socket.create_connection((host, PORT), timeout=10)
            print("TCP 摄像头流已连接, 开始推理 (按 q 或 ESC 退出)")
            break
        except OSError as e:
            print(f"连接失败({e}), 5 秒后重试...")
            time.sleep(5)

    win = "RKNN(RK3588模拟) YOLOv8 Camera"
    last = time.time()
    while True:
        try:
            size = struct.unpack(">I", recv_exact(sock, 4))[0]
            data = recv_exact(sock, size)
        except ConnectionError:
            print("推流端断开, 5 秒后重连...")
            time.sleep(5)
            while True:
                try:
                    sock = socket.create_connection((host, PORT), timeout=10)
                    print("已重新连接推流端")
                    break
                except OSError as e:
                    print(f"重连失败({e}), 5 秒后重试...")
                    time.sleep(5)
            continue
        frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            continue

        t0 = time.time()
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        padded, scale, pad_top, pad_left = letterbox(img_rgb, INPUT_SIZE)
        input_img = np.expand_dims(padded, 0).astype(np.uint8)

        outputs = rknn.inference(inputs=[input_img])
        dets = postprocess(outputs[0], scale, pad_top, pad_left,
                           frame.shape[:2], CONF_THRES, NMS_THRES)

        for cls_id, score, (x1, y1, x2, y2) in dets:
            label = COCO_NAMES[cls_id] if cls_id < len(COCO_NAMES) else f"cls_{cls_id}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            text = f"{label} {score:.2f}"
            cv2.putText(frame, text, (x1, max(y1 - 6, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

        fps = 1.0 / max(time.time() - t0, 1e-6)
        cv2.putText(frame, f"FPS: {fps:.1f}  dets: {len(dets)}  (TCP-Cam)",
                    (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow(win, frame)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break

    cv2.destroyAllWindows()
    rknn.release()
    print("已退出")


if __name__ == "__main__":
    main()
