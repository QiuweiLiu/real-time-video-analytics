"""YOLO + ByteTrack wrapper — owns model lifecycle and Track conversion."""

from pathlib import Path
from typing import List
import numpy as np

from ultralytics import YOLO

from .types import Track, tracks_from_results
from ..utils.device import resolve_device


class YOLOTracker:
    """Thin wrapper around ultralytics YOLO.track.

    - Model loading handled here (auto-download if yolov8n.pt missing via ultralytics cache)
    - Device resolved via utils/device (auto -> mps/cuda/cpu)
    - `track(frame)` returns List[Track] with stable IDs, no ultralytics leakage
    """

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        device: str = "auto",
        conf: float = 0.25,
        iou: float = 0.5,
        tracker: str = "bytetrack.yaml",
        imgsz: int = 640,
        classes: list[int] | None = None,
        verbose: bool = False,
    ):
        self.raw_device = device
        self.device = resolve_device(device)
        self.conf = conf
        self.iou = iou
        self.tracker = tracker
        self.imgsz = imgsz
        self.classes = classes
        self.verbose = verbose

        # YOLO will auto-download to cache if model_path is like yolov8n.pt
        # If user gives absolute path, use as-is
        self.model_path = model_path
        self.model = YOLO(model_path)

    def track(self, frame: np.ndarray) -> List[Track]:
        """Track on a single BGR frame (np.ndarray HxWx3 uint8)."""
        if frame is None or frame.size == 0:
            return []

        # ultralytics expects BGR ndarray; persist=True keeps IDs across frames
        results = self.model.track(
            source=frame,
            persist=True,
            conf=self.conf,
            iou=self.iou,
            device=self.device,
            tracker=self.tracker,
            imgsz=self.imgsz,
            classes=self.classes,
            verbose=self.verbose,
        )
        if not results:
            return []
        return tracks_from_results(results[0])

    def close(self):
        # placeholder for future resource cleanup
        pass

    def __repr__(self) -> str:
        return f"YOLOTracker(model={self.model_path}, device={self.device}<-{self.raw_device}, conf={self.conf}, tracker={self.tracker})"
