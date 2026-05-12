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
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class CameraApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Python Camera GUI - Tahap 1")
        self.resize(960, 640)

        self.cap = None
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
        self.stop_button.setEnabled(False)

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

        controls_layout = QGridLayout()
        controls_layout.addWidget(QLabel("Pilih Level:"), 0, 0)
        controls_layout.addWidget(self.level_combo, 0, 1)
        controls_layout.addWidget(QLabel("Camera Index:"), 0, 2)
        controls_layout.addWidget(self.camera_combo, 0, 3)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
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
        self.level_combo.setEnabled(False)
        self.camera_combo.setEnabled(False)
        self.status_label.setText(f"Status: Kamera aktif | {selected_level}")

    def stop_camera(self):
        self.timer.stop()

        if self.cap is not None:
            self.cap.release()
            self.cap = None

        self.preview_label.clear()
        self.preview_label.setText("Preview kamera akan tampil di sini")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.level_combo.setEnabled(True)
        self.camera_combo.setEnabled(True)
        self.status_label.setText("Status: Kamera berhenti")

    def update_frame(self):
        if self.cap is None:
            return

        ret, frame = self.cap.read()

        if not ret:
            self.status_label.setText("Status: Gagal membaca frame kamera")
            self.stop_camera()
            return

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
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
