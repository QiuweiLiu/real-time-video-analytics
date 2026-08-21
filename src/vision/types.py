"""Custom Track structure — decouples downstream from ultralytics Results format."""

from dataclasses import dataclass
from typing import Tuple, List


@dataclass(frozen=True)
class Track:
    """Minimal track representation for all downstream modules.

    Attributes:
        track_id: stable ID from ByteTrack
        class_id: integer class index (COCO)
        class_name: human-readable label (e.g. 'person')
        confidence: detection confidence [0,1]
        bbox: (x1, y1, x2, y2) in absolute pixel coordinates (float)
        center: (cx, cy) derived from bbox
    """

    track_id: int
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[float, float, float, float]
    center: Tuple[float, float]

    @staticmethod
    def from_values(
        track_id: int,
        class_id: int,
        class_name: str,
        confidence: float,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
    ) -> "Track":
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        return Track(
            track_id=int(track_id),
            class_id=int(class_id),
            class_name=str(class_name),
            confidence=float(confidence),
            bbox=(float(x1), float(y1), float(x2), float(y2)),
            center=(float(cx), float(cy)),
        )


def tracks_from_results(result) -> List[Track]:
    """Convert a single ultralytics Results object to List[Track].

    Handles:
    - empty detections (boxes is None or len 0)
    - tracking vs detection mode (6 cols vs 7 cols)
    - tensor / ndarray conversion
    """
    if result.boxes is None or len(result.boxes) == 0:
        return []

    # Ensure numpy for uniform handling
    boxes = result.boxes
    # .xyxy, .conf, .cls, .id may be tensors
    try:
        xyxy = boxes.xyxy.cpu().numpy() if hasattr(boxes.xyxy, "cpu") else boxes.xyxy
        confs = boxes.conf.cpu().numpy() if hasattr(boxes.conf, "cpu") else boxes.conf
        clss = boxes.cls.cpu().numpy() if hasattr(boxes.cls, "cpu") else boxes.cls
        ids = boxes.id.cpu().numpy() if boxes.id is not None and hasattr(boxes.id, "cpu") else (boxes.id if boxes.id is not None else None)
        if ids is not None and hasattr(ids, "numpy"):
            ids = ids  # already
        # handle torch tensor ids that were not cpu-converted due to missing .cpu? above covers
    except Exception:
        # fallback: try direct numpy conversion
        xyxy = boxes.xyxy
        confs = boxes.conf
        clss = boxes.cls
        ids = boxes.id
        import numpy as np
        if hasattr(xyxy, "numpy"):
            xyxy = xyxy.numpy()
        if hasattr(confs, "numpy"):
            confs = confs.numpy()
        if hasattr(clss, "numpy"):
            clss = clss.numpy()
        if ids is not None and hasattr(ids, "numpy"):
            ids = ids.numpy()

    import numpy as np

    xyxy = np.asarray(xyxy)
    confs = np.asarray(confs)
    clss = np.asarray(clss)
    if ids is not None:
        ids = np.asarray(ids).flatten()
    else:
        # detection mode without tracking — assign -1
        ids = np.full((len(xyxy),), -1, dtype=int)

    names = getattr(result, "names", {})

    tracks: List[Track] = []
    for i in range(len(xyxy)):
        x1, y1, x2, y2 = [float(v) for v in xyxy[i]]
        tid = int(ids[i]) if i < len(ids) else -1
        cid = int(clss[i])
        conf = float(confs[i])
        cname = names.get(cid, str(cid)) if isinstance(names, dict) else str(cid)
        tracks.append(
            Track.from_values(tid, cid, cname, conf, x1, y1, x2, y2)
        )
    return tracks
