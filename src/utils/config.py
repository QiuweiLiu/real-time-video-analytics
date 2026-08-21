"""Config loading and validation — minimal, fail-fast."""

from dataclasses import dataclass
from pathlib import Path
import yaml


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
    )
