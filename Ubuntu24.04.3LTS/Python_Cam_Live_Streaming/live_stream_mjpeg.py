"""
Live stream MJPEG — streaming saja, tanpa rekaman ke file.

Jalankan di Raspberry Pi / Ubuntu 24.04, lalu buka dari LAN:
  http://<IP-raspi>:8080/
Contoh IP: http://10.45.2.103:8080/
"""
from __future__ import annotations

import argparse
import sys

import cv2
from flask import Flask, Response

from v4l2_camera import open_video_capture

# Raspberry Pi / Ubuntu: indeks 0 untuk webcam USB pertama (/dev/video0).
CAMERA_INDEX = 0
HOST = "0.0.0.0"
PORT = 8080
JPEG_QUALITY = 80
MIRROR_HORIZONTAL = True

app = Flask(__name__)
_camera_index = CAMERA_INDEX


def frame_generator():
    cap = open_video_capture(_camera_index)
    if not cap.isOpened():
        raise RuntimeError(
            f"Kamera tidak terbuka (index {_camera_index}). "
            "Cek: v4l2-ctl --list-devices"
        )
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            if MIRROR_HORIZONTAL:
                frame = cv2.flip(frame, 1)
            ok, buf = cv2.imencode(
                ".jpg",
                frame,
                [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY],
            )
            if not ok:
                continue
            chunk = buf.tobytes()
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + chunk + b"\r\n"
            )
    finally:
        cap.release()


@app.route("/")
def index():
    return """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Live Cam</title>
  <style>
    body { margin: 0; background: #111; color: #eee; font-family: sans-serif; text-align: center; }
    h1 { font-size: 1.25rem; font-weight: 600; padding: 1rem; margin: 0; }
    img { max-width: 100%; height: auto; display: block; margin: 0 auto; }
    p { font-size: 0.85rem; color: #888; padding-bottom: 1rem; }
  </style>
</head>
<body>
  <h1>Live stream kamera</h1>
  <img src="/video_feed" alt="Live stream"/>
  <p>Streaming saja — tidak ada rekaman ke disk.</p>
</body>
</html>"""


@app.route("/video_feed")
def video_feed():
    return Response(
        frame_generator(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Live stream MJPEG dari webcam (tanpa rekaman)."
    )
    parser.add_argument(
        "--host",
        default=HOST,
        help=f"Alamat bind (default: {HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=PORT,
        help=f"Port HTTP (default: {PORT})",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=CAMERA_INDEX,
        help=f"Indeks kamera V4L2 (default: {CAMERA_INDEX})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    global _camera_index
    args = parse_args(argv)
    _camera_index = args.camera

    print("Live stream MJPEG — tidak merekam video ke file.")
    print(f"  Kamera index : {args.camera}")
    print(f"  Listen       : http://{args.host}:{args.port}/")
    print("  Dari LAN     : http://<IP-perangkat>:{}/".format(args.port))
    print("  Contoh       : http://10.45.2.103:{}/".format(args.port))
    print("  Hentikan     : Ctrl+C")
    print()

    try:
        app.run(host=args.host, port=args.port, threaded=True, debug=False)
    except OSError as exc:
        print(f"Gagal bind {args.host}:{args.port} — {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
