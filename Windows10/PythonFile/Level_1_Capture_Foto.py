from datetime import datetime
from pathlib import Path

import cv2


CAMERA_INDEX = 1  # 0 untuk kamera internal, 1 untuk kamera eksternal

cap = cv2.VideoCapture(CAMERA_INDEX)
capture_dir = Path("captures")
capture_dir.mkdir(exist_ok=True)

if not cap.isOpened():
    print("Kamera tidak terdeteksi")
    exit()

print("Level 1: Capture foto")
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
        print(f"Foto tersimpan: {filename}")

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
