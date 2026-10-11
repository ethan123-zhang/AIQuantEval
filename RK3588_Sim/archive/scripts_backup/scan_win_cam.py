#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描 Windows 摄像头: 后端(DSHOW/MSMF) x index(0-4)"""
import cv2

for backend_name, backend in [("DSHOW", cv2.CAP_DSHOW), ("MSMF", cv2.CAP_MSMF)]:
    for idx in range(5):
        cap = cv2.VideoCapture(idx, backend)
        if cap.isOpened():
            ok, frame = cap.read()
            if ok and frame is not None:
                b, g, r = (frame[:, :, 0].mean(), frame[:, :, 1].mean(), frame[:, :, 2].mean())
                print(f"{backend_name} index {idx}: OPEN+READ OK  BGR=({b:.1f},{g:.1f},{r:.1f})")
                cv2.imwrite(f"C:/Users/hp/Doubao/chats/2026-10-09/new-chat-1/win_cam_{backend_name}_{idx}.jpg", frame)
            else:
                print(f"{backend_name} index {idx}: OPEN OK, 读帧失败")
            cap.release()
        else:
            cap.release()
print("扫描完成")
