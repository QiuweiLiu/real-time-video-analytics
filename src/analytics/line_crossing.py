"""Line crossing counter — minimal, no external dependencies."""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from collections import defaultdict

from ..vision.types import Track


@dataclass(frozen=True)
class CrossingEvent:
    frame_idx: int
    track_id: int
    class_id: int
    class_name: str
    direction: str  # a_to_b | b_to_a
    p1: Tuple[float, float]
    p2: Tuple[float, float]
    center: Tuple[float, float]


def _cross(ax, ay, bx, by):
    return ax * by - ay * bx


def _side(p1, p2, pt):
    """Signed side: cross of (p2-p1) x (pt-p1). >0 = left/a side, <0 = right/b side, 0 = on line."""
    return (p2[0] - p1[0]) * (pt[1] - p1[1]) - (p2[1] - p1[1]) * (pt[0] - p1[0])


def _on_segment(p1, p2, q):
    """Check if q's projection lies within segment p1-p2 bounding box (with epsilon)."""
    eps = 1e-9
    return (min(p1[0], p2[0]) - eps <= q[0] <= max(p1[0], p2[0]) + eps and
            min(p1[1], p2[1]) - eps <= q[1] <= max(p1[1], p2[1]) + eps)


def _segments_intersect(p1, p2, q1, q2):
    """Check if segments p1-p2 and q1-q2 intersect (including endpoints)."""
    # Using orientation method
    def orient(a, b, c):
        v = (b[1]-a[1])*(c[0]-b[0]) - (b[0]-a[0])*(c[1]-b[1])  # variant of cross, but consistent
        # Actually standard: (b-a) x (c-b)
        # For simplicity use cross of (b-a) x (c-a)
        val = (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
        if abs(val) < 1e-9:
            return 0
        return 1 if val > 0 else 2

    def on_seg(a, b, c):
        return (min(a[0], c[0]) - 1e-9 <= b[0] <= max(a[0], c[0]) + 1e-9 and
                min(a[1], c[1]) - 1e-9 <= b[1] <= max(a[1], c[1]) + 1e-9)

    o1 = orient(p1, p2, q1)
    o2 = orient(p1, p2, q2)
    o3 = orient(q1, q2, p1)
    o4 = orient(q1, q2, p2)

    if o1 != o2 and o3 != o4:
        return True
    if o1 == 0 and on_seg(p1, q1, p2): return True
    if o2 == 0 and on_seg(p1, q2, p2): return True
    if o3 == 0 and on_seg(q1, p1, q2): return True
    if o4 == 0 and on_seg(q1, p2, q2): return True
    return False


class LineCrossingCounter:
    """Counts tracks crossing a single directed line.

    Direction semantics:
    - side >0 is "a side" (left of directed line p1->p2)
    - side <0 is "b side"
    - crossing a_to_b: moving from a side ( >0 ) to b side ( <0 )
    - crossing b_to_a: opposite
    - mode filters which directions to count
    """

    def __init__(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        mode: str = "both",
        classes: Optional[List[int]] = None,
        frame_width: Optional[int] = None,
        frame_height: Optional[int] = None,
        min_distance: float = 3.0,
        cooldown_frames: int = 10,
    ):
        self.raw_p1 = tuple(p1)
        self.raw_p2 = tuple(p2)
        self.p1 = tuple(float(v) for v in p1)
        self.p2 = tuple(float(v) for v in p2)
        self.mode = mode
        self.classes = set(classes) if classes is not None else None
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.min_distance = float(min_distance) if min_distance is not None else 1.0
        self.cooldown_frames = int(cooldown_frames) if cooldown_frames is not None else 8

        # Resolve normalized coords if needed (0-1 range and frame size known)
        if frame_width and frame_height:
            self._resolve_normalized()

        # per-track history: track_id -> (last_center, last_side)
        self._history: Dict[int, Tuple[Tuple[float,float], float]] = {}
        # last crossing frame per id for debounce
        self._last_cross: Dict[int, int] = {}
        self._counts = {"total": 0, "a_to_b": 0, "b_to_a": 0, "by_class": defaultdict(int)}
        self._events: List[CrossingEvent] = []

        self._line_len = ((self.p2[0]-self.p1[0])**2 + (self.p2[1]-self.p1[1])**2) ** 0.5
        if self._line_len < 1e-6:
            raise ValueError(f"line p1 and p2 must be different, got {p1} {p2}")
        if self.p1 == self.p2:
            raise ValueError(f"line p1 and p2 must be different, got {p1} {p2}")

    def _resolve_normalized(self):
        # If both points are within [0,1], treat as normalized
        def is_norm(v):
            return 0 <= v <= 1
        if all(is_norm(c) for pt in (self.raw_p1, self.raw_p2) for c in pt):
            # need frame size to convert; if still small values 0-1 but frame is also small? ambiguous
            # Assume normalized if values <=1 and at least one coordinate is <1 and frame >200
            # Simple heuristic: if max coord <=1.0 and frame size >10
            self.p1 = (self.raw_p1[0] * self.frame_width, self.raw_p1[1] * self.frame_height)
            self.p2 = (self.raw_p2[0] * self.frame_width, self.raw_p2[1] * self.frame_height)

    def set_frame_size(self, w: int, h: int):
        """Late binding for normalized conversion after VideoSource is known."""
        self.frame_width = w
        self.frame_height = h
        # re-resolve if raw was normalized
        if all(0 <= c <= 1 for pt in (self.raw_p1, self.raw_p2) for c in pt):
            # check if already resolved? if p1 currently equals raw*old? Just recompute
            self.p1 = (self.raw_p1[0] * w, self.raw_p1[1] * h)
            self.p2 = (self.raw_p2[0] * w, self.raw_p2[1] * h)
            self._line_len = ((self.p2[0]-self.p1[0])**2 + (self.p2[1]-self.p1[1])**2) ** 0.5

    def update(self, tracks: List[Track], frame_idx: int) -> List[CrossingEvent]:
        events: List[CrossingEvent] = []
        # For quick lookup, build dict of current tracks by id
        cur_by_id = {t.track_id: t for t in tracks}

        # Optionally filter by classes
        for tid, track in cur_by_id.items():
            if self.classes is not None and track.class_id not in self.classes:
                # still need to update history? No, skip history to avoid spurious side
                continue

            cur_center = track.center
            cur_side = _side(self.p1, self.p2, cur_center)

            # If point exactly on line (side ~0), treat as no side change; keep previous side to avoid flicker
            # We'll consider epsilon 1e-6; if on line, skip counting this frame but update position for next?
            # Better to not update history when side==0 to keep last valid side
            if abs(cur_side) < 1e-6:
                # keep last history but update center? Keep center for intersection test but side stays last
                # we store last valid side, but center should be current for next intersection check?
                # To avoid losing intersection due to on-line, we keep history center as current but side as previous
                prev = self._history.get(tid)
                if prev is not None:
                    prev_center, prev_side = prev
                    # Still check intersection with segment prev_center -> cur_center vs line
                    if _segments_intersect(self.p1, self.p2, prev_center, cur_center):
                        # side transition is ambiguous; determine direction via prev_side sign vs cur_side? cur_side~0 => use geometric
                        # We'll infer direction from prev_side to opposite of prev_side? Not reliable. Skip.
                        pass
                    # update center but keep side
                    self._history[tid] = (cur_center, prev_side)
                else:
                    self._history[tid] = (cur_center, cur_side)  # side 0
                continue

            prev = self._history.get(tid)
            if prev is not None:
                prev_center, prev_side = prev
                # side changed?
                if prev_side * cur_side < 0:  # opposite signs
                    # debounce: require movement large enough to avoid jitter near line
                    mov = ((cur_center[0]-prev_center[0])**2 + (cur_center[1]-prev_center[1])**2) ** 0.5
                    if mov < self.min_distance:
                        # jitter near line — ignore small movements
                        self._history[tid] = (cur_center, cur_side)
                        continue
                    # cooldown debounce
                    last_cf = self._last_cross.get(tid, -9999)
                    if frame_idx - last_cf < self.cooldown_frames:
                        self._history[tid] = (cur_center, cur_side)
                        continue
                    # confirm segments intersect (redundant with side change for infinite line, but validates finite segment)
                    if _segments_intersect(self.p1, self.p2, prev_center, cur_center):
                        direction = "a_to_b" if prev_side > 0 and cur_side < 0 else "b_to_a"
                        # mode filter
                        if self.mode == "both" or self.mode == direction:
                            self._counts["total"] += 1
                            self._counts[direction] += 1
                            self._counts["by_class"][track.class_name] += 1
                            ev = CrossingEvent(
                                frame_idx=frame_idx,
                                track_id=tid,
                                class_id=track.class_id,
                                class_name=track.class_name,
                                direction=direction,
                                p1=self.p1,
                                p2=self.p2,
                                center=cur_center,
                            )
                            self._events.append(ev)
                            events.append(ev)
                            self._last_cross[tid] = frame_idx
                # update history
                self._history[tid] = (cur_center, cur_side)
            else:
                # first observation
                self._history[tid] = (cur_center, cur_side)

        # cleanup: tracks that disappeared should keep history for a short buffer? But if reappears after many frames far away, previous center distant may falsely count.
        # We keep history; ByteTrack buffer is 30 frames; crossing across long gap may be missed or false counted. For M2 minimal, keep forever.
        # Optional pruning not needed.

        return events

    def get_counts(self) -> Dict:
        # return copy with by_class as dict
        return {
            "total": self._counts["total"],
            "a_to_b": self._counts["a_to_b"],
            "b_to_a": self._counts["b_to_a"],
            "by_class": dict(self._counts["by_class"]),
        }

    def get_events(self) -> List[CrossingEvent]:
        return list(self._events)

    def __repr__(self):
        return f"LineCrossingCounter(p1={self.p1}, p2={self.p2}, mode={self.mode}, counts={self.get_counts()})"
