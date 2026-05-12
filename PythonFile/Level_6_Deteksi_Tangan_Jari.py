from datetime import datetime
from pathlib import Path
from time import monotonic
from urllib.error import URLError
from urllib.request import urlretrieve

import cv2

try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
except ModuleNotFoundError:
    print("Library mediapipe belum terinstall.")
    print("Jalankan perintah ini terlebih dahulu:")
    print("pip install mediapipe")
    exit()


CAMERA_INDEX = 1  # 0 untuk kamera internal, 1 untuk kamera eksternal
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_PATH = Path("models/hand_landmarker.task")
HAND_CONNECTIONS = vision.HandLandmarksConnections.HAND_CONNECTIONS

WRIST = 0
THUMB_IP = 3
THUMB_TIP = 4
INDEX_FINGER_PIP = 6
INDEX_FINGER_TIP = 8
MIDDLE_FINGER_PIP = 10
MIDDLE_FINGER_TIP = 12
RING_FINGER_PIP = 14
RING_FINGER_TIP = 16
PINKY_PIP = 18
PINKY_TIP = 20

cap = cv2.VideoCapture(CAMERA_INDEX)
capture_dir = Path("captures")
capture_dir.mkdir(exist_ok=True)

if not cap.isOpened():
    print("Kamera tidak terdeteksi")
    exit()


def ensure_hand_landmarker_model():
    if MODEL_PATH.exists():
        return True

    MODEL_PATH.parent.mkdir(exist_ok=True)
    print("Model hand landmarker belum ada. Mengunduh model...")

    try:
        urlretrieve(MODEL_URL, MODEL_PATH)
    except URLError:
        print("Gagal mengunduh model hand landmarker.")
        print("Pastikan laptop terhubung internet, lalu jalankan ulang script ini.")
        return False

    print(f"Model tersimpan: {MODEL_PATH}")
    return True


def count_raised_fingers(hand_landmarks, hand_label):
    landmarks = hand_landmarks
    raised_fingers = 0

    thumb_tip = landmarks[THUMB_TIP]
    thumb_ip = landmarks[THUMB_IP]

    if hand_label == "Right" and thumb_tip.x < thumb_ip.x:
        raised_fingers += 1
    elif hand_label == "Left" and thumb_tip.x > thumb_ip.x:
        raised_fingers += 1

    finger_tips = [
        INDEX_FINGER_TIP,
        MIDDLE_FINGER_TIP,
        RING_FINGER_TIP,
        PINKY_TIP,
    ]
    finger_pips = [
        INDEX_FINGER_PIP,
        MIDDLE_FINGER_PIP,
        RING_FINGER_PIP,
        PINKY_PIP,
    ]

    for tip_id, pip_id in zip(finger_tips, finger_pips):
        if landmarks[tip_id].y < landmarks[pip_id].y:
            raised_fingers += 1

    return raised_fingers


def draw_hand_landmarks(frame, hand_landmarks):
    frame_height, frame_width, _ = frame.shape

    for connection in HAND_CONNECTIONS:
        start = hand_landmarks[connection.start]
        end = hand_landmarks[connection.end]
        start_point = (int(start.x * frame_width), int(start.y * frame_height))
        end_point = (int(end.x * frame_width), int(end.y * frame_height))
        cv2.line(frame, start_point, end_point, (0, 255, 0), 2)

    for landmark in hand_landmarks:
        point = (int(landmark.x * frame_width), int(landmark.y * frame_height))
        cv2.circle(frame, point, 4, (0, 0, 255), -1)


if not ensure_hand_landmarker_model():
    exit()

print("Level 6: Deteksi tangan dan hitung jari")
print("Tekan 's' untuk simpan foto")
print("Tekan 'q' untuk keluar")

base_options = python.BaseOptions(model_asset_path=str(MODEL_PATH))
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=2,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5,
)

with vision.HandLandmarker.create_from_options(options) as landmarker:
    start_time = monotonic()

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Gagal membaca frame")
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = int((monotonic() - start_time) * 1000)
        results = landmarker.detect_for_video(mp_image, timestamp_ms)

        total_fingers = 0
        hand_count = 0

        if results.hand_landmarks and results.handedness:
            for hand_landmarks, handedness_list in zip(
                results.hand_landmarks,
                results.handedness,
            ):
                hand_count += 1
                hand_label = handedness_list[0].category_name
                raised_fingers = count_raised_fingers(hand_landmarks, hand_label)
                total_fingers += raised_fingers

                draw_hand_landmarks(frame, hand_landmarks)

                wrist = hand_landmarks[WRIST]
                text_x = int(wrist.x * frame.shape[1])
                text_y = int(wrist.y * frame.shape[0]) - 20
                cv2.putText(
                    frame,
                    f"{hand_label}: {raised_fingers} jari",
                    (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

        cv2.putText(
            frame,
            f"Tangan: {hand_count} | Total jari: {total_fingers}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )

        cv2.imshow("Level 6 - Deteksi Tangan dan Jari", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("s"):
            filename = capture_dir / f"hand_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(str(filename), frame)
            print(f"Foto tersimpan: {filename}")

        if key == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()
