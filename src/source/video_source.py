"""VideoSource — OpenCV VideoCapture wrapper with context manager and iterator."""

import cv2
from pathlib import Path
from typing import Iterator, Tuple


class VideoSource:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"video not found: {self.path.resolve()}")
        self.cap = cv2.VideoCapture(str(self.path))
        if not self.cap.isOpened():
            raise RuntimeError(f"failed to open video: {self.path}")

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps is None or self.fps <= 0 or self.fps != self.fps:  # NaN check
            self.fps = 30.0
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Some containers report 0
        if self.frame_count <= 0:
            self.frame_count = -1
        self.fourcc = int(self.cap.get(cv2.CAP_PROP_FOURCC))

    def __iter__(self) -> Iterator:
        return self

    def __next__(self):
        ok, frame = self.cap.read()
        if not ok or frame is None:
            raise StopIteration
        return frame

    def read(self) -> Tuple[bool, any]:
        return self.cap.read()

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def __del__(self):
        try:
            self.release()
        except Exception:
            pass

    def info(self) -> dict:
        return {
            "path": str(self.path),
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "frame_count": self.frame_count,
        }
