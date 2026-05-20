"""Deteksi gerakan frame-differencing — sama seperti Level_3_Deteksi_Gerakan.py."""
from __future__ import annotations

import cv2
import numpy as np

# Referensi Level 3 @ 640×480.
BASE_MIN_MOTION_AREA = 1000
BASE_FRAME_PIXELS = 640 * 480


def scaled_min_motion_area(
    width: int,
    height: int,
    base_area: int = BASE_MIN_MOTION_AREA,
) -> int:
    return max(100, int(base_area * width * height / BASE_FRAME_PIXELS))


class MotionDetector:
    """Background subtraction sederhana: absdiff + kontur."""

    def __init__(self, min_motion_area: int) -> None:
        self._min_motion_area = min_motion_area
        self._previous_gray: np.ndarray | None = None

    def reset(self) -> None:
        self._previous_gray = None

    def process(self, frame: np.ndarray) -> tuple[np.ndarray, bool]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        motion_detected = False

        if self._previous_gray is None:
            self._previous_gray = gray
            return frame, False

        frame_delta = cv2.absdiff(self._previous_gray, gray)
        threshold = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        threshold = cv2.dilate(threshold, None, iterations=2)

        contours, _ = cv2.findContours(
            threshold,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        for contour in contours:
            if cv2.contourArea(contour) < self._min_motion_area:
                continue

            motion_detected = True
            x, y, width, height = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 0), 2)

        self._previous_gray = gray

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

        return frame, motion_detected
