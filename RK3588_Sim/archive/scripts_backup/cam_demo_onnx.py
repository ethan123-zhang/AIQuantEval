#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cam_demo_onnx.py — 临时可运行版本: onnxruntime(CPU) + yolov8n.onnx
与 rknn_cam_demo.py 共用 yolo_common.py, 画面显示方式一致。
按 q 或 ESC 退出。
"""
import time

import cv2
import numpy as np
import onnxruntime as ort

from yolo_common import (CONF_THRES, INPUT_SIZE, NMS_THRES, COCO_NAMES,
                         letterbox, postprocess)

MODEL = "/home/ethan/rknn_workspace/model/yolov8n.onnx"
CAM_ID = 0


def main():
    print("加载 ONNX 模型:", MODEL)
    sess = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])
    in_name = sess.get_inputs()[0].name

    cap = cv2.VideoCapture(CAM_ID, cv2.CAP_V4L2)
    if not cap.isOpened():
        cap = cv2.VideoCapture(CAM_ID)
    if not cap.isOpened():
        raise RuntimeError("无法打开摄像头")

    print("摄像头已打开, 开始推理 (按 q 或 ESC 退出)")
    win = "YOLOv8 Camera (onnxruntime)"
    while True:
        ok, frame = cap.read()
        if not ok:
            continue

        t0 = time.time()
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        padded, scale, pad_top, pad_left = letterbox(img_rgb, INPUT_SIZE)
        inp = (np.expand_dims(padded, 0).astype(np.float32) / 255.0).transpose(0, 3, 1, 2)
        out = sess.run(None, {in_name: inp})[0]

        dets = postprocess(out, scale, pad_top, pad_left,
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
    print("已退出")


if __name__ == "__main__":
    main()
