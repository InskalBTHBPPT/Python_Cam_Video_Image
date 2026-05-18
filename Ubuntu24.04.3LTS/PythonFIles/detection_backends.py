"""
Backend deteksi objek Level 7 — dipilih satu per satu di GUI.

1. yolo      — Ultralytics PyTorch (imgsz=320)
2. mobilenet — OpenCV DNN MobileNet-SSD (cepat di Pi)
3. mediapipe — MediaPipe EfficientDet-Lite0
4. ncnn      — folder hasil `yolo export format=ncnn` (Ultralytics)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from time import monotonic
from urllib.error import URLError
from urllib.request import urlretrieve

import cv2
import numpy as np

YOLO_IMGSZ = 320

BACKEND_CHOICES = [
    ("yolo", "1. YOLO PyTorch (akurat, lambat di Pi)"),
    ("mobilenet", "2. MobileNet-SSD (cepat, OpenCV)"),
    ("mediapipe", "3. MediaPipe EfficientDet (cepat)"),
    ("ncnn", "4. NCNN YOLO (cepat, perlu export)"),
]

MOBILENET_PROTOTXT_URL = (
    "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/dnn/"
    "MobileNetSSD_deploy.prototxt"
)
MOBILENET_CAFFEMODEL_URL = (
    "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/dnn/"
    "MobileNetSSD_deploy.caffemodel"
)

MOBILENET_CLASSES = [
    "background",
    "aeroplane",
    "bicycle",
    "bird",
    "boat",
    "bottle",
    "bus",
    "car",
    "cat",
    "chair",
    "cow",
    "diningtable",
    "dog",
    "horse",
    "motorbike",
    "person",
    "pottedplant",
    "sheep",
    "sofa",
    "train",
    "tvmonitor",
]

MEDIAPIPE_OBJECT_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/object_detector/"
    "efficientdet_lite0/float16/1/efficientdet_lite0.tflite"
)


class DetectionResult:
    def __init__(self, frame: np.ndarray, object_count: int, summary: str):
        self.frame = frame
        self.object_count = object_count
        self.summary = summary


class ObjectDetectorBackend(ABC):
    backend_id: str = ""
    display_name: str = ""

    @abstractmethod
    def load(self, model_dir: Path, yolo_model_name: str) -> tuple[bool, str]:
        """Muat model. Kembalikan (berhasil, pesan_error)."""

    @abstractmethod
    def detect(
        self,
        frame: np.ndarray,
        confidence: float,
        class_filter: str | None,
    ) -> DetectionResult:
        """Deteksi pada satu frame BGR."""

    @abstractmethod
    def class_names(self) -> list[str]:
        """Daftar nama kelas untuk filter (tanpa 'semua')."""

    def release(self):
        """Bebaskan sumber daya."""


class YoloPytorchBackend(ObjectDetectorBackend):
    backend_id = "yolo"
    display_name = "YOLO PyTorch"

    def __init__(self, yolo_class=None, torch_check=None):
        self._yolo_class = yolo_class
        self._torch_check = torch_check
        self._model = None
        self._model_path: Path | None = None
        self._loaded_name: str | None = None

    def load(self, model_dir: Path, yolo_model_name: str) -> tuple[bool, str]:
        if self._yolo_class is None:
            return False, "Ultralytics belum terpasang."

        if self._torch_check is not None:
            ok, message = self._torch_check()
            if not ok:
                return False, message

        model_path = model_dir / yolo_model_name
        source = model_path if model_path.exists() else yolo_model_name

        try:
            self._model = self._yolo_class(str(source))
            self._model_path = model_path
            self._loaded_name = yolo_model_name
        except Exception as error:
            self._model = None
            return False, f"Model YOLO gagal dimuat:\n{error}"

        return True, ""

    def detect(self, frame, confidence, class_filter):
        options = {"conf": confidence, "imgsz": YOLO_IMGSZ, "verbose": False}
        class_id = self._resolve_class_id(class_filter)
        if class_id is not None:
            options["classes"] = [class_id]

        results = self._model.predict(frame, **options)
        result = results[0]
        annotated = result.plot()
        count = len(result.boxes) if result.boxes is not None else 0
        label = class_filter or "semua"
        summary = f"YOLO: {label} | Objek: {count} | Conf: {confidence}"
        return DetectionResult(annotated, count, summary)

    def class_names(self) -> list[str]:
        if self._model is None:
            return []
        return [self._model.names[i] for i in sorted(self._model.names)]

    def _resolve_class_id(self, class_filter: str | None):
        if not class_filter or self._model is None:
            return None
        for class_id, name in self._model.names.items():
            if name == class_filter:
                return class_id
        return None

    def release(self):
        self._model = None
        self._model_path = None


class MobileNetBackend(ObjectDetectorBackend):
    backend_id = "mobilenet"
    display_name = "MobileNet-SSD"

    def __init__(self):
        self._net = None

    def load(self, model_dir: Path, yolo_model_name: str) -> tuple[bool, str]:
        del yolo_model_name
        prototxt = model_dir / "MobileNetSSD_deploy.prototxt"
        weights = model_dir / "MobileNetSSD_deploy.caffemodel"
        model_dir.mkdir(exist_ok=True)

        try:
            if not prototxt.exists():
                urlretrieve(MOBILENET_PROTOTXT_URL, prototxt)
            if not weights.exists():
                urlretrieve(MOBILENET_CAFFEMODEL_URL, weights)
        except (OSError, URLError) as error:
            return False, f"Unduhan MobileNet gagal:\n{error}"

        try:
            self._net = cv2.dnn.readNetFromCaffe(str(prototxt), str(weights))
        except Exception as error:
            self._net = None
            return False, f"MobileNet gagal dimuat:\n{error}"

        return True, ""

    def detect(self, frame, confidence, class_filter):
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 0.007843, (300, 300), 127.5)
        self._net.setInput(blob)
        detections = self._net.forward()

        annotated = frame.copy()
        count = 0

        for i in range(detections.shape[2]):
            score = float(detections[0, 0, i])
            if score < confidence:
                continue

            class_id = int(detections[0, 1, i])
            if class_id < 0 or class_id >= len(MOBILENET_CLASSES):
                continue

            label = MOBILENET_CLASSES[class_id]
            if label == "background":
                continue
            if class_filter and label != class_filter:
                continue

            box = detections[0, 3:7, i] * np.array([w, h, w, h])
            x1, y1, x2, y2 = box.astype(int)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                annotated,
                f"{label} {score:.2f}",
                (x1, max(y1 - 8, 0)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )
            count += 1

        label = class_filter or "semua"
        summary = f"MobileNet: {label} | Objek: {count} | Conf: {confidence}"
        return DetectionResult(annotated, count, summary)

    def class_names(self) -> list[str]:
        return [name for name in MOBILENET_CLASSES if name != "background"]

    def release(self):
        self._net = None


class MediaPipeObjectBackend(ObjectDetectorBackend):
    backend_id = "mediapipe"
    display_name = "MediaPipe EfficientDet"

    def __init__(self, mp_module=None, vision_module=None, python_module=None):
        self._mp = mp_module
        self._vision = vision_module
        self._python = python_module
        self._detector = None
        self._start_time = None

    def load(self, model_dir: Path, yolo_model_name: str) -> tuple[bool, str]:
        del yolo_model_name
        if self._mp is None or self._vision is None:
            return False, "MediaPipe belum terpasang.\npip install mediapipe"

        model_path = model_dir / "efficientdet_lite0.tflite"
        model_dir.mkdir(exist_ok=True)

        if not model_path.exists():
            try:
                urlretrieve(MEDIAPIPE_OBJECT_MODEL_URL, model_path)
            except (OSError, URLError) as error:
                return False, f"Unduhan model MediaPipe gagal:\n{error}"

        try:
            if self._detector is not None:
                self._detector.close()

            base_options = self._python.BaseOptions(model_asset_path=str(model_path))
            options = self._vision.ObjectDetectorOptions(
                base_options=base_options,
                running_mode=self._vision.RunningMode.VIDEO,
                score_threshold=0.4,
                max_results=10,
            )
            self._detector = self._vision.ObjectDetector.create_from_options(options)
            self._start_time = monotonic()
        except Exception as error:
            self._detector = None
            return False, f"MediaPipe Object Detector gagal:\n{error}"

        return True, ""

    def detect(self, frame, confidence, class_filter):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = int((monotonic() - self._start_time) * 1000)
        result = self._detector.detect_for_video(mp_image, timestamp_ms)

        annotated = frame.copy()
        count = 0

        for detection in result.detections:
            score = detection.categories[0].score
            if score < confidence:
                continue

            label = detection.categories[0].category_name
            if class_filter and label != class_filter:
                continue

            bbox = detection.bounding_box
            x1 = int(bbox.origin_x * frame.shape[1])
            y1 = int(bbox.origin_y * frame.shape[0])
            x2 = int((bbox.origin_x + bbox.width) * frame.shape[1])
            y2 = int((bbox.origin_y + bbox.height) * frame.shape[0])
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 128, 0), 2)
            cv2.putText(
                annotated,
                f"{label} {score:.2f}",
                (x1, max(y1 - 8, 0)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 128, 0),
                2,
            )
            count += 1

        filter_label = class_filter or "semua"
        summary = f"MediaPipe: {filter_label} | Objek: {count} | Conf: {confidence}"
        return DetectionResult(annotated, count, summary)

    def class_names(self) -> list[str]:
        return []

    def release(self):
        if self._detector is not None:
            self._detector.close()
        self._detector = None
        self._start_time = None


class NcnnYoloBackend(ObjectDetectorBackend):
    backend_id = "ncnn"
    display_name = "NCNN YOLO"

    def __init__(self, yolo_class=None):
        self._yolo_class = yolo_class
        self._model = None
        self._export_dir: Path | None = None
        self._loaded_name: str | None = None

    def load(self, model_dir: Path, yolo_model_name: str) -> tuple[bool, str]:
        if self._yolo_class is None:
            return False, "Ultralytics belum terpasang (untuk inferensi NCNN)."

        stem = Path(yolo_model_name).stem
        export_dir = model_dir / f"{stem}_ncnn_model"

        if not export_dir.is_dir():
            return (
                False,
                f"Folder NCNN tidak ditemukan:\n{export_dir}\n\n"
                "Export sekali di venv:\n"
                f"  yolo export model={yolo_model_name} format=ncnn imgsz=320",
            )

        try:
            self._model = self._yolo_class(str(export_dir))
            self._export_dir = export_dir
            self._loaded_name = yolo_model_name
        except Exception as error:
            self._model = None
            return False, f"NCNN YOLO gagal dimuat:\n{error}"

        return True, ""

    def detect(self, frame, confidence, class_filter):
        options = {"conf": confidence, "imgsz": YOLO_IMGSZ, "verbose": False}
        if self._model is not None and class_filter:
            for class_id, name in self._model.names.items():
                if name == class_filter:
                    options["classes"] = [class_id]
                    break

        results = self._model.predict(frame, **options)
        result = results[0]
        annotated = result.plot()
        count = len(result.boxes) if result.boxes is not None else 0
        label = class_filter or "semua"
        summary = f"NCNN: {label} | Objek: {count} | Conf: {confidence}"
        return DetectionResult(annotated, count, summary)

    def class_names(self) -> list[str]:
        if self._model is None:
            return []
        return [self._model.names[i] for i in sorted(self._model.names)]

    def release(self):
        self._model = None
        self._export_dir = None


def create_backend(
    backend_id: str,
    *,
    yolo_class=None,
    torch_check=None,
    mp_module=None,
    vision_module=None,
    python_module=None,
) -> ObjectDetectorBackend:
    if backend_id == "yolo":
        return YoloPytorchBackend(yolo_class=yolo_class, torch_check=torch_check)
    if backend_id == "mobilenet":
        return MobileNetBackend()
    if backend_id == "mediapipe":
        return MediaPipeObjectBackend(
            mp_module=mp_module,
            vision_module=vision_module,
            python_module=python_module,
        )
    if backend_id == "ncnn":
        return NcnnYoloBackend(yolo_class=yolo_class)
    return YoloPytorchBackend(yolo_class=yolo_class, torch_check=torch_check)
