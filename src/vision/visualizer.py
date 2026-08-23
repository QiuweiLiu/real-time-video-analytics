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


def draw_line_and_counts(frame: np.ndarray, p1, p2, counts: dict, mode: str = "both") -> np.ndarray:
    """Overlay counting line and counter text. Modifies frame in-place for efficiency, returns frame."""
    # line in BGR: yellow for both, green/red for directional
    if mode == "a_to_b":
        line_color = (0, 255, 0)
    elif mode == "b_to_a":
        line_color = (255, 0, 255)
    else:
        line_color = (0, 255, 255)  # yellow both

    x1, y1 = int(round(p1[0])), int(round(p1[1]))
    x2, y2 = int(round(p2[0])), int(round(p2[1]))
    cv2.line(frame, (x1, y1), (x2, y2), line_color, 2, cv2.LINE_AA)
    # arrow mid
    mx, my = (x1 + x2)//2, (y1 + y2)//2
    # perpendicular arrow to indicate direction? simple arrow along line
    cv2.circle(frame, (mx, my), 4, line_color, -1)
    cv2.circle(frame, (mx, my), 4, (0,0,0), 1)

    # counts overlay top-left
    total = counts.get("total", 0)
    a2b = counts.get("a_to_b", 0)
    b2a = counts.get("b_to_a", 0)
    if mode == "both":
        text = f"Count: {total} (A->B:{a2b} B->A:{b2a})"
    elif mode == "a_to_b":
        text = f"Count A->B: {a2b} / {total}"
    else:
        text = f"Count B->A: {b2a} / {total}"

    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
    pad = 6
    cv2.rectangle(frame, (5, 5), (5+tw+pad*2, 5+th+pad*2), (0,0,0), -1)
    cv2.rectangle(frame, (5, 5), (5+tw+pad*2, 5+th+pad*2), line_color, 1)
    cv2.putText(frame, text, (5+pad, 5+th+pad), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2, cv2.LINE_AA)
    # also small legend
    cv2.putText(frame, f"Line {p1}->{p2} mode={mode}", (5, 5+th+pad*2+15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, line_color, 1, cv2.LINE_AA)
    return frame
