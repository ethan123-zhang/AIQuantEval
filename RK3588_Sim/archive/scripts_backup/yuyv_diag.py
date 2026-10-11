#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断: usbip 透传下 YUYV 原始数据是否正常"""
import cv2
import numpy as np

# 1) 拿原始 YUYV 字节(不转 RGB)
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'YUYV'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
ok, raw = cap.read()
cap.release()
print("raw ok:", ok, "shape:", None if raw is None else raw.shape,
      "dtype:", None if raw is None else raw.dtype)
if raw is None:
    raise SystemExit("raw None")

# raw 可能是 2通道 YUYV 交错, 或 3通道; 统一下采样
if raw.ndim == 3 and raw.shape[2] == 2:
    yuyv = raw
else:
    yuyv = raw.reshape(raw.shape[0], raw.shape[1], 1) if raw.ndim == 2 else raw

h, w = yuyv.shape[:2]
# 展平处理
flat = yuyv.reshape(-1).astype(np.uint8) if yuyv.dtype == np.uint8 else yuyv.reshape(-1)
n = flat.size
print("flat bytes:", n, "期望 YUYV 640x480 =", 640 * 480 * 2)

# 用前 w*h*2 字节手动 YUYV->BGR
need = w * h * 2
data = flat[:need]
Y = data[0::2].astype(np.float32)
U = data[1::2].astype(np.float32) - 128.0
# YUYV 布局: Y0 U0 Y1 V0 Y2 U1 Y3 V1 ... U/V 共享
# 简化: 偶数像素用 (Y0,U0,V0), 奇数像素用 (Y1,U0,V0)
Y0 = data[0::4].astype(np.float32)
U0 = data[1::4].astype(np.float32) - 128.0
Y1 = data[2::4].astype(np.float32)
V0 = data[3::4].astype(np.float32) - 128.0

def yuv2bgr(y, u, v):
    r = np.clip(y + 1.402 * v, 0, 255)
    g = np.clip(y - 0.344136 * u - 0.714136 * v, 0, 255)
    b = np.clip(y + 1.772 * u, 0, 255)
    return r, g, b

r0, g0, b0 = yuv2bgr(Y0, U0, V0)
r1, g1, b1 = yuv2bgr(Y1, U0, V0)
img = np.empty((h, w, 3), np.uint8)
img[:, 0::2, 0] = b0.reshape(h, w // 2)
img[:, 0::2, 1] = g0.reshape(h, w // 2)
img[:, 0::2, 2] = r0.reshape(h, w // 2)
img[:, 1::2, 0] = b1.reshape(h, w // 2)
img[:, 1::2, 1] = g1.reshape(h, w // 2)
img[:, 1::2, 2] = r1.reshape(h, w // 2)

print("手动转换 BGR 均值:", img[:, :, 0].mean(), img[:, :, 1].mean(), img[:, :, 2].mean())
print("标准差:", img.std(axis=(0, 1)))
cv2.imwrite("/home/ethan/rknn_workspace/yuyv_manual.jpg", img)

# 数据熵检查: 如果是垃圾/恒定数据, 值分布会很窄
print("Y0 分布: min/max/mean/std =", Y0.min(), Y0.max(), Y0.mean(), Y0.std())
