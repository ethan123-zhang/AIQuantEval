#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探测所有可用摄像头 index 并保存帧"""
import cv2

for idx in range(5):
    cap = cv2.VideoCapture(idx, cv2.CAP_MSMF)
    if cap.isOpened():
        ok, f = cap.read()
        if ok and f is not None:
            print(f"index {idx}: OPEN+READ OK")
            cv2.imwrite(f"C:/Users/hp/Doubao/chats/2026-10-09/new-chat-1/probe_{idx}.jpg", f)
        else:
            print(f"index {idx}: OPEN OK, 读帧失败")
        cap.release()
print("done")
