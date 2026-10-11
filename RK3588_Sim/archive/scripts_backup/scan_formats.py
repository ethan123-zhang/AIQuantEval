#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描 MJPG/YUYV x 各分辨率, 找出能出正常画面的组合"""
import cv2
import numpy as np

SIZES = [(640, 480), (640, 360), (1280, 720), (320, 240), (176, 144), (352, 288)]
FOURCCS = ["MJPG", "YUYV"]


def try_open(fourcc, w, h):
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourcc))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 1500)
    cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 1500)
    frames = []
    for _ in range(3):
        ok, f = cap.read()
        if ok:
            frames.append(f)
    cap.release()
    if not frames:
        return None, "读帧失败"
    f = frames[-1]
    b, g, r = f[:, :, 0].mean(), f[:, :, 1].mean(), f[:, :, 2].mean()
    std = f.std()
    green = (g > 100 and r < 40 and b < 40) or (g - r > 90 and g - b > 90)
    verdict = "绿屏" if green else ("正常" if std > 30 else "偏黑/偏平")
    return (b, g, r, std), verdict


for fc in FOURCCS:
    for w, h in SIZES:
        stats, verdict = try_open(fc, w, h)
        if stats is None:
            print(f"{fc} {w}x{h}: {verdict}")
        else:
            b, g, r, std = stats
            print(f"{fc} {w}x{h}: {verdict}  BGR=({b:.0f},{g:.0f},{r:.0f}) std={std:.1f}")
