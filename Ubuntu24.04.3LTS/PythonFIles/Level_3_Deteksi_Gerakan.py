"""
Level 3 — Deteksi gerakan (Ubuntu 24.04 / Raspberry Pi).

Di Linux, USB webcam biasanya /dev/video0 (indeks 0).
Rekaman memakai MP4 + mp4v (lebih umum di Ubuntu daripada AVI + XVID).
"""
from datetime import datetime
from pathlib import Path
import platform

import cv2

# Ubuntu / Raspberry Pi: mulai dari 0. Windows laptop+USB eksternal sering pakai 1.
CAMERA_INDEX = 0
MIN_MOTION_AREA = 1000

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
is_motion_detection_enabled = False
previous_gray = None
video_writer = None
current_recording_path = None

print("Level 3: Deteksi gerakan seperti CCTV")
print(f"Kamera aktif — index {CAMERA_INDEX}")
print("Tekan 's' untuk simpan foto")
print("Tekan 'r' untuk mulai/berhenti rekam video")
print("Tekan 'm' untuk aktif/nonaktif deteksi gerakan")
print("Tekan 'q' untuk keluar")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Gagal membaca frame")
        break

    if is_motion_detection_enabled:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        motion_detected = False

        if previous_gray is None:
            previous_gray = gray
        else:
            frame_delta = cv2.absdiff(previous_gray, gray)
            threshold = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
            threshold = cv2.dilate(threshold, None, iterations=2)

            contours, _ = cv2.findContours(
                threshold,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE,
            )

            for contour in contours:
                if cv2.contourArea(contour) < MIN_MOTION_AREA:
                    continue

                motion_detected = True
                x, y, width, height = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 0), 2)

            previous_gray = gray

        if motion_detected:
            cv2.putText(
                frame,
                "MOTION DETECTED",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2,
            )

        cv2.putText(
            frame,
            "MOTION ON",
            (20, frame_height - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

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

    cv2.imshow("Level 3 - Deteksi Gerakan", frame)

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

    if key == ord("m"):
        is_motion_detection_enabled = not is_motion_detection_enabled
        previous_gray = None

        if is_motion_detection_enabled:
            print("Deteksi gerakan aktif")
        else:
            print("Deteksi gerakan nonaktif")

    if key == ord("q"):
        break

if video_writer is not None:
    video_writer.release()

cap.release()
cv2.destroyAllWindows()
