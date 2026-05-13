from datetime import datetime
from pathlib import Path

import cv2

try:
    from ultralytics import YOLO
except ModuleNotFoundError:
    print("Library ultralytics belum terinstall.")
    print("Jalankan perintah ini terlebih dahulu:")
    print("pip install ultralytics")
    exit()


CAMERA_INDEX = 1  # 0 untuk kamera internal, 1 untuk kamera eksternal
MODEL_FILE_NAME = "yolo11n.pt"
BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / MODEL_FILE_NAME
CONFIDENCE_THRESHOLD = 0.5


def migrate_yolo_model_to_models_dir():
    MODEL_DIR.mkdir(exist_ok=True)

    if MODEL_PATH.exists():
        return

    legacy_paths = [
        BASE_DIR / MODEL_FILE_NAME,
        Path.cwd() / MODEL_FILE_NAME,
        Path(__file__).resolve().parent / MODEL_FILE_NAME,
    ]

    for legacy_path in legacy_paths:
        if legacy_path.exists() and legacy_path.resolve() != MODEL_PATH.resolve():
            legacy_path.replace(MODEL_PATH)
            return


def print_detectable_objects(model):
    object_names = [model.names[index] for index in sorted(model.names)]
    print("\nDaftar objek yang bisa dideteksi model ini:")

    for index, object_name in enumerate(object_names, start=1):
        print(f"{index:02d}. {object_name}")

    print()


cap = cv2.VideoCapture(CAMERA_INDEX)
capture_dir = Path("captures")
capture_dir.mkdir(exist_ok=True)

if not cap.isOpened():
    print("Kamera tidak terdeteksi")
    exit()

print("Level 7: Deteksi objek dengan YOLO")
print(f"Model: {MODEL_PATH}")
print("Tekan 's' untuk simpan foto")
print("Tekan 'l' untuk lihat daftar objek yang bisa dideteksi")
print("Tekan 'q' untuk keluar")
print("Catatan: pertama kali dijalankan, model YOLO akan diunduh otomatis.")

migrate_yolo_model_to_models_dir()
model_source = MODEL_PATH if MODEL_PATH.exists() else MODEL_FILE_NAME
model = YOLO(str(model_source))
migrate_yolo_model_to_models_dir()

while True:
    ret, frame = cap.read()

    if not ret:
        print("Gagal membaca frame")
        break

    results = model.predict(
        frame,
        conf=CONFIDENCE_THRESHOLD,
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
        print(f"Foto tersimpan: {filename}")

    if key == ord("l"):
        print_detectable_objects(model)

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
