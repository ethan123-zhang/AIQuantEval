#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全面探测 DSHOW/MSMF 所有 index, 抓帧保存"""
import cv2
import time

for name, be in [("DSHOW", cv2.CAP_DSHOW), ("MSMF", cv2.CAP_MSMF)]:
    for idx in range(6):
        cap = cv2.VideoCapture(idx, be)
        time.sleep(0.2)
        if cap.isOpened():
            ok, f = cap.read()
            if ok and f is not None:
                print(f"[OK] {name} index {idx}")
                cv2.imwrite(f"C:/Users/hp/Doubao/chats/2026-10-09/new-chat-1/probe_{name}_{idx}.jpg", f)
            else:
                print(f"[FAIL-RD] {name} index {idx} 读帧失败")
            cap.release()
        else:
            print(f"[FAIL-OP] {name} index {idx} 打开失败")
        time.sleep(0.2)
print("done")
