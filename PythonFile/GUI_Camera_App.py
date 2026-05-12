from datetime import datetime
from pathlib import Path
import sys

import cv2
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class CameraApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Python Camera GUI - Tahap 3")
        self.resize(960, 640)

        self.cap = None
        self.last_frame = None
        self.video_writer = None
        self.current_recording_path = None
        self.is_recording = False
        self.capture_dir = Path("captures")
        self.recording_dir = Path("recordings")
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
        self.camera_combo.setCurrentText("1")

        self.start_button = QPushButton("Start Camera")
        self.stop_button = QPushButton("Stop Camera")
        self.capture_button = QPushButton("Save Capture Image")
        self.record_button = QPushButton("Start Record")
        self.stop_button.setEnabled(False)
        self.capture_button.setEnabled(False)
        self.record_button.setEnabled(False)

        self.status_label = QLabel("Status: Kamera belum aktif")
        self.status_label.setAlignment(Qt.AlignLeft)

        self.preview_label = QLabel("Preview kamera akan tampil di sini")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(800, 500)
        self.preview_label.setStyleSheet(
            "background-color: #202020; color: white; border: 1px solid #555;"
        )

        self.start_button.clicked.connect(self.start_camera)
        self.stop_button.clicked.connect(self.stop_camera)
        self.capture_button.clicked.connect(self.save_capture_image)
        self.record_button.clicked.connect(self.toggle_recording)

        controls_layout = QGridLayout()
        controls_layout.addWidget(QLabel("Pilih Level:"), 0, 0)
        controls_layout.addWidget(self.level_combo, 0, 1)
        controls_layout.addWidget(QLabel("Camera Index:"), 0, 2)
        controls_layout.addWidget(self.camera_combo, 0, 3)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.capture_button)
        button_layout.addWidget(self.record_button)
        button_layout.addStretch()

        main_layout = QVBoxLayout()
        main_layout.addLayout(controls_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.preview_label)
        main_layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def start_camera(self):
        camera_index = int(self.camera_combo.currentText())
        selected_level = self.level_combo.currentText()

        self.cap = cv2.VideoCapture(camera_index)

        if not self.cap.isOpened():
            self.cap.release()
            self.cap = None
            self.status_label.setText(f"Status: Kamera index {camera_index} tidak terdeteksi")
            return

        self.timer.start(30)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.capture_button.setEnabled(True)
        self.record_button.setEnabled(True)
        self.level_combo.setEnabled(False)
        self.camera_combo.setEnabled(False)
        self.status_label.setText(f"Status: Kamera aktif | {selected_level}")

    def stop_camera(self):
        if self.is_recording:
            self.stop_recording(show_notification=True)

        self.timer.stop()

        if self.cap is not None:
            self.cap.release()
            self.cap = None

        self.preview_label.clear()
        self.preview_label.setText("Preview kamera akan tampil di sini")
        self.last_frame = None
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.capture_button.setEnabled(False)
        self.record_button.setEnabled(False)
        self.record_button.setText("Start Record")
        self.level_combo.setEnabled(True)
        self.camera_combo.setEnabled(True)
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

        filename = self.recording_dir / f"gui_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
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

    def update_frame(self):
        if self.cap is None:
            return

        ret, frame = self.cap.read()

        if not ret:
            self.status_label.setText("Status: Gagal membaca frame kamera")
            self.stop_camera()
            return

        frame = cv2.flip(frame, 1)
        self.last_frame = frame.copy()

        display_frame = frame.copy()

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
