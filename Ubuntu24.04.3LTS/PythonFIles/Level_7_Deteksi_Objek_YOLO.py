"""
Level 7 — Deteksi objek YOLO (Ubuntu 24.04 / Raspberry Pi).

Di Linux, USB webcam biasanya /dev/video0 (indeks 0).
Model YOLO (default yolo11n.pt) disimpan di folder models/; unduh otomatis saat pertama kali.
"""
import os
from datetime import datetime
from pathlib import Path
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import cv2

from v4l2_camera import open_video_capture

try:
    from ultralytics import YOLO
except ModuleNotFoundError:
    print("Library ultralytics belum terinstall.")
    print("Aktifkan venv lalu jalankan:")
    print("  source usbcamtest/bin/activate")
    print("  pip install ultralytics")
    exit(1)

# Ubuntu / Raspberry Pi: mulai dari 0. Windows laptop+USB eksternal sering pakai 1.
CAMERA_INDEX = 0
YOLO_MODEL_NAME = "yolo11n.pt"
CONFIDENCE_THRESHOLD = 0.5

APP_ROOT = Path(__file__).resolve().parent
MODEL_DIR = APP_ROOT / "models"
YOLO_MODEL_PATH = MODEL_DIR / YOLO_MODEL_NAME
capture_dir = APP_ROOT / "captures"
capture_dir.mkdir(exist_ok=True)


def migrate_yolo_model_to_models_dir():
    MODEL_DIR.mkdir(exist_ok=True)

    legacy_dirs = [
        APP_ROOT,
        Path.cwd(),
        APP_ROOT.parent,
    ]

    for legacy_dir in legacy_dirs:
        for legacy_path in legacy_dir.glob("*.pt"):
            target_path = MODEL_DIR / legacy_path.name

            if legacy_path.resolve() != target_path.resolve() and not target_path.exists():
                legacy_path.replace(target_path)


def print_detectable_objects(model):
    object_names = [model.names[index] for index in sorted(model.names)]
    print("\nDaftar objek yang bisa dideteksi model ini:")

    for index, object_name in enumerate(object_names, start=1):
        print(f"{index:02d}. {object_name}")

    print()


migrate_yolo_model_to_models_dir()
model_source = YOLO_MODEL_PATH if YOLO_MODEL_PATH.exists() else YOLO_MODEL_NAME

print("Level 7: Deteksi objek dengan YOLO")
print(f"Model: {YOLO_MODEL_PATH}")
print("Memuat model YOLO (unduh otomatis jika belum ada)...")

try:
    model = YOLO(str(model_source))
    migrate_yolo_model_to_models_dir()
except Exception as error:
    print(f"Model YOLO gagal dimuat: {error}")
    print("Pastikan internet aktif untuk unduhan pertama, atau letakkan file .pt di folder models/.")
    exit(1)

cap = open_video_capture(CAMERA_INDEX)

if not cap.isOpened():
    print(f"Kamera tidak terdeteksi (index {CAMERA_INDEX})")
    print("Coba ubah CAMERA_INDEX ke 0, atau jalankan: v4l2-ctl --list-devices")
    exit(1)

print(f"Kamera aktif — index {CAMERA_INDEX}")
print("Tekan 's' untuk simpan foto")
print("Tekan 'l' untuk lihat daftar objek yang bisa dideteksi")
print("Tekan 'q' untuk keluar")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Gagal membaca frame")
        break

    results = model.predict(
        frame,
        conf=CONFIDENCE_THRESHOLD,
        imgsz=320,
        verbose=False,
    )
    result = results[0]
    annotated_frame = result.plot()

    object_count = 0
    if result.boxes is not None:
        object_count = len(result.boxes)

    cv2.putText(
        annotated_frame,
        f"Objek: {object_count} | Conf: {CONFIDENCE_THRESHOLD}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
    )

    cv2.imshow("Level 7 - Deteksi Objek YOLO", annotated_frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("s"):
        filename = capture_dir / f"object_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(str(filename), annotated_frame)
        print(f"Foto tersimpan: {filename.resolve()}")

    if key == ord("l"):
        print_detectable_objects(model)

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
