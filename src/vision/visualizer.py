"""Minimal visualizer — draws bbox, class, ID."""

import cv2
import numpy as np
from typing import List
from .types import Track


# Distinct palette (BGR) — hash id mod len
_PALETTE = [
    (56, 56, 255),   # red
    (56, 255, 56),   # green
    (255, 56, 56),   # blue
    (255, 178, 56),  # orange
    (255, 56, 178),  # magenta
    (178, 56, 255),  # purple
    (56, 255, 178),  # cyan
    (178, 255, 56),  # lime
]


def _color_for_id(track_id: int):
    return _PALETTE[track_id % len(_PALETTE)] if track_id >= 0 else (200, 200, 200)


def draw_tracks(frame: np.ndarray, tracks: List[Track]) -> np.ndarray:
    """Draw tracks on a copy of frame and return it."""
    out = frame.copy()
    for t in tracks:
        x1, y1, x2, y2 = map(int, map(round, t.bbox))
        color = _color_for_id(t.track_id)
        # bbox
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        # label background
        label = f"{t.class_name} #{t.track_id} {t.confidence:.2f}"
        (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        # ensure text stays inside
        ty1 = max(0, y1 - th - 8)
        ty2 = y1
        cv2.rectangle(out, (x1, ty1), (x1 + tw + 6, ty2), color, -1)
        cv2.putText(out, label, (x1 + 3, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        # center dot
        cx, cy = int(round(t.center[0])), int(round(t.center[1]))
        cv2.circle(out, (cx, cy), 3, color, -1)
    return out
