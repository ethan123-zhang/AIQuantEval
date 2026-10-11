#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断: int8 输出数值分布 + float 构建的检测对比"""
import cv2
import numpy as np

from rknn.api import RKNN

from yolo_common import COCO_NAMES, letterbox, postprocess

ONNX = "/home/ethan/rknn_workspace/model/yolov8n.onnx"
IMG = "/home/ethan/rknn_workspace/bus.jpg"


def run(quant):
    print(f"\n===== build(quantize={quant}) =====")
    rknn = RKNN(verbose=False)
    rknn.config(mean_values=[[0, 0, 0]], std_values=[[255, 255, 255]], target_platform="rk3588")
    rknn.load_onnx(model=ONNX)
    if quant:
        rknn.build(do_quantization=True, dataset="/home/ethan/rknn_workspace/dataset.txt")
    else:
        rknn.build(do_quantization=False)
    rknn.init_runtime()

    img = cv2.imread(IMG)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    padded, scale, pad_top, pad_left = letterbox(img_rgb, 640)
    inp = np.expand_dims(padded, 0).astype(np.uint8)
    outputs = rknn.inference(inputs=[inp])
    out = np.array(outputs[0])
    print("dtype:", out.dtype, "shape:", out.shape)
    print("min/max/mean:", out.min(), out.max(), out.mean())
    print("sample[0,:6]:", out.reshape(84, -1)[:4, :6].tolist())

    # 输出是 logits(0~600+), 直接送后处理(内部做 sigmoid)
    dets = postprocess(outputs[0], scale, pad_top, pad_left, img.shape[:2], 0.25, 0.45)
    print("detections:",
          [(COCO_NAMES[c] if c < len(COCO_NAMES) else c, round(s, 3)) for c, s, _ in dets])
    rknn.release()


run(True)
run(False)
