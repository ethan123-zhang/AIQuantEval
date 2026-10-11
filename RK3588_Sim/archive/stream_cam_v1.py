#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stream_cam.py  (Windows 侧运行)
读取摄像头(默认外接 USB 摄像头), JPEG 压缩后通过 TCP(localhost:8899) 推流给 WSL。
协议: 4字节大端长度 + JPEG 字节流, 支持客户端断开后重连。

用法:
  python stream_cam.py                 # 自动探测(DSHOW 优先)
  python stream_cam.py --backend dshow --index 2   # 指定后端与 index
"""
import argparse
import socket
import struct
import sys
import time

import cv2

PORT = 8899


def try_open(backend, idx):
    cap = cv2.VideoCapture(idx, backend)
    if cap.isOpened():
        ok, f = cap.read()
        if ok and f is not None:
            return cap, f.shape
        cap.release()
    return None, None


def open_cam(args):
    """按参数/自动探测打开摄像头"""
    if args.backend != "auto" and args.index >= 0:
        be = cv2.CAP_DSHOW if args.backend == "dshow" else cv2.CAP_MSMF
        cap, shape = try_open(be, args.index)
        if cap:
            print(f"[stream_cam] 使用 {args.backend} index={args.index} shape={shape}")
            return cap
        print(f"[stream_cam] 指定的 {args.backend} index={args.index} 打不开, 回退自动探测")

    # 自动探测: DSHOW 优先, 各 index 逐个尝试
    for be_name, be in [("DSHOW", cv2.CAP_DSHOW), ("MSMF", cv2.CAP_MSMF)]:
        for idx in range(6):
            cap, shape = try_open(be, idx)
            if cap:
                print(f"[stream_cam] 自动探测到: {be_name} index={idx} shape={shape}")
                return cap
    raise RuntimeError("未找到可用摄像头")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["auto", "dshow", "msmf"], default="auto")
    parser.add_argument("--index", type=int, default=-1)
    args = parser.parse_args()

    cap = open_cam(args)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", PORT))
    srv.listen(1)
    print(f"[stream_cam] 摄像头已打开, TCP 推流监听 :{PORT}")

    while True:
        conn, addr = srv.accept()
        print(f"[stream_cam] 客户端接入: {addr}")
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    time.sleep(0.02)
                    continue
                enc = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])[1]
                data = enc.tobytes()
                conn.sendall(struct.pack(">I", len(data)) + data)
        except (ConnectionResetError, BrokenPipeError, OSError):
            print("[stream_cam] 客户端断开, 等待重连")
            conn.close()


if __name__ == "__main__":
    main()
