"""Pembukaan kamera V4L2 yang stabil di Ubuntu / Raspberry Pi (USB webcam)."""
import platform

import cv2

# MJPG + resolusi tetap menghindari gambar "terpotong" / bagian atas-bawah tertukar (buffer YUYV).
DEFAULT_WIDTH = 640
DEFAULT_HEIGHT = 320
WARMUP_FRAMES = 10


def configure_linux_camera(
    cap: cv2.VideoCapture,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
) -> tuple[int, int]:
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if width <= 0 or height <= 0:
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"YUYV"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    for _ in range(WARMUP_FRAMES):
        cap.read()

    return width, height


def open_video_capture(
    camera_index: int,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
) -> cv2.VideoCapture:
    if platform.system() == "Linux":
        cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
        if cap.isOpened():
            configure_linux_camera(cap, width, height)
        return cap
    cap = cv2.VideoCapture(camera_index)
    if cap.isOpened():
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    return cap
