"""Config loading and validation — minimal, fail-fast."""

from dataclasses import dataclass
from pathlib import Path
import yaml


@dataclass(frozen=True)
class LineCrossingConfig:
    enabled: bool
    p1: tuple[float, float]
    p2: tuple[float, float]
    mode: str
    classes: list[int] | None


@dataclass(frozen=True)
class ROIConfig:
    enabled: bool
    polygon: tuple[tuple[float, float], ...]
    dwell_sec: float
    classes: list[int] | None


@dataclass(frozen=True)
class EventsConfig:
    enabled: bool
    json_path: str
    snapshot_dir: str
    snapshot_expand: float
    snapshot_max: int


@dataclass(frozen=True)
class PipelineConfig:
    model: str
    source: str
    output: str
    device: str
    conf: float
    iou: float
    imgsz: int
    tracker: str
    classes: list[int] | None
    fourcc: str
    line_crossing: LineCrossingConfig
    roi: ROIConfig
    events: EventsConfig


def _parse_line_crossing(raw: dict) -> LineCrossingConfig:
    lc = raw.get("line_crossing", None)
    if lc is None:
        return LineCrossingConfig(enabled=False, p1=(320, 0), p2=(320, 480), mode="both", classes=None)
    if isinstance(lc, dict) and not lc:
        return LineCrossingConfig(enabled=False, p1=(320, 0), p2=(320, 480), mode="both", classes=None)
    enabled = bool(lc.get("enabled", True))
    line = lc.get("line", [[320, 0], [320, 480]])
    if not (isinstance(line, (list, tuple)) and len(line) == 2):
        raise ValueError(f"line_crossing.line must be [[x1,y1],[x2,y2]], got {line}")
    try:
        p1 = (float(line[0][0]), float(line[0][1]))
        p2 = (float(line[1][0]), float(line[1][1]))
    except Exception as e:
        raise ValueError(f"invalid line coords {line}: {e}")
    mode = str(lc.get("mode", "both")).strip().lower()
    if mode not in {"both", "a_to_b", "b_to_a", "a2b", "b2a"}:
        raise ValueError(f"line_crossing.mode must be both|a_to_b|b_to_a, got {mode}")
    if mode == "a2b":
        mode = "a_to_b"
    if mode == "b2a":
        mode = "b_to_a"
    classes = lc.get("classes", None)
    if classes is not None:
        classes = [int(c) for c in classes]
    return LineCrossingConfig(enabled=enabled, p1=p1, p2=p2, mode=mode, classes=classes)


def _parse_roi(raw: dict) -> ROIConfig:
    rc = raw.get("roi", None)
    if rc is None:
        return ROIConfig(enabled=False, polygon=((160,120),(480,120),(480,360),(160,360)), dwell_sec=1.5, classes=None)
    if isinstance(rc, dict) and not rc:
        return ROIConfig(enabled=False, polygon=((160,120),(480,120),(480,360),(160,360)), dwell_sec=1.5, classes=None)
    enabled = bool(rc.get("enabled", True))
    polygon = rc.get("polygon", [[0.25,0.25],[0.75,0.25],[0.75,0.75],[0.25,0.75]])
    if not isinstance(polygon, (list, tuple)) or len(polygon) < 3:
        raise ValueError(f"roi.polygon must be list of >=3 points, got {polygon}")
    pts = []
    for pt in polygon:
        if not isinstance(pt, (list, tuple)) or len(pt) != 2:
            raise ValueError(f"roi polygon point must be [x,y], got {pt}")
        pts.append((float(pt[0]), float(pt[1])))
    polygon_t = tuple(pts)
    dwell_sec = float(rc.get("dwell_sec", rc.get("dwell_threshold_sec", 1.5)))
    if dwell_sec <= 0:
        raise ValueError(f"roi dwell_sec must be >0, got {dwell_sec}")
    classes = rc.get("classes", None)
    if classes is not None:
        classes = [int(c) for c in classes]
    return ROIConfig(enabled=enabled, polygon=polygon_t, dwell_sec=dwell_sec, classes=classes)


def _parse_events(raw: dict) -> EventsConfig:
    ec = raw.get("events", None)
    if ec is None:
        return EventsConfig(enabled=True, json_path="outputs/events.jsonl", snapshot_dir="outputs/snapshots", snapshot_expand=0.2, snapshot_max=100)
    if isinstance(ec, dict) and not ec:
        return EventsConfig(enabled=False, json_path="outputs/events.jsonl", snapshot_dir="outputs/snapshots", snapshot_expand=0.2, snapshot_max=100)
    enabled = bool(ec.get("enabled", True))
    json_path = str(ec.get("json_path", ec.get("json", "outputs/events.jsonl")))
    snapshot_dir = str(ec.get("snapshot_dir", "outputs/snapshots"))
    snapshot_expand = float(ec.get("snapshot_expand", 0.2))
    if not 0 <= snapshot_expand <= 1:
        raise ValueError(f"events.snapshot_expand must be 0-1, got {snapshot_expand}")
    snapshot_max = int(ec.get("snapshot_max", 100))
    if snapshot_max < 0:
        raise ValueError(f"snapshot_max must be >=0, got {snapshot_max}")
    return EventsConfig(enabled=enabled, json_path=json_path, snapshot_dir=snapshot_dir, snapshot_expand=snapshot_expand, snapshot_max=snapshot_max)


def load_config(path: str | Path) -> PipelineConfig:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"config not found: {p.resolve()}")

    with open(p, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    model = raw.get("model", "yolov8n.pt")
    source = raw.get("source", "assets/sample.mp4")
    output = raw.get("output", "outputs/result.mp4")
    device = raw.get("device", "auto")
    conf = float(raw.get("conf", 0.25))
    iou = float(raw.get("iou", 0.5))
    imgsz = int(raw.get("imgsz", 640))
    tracker = raw.get("tracker", "bytetrack.yaml")
    fourcc = raw.get("fourcc", "mp4v")
    classes = raw.get("classes", None)
    if classes is not None:
        classes = [int(c) for c in classes]

    if not 0 < conf <= 1:
        raise ValueError(f"conf must be in (0,1], got {conf}")
    if not 0 < iou <= 1:
        raise ValueError(f"iou must be in (0,1], got {iou}")

    line_crossing = _parse_line_crossing(raw)
    roi = _parse_roi(raw)
    events = _parse_events(raw)

    return PipelineConfig(
        model=str(model),
        source=str(source),
        output=str(output),
        device=str(device),
        conf=conf,
        iou=iou,
        imgsz=imgsz,
        tracker=str(tracker),
        classes=classes,
        fourcc=str(fourcc),
        line_crossing=line_crossing,
        roi=roi,
        events=events,
    )
