"""Snapshot saver — bbox crop with expand & clamp."""

import cv2
import numpy as np
from pathlib import Path


def save_snapshot(frame: np.ndarray, bbox: tuple[float,float,float,float], out_dir: str | Path, event_id: str, expand: float = 0.2) -> Path | None:
    """
    Crop frame by bbox (x1,y1,x2,y2) with expand, clamp to frame, save as jpg.
    Returns saved path or None on failure.
    """
    if frame is None or frame.size == 0:
        return None
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = bbox
    # ensure x1 < x2
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1
    bw = x2 - x1
    bh = y2 - y1
    # expand
    ex = bw * expand
    ey = bh * expand
    x1e = max(0, int(round(x1 - ex)))
    y1e = max(0, int(round(y1 - ey)))
    x2e = min(w, int(round(x2 + ex)))
    y2e = min(h, int(round(y2 + ey)))
    # ensure min size 10
    if x2e - x1e < 10:
        cx = (x1e + x2e)//2
        x1e = max(0, cx - 5)
        x2e = min(w, cx + 5)
    if y2e - y1e < 10:
        cy = (y1e + y2e)//2
        y1e = max(0, cy - 5)
        y2e = min(h, cy + 5)
    if x2e <= x1e or y2e <= y1e:
        return None
    crop = frame[y1e:y2e, x1e:x2e]
    if crop.size == 0:
        return None
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{event_id}.jpg"
    # handle duplicate id (should not happen with uuid) but add suffix
    if out_path.exists():
        out_path = out_dir / f"{event_id}_{np.random.randint(1000):03d}.jpg"
    ok = cv2.imwrite(str(out_path), crop)
    return out_path if ok else None
