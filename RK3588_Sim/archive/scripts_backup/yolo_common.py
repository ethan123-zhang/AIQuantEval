#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""yolo_common.py — YOLOv8 通用工具: COCO 标签, letterbox, 后处理(NMS)"""

import cv2
import numpy as np

INPUT_SIZE = 640
CONF_THRES = 0.25
NMS_THRES = 0.45

COCO_NAMES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
    "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
    "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
    "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
    "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
    "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
    "toothbrush",
]


def letterbox(img, size=INPUT_SIZE, pad_value=114):
    """等比缩放 + 灰色填充, 输出 size x size, 返回 (填充图, scale, pad_top, pad_left)"""
    h, w = img.shape[:2]
    scale = min(size / h, size / w)
    nh, nw = int(round(h * scale)), int(round(w * scale))
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    pad_top = (size - nh) // 2
    pad_bottom = size - nh - pad_top
    pad_left = (size - nw) // 2
    pad_right = size - nw - pad_left
    padded = cv2.copyMakeBorder(
        resized, pad_top, pad_bottom, pad_left, pad_right,
        cv2.BORDER_CONSTANT, value=(pad_value, pad_value, pad_value),
    )
    return padded, scale, pad_top, pad_left


def postprocess(output, scale, pad_top, pad_left, orig_shape, conf_thres=CONF_THRES,
                nms_thres=NMS_THRES):
    """
    output: (1, 4+nc, 8400) 的 YOLOv8 输出
    过滤低置信度 -> xywh 转 xyxy -> 映射回原图坐标 -> NMS
    返回 [(class_id, score, (x1,y1,x2,y2)), ...]
    """
    ch = output.shape[1] if len(output.shape) == 3 else output.shape[0]
    data = np.array(output).reshape(ch, -1).T
    xywh = data[:, :4]
    cls_probs = data[:, 4:]
    scores = cls_probs.max(axis=1)
    cls_ids = cls_probs.argmax(axis=1)

    keep = scores >= conf_thres
    xywh, scores, cls_ids = xywh[keep], scores[keep], cls_ids[keep]
    if len(scores) == 0:
        return []

    x1 = xywh[:, 0] - xywh[:, 2] / 2
    y1 = xywh[:, 1] - xywh[:, 3] / 2
    x2 = xywh[:, 0] + xywh[:, 2] / 2
    y2 = xywh[:, 1] + xywh[:, 3] / 2
    boxes = np.stack([x1, y1, x2, y2], axis=1)

    boxes = (boxes - np.array([pad_left, pad_top, pad_left, pad_top])) / scale
    boxes[:, 0::2] = np.clip(boxes[:, 0::2], 0, orig_shape[1])
    boxes[:, 1::2] = np.clip(boxes[:, 1::2], 0, orig_shape[0])

    indices = cv2.dnn.NMSBoxes(boxes.tolist(), scores.tolist(), conf_thres, nms_thres)
    if len(indices) == 0:
        return []
    indices = np.array(indices).flatten()
    results = []
    for i in indices:
        x1i, y1i, x2i, y2i = boxes[i].astype(int)
        results.append((int(cls_ids[i]), float(scores[i]), (x1i, y1i, x2i, y2i)))
    return results
