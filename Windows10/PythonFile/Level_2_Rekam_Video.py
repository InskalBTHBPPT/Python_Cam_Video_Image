from datetime import datetime
from pathlib import Path

import cv2


CAMERA_INDEX = 1  # 0 untuk kamera internal, 1 untuk kamera eksternal

cap = cv2.VideoCapture(CAMERA_INDEX)
capture_dir = Path("captures")
recording_dir = Path("recordings")
capture_dir.mkdir(exist_ok=True)
recording_dir.mkdir(exist_ok=True)

if not cap.isOpened():
    print("Kamera tidak terdeteksi")
    exit()

fps = cap.get(cv2.CAP_PROP_FPS)
if fps == 0:
    fps = 20.0

frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
frame_size = (frame_width, frame_height)

is_recording = False
video_writer = None

print("Level 2: Rekam video")
print("Tekan 's' untuk simpan foto")
print("Tekan 'r' untuk mulai/berhenti rekam video")
print("Tekan 'q' untuk keluar")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Gagal membaca frame")
        break

    if is_recording:
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
        print(f"Foto tersimpan: {filename}")

    if key == ord("r"):
        if not is_recording:
            filename = recording_dir / f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
            fourcc = cv2.VideoWriter_fourcc(*"XVID")
            video_writer = cv2.VideoWriter(str(filename), fourcc, fps, frame_size)
            is_recording = True
            print(f"Mulai rekam: {filename}")
        else:
            is_recording = False
            video_writer.release()
            video_writer = None
            print("Rekaman dihentikan")

    if key == ord("q"):
        break

if video_writer is not None:
    video_writer.release()

cap.release()
cv2.destroyAllWindows()
