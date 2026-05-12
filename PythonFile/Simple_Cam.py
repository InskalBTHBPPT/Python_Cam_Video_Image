from datetime import datetime
from pathlib import Path

import cv2

cap = cv2.VideoCapture(1) # 0 untuk kamera internal, 1 untuk kamera eksternal
capture_dir = Path("captures")
capture_dir.mkdir(exist_ok=True)

if not cap.isOpened():
    print("Kamera tidak terdeteksi")
    exit()

while True:
    ret, frame = cap.read()

    if not ret:
        print("Gagal membaca frame")
        break

    cv2.imshow("USB Camera", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("s"):
        filename = capture_dir / f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(str(filename), frame)
        print(f"Foto tersimpan: {filename}")

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()