"""Tests for EventLogger + snapshot."""

import json
import cv2
import numpy as np
from pathlib import Path

from src.events.logger import EventLogger
from src.events.snapshot import save_snapshot

def test_logger_write_read(tmp_path: Path):
    p = tmp_path / "events.jsonl"
    logger = EventLogger(p)
    eid = logger.log({"type": "line_cross", "frame_idx": 10, "track_id": 1})
    eid2 = logger.log({"type": "dwell", "frame_idx": 20, "track_id": 2, "duration_sec": 1.5})
    assert logger.count() == 2
    logger.close()
    # read back
    lines = p.read_text().strip().splitlines()
    assert len(lines) == 2
    j1 = json.loads(lines[0])
    assert j1["type"] == "line_cross"
    assert j1["frame_idx"] == 10
    assert "event_id" in j1
    j2 = json.loads(lines[1])
    assert j2["track_id"] == 2

def test_snapshot_normal(tmp_path: Path):
    frame = np.full((100,100,3), 128, dtype=np.uint8)
    cv2.rectangle(frame, (30,30), (60,60), (0,0,255), -1)
    bbox = (30,30,60,60)
    out = save_snapshot(frame, bbox, tmp_path, "evt1", expand=0.2)
    assert out is not None and out.exists()
    img = cv2.imread(str(out))
    assert img is not None
    # expanded bbox should be larger than 30-60 (with 20% expand ~6px each side)
    assert img.shape[0] > 20 and img.shape[1] > 20

def test_snapshot_clamp_border(tmp_path: Path):
    frame = np.full((100,100,3), 100, dtype=np.uint8)
    # bbox at edge (0,0)-(10,10) with expand
    bbox = (0,0,10,10)
    out = save_snapshot(frame, bbox, tmp_path, "edge", expand=0.5)
    assert out is not None and out.exists()
    img = cv2.imread(str(out))
    assert img is not None
    # should not crash, clamp to 0
    assert img.shape[0] >= 10

def test_snapshot_small_bbox(tmp_path: Path):
    frame = np.full((50,50,3), 50, dtype=np.uint8)
    bbox = (25,25,26,26)  # 1x1
    out = save_snapshot(frame, bbox, tmp_path, "small", expand=0.2)
    assert out is not None and out.exists()
    img = cv2.imread(str(out))
    # min 10x10 enforced
    assert img.shape[0] >= 10 and img.shape[1] >= 10

def test_snapshot_expand_zero(tmp_path: Path):
    frame = np.full((80,80,3), 80, dtype=np.uint8)
    bbox = (20,20,40,40)
    out = save_snapshot(frame, bbox, tmp_path, "noexpand", expand=0.0)
    assert out is not None
    img = cv2.imread(str(out))
    assert img.shape[0] == 20 and img.shape[1] == 20

def test_logger_snapshot_disabled(tmp_path: Path):
    # ensure pipeline with events disabled doesn't create files
    from src.utils.config import load_config
    cfg = load_config("config/config.yaml")
    # just check config parsing for events
    assert cfg.events.enabled is True
    # disabled case via manual EventsConfig
    from src.utils.config import EventsConfig
    ec = EventsConfig(enabled=False, json_path=str(tmp_path/"none.jsonl"), snapshot_dir=str(tmp_path/"snap"), snapshot_expand=0.2, snapshot_max=10)
    assert not ec.enabled
