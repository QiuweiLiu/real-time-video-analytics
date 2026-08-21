from pathlib import Path
import cv2
import numpy as np

def test_video_source(tmp_path: Path):
    # create synthetic 10-frame video
    p = tmp_path / "tmp_test.mp4"
    w, h, fps = 320, 240, 10
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(p), fourcc, fps, (w, h))
    for i in range(10):
        frame = np.full((h, w, 3), 255, dtype=np.uint8)
        cv2.rectangle(frame, (10+i*5, 10), (50+i*5, 50), (0,0,255), -1)
        writer.write(frame)
    writer.release()

    from src.source.video_source import VideoSource
    vs = VideoSource(str(p))
    assert vs.width == w
    assert vs.height == h
    frames = list(vs)
    assert len(frames) == 10
    # ensure iterator exhausts
    assert vs.frame_count == 10 or vs.frame_count == -1  # some codecs report -1? but we set 10
