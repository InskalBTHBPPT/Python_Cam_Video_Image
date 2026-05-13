from datetime import datetime
from pathlib import Path

import cv2

cap = cv2.VideoCapture(1) # 0 untuk kamera internal, 1 untuk kamera eksternal
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
is_motion_detection_enabled = False
previous_gray = None
min_motion_area = 1000

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
            # Bandingkan frame saat ini dengan frame sebelumnya untuk mencari gerakan.
            frame_delta = cv2.absdiff(previous_gray, gray)
            threshold = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
            threshold = cv2.dilate(threshold, None, iterations=2)

            contours, _ = cv2.findContours(
                threshold,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE,
            )

            for contour in contours:
                if cv2.contourArea(contour) < min_motion_area:
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

    if is_motion_detection_enabled:
        cv2.putText(
            frame,
            "MOTION ON",
            (20, frame_height - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

    cv2.imshow("USB Camera", frame)

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