#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rknn_cam_demo.py
读取摄像头 -> RKNN(YOLOv8n, 会话内重建) 推理 -> 目标框/标签叠加 -> 窗口显示

说明:
  - x86 WSL 上 rknn-toolkit2 不允许直接 load_rknn 后用模拟器推理(.rknn 供 RK3588 真机用)。
    本脚本按 convert_quant.py 的相同配置(mean=0/std=255/rk3588/INT8 量化校准集)在会话内
    load_onnx + build 重建同一模型, 再进入模拟器推理 —— 推理内容与 yolov8n.rknn 一致。
  - 按 q 或 ESC 退出
  - 类别: COCO 80 类 (模型输出 [1,84,8400])
"""

import os
import time

import cv2
import numpy as np
from rknn.api import RKNN

from yolo_common import (CONF_THRES, INPUT_SIZE, NMS_THRES, COCO_NAMES,
                         letterbox, postprocess)

ONNX = "/home/ethan/rknn_workspace/model/yolov8n.onnx"
DATASET = "/home/ethan/rknn_workspace/dataset.txt"
TARGET = "rk3588"
CAM_ID = 0


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


def main():
    rknn = build_rknn()

    cap = cv2.VideoCapture(CAM_ID, cv2.CAP_V4L2)
    if not cap.isOpened():
        cap = cv2.VideoCapture(CAM_ID)
    if not cap.isOpened():
        raise RuntimeError("无法打开摄像头")

    print("摄像头已打开, 开始推理 (按 q 或 ESC 退出)")
    win = "RKNN(RK3588模拟) YOLOv8 Camera"
    while True:
        ok, frame = cap.read()
        if not ok:
            continue

        t0 = time.time()
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        padded, scale, pad_top, pad_left = letterbox(img_rgb, INPUT_SIZE)
        input_img = np.expand_dims(padded, 0).astype(np.uint8)  # NHWC uint8

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
        cv2.putText(frame, f"FPS: {fps:.1f}  dets: {len(dets)}",
                    (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow(win, frame)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break

    cap.release()
    cv2.destroyAllWindows()
    rknn.release()
    print("已退出")


if __name__ == "__main__":
    main()
