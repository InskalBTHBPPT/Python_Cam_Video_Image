#!/usr/bin/env python3
"""Tes singkat: torch CPU + inferensi YOLO (untuk Raspberry Pi / debug venv)."""
import sys
from pathlib import Path

import numpy as np

APP_ROOT = Path(__file__).resolve().parent
MODEL = APP_ROOT / "models" / "yolo11n.pt"


def main():
    import torch

    version = torch.__version__
    print(f"torch: {version}")

    if "+cu" in version:
        print("ERROR: torch bertanda CUDA (+cu) — tidak cocok untuk Pi 4.")
        return 1

    from ultralytics import YOLO

    source = MODEL if MODEL.exists() else "yolo11n.pt"
    print(f"model: {source}")
    model = YOLO(str(source))

    frame = np.zeros((320, 320, 3), dtype=np.uint8)
    results = model.predict(frame, conf=0.5, imgsz=320, verbose=False)
    n = len(results[0].boxes) if results[0].boxes is not None else 0
    print(f"YOLO predict: OK (deteksi pada frame kosong: {n} objek)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
