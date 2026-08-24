"""VideoSource — OpenCV VideoCapture wrapper with basic RTSP/stream support."""

import time

import cv2
from pathlib import Path
from typing import Iterator, Tuple


def _is_stream(path: str) -> bool:
    s = str(path).lower()
    return s.startswith(("rtsp://", "rtmp://", "http://", "https://")) or s.isdigit()


class VideoSource:
    def __init__(
        self,
        path: str | Path,
        max_frames: int | None = None,
        reconnect_attempts: int = 0,
        reconnect_delay: float = 0.5,
    ):
        self.raw_path = str(path)
        self.is_stream = _is_stream(self.raw_path)
        self.max_frames = max_frames  # for RTSP limiting, None = no limit / file's count
        self.reconnect_attempts = reconnect_attempts if self.is_stream else 0
        self.reconnect_delay = reconnect_delay

        if self.is_stream:
            # stream: don't check file exists
            self.path = Path(self.raw_path) if not self.raw_path.isdigit() else Path(self.raw_path)
            # handle numeric camera index
            src = int(self.raw_path) if self.raw_path.isdigit() else self.raw_path
            self.cap = cv2.VideoCapture(src)
        else:
            self.path = Path(path)
            if not self.path.exists():
                raise FileNotFoundError(f"video not found: {self.path.resolve()}")
            self.cap = cv2.VideoCapture(str(self.path))

        if not self.cap.isOpened():
            raise RuntimeError(f"failed to open video: {self.raw_path}")

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        # fallback if not available (RTSP may report 0)
        if self.width <= 0:
            self.width = 640
        if self.height <= 0:
            self.height = 480

        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps is None or self.fps <= 0 or self.fps != self.fps:  # NaN check
            self.fps = 25.0 if self.is_stream else 30.0

        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if self.frame_count <= 0 or self.is_stream:
            self.frame_count = -1
        # apply max_frames for streams
        if self.is_stream and self.max_frames is not None:
            self.frame_count = self.max_frames

        self.fourcc = int(self.cap.get(cv2.CAP_PROP_FOURCC))
        self._read_count = 0

    def _reopen(self) -> bool:
        """Attempt to re-open the stream (best-effort reconnect)."""
        try:
            self.cap.release()
        except Exception:
            pass
        src = int(self.raw_path) if self.raw_path.isdigit() else self.raw_path
        self.cap = cv2.VideoCapture(src)
        return self.cap.isOpened()

    def _read_with_reconnect(self):
        ok, frame = self.cap.read()
        if (ok and frame is not None) or not self.is_stream or self.reconnect_attempts <= 0:
            return ok, frame
        # stream read failed — try reconnect with backoff
        for attempt in range(1, self.reconnect_attempts + 1):
            time.sleep(self.reconnect_delay * attempt)
            if self._reopen():
                ok, frame = self.cap.read()
                if ok and frame is not None:
                    return ok, frame
        return False, None

    def __iter__(self) -> Iterator:
        return self

    def __next__(self):
        if self.max_frames is not None and self._read_count >= self.max_frames:
            raise StopIteration
        ok, frame = self._read_with_reconnect()
        if not ok or frame is None:
            raise StopIteration
        self._read_count += 1
        return frame

    def read(self) -> Tuple[bool, any]:
        if self.max_frames is not None and self._read_count >= self.max_frames:
            return False, None
        ok, frame = self._read_with_reconnect()
        if ok:
            self._read_count += 1
        return ok, frame

    def release(self):
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
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
            "path": str(self.raw_path),
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "frame_count": self.frame_count,
            "is_stream": self.is_stream,
        }
