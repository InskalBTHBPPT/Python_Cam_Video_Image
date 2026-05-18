"""
Level 1 — Capture foto (Ubuntu 24.04 / Raspberry Pi).

Di Linux, USB webcam biasanya /dev/video0 (indeks 0).
/dev/video1 pada perangkat yang sama sering bukan perangkat capture — jangan pakai indeks 1
kecuali Anda sudah memastikan dengan: v4l2-ctl --list-devices
"""
from datetime import datetime
from pathlib import Path
import platform

import cv2

# Ubuntu / Raspberry Pi: mulai dari 0. Windows laptop+USB eksternal sering pakai 1.
CAMERA_INDEX = 0

APP_ROOT = Path(__file__).resolve().parent
capture_dir = APP_ROOT / "captures"
capture_dir.mkdir(exist_ok=True)


def open_video_capture(camera_index: int) -> cv2.VideoCapture:
    if platform.system() == "Linux":
        return cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
    return cv2.VideoCapture(camera_index)


cap = open_video_capture(CAMERA_INDEX)

if not cap.isOpened():
    print(f"Kamera tidak terdeteksi (index {CAMERA_INDEX})")
    print("Coba ubah CAMERA_INDEX ke 0, atau jalankan: v4l2-ctl --list-devices")
    exit(1)

print("Level 1: Capture foto")
print(f"Kamera aktif — index {CAMERA_INDEX}")
print("Tekan 's' untuk simpan foto")
print("Tekan 'q' untuk keluar")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Gagal membaca frame")
        break

    cv2.imshow("Level 1 - Capture Foto", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("s"):
        filename = capture_dir / f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(str(filename), frame)
        print(f"Foto tersimpan: {filename.resolve()}")

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
