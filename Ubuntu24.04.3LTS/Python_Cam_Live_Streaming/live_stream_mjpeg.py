"""
Live stream MJPEG — streaming saja, tanpa rekaman ke file.

Jalankan di Raspberry Pi / Ubuntu 24.04, lalu buka dari LAN:
  http://<IP-raspi>:8080/
Contoh IP: http://10.45.2.103:8080/
"""
from __future__ import annotations

import argparse
import os
import sys
import threading
import time

import cv2
from flask import Flask, Response, jsonify

from motion_detector import MotionDetector, scaled_min_motion_area
from telegram_notifier import TelegramNotifier, load_env_file
from v4l2_camera import open_video_capture

# Raspberry Pi / Ubuntu: indeks 0 untuk webcam USB pertama (/dev/video0).
CAMERA_INDEX = 0
HOST = "0.0.0.0"
PORT = 8080
FRAME_WIDTH = 640
FRAME_HEIGHT = 320
JPEG_QUALITY = 50
TARGET_FPS = 15
MIRROR_HORIZONTAL = True
MOTION_DETECTION = True

app = Flask(__name__)


class MjpegBroadcaster:
    """Satu thread baca kamera; semua klien dapat frame JPEG terbaru."""

    def __init__(
        self,
        camera_index: int,
        width: int,
        height: int,
        quality: int,
        mirror: bool,
        target_fps: float,
        motion_enabled: bool,
        min_motion_area: int | None,
        telegram: TelegramNotifier | None = None,
    ) -> None:
        self._camera_index = camera_index
        self._width = width
        self._height = height
        self._quality = quality
        self._mirror = mirror
        self._target_fps = target_fps
        self.motion_enabled = motion_enabled
        area = min_motion_area or scaled_min_motion_area(width, height)
        self._motion = MotionDetector(area) if motion_enabled else None
        self._telegram = telegram if motion_enabled else None
        self._lock = threading.Lock()
        self._latest_chunk: bytes | None = None
        self.motion_detected = False
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def _capture_loop(self) -> None:
        cap = open_video_capture(self._camera_index, self._width, self._height)
        if not cap.isOpened():
            raise RuntimeError(
                f"Kamera tidak terbuka (index {self._camera_index}). "
                "Cek: v4l2-ctl --list-devices"
            )

        min_interval = 1.0 / self._target_fps if self._target_fps > 0 else 0.0
        try:
            while not self._stop.is_set():
                loop_start = time.monotonic()

                # Buang frame lama di buffer driver agar tidak terasa slow-motion.
                cap.grab()
                ret, frame = cap.retrieve()
                if not ret:
                    continue

                if self._mirror:
                    frame = cv2.flip(frame, 1)

                detected = False
                if self._motion is not None:
                    frame, detected = self._motion.process(frame)
                    cv2.putText(
                        frame,
                        "MOTION ON",
                        (20, self._height - 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                    )

                ok, buf = cv2.imencode(
                    ".jpg",
                    frame,
                    [int(cv2.IMWRITE_JPEG_QUALITY), self._quality],
                )
                if not ok:
                    continue

                chunk = buf.tobytes()
                with self._lock:
                    self._latest_chunk = chunk
                    self.motion_detected = detected

                if detected and self._telegram is not None:
                    self._telegram.notify_motion(chunk)

                if min_interval:
                    elapsed = time.monotonic() - loop_start
                    time.sleep(max(0.0, min_interval - elapsed))
        finally:
            cap.release()

    def frame_generator(self):
        interval = 1.0 / self._target_fps if self._target_fps > 0 else 0.033
        while True:
            with self._lock:
                chunk = self._latest_chunk
            if chunk is None:
                time.sleep(0.01)
                continue
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + chunk + b"\r\n"
            )
            time.sleep(interval)


_broadcaster: MjpegBroadcaster | None = None


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
  <p>Streaming saja — tidak ada rekaman ke disk. Deteksi gerakan tampil langsung di video.</p>
</body>
</html>"""


@app.route("/video_feed")
def video_feed():
    if _broadcaster is None:
        return Response("Server belum siap", status=503)
    return Response(
        _broadcaster.frame_generator(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/api/motion")
def motion_status():
    if _broadcaster is None:
        return jsonify({"enabled": False, "detected": False})
    return jsonify(
        {
            "enabled": _broadcaster.motion_enabled,
            "detected": _broadcaster.motion_detected,
        }
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
    parser.add_argument(
        "--width",
        type=int,
        default=FRAME_WIDTH,
        help=f"Lebar frame (default: {FRAME_WIDTH})",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=FRAME_HEIGHT,
        help=f"Tinggi frame (default: {FRAME_HEIGHT})",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=JPEG_QUALITY,
        help=f"Kualitas JPEG 1-100 (default: {JPEG_QUALITY})",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=TARGET_FPS,
        help=f"Target FPS stream (default: {TARGET_FPS})",
    )
    parser.add_argument(
        "--no-mirror",
        action="store_true",
        help="Matikan cermin horizontal",
    )
    parser.add_argument(
        "--no-motion",
        action="store_true",
        help="Matikan deteksi gerakan (default: aktif)",
    )
    parser.add_argument(
        "--min-motion-area",
        type=int,
        default=None,
        help="Luas kontur minimum (piksel²); default otomatis sesuai resolusi",
    )
    parser.add_argument(
        "--telegram-env",
        default="telegram.env",
        help="File env Telegram (default: telegram.env, kosongkan untuk lewati)",
    )
    parser.add_argument(
        "--telegram-token",
        default=None,
        help="Token bot Telegram (override env TELEGRAM_BOT_TOKEN)",
    )
    parser.add_argument(
        "--telegram-chat-id",
        default=None,
        help="Chat ID Telegram (override env TELEGRAM_CHAT_ID)",
    )
    parser.add_argument(
        "--telegram-cooldown",
        type=float,
        default=None,
        help="Jeda antar notifikasi dalam detik (default: 60)",
    )
    parser.add_argument(
        "--telegram-text-only",
        action="store_true",
        help="Telegram: kirim teks saja, tanpa foto",
    )
    return parser.parse_args(argv)


def build_telegram_notifier(args: argparse.Namespace) -> TelegramNotifier | None:
    if args.telegram_env:
        load_env_file(args.telegram_env)

    token = (args.telegram_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")).strip()
    chat_id = (args.telegram_chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")).strip()
    if not token or not chat_id:
        return None

    if args.telegram_cooldown is not None:
        cooldown = args.telegram_cooldown
    else:
        cooldown = float(os.environ.get("TELEGRAM_COOLDOWN_SEC", "60"))

    if args.telegram_text_only:
        send_photo = False
    else:
        env_photo = os.environ.get("TELEGRAM_SEND_PHOTO", "1").strip().lower()
        send_photo = env_photo not in {"0", "false", "no"}

    return TelegramNotifier.from_settings(token, chat_id, cooldown, send_photo)


def main(argv: list[str] | None = None) -> int:
    global _broadcaster
    args = parse_args(argv)
    motion_enabled = not args.no_motion
    telegram = build_telegram_notifier(args)

    _broadcaster = MjpegBroadcaster(
        camera_index=args.camera,
        width=args.width,
        height=args.height,
        quality=args.quality,
        mirror=not args.no_mirror,
        target_fps=args.fps,
        motion_enabled=motion_enabled,
        min_motion_area=args.min_motion_area,
        telegram=telegram,
    )
    _broadcaster.start()
    time.sleep(0.5)

    print("Live stream MJPEG — tidak merekam video ke file.")
    print(f"  Kamera index : {args.camera}")
    print(f"  Resolusi     : {args.width}x{args.height}")
    print(f"  Kualitas JPEG: {args.quality}")
    print(f"  Target FPS   : {args.fps}")
    print(f"  Deteksi gerak: {'aktif' if motion_enabled else 'nonaktif'}")
    if telegram is not None:
        mode = "foto + teks" if telegram.send_photo else "teks saja"
        print(f"  Telegram     : aktif ({mode}, cooldown {telegram.cooldown_sec:.0f}s)")
    else:
        print("  Telegram     : nonaktif (lihat telegram.env.example)")
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
