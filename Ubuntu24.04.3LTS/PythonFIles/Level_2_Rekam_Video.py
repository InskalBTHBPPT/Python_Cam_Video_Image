"""
Level 2 — Rekam video (Ubuntu 24.04 / Raspberry Pi).

Di Linux, USB webcam biasanya /dev/video0 (indeks 0).
Rekaman memakai MP4 + mp4v (lebih umum di Ubuntu daripada AVI + XVID).
"""
from datetime import datetime
from pathlib import Path
import platform

import cv2

# Ubuntu / Raspberry Pi: mulai dari 0. Windows laptop+USB eksternal sering pakai 1.
CAMERA_INDEX = 0

APP_ROOT = Path(__file__).resolve().parent
capture_dir = APP_ROOT / "captures"
recording_dir = APP_ROOT / "recordings"
capture_dir.mkdir(exist_ok=True)
recording_dir.mkdir(exist_ok=True)


def open_video_capture(camera_index: int) -> cv2.VideoCapture:
    if platform.system() == "Linux":
        return cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
    return cv2.VideoCapture(camera_index)


cap = open_video_capture(CAMERA_INDEX)

if not cap.isOpened():
    print(f"Kamera tidak terdeteksi (index {CAMERA_INDEX})")
    print("Coba ubah CAMERA_INDEX ke 0, atau jalankan: v4l2-ctl --list-devices")
    exit(1)

fps = cap.get(cv2.CAP_PROP_FPS)
if fps == 0:
    fps = 20.0

frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
frame_size = (frame_width, frame_height)

is_recording = False
video_writer = None
current_recording_path = None

print("Level 2: Rekam video")
print(f"Kamera aktif — index {CAMERA_INDEX}")
print("Tekan 's' untuk simpan foto")
print("Tekan 'r' untuk mulai/berhenti rekam video")
print("Tekan 'q' untuk keluar")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Gagal membaca frame")
        break

    if is_recording and video_writer is not None:
        cv2.putText(
            frame,
            "REC",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
        )
        video_writer.write(frame)

    cv2.imshow("Level 2 - Rekam Video", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("s"):
        filename = capture_dir / f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(str(filename), frame)
        print(f"Foto tersimpan: {filename.resolve()}")

    if key == ord("r"):
        if not is_recording:
            filename = recording_dir / f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            video_writer = cv2.VideoWriter(str(filename), fourcc, fps, frame_size)

            if not video_writer.isOpened():
                video_writer.release()
                video_writer = None
                print("Gagal membuka video writer — coba pasang paket multimedia (ffmpeg).")
            else:
                current_recording_path = filename.resolve()
                is_recording = True
                print(f"Mulai rekam: {current_recording_path}")
        else:
            is_recording = False
            if video_writer is not None:
                video_writer.release()
                video_writer = None
            if current_recording_path is not None:
                print(f"Rekaman dihentikan: {current_recording_path}")
                current_recording_path = None
            else:
                print("Rekaman dihentikan")

    if key == ord("q"):
        break

if video_writer is not None:
    video_writer.release()

cap.release()
cv2.destroyAllWindows()
