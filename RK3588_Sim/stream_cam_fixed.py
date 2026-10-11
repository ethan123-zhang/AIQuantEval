#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stream_cam_fixed.py  (Windows 侧运行)
读取摄像头, JPEG 压缩后通过 TCP 推流给 WSL。
协议: 4字节大端长度 + JPEG 字节流, 支持客户端断开后重连。

用法:
  python stream_cam_fixed.py --list                    # 只探测设备
  python stream_cam_fixed.py --backend msmf --index 1  # 推流
  python stream_cam_fixed.py --preview                 # 本地预览(不开 TCP), 确认画面
"""
import argparse
import socket
import struct
import sys
import time

import cv2

PORT = 8899
WIDTH, HEIGHT = 640, 480


def open_device(backend, idx, verbose=True):
    """打开设备。注意: MSMF 下不要 set FOURCC/FPS。

    MSMF 通过 Media Foundation 自行协商格式, 并由 OpenCV 输出已解码的 BGR 帧。
    对它 set(CAP_PROP_FOURCC) 的读回值是无意义的(实测返回 0x16), 强行 set
    FPS 还可能让流降级成"能读帧但内容全黑"。因此 MSMF 只设分辨率, 且失败也无妨。
    DSHOW 才需要显式协商 MJPG。
    """
    cap = cv2.VideoCapture(idx, backend)
    if not cap.isOpened():
        return None

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    if backend == cv2.CAP_DSHOW:
        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        ok = cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        if verbose:
            got = int(cap.get(cv2.CAP_PROP_FOURCC))
            got_s = "".join(chr((got >> (8 * i)) & 0xFF) for i in range(4))
            print(f"[cam] DSHOW index={idx} set(MJPG)={ok} 读回={got_s!r}")

    if verbose:
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"[cam] {backend} index={idx} 实际 {w}x{h}")
    return cap


def frame_std(cap, n=3):
    """连读 n 帧取最后一帧的 std; 同时返回帧本身。用于判断是否黑帧。"""
    last = None
    for _ in range(n):
        ok, f = cap.read()
        if not ok or f is None:
            return None, None
        last = f
    return last, float(last.std())


def probe_all():
    real = None
    for be_name, be in [("MSMF", cv2.CAP_MSMF), ("DSHOW", cv2.CAP_DSHOW)]:
        for idx in range(6):
            cap = open_device(be, idx, verbose=False)
            if cap is None:
                print(f"[probe] {be_name} index={idx}: 打不开")
                continue
            # 先丢掉前几帧, 很多摄像头刚启动时会吐黑帧
            for _ in range(5):
                cap.read()
            f, std = frame_std(cap, 3)
            if f is None:
                print(f"[probe] {be_name} index={idx}: OPEN OK 但读帧失败")
                cap.release()
                continue
            blank = std < 3.0
            print(f"[probe] {be_name} index={idx}: OK shape={f.shape} "
                  f"std={std:.2f} {'(空帧)' if blank else '(有画面)'}")
            if not blank and real is None:
                real = (be_name, idx, cap)
            else:
                cap.release()
    if real:
        be_name, idx, cap = real
        print(f"\n[probe] ==> 建议: --backend {be_name.lower()} --index {idx}")
        cap.release()
    else:
        print("\n[probe] ==> 未找到有画面的设备")


def preview(backend, idx):
    """本地窗口预览, 确认 Windows 侧画面本身是否正常"""
    be = cv2.CAP_MSMF if backend == "msmf" else cv2.CAP_DSHOW
    cap = open_device(be, idx)
    if cap is None:
        print("[preview] 打不开")
        return
    print("[preview] 按 q 退出。如果这里是黑的, 黑屏来自摄像头/Windows, 与 TCP 无关。")
    while True:
        ok, f = cap.read()
        if not ok:
            continue
        cv2.putText(f, f"std={f.std():.1f}", (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.imshow("win preview", f)
        if (cv2.waitKey(1) & 0xFF) in (ord("q"), 27):
            break
    cv2.destroyAllWindows()
    cap.release()


def open_cam(args):
    if args.backend != "auto" and args.index >= 0:
        be = cv2.CAP_MSMF if args.backend == "msmf" else cv2.CAP_DSHOW
        cap = open_device(be, args.index)
        if cap is not None:
            return cap
        print(f"[stream_cam] 指定的 {args.backend} index={args.index} 打不开, 回退自动探测")

    fallback = None
    for be_name, be in [("MSMF", cv2.CAP_MSMF), ("DSHOW", cv2.CAP_DSHOW)]:
        for idx in range(6):
            cap = open_device(be, idx, verbose=False)
            if cap is None:
                continue
            for _ in range(5):      # 丢弃启动阶段的黑帧
                cap.read()
            f, std = frame_std(cap, 3)
            if f is None:
                cap.release()
                continue
            if std >= 3.0:
                print(f"[stream_cam] 自动探测到: {be_name} index={idx} std={std:.2f}")
                if fallback is not None:
                    fallback[0].release()
                return cap
            if fallback is None:
                fallback = (cap, be_name, idx)
            else:
                cap.release()

    if fallback is not None:
        cap, be_name, idx = fallback
        print(f"[stream_cam] 警告: 只有空帧设备, 仍用 {be_name} index={idx}")
        return cap
    raise RuntimeError("未找到可用摄像头")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--backend", choices=["auto", "dshow", "msmf"], default="auto")
    p.add_argument("--index", type=int, default=-1)
    p.add_argument("--list", action="store_true", help="只探测设备")
    p.add_argument("--preview", action="store_true", help="本地预览, 不开 TCP")
    p.add_argument("--dump", metavar="PATH", help="存一帧 JPEG 到文件后退出")
    args = p.parse_args()

    if args.list:
        probe_all()
        return

    if args.preview:
        preview("msmf" if args.backend == "auto" else args.backend,
                1 if args.index < 0 else args.index)
        return

    if args.dump:
        back = "msmf" if args.backend == "auto" else args.backend
        be = cv2.CAP_MSMF if back == "msmf" else cv2.CAP_DSHOW
        i = 1 if args.index < 0 else args.index
        cap = open_device(be, i)
        if cap is None:
            print("[dump] 打不开")
            return
        for _ in range(10):
            cap.read()
        f, std = frame_std(cap, 3)
        if f is None:
            print("[dump] 读帧失败")
            return
        cv2.imwrite(args.dump, f)
        print(f"[dump] 已存 {args.dump}  shape={f.shape}  std={std:.2f} "
              f"mean={f.mean():.1f}")
        cap.release()
        return

    cap = open_cam(args)

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", PORT))
    srv.listen(1)
    print(f"[stream_cam] TCP 推流监听 :{PORT}")

    n = 0
    while True:
        conn, addr = srv.accept()
        print(f"[stream_cam] 客户端接入: {addr}")
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    time.sleep(0.02)
                    continue
                if n % 30 == 0:      # 每 30 帧报一次实际画面亮度, 便于定位黑帧
                    print(f"[stream_cam] 发送第 {n} 帧: shape={frame.shape} "
                          f"mean={frame.mean():.1f} std={frame.std():.1f}")
                n += 1
                enc = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])[1]
                data = enc.tobytes()
                conn.sendall(struct.pack(">I", len(data)) + data)
        except (ConnectionResetError, BrokenPipeError, OSError):
            print("[stream_cam] 客户端断开, 等待重连")
            conn.close()


if __name__ == "__main__":
    main()
