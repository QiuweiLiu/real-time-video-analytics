"""Config loading and validation — minimal, fail-fast."""

from dataclasses import dataclass
from pathlib import Path
import yaml


@dataclass(frozen=True)
class LineCrossingConfig:
    enabled: bool
    p1: tuple[float, float]
    p2: tuple[float, float]
    mode: str  # both | a_to_b | b_to_a
    classes: list[int] | None


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


def _parse_line_crossing(raw: dict) -> LineCrossingConfig:
    lc = raw.get("line_crossing", None)
    if lc is None:
        # backward compatible: disabled
        return LineCrossingConfig(enabled=False, p1=(320, 0), p2=(320, 480), mode="both", classes=None)

    if isinstance(lc, dict) and not lc:
        return LineCrossingConfig(enabled=False, p1=(320, 0), p2=(320, 480), mode="both", classes=None)

    enabled = bool(lc.get("enabled", True))
    # line: [[x1,y1],[x2,y2]]
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
    # normalize aliases
    if mode == "a2b":
        mode = "a_to_b"
    if mode == "b2a":
        mode = "b_to_a"

    classes = lc.get("classes", None)
    if classes is not None:
        classes = [int(c) for c in classes]

    return LineCrossingConfig(enabled=enabled, p1=p1, p2=p2, mode=mode, classes=classes)


def load_config(path: str | Path) -> PipelineConfig:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"config not found: {p.resolve()}")

    with open(p, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    # defaults
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

    # validation
    if not 0 < conf <= 1:
        raise ValueError(f"conf must be in (0,1], got {conf}")
    if not 0 < iou <= 1:
        raise ValueError(f"iou must be in (0,1], got {iou}")

    line_crossing = _parse_line_crossing(raw)

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
    )
