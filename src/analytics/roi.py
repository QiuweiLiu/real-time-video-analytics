"""ROI / Occupancy / Dwell — minimal polygon + dwell tracking."""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from collections import defaultdict

from ..vision.types import Track


def point_in_polygon(pt: Tuple[float,float], polygon: List[Tuple[float,float]]) -> bool:
    """Ray casting, includes edge as inside. polygon: list of (x,y)."""
    x, y = pt
    n = len(polygon)
    inside = False
    # epsilon for edge check
    eps = 1e-9
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i+1) % n]
        # check on edge: distance to segment small and within bbox
        # cross product zero and within segment
        cross = (x2 - x1)*(y - y1) - (y2 - y1)*(x - x1)
        if abs(cross) < 1e-6:
            if min(x1,x2)-eps <= x <= max(x1,x2)+eps and min(y1,y2)-eps <= y <= max(y1,y2)+eps:
                return True
        # ray crossing
        if ((y1 > y) != (y2 > y)):
            xinters = (x2 - x1)*(y - y1) / (y2 - y1 + eps) + x1
            if x <= xinters:
                inside = not inside
    return inside


@dataclass(frozen=True)
class DwellEvent:
    frame_idx: int
    track_id: int
    class_id: int
    class_name: str
    enter_frame: int
    duration_sec: float
    center: Tuple[float,float]
    polygon: Tuple[Tuple[float,float], ...]


class ROIAnalytics:
    """Single polygon ROI that provides occupancy and dwell.

    - occupancy: current count inside
    - dwell: emit once per track when continuous stay >= dwell_sec
    - classes filter optional
    - supports normalized polygon (0-1) via frame_size
    """

    def __init__(
        self,
        polygon: List[Tuple[float,float]],
        dwell_sec: float = 1.5,
        fps: float = 20.0,
        classes: Optional[List[int]] = None,
        frame_width: Optional[int] = None,
        frame_height: Optional[int] = None,
    ):
        self.raw_polygon = tuple(tuple(float(c) for c in pt) for pt in polygon)
        self.polygon = tuple(tuple(float(c) for c in pt) for pt in polygon)
        self.dwell_sec = float(dwell_sec)
        self.fps = float(fps) if fps and fps>0 else 20.0
        self.classes = set(classes) if classes is not None else None
        self.frame_width = frame_width
        self.frame_height = frame_height

        if frame_width and frame_height:
            self._resolve_normalized()

        if len(self.polygon) < 3:
            raise ValueError(f"polygon need >=3 points, got {polygon}")
        self._dwell_frames = int(self.dwell_sec * self.fps + 0.5)
        if self._dwell_frames < 1:
            self._dwell_frames = 1

        # per track: {tid: {enter_frame, last_inside, triggered}}
        self._state: Dict[int, Dict] = {}
        self._events: List[DwellEvent] = []
        self._max_occupancy = 0
        self._occupancy_by_class: Dict[str,int] = defaultdict(int)
        self._history_occupancy: List[int] = []

    def _resolve_normalized(self):
        # if all coords 0-1, treat as normalized
        if all(0 <= c <= 1 for pt in self.raw_polygon for c in pt):
            self.polygon = tuple((pt[0]*self.frame_width, pt[1]*self.frame_height) for pt in self.raw_polygon)

    def set_frame_size(self, w: int, h: int, fps: Optional[float]=None):
        self.frame_width = w
        self.frame_height = h
        if fps:
            self.fps = float(fps)
            self._dwell_frames = int(self.dwell_sec * self.fps + 0.5)
        if all(0 <= c <= 1 for pt in self.raw_polygon for c in pt):
            self.polygon = tuple((pt[0]*w, pt[1]*h) for pt in self.raw_polygon)

    def update(self, tracks: List[Track], frame_idx: int) -> Dict:
        """
        Returns dict:
          occupancy: int
          inside_ids: List[int]
          dwell_events: List[DwellEvent] newly triggered this frame
          max_occupancy: int
        """
        inside_ids = []
        newly = []
        # filter by class if needed, but occupancy only counts filtered? Use classes filter for roi
        for tr in tracks:
            if self.classes is not None and tr.class_id not in self.classes:
                # still need to maintain state? skip to avoid counting, but also clear if previously inside
                # if previously inside and now filtered, treat as outside (exit)
                st = self._state.get(tr.track_id)
                if st and st.get("inside"):
                    # leaving due to class filter
                    st["inside"] = False
                    st["triggered"] = False
                continue
            inside = point_in_polygon(tr.center, list(self.polygon))
            tid = tr.track_id
            st = self._state.get(tid)
            if st is None:
                st = {"enter_frame": None, "inside": False, "triggered": False, "last_seen": frame_idx}
                self._state[tid] = st
            st["last_seen"] = frame_idx

            if inside:
                inside_ids.append(tid)
                if not st["inside"]:
                    # entering
                    st["inside"] = True
                    st["enter_frame"] = frame_idx
                    st["triggered"] = False
                else:
                    # staying — check dwell
                    if not st["triggered"]:
                        dur_frames = frame_idx - st["enter_frame"] + 1
                        if dur_frames >= self._dwell_frames:
                            dur_sec = dur_frames / self.fps
                            ev = DwellEvent(
                                frame_idx=frame_idx,
                                track_id=tid,
                                class_id=tr.class_id,
                                class_name=tr.class_name,
                                enter_frame=st["enter_frame"],
                                duration_sec=round(dur_sec,2),
                                center=tr.center,
                                polygon=self.polygon,
                            )
                            self._events.append(ev)
                            newly.append(ev)
                            st["triggered"] = True
            else:
                if st["inside"]:
                    # exiting
                    st["inside"] = False
                    st["triggered"] = False
                    st["enter_frame"] = None

        # cleanup: tracks not seen for a while? Keep but if not seen for > fps*2, reset entry
        # For minimal, keep forever; ByteTrack may keep ID for 30 frames; dwell will remain.
        occupancy = len(inside_ids)
        self._max_occupancy = max(self._max_occupancy, occupancy)
        self._history_occupancy.append(occupancy)
        # occupancy by class current
        by_class = defaultdict(int)
        for tr in tracks:
            if tr.track_id in inside_ids:
                by_class[tr.class_name] += 1

        return {
            "occupancy": occupancy,
            "inside_ids": sorted(inside_ids),
            "dwell_events": newly,
            "max_occupancy": self._max_occupancy,
            "by_class": dict(by_class),
            "total_dwell": len(self._events),
        }

    def get_events(self) -> List[DwellEvent]:
        return list(self._events)

    def get_polygon(self) -> Tuple[Tuple[float,float], ...]:
        return self.polygon

    def __repr__(self):
        return f"ROIAnalytics(polygon={self.polygon}, dwell={self.dwell_sec}s@{self.fps}fps={self._dwell_frames}f, max_occ={self._max_occupancy})"
