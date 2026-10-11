#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 MJPG vs YUYV 哪种格式能正常出画面"""
import cv2
import numpy as np


def test_fourcc(name, fourcc):
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    if fourcc:
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourcc))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    ok, frame = cap.read()
    if not ok:
        print(f"{name}: 读帧失败")
        cap.release()
        return
    b, g, r = frame[:, :, 0].mean(), frame[:, :, 1].mean(), frame[:, :, 2].mean()
    green = g > 200 and b < 50 and r < 50
    print(f"{name}: ok, shape={frame.shape}, BGR均值=({b:.1f},{g:.1f},{r:.1f}), 绿屏={green}")
    if not green:
        cv2.imwrite(f"/home/ethan/rknn_workspace/fmt_test_{name}.jpg", frame)
    cap.release()


test_fourcc("mjpg", "MJPG")
test_fourcc("yuyv", "YUYV")
