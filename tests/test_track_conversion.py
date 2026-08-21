import numpy as np
import cv2
from pathlib import Path
from ultralytics import YOLO
from ultralytics.utils import ASSETS
from src.vision.types import tracks_from_results

def test_tracks_from_results_with_bus_image():
    model = YOLO("yolov8n.pt")
    bus_path = Path(ASSETS) / "bus.jpg"
    # fallback to assets/sample.mp4 frame if ASSETS not found (portable)
    if bus_path.exists():
        img = cv2.imread(str(bus_path))
    else:
        # try project sample video first frame
        cap = cv2.VideoCapture("assets/sample.mp4")
        ok, img = cap.read()
        cap.release()
        if not ok:
            img = None
    assert img is not None, f"test image not found: {bus_path}"
    results = model.track(source=img, persist=True, conf=0.25, device="cpu", verbose=False, tracker="bytetrack.yaml")
    tracks = tracks_from_results(results[0])
    assert len(tracks) == 5, f"expected 5 tracks, got {len(tracks)}"
    # check structure
    for t in tracks:
        assert isinstance(t.track_id, int) and t.track_id > 0
        assert isinstance(t.class_name, str)
        assert 0 < t.confidence <= 1
        assert len(t.bbox) == 4
        assert len(t.center) == 2
        assert t.bbox[0] < t.bbox[2] and t.bbox[1] < t.bbox[3]
    # persist stability
    results2 = model.track(source=img, persist=True, conf=0.25, device="cpu", verbose=False, tracker="bytetrack.yaml")
    tracks2 = tracks_from_results(results2[0])
    ids1 = sorted([t.track_id for t in tracks])
    ids2 = sorted([t.track_id for t in tracks2])
    assert ids1 == ids2, f"IDs not stable: {ids1} vs {ids2}"

def test_tracks_empty():
    model = YOLO("yolov8n.pt")
    black = np.zeros((640,640,3), dtype=np.uint8)
    results = model.track(source=black, persist=True, conf=0.25, device="cpu", verbose=False)
    tracks = tracks_from_results(results[0])
    assert len(tracks) == 0
