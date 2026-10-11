#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 onnxruntime 在 CPU 上跑 yolov8n.onnx, 验证后处理管线"""
import sys

import cv2
import numpy as np
import onnxruntime as ort

from yolo_common import COCO_NAMES, letterbox, postprocess

img_path = sys.argv[1] if len(sys.argv) > 1 else "/home/ethan/rknn_workspace/bus.jpg"
out_path = sys.argv[2] if len(sys.argv) > 2 else "/home/ethan/rknn_workspace/onnx_test_out.jpg"

sess = ort.InferenceSession(
    "/home/ethan/rknn_workspace/model/yolov8n.onnx", providers=["CPUExecutionProvider"]
)
img = cv2.imread(img_path)
if img is None:
    raise SystemExit("cannot read image: " + img_path)

img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
padded, scale, pad_top, pad_left = letterbox(img_rgb, 640)
inp = np.expand_dims(padded, 0).astype(np.float32) / 255.0
inp = inp.transpose(0, 3, 1, 2)  # NHWC -> NCHW, ONNX 输入为 [1,3,640,640]
out = sess.run(None, {sess.get_inputs()[0].name: inp})[0]

dets = postprocess(out, scale, pad_top, pad_left, img.shape[:2], 0.25, 0.45)
for cls_id, score, (x1, y1, x2, y2) in dets:
    label = COCO_NAMES[cls_id] if cls_id < len(COCO_NAMES) else f"cls_{cls_id}"
    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(img, f"{label} {score:.2f}", (x1, max(y1 - 6, 15)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

cv2.imwrite(out_path, img)
print("detections:", [(COCO_NAMES[c] if c < len(COCO_NAMES) else c, round(s, 3), b) for c, s, b in dets])
print("saved:", out_path)
