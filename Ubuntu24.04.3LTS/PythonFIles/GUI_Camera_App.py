"""
GUI Camera App — port untuk Ubuntu 24.04 LTS (termasuk Raspberry Pi).

Perbedaan utama dari versi Windows:
- ROOT aplikasi = folder skrip ini (models/captures/recordings di samping file).
- Pembukaan kamera memakai backend V4L2 di Linux (lebih stabil untuk /dev/video*).
- Rekaman video: MP4 + fourcc mp4v (lebih umum tersedia di Ubuntu daripada XVID).
- Indeks kamera default 0 (umum di Raspberry Pi /dev/video0).
"""
from datetime import datetime
from pathlib import Path
import os
import platform
import sys
from time import monotonic
from urllib.error import URLError
from urllib.request import urlretrieve

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("GLOG_minloglevel", "2")

import cv2
import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision

    MEDIAPIPE_AVAILABLE = True
except ModuleNotFoundError:
    MEDIAPIPE_AVAILABLE = False
    mp = None
    python = None
    vision = None

try:
    from ultralytics import YOLO

    ULTRALYTICS_AVAILABLE = True
except ModuleNotFoundError:
    ULTRALYTICS_AVAILABLE = False
    YOLO = None

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

HAND_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
# Folder skrip = root aplikasi (mudah di-copy ke Raspberry Pi)
APP_ROOT = Path(__file__).resolve().parent
MODEL_DIR = APP_ROOT / "models"

HAND_MODEL_PATH = MODEL_DIR / "hand_landmarker.task"
HAND_CONNECTIONS = vision.HandLandmarksConnections.HAND_CONNECTIONS if MEDIAPIPE_AVAILABLE else []

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

YOLO_MODEL_NAME = "yolo11n.pt"
YOLO_MODEL_PATH = MODEL_DIR / YOLO_MODEL_NAME
# Resolusi inferensi lebih kecil — penting untuk performa di Raspberry Pi
YOLO_IMGSZ = 320


def open_video_capture(camera_index: int) -> cv2.VideoCapture:
    """Buka kamera dengan backend yang sesuai OS."""
    if platform.system() == "Linux":
        return cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
    return cv2.VideoCapture(camera_index)


def check_pytorch_for_arm() -> tuple[bool, str]:
    """Pastikan torch CPU cocok di aarch64 (hindari +cu / Illegal instruction)."""
    if platform.machine() != "aarch64":
        return True, ""

    try:
        import torch
    except ModuleNotFoundError:
        return (
            False,
            "PyTorch belum terpasang.\n\n"
            "Di Raspberry Pi jalankan:\n"
            "  pip install -r requirements-raspberrypi.txt\n"
            "atau: ./fix_pytorch_raspi.sh",
        )

    version = torch.__version__
    if "+cu" in version or version.startswith(("2.11", "2.12")):
        return (
            False,
            f"PyTorch {version} tidak cocok untuk Raspberry Pi.\n\n"
            "Jalankan di folder PythonFIles:\n"
            "  ./fix_pytorch_raspi.sh",
        )

    return True, ""


class CameraApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Python Camera GUI - Tahap 7 (Ubuntu / Raspberry Pi)")
        self.resize(960, 640)

        self.cap = None
        self.last_frame = None
        self.video_writer = None
        self.current_recording_path = None
        self.is_recording = False
        self.previous_gray = None
        self.min_motion_area = 1000
        self.hand_landmarker = None
        self.hand_start_time = None
        self.yolo_model = None
        self.yolo_model_path = None
        self.capture_dir = APP_ROOT / "captures"
        self.recording_dir = APP_ROOT / "recordings"
        self.capture_dir.mkdir(exist_ok=True)
        self.recording_dir.mkdir(exist_ok=True)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        self.level_combo = QComboBox()
        self.level_combo.addItems(
            [
                "Level 1 - Capture Foto",
                "Level 2 - Rekam Video",
                "Level 3 - Deteksi Gerakan",
                "Level 4 - Deteksi Warna",
                "Level 6 - Deteksi Tangan/Jari",
                "Level 7 - Deteksi Objek YOLO",
            ]
        )

        self.camera_combo = QComboBox()
        self.camera_combo.addItems(["0", "1", "2", "3"])
        self.camera_combo.setCurrentText("0")

        self.color_combo = QComboBox()
        self.color_combo.addItems(["semua", "merah", "hijau", "biru"])

        self.yolo_model_combo = QComboBox()
        self.refresh_yolo_model_combo()

        self.yolo_object_combo = QComboBox()
        self.yolo_object_combo.addItem("semua")

        self.yolo_confidence_combo = QComboBox()
        self.yolo_confidence_combo.addItems(["0.25", "0.50", "0.70", "0.90"])
        self.yolo_confidence_combo.setCurrentText("0.50")

        self.start_button = QPushButton("Start Camera")
        self.stop_button = QPushButton("Stop Camera")
        self.capture_button = QPushButton("Save Image")
        self.record_button = QPushButton("Start Record")
        self.stop_button.setEnabled(False)
        self.capture_button.setEnabled(False)
        self.record_button.setEnabled(False)

        self.status_label = QLabel("Status: Kamera belum aktif")
        self.status_label.setAlignment(Qt.AlignLeft)

        self.preview_label = QLabel("Preview kamera akan tampil di sini")
        self.preview_label.setObjectName("previewLabel")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(800, 500)

        self.status_label.setObjectName("statusLabel")

        self.start_button.clicked.connect(self.start_camera)
        self.stop_button.clicked.connect(self.stop_camera)
        self.capture_button.clicked.connect(self.save_capture_image)
        self.record_button.clicked.connect(self.toggle_recording)
        self.level_combo.currentTextChanged.connect(self.update_level_controls)
        self.yolo_model_combo.currentTextChanged.connect(self.on_yolo_model_changed)

        camera_group = QGroupBox("Camera Settings")
        camera_layout = QGridLayout()
        camera_layout.addWidget(QLabel("Pilih Level:"), 0, 0)
        camera_layout.addWidget(self.level_combo, 0, 1)
        camera_layout.addWidget(QLabel("Camera Index:"), 0, 2)
        camera_layout.addWidget(self.camera_combo, 0, 3)
        camera_group.setLayout(camera_layout)

        detection_group = QGroupBox("Detection Settings")
        detection_layout = QGridLayout()
        self.detection_hint_label = QLabel("Tidak ada pengaturan tambahan untuk level ini.")
        self.detection_hint_label.setObjectName("hintLabel")
        self.color_label = QLabel("Warna:")
        self.yolo_model_label = QLabel("Model YOLO:")
        self.yolo_object_label = QLabel("Objek YOLO:")
        self.yolo_confidence_label = QLabel("Confidence YOLO:")
        detection_layout.addWidget(self.detection_hint_label, 0, 0, 1, 4)
        detection_layout.addWidget(self.color_label, 1, 0)
        detection_layout.addWidget(self.color_combo, 1, 1)
        detection_layout.addWidget(self.yolo_model_label, 1, 0)
        detection_layout.addWidget(self.yolo_model_combo, 1, 1)
        detection_layout.addWidget(self.yolo_object_label, 2, 0)
        detection_layout.addWidget(self.yolo_object_combo, 2, 1)
        detection_layout.addWidget(self.yolo_confidence_label, 2, 2)
        detection_layout.addWidget(self.yolo_confidence_combo, 2, 3)
        detection_group.setLayout(detection_layout)

        action_group = QGroupBox("Actions")
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.capture_button)
        button_layout.addWidget(self.record_button)
        button_layout.addStretch()
        action_group.setLayout(button_layout)

        top_controls_layout = QHBoxLayout()
        top_controls_layout.addWidget(camera_group, 1)
        top_controls_layout.addWidget(detection_group, 1)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_controls_layout)
        main_layout.addWidget(action_group)
        main_layout.addWidget(self.preview_label)
        main_layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        self.apply_modern_style()
        self.update_level_controls()
        self.load_selected_yolo_model(show_errors=False)

    def apply_modern_style(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #d8dde5;
            }

            QGroupBox {
                background-color: #e8ebf0;
                border: 1px solid #b8c0cc;
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px;
                font-weight: 600;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #263241;
            }

            QLabel {
                color: #263241;
            }

            QLabel#hintLabel {
                color: #667085;
                font-style: italic;
            }

            QLabel#statusLabel {
                color: #263241;
                padding: 6px 2px;
            }

            QLabel#previewLabel {
                background-color: #15171a;
                color: #d1d5db;
                border: 1px solid #2f3542;
                border-radius: 8px;
            }

            QComboBox {
                background-color: #f7f8fa;
                border: 1px solid #aeb7c4;
                border-radius: 6px;
                padding: 5px 8px;
                min-height: 24px;
            }

            QComboBox:disabled {
                background-color: #cfd5de;
                color: #7b8491;
            }

            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 7px 12px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #1d4ed8;
            }

            QPushButton:disabled {
                background-color: #bfc6d1;
                color: #6f7885;
            }
            """
        )

    def refresh_yolo_model_combo(self):
        MODEL_DIR.mkdir(exist_ok=True)
        current_model = self.yolo_model_combo.currentData() if hasattr(self, "yolo_model_combo") else None
        current_text = self.yolo_model_combo.currentText() if hasattr(self, "yolo_model_combo") else ""
        model_paths = sorted(MODEL_DIR.glob("*.pt"), key=lambda path: (path.stat().st_size, path.name))
        model_items = []

        for model_path in model_paths:
            size_mb = model_path.stat().st_size / (1024 * 1024)
            model_items.append((f"{model_path.name} ({size_mb:.1f} MB)", model_path.name))

        if YOLO_MODEL_NAME not in [model_name for _, model_name in model_items]:
            model_items.insert(0, (f"{YOLO_MODEL_NAME} (download jika belum ada)", YOLO_MODEL_NAME))

        self.yolo_model_combo.blockSignals(True)
        self.yolo_model_combo.clear()

        for label, model_name in model_items:
            self.yolo_model_combo.addItem(label, model_name)

        selected_index = self.yolo_model_combo.findData(current_model)

        if selected_index < 0:
            selected_index = self.yolo_model_combo.findText(current_text)

        if selected_index < 0:
            selected_index = self.yolo_model_combo.findData(YOLO_MODEL_NAME)

        if selected_index >= 0:
            self.yolo_model_combo.setCurrentIndex(selected_index)

        self.yolo_model_combo.blockSignals(False)

    def get_selected_yolo_model_path(self):
        selected_model = self.yolo_model_combo.currentData()

        if not selected_model:
            selected_model = YOLO_MODEL_NAME

        return MODEL_DIR / selected_model

    def on_yolo_model_changed(self):
        if self.cap is not None:
            return

        self.load_selected_yolo_model(show_errors=True)
        self.update_level_controls()

    def update_level_controls(self):
        selected_level = self.level_combo.currentText()
        is_level_4 = selected_level.startswith("Level 4")
        is_level_7 = selected_level.startswith("Level 7")
        is_camera_stopped = self.cap is None

        self.detection_hint_label.setVisible(not is_level_4 and not is_level_7)
        self.color_label.setVisible(is_level_4)
        self.color_combo.setVisible(is_level_4)
        self.color_combo.setEnabled(is_level_4)
        self.yolo_model_label.setVisible(is_level_7)
        self.yolo_model_combo.setVisible(is_level_7)
        self.yolo_model_combo.setEnabled(is_level_7 and is_camera_stopped)
        self.yolo_object_label.setVisible(is_level_7)
        self.yolo_object_combo.setVisible(is_level_7)
        self.yolo_object_combo.setEnabled(is_level_7)
        self.yolo_confidence_label.setVisible(is_level_7)
        self.yolo_confidence_combo.setVisible(is_level_7)
        self.yolo_confidence_combo.setEnabled(is_level_7)

    def start_camera(self):
        camera_index = int(self.camera_combo.currentText())
        selected_level = self.level_combo.currentText()

        self.cap = open_video_capture(camera_index)

        if not self.cap.isOpened():
            self.cap.release()
            self.cap = None
            self.status_label.setText(f"Status: Kamera index {camera_index} tidak terdeteksi")
            return

        if selected_level.startswith("Level 6") and not self.setup_hand_landmarker():
            self.cap.release()
            self.cap = None
            return

        if selected_level.startswith("Level 7") and not self.setup_yolo_model():
            self.cap.release()
            self.cap = None
            return

        self.previous_gray = None
        self.timer.start(30)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.capture_button.setEnabled(True)
        self.record_button.setEnabled(True)
        self.level_combo.setEnabled(False)
        self.camera_combo.setEnabled(False)
        self.update_level_controls()
        self.status_label.setText(f"Status: Kamera aktif | {selected_level}")

    def stop_camera(self):
        if self.is_recording:
            self.stop_recording(show_notification=True)

        self.timer.stop()

        if self.cap is not None:
            self.cap.release()
            self.cap = None

        self.release_hand_landmarker()

        self.preview_label.clear()
        self.preview_label.setText("Preview kamera akan tampil di sini")
        self.last_frame = None
        self.previous_gray = None
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.capture_button.setEnabled(False)
        self.record_button.setEnabled(False)
        self.record_button.setText("Start Record")
        self.level_combo.setEnabled(True)
        self.camera_combo.setEnabled(True)
        self.update_level_controls()
        self.status_label.setText("Status: Kamera berhenti")

    def save_capture_image(self):
        if self.last_frame is None:
            QMessageBox.warning(self, "Capture gagal", "Belum ada frame kamera untuk disimpan.")
            return

        filename = self.capture_dir / f"gui_capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(str(filename), self.last_frame)
        saved_path = filename.resolve()

        self.status_label.setText(f"Status: Foto tersimpan di {saved_path}")
        QMessageBox.information(self, "Foto tersimpan", f"File disimpan di:\n{saved_path}")

    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording(show_notification=True)
        else:
            self.start_recording()

    def start_recording(self):
        if self.cap is None:
            QMessageBox.warning(self, "Record gagal", "Kamera belum aktif.")
            return

        frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self.cap.get(cv2.CAP_PROP_FPS)

        if fps == 0:
            fps = 20.0

        filename = self.recording_dir / f"gui_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.video_writer = cv2.VideoWriter(
            str(filename),
            fourcc,
            fps,
            (frame_width, frame_height),
        )

        if not self.video_writer.isOpened():
            self.video_writer.release()
            self.video_writer = None
            QMessageBox.warning(self, "Record gagal", "Video writer tidak bisa dibuka.")
            return

        self.current_recording_path = filename.resolve()
        self.is_recording = True
        self.record_button.setText("Stop Record")
        self.status_label.setText(f"Status: Sedang merekam ke {self.current_recording_path}")

    def stop_recording(self, show_notification):
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None

        saved_path = self.current_recording_path
        self.current_recording_path = None
        self.is_recording = False
        self.record_button.setText("Start Record")

        if saved_path is not None:
            self.status_label.setText(f"Status: Video tersimpan di {saved_path}")

            if show_notification:
                QMessageBox.information(self, "Video tersimpan", f"File disimpan di:\n{saved_path}")

    def apply_motion_detection(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        motion_detected = False

        if self.previous_gray is None:
            self.previous_gray = gray
            return frame

        frame_delta = cv2.absdiff(self.previous_gray, gray)
        threshold = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        threshold = cv2.dilate(threshold, None, iterations=2)

        contours, _ = cv2.findContours(
            threshold,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        for contour in contours:
            if cv2.contourArea(contour) < self.min_motion_area:
                continue

            motion_detected = True
            x, y, width, height = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 0), 2)

        self.previous_gray = gray

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
            (20, frame.shape[0] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )
        return frame

    def build_color_mask(self, hsv_frame, color_name):
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

    def apply_color_detection(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        selected_color = self.color_combo.currentText()
        colors_to_detect = COLOR_RANGES.keys()

        if selected_color != "semua":
            colors_to_detect = [selected_color]

        for color_name in colors_to_detect:
            mask = self.build_color_mask(hsv, color_name)
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
            f"COLOR MODE: {selected_color.upper()}",
            (20, frame.shape[0] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
        return frame

    def ensure_hand_landmarker_model(self):
        if HAND_MODEL_PATH.exists():
            return True

        HAND_MODEL_PATH.parent.mkdir(exist_ok=True)
        self.status_label.setText("Status: Mengunduh model hand landmarker...")
        QApplication.processEvents()

        try:
            urlretrieve(HAND_MODEL_URL, HAND_MODEL_PATH)
        except (OSError, URLError):
            QMessageBox.warning(
                self,
                "Model gagal diunduh",
                "Model hand landmarker gagal diunduh.\nPastikan perangkat terhubung internet.",
            )
            return False

        return True

    def setup_hand_landmarker(self):
        if self.hand_landmarker is not None:
            return True

        if not MEDIAPIPE_AVAILABLE:
            QMessageBox.warning(
                self,
                "MediaPipe belum tersedia",
                "Install MediaPipe di venv usbcamtest:\n\n"
                "pip install -r requirements-raspberrypi.txt\n"
                "(atau requirements.txt di PC)",
            )
            return False

        if not self.ensure_hand_landmarker_model():
            return False

        base_options = python.BaseOptions(model_asset_path=str(HAND_MODEL_PATH))
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.hand_landmarker = vision.HandLandmarker.create_from_options(options)
        self.hand_start_time = monotonic()
        return True

    def release_hand_landmarker(self):
        if self.hand_landmarker is not None:
            self.hand_landmarker.close()
            self.hand_landmarker = None

        self.hand_start_time = None

    def migrate_yolo_model_to_models_dir(self):
        MODEL_DIR.mkdir(exist_ok=True)

        legacy_dirs = [
            APP_ROOT,
            Path.cwd(),
            Path(__file__).resolve().parent,
        ]

        for legacy_dir in legacy_dirs:
            for legacy_path in legacy_dir.glob("*.pt"):
                target_path = MODEL_DIR / legacy_path.name

                if legacy_path.resolve() != target_path.resolve() and not target_path.exists():
                    legacy_path.replace(target_path)

    def count_raised_fingers(self, hand_landmarks, hand_label):
        raised_fingers = 0
        thumb_tip = hand_landmarks[THUMB_TIP]
        thumb_ip = hand_landmarks[THUMB_IP]

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
            if hand_landmarks[tip_id].y < hand_landmarks[pip_id].y:
                raised_fingers += 1

        return raised_fingers

    def draw_hand_landmarks(self, frame, hand_landmarks):
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

    def apply_hand_detection(self, frame):
        if self.hand_landmarker is None or self.hand_start_time is None:
            return frame

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = int((monotonic() - self.hand_start_time) * 1000)
        results = self.hand_landmarker.detect_for_video(mp_image, timestamp_ms)

        total_fingers = 0
        hand_count = 0

        if results.hand_landmarks and results.handedness:
            for hand_landmarks, handedness_list in zip(
                results.hand_landmarks,
                results.handedness,
            ):
                hand_count += 1
                raw_hand_label = handedness_list[0].category_name
                hand_label = "Left" if raw_hand_label == "Right" else "Right"
                raised_fingers = self.count_raised_fingers(hand_landmarks, hand_label)
                total_fingers += raised_fingers

                self.draw_hand_landmarks(frame, hand_landmarks)

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
        return frame

    def setup_yolo_model(self):
        return self.load_selected_yolo_model(show_errors=True)

    def load_selected_yolo_model(self, show_errors):
        selected_model_path = self.get_selected_yolo_model_path()

        if self.yolo_model is not None and self.yolo_model_path == selected_model_path:
            return True

        if not ULTRALYTICS_AVAILABLE:
            if show_errors:
                QMessageBox.warning(
                    self,
                    "Ultralytics belum tersedia",
                    "Install dependensi di venv usbcamtest:\n\n"
                    "Raspberry Pi:\n"
                    "  pip install -r requirements-raspberrypi.txt\n"
                    "PC:\n"
                    "  pip install -r requirements.txt",
                )
            return False

        torch_ok, torch_message = check_pytorch_for_arm()
        if not torch_ok:
            if show_errors:
                QMessageBox.warning(self, "PyTorch tidak cocok", torch_message)
            return False

        self.status_label.setText(f"Status: Memuat model YOLO {selected_model_path.name}...")
        QApplication.processEvents()
        self.migrate_yolo_model_to_models_dir()
        selected_model_path = self.get_selected_yolo_model_path()

        try:
            model_source = selected_model_path if selected_model_path.exists() else selected_model_path.name
            self.yolo_model = YOLO(str(model_source))
            self.yolo_model_path = selected_model_path
            self.migrate_yolo_model_to_models_dir()
            self.refresh_yolo_model_combo()
        except Exception as error:
            if show_errors:
                QMessageBox.warning(
                    self,
                    "YOLO gagal dimuat",
                    f"Model YOLO gagal dimuat:\n{error}",
                )

            self.yolo_model = None
            self.yolo_model_path = None
            return False

        self.populate_yolo_object_combo()
        self.status_label.setText(f"Status: Model YOLO aktif: {selected_model_path.name}")
        return True

    def populate_yolo_object_combo(self):
        current_text = self.yolo_object_combo.currentText()
        self.yolo_object_combo.clear()
        self.yolo_object_combo.addItem("semua")

        for class_id in sorted(self.yolo_model.names):
            self.yolo_object_combo.addItem(self.yolo_model.names[class_id])

        if current_text:
            index = self.yolo_object_combo.findText(current_text)

            if index >= 0:
                self.yolo_object_combo.setCurrentIndex(index)

    def get_selected_yolo_class_id(self):
        selected_object = self.yolo_object_combo.currentText()

        if selected_object == "semua":
            return None

        for class_id, object_name in self.yolo_model.names.items():
            if object_name == selected_object:
                return class_id

        return None

    def apply_yolo_detection(self, frame):
        if self.yolo_model is None:
            return frame

        confidence_threshold = float(self.yolo_confidence_combo.currentText())
        selected_class_id = self.get_selected_yolo_class_id()
        predict_options = {
            "conf": confidence_threshold,
            "imgsz": YOLO_IMGSZ,
            "verbose": False,
        }

        if selected_class_id is not None:
            predict_options["classes"] = [selected_class_id]

        results = self.yolo_model.predict(frame, **predict_options)
        result = results[0]
        annotated_frame = result.plot()

        object_count = 0
        if result.boxes is not None:
            object_count = len(result.boxes)

        selected_object = self.yolo_object_combo.currentText()
        cv2.putText(
            annotated_frame,
            f"YOLO: {selected_object} | Objek: {object_count} | Conf: {confidence_threshold}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
        return annotated_frame

    def update_frame(self):
        if self.cap is None:
            return

        ret, frame = self.cap.read()

        if not ret:
            self.status_label.setText("Status: Gagal membaca frame kamera")
            self.stop_camera()
            return

        frame = cv2.flip(frame, 1)
        display_frame = frame.copy()
        selected_level = self.level_combo.currentText()

        if selected_level.startswith("Level 3"):
            display_frame = self.apply_motion_detection(display_frame)
        elif selected_level.startswith("Level 4"):
            self.previous_gray = None
            display_frame = self.apply_color_detection(display_frame)
        elif selected_level.startswith("Level 6"):
            self.previous_gray = None
            display_frame = self.apply_hand_detection(display_frame)
        elif selected_level.startswith("Level 7"):
            self.previous_gray = None
            display_frame = self.apply_yolo_detection(display_frame)
        else:
            self.previous_gray = None

        self.last_frame = display_frame.copy()

        if self.is_recording and self.video_writer is not None:
            cv2.putText(
                display_frame,
                "REC",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2,
            )
            self.video_writer.write(display_frame)

        rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        height, width, channel = rgb_frame.shape
        bytes_per_line = channel * width

        image = QImage(
            rgb_frame.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_RGB888,
        ).copy()

        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(
            self.preview_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled_pixmap)

    def closeEvent(self, event):
        self.stop_camera()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec())
