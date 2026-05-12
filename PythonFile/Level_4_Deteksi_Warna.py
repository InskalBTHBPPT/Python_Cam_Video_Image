from datetime import datetime
from pathlib import Path

import cv2
import numpy as np


CAMERA_INDEX = 1  # 0 untuk kamera internal, 1 untuk kamera eksternal
MIN_COLOR_AREA = 1200

COLOR_RANGES = {
    "merah": [
        (np.array([0, 120, 70]), np.array([10, 255, 255])),
        (np.array([170, 120, 70]), np.array([180, 255, 255])),
    ],
    "hijau": [
        (np.array([40, 70, 70]), np.array([85, 255, 255])),
    ],
    "biru": [
        (np.array([90, 70, 70]), np.array([130, 255, 255])),
    ],
}

BOX_COLORS = {
    "merah": (0, 0, 255),
    "hijau": (0, 255, 0),
    "biru": (255, 0, 0),
}


def build_color_mask(hsv_frame, color_name):
    mask = None

    for lower_color, upper_color in COLOR_RANGES[color_name]:
        current_mask = cv2.inRange(hsv_frame, lower_color, upper_color)

        if mask is None:
            mask = current_mask
        else:
            mask = cv2.bitwise_or(mask, current_mask)

    mask = cv2.erode(mask, None, iterations=1)
    mask = cv2.dilate(mask, None, iterations=2)
    return mask


cap = cv2.VideoCapture(CAMERA_INDEX)
capture_dir = Path("captures")
capture_dir.mkdir(exist_ok=True)

if not cap.isOpened():
    print("Kamera tidak terdeteksi")
    exit()

selected_color = "semua"

print("Level 4: Deteksi warna merah, hijau, dan biru")
print("Tekan '1' untuk deteksi merah")
print("Tekan '2' untuk deteksi hijau")
print("Tekan '3' untuk deteksi biru")
print("Tekan 'a' untuk deteksi semua warna")
print("Tekan 's' untuk simpan foto")
print("Tekan 'q' untuk keluar")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Gagal membaca frame")
        break

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    colors_to_detect = COLOR_RANGES.keys()

    if selected_color != "semua":
        colors_to_detect = [selected_color]

    for color_name in colors_to_detect:
        mask = build_color_mask(hsv, color_name)
        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        for contour in contours:
            if cv2.contourArea(contour) < MIN_COLOR_AREA:
                continue

            x, y, width, height = cv2.boundingRect(contour)
            box_color = BOX_COLORS[color_name]
            cv2.rectangle(frame, (x, y), (x + width, y + height), box_color, 2)
            cv2.putText(
                frame,
                color_name.upper(),
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                box_color,
                2,
            )

    cv2.putText(
        frame,
        f"MODE: {selected_color.upper()}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
    )

    cv2.imshow("Level 4 - Deteksi Warna", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("1"):
        selected_color = "merah"
        print("Mode deteksi: merah")

    if key == ord("2"):
        selected_color = "hijau"
        print("Mode deteksi: hijau")

    if key == ord("3"):
        selected_color = "biru"
        print("Mode deteksi: biru")

    if key == ord("a"):
        selected_color = "semua"
        print("Mode deteksi: semua warna")

    if key == ord("s"):
        filename = capture_dir / f"color_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(str(filename), frame)
        print(f"Foto tersimpan: {filename}")

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
