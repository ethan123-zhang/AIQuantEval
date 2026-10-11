#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""离线验证: 无 torch 环境下用 rknn-toolkit2 加载 .rknn 并推理"""
import cv2
import numpy as np

from rknn.api import RKNN

from yolo_common import COCO_NAMES, letterbox, postprocess

MODEL = "/home/ethan/rknn_workspace/model/yolov8n.rknn"
IMG = "/home/ethan/rknn_workspace/bus.jpg"

print("== import rknn ok, 开始加载模型 ==")
rknn = RKNN(verbose=False)
ret = rknn.load_rknn(MODEL)
print("load_rknn ret:", ret)
if ret != 0:
    raise SystemExit("load_rknn 失败")

ret = rknn.init_runtime()
print("init_runtime ret:", ret)
if ret != 0:
    raise SystemExit("init_runtime 失败")

img = cv2.imread(IMG)
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
padded, scale, pad_top, pad_left = letterbox(img_rgb, 640)
inp = np.expand_dims(padded, 0).astype(np.uint8)  # NHWC uint8, mean=0/std=255 由 runtime 处理

outputs = rknn.inference(inputs=[inp])
print("outputs:", type(outputs), len(outputs), "shape:", outputs[0].shape)

dets = postprocess(outputs[0], scale, pad_top, pad_left, img.shape[:2], 0.25, 0.45)
print("detections:", len(dets))
for cls_id, score, box in dets:
    label = COCO_NAMES[cls_id] if cls_id < len(COCO_NAMES) else f"cls_{cls_id}"
    print(label, round(score, 3), box)
    x1, y1, x2, y2 = box
    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(img, f"{label} {score:.2f}", (x1, max(y1 - 6, 15)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

cv2.imwrite("/home/ethan/rknn_workspace/rknn_test_out.jpg", img)
print("saved /home/ethan/rknn_workspace/rknn_test_out.jpg")
rknn.release()
