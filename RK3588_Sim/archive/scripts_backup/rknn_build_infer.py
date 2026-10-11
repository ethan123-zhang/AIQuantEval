#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rknn_build_infer.py — x86 模拟器推理:
load_onnx + build(INT8 量化, 使用现有校准集) + init_runtime(模拟器) + inference
与用户已导出的 yolov8n.rknn 使用相同 ONNX / 预处理 / 量化配置。
"""
import cv2
import numpy as np

from rknn.api import RKNN

from yolo_common import COCO_NAMES, letterbox, postprocess

ONNX = "/home/ethan/rknn_workspace/model/yolov8n.onnx"
DATASET = "/home/ethan/rknn_workspace/dataset.txt"
IMG = "/home/ethan/rknn_workspace/bus.jpg"
TARGET = "rk3588"  # 与 convert_quant.py 一致

rknn = RKNN(verbose=False)

print("== config ==")
ret = rknn.config(
    mean_values=[[0, 0, 0]],
    std_values=[[255, 255, 255]],
    target_platform=TARGET,
)
print("config ret:", ret)

print("== load_onnx ==")
ret = rknn.load_onnx(model=ONNX)
print("load_onnx ret:", ret)
if ret != 0:
    raise SystemExit("load_onnx 失败")

print("== build (INT8 量化) ==")
ret = rknn.build(do_quantization=True, dataset=DATASET)
print("build ret:", ret)
if ret != 0:
    raise SystemExit("build 失败")

print("== init_runtime (模拟器) ==")
ret = rknn.init_runtime()
print("init_runtime ret:", ret)
if ret != 0:
    raise SystemExit("init_runtime 失败")

img = cv2.imread(IMG)
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
padded, scale, pad_top, pad_left = letterbox(img_rgb, 640)
inp = np.expand_dims(padded, 0).astype(np.uint8)

outputs = rknn.inference(inputs=[inp])
print("outputs shape:", outputs[0].shape)

dets = postprocess(outputs[0], scale, pad_top, pad_left, img.shape[:2], 0.25, 0.45)
print("detections:", len(dets))
for cls_id, score, box in dets:
    label = COCO_NAMES[cls_id] if cls_id < len(COCO_NAMES) else f"cls_{cls_id}"
    print(label, round(score, 3), box)
    x1, y1, x2, y2 = box
    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(img, f"{label} {score:.2f}", (x1, max(y1 - 6, 15)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

cv2.imwrite("/home/ethan/rknn_workspace/rknn_build_out.jpg", img)
print("saved /home/ethan/rknn_workspace/rknn_build_out.jpg")
rknn.release()
