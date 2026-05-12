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
MODEL_NAME = "yolo11n.pt"
CONFIDENCE_THRESHOLD = 0.5

cap = cv2.VideoCapture(CAMERA_INDEX)
capture_dir = Path("captures")
capture_dir.mkdir(exist_ok=True)

if not cap.isOpened():
    print("Kamera tidak terdeteksi")
    exit()

print("Level 7: Deteksi objek dengan YOLO")
print(f"Model: {MODEL_NAME}")
print("Tekan 's' untuk simpan foto")
print("Tekan 'q' untuk keluar")
print("Catatan: pertama kali dijalankan, model YOLO akan diunduh otomatis.")

model = YOLO(MODEL_NAME)

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

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
