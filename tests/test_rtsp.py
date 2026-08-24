"""Tests for RTSP/stream support."""

import pytest
from src.source.video_source import VideoSource, _is_stream

def test_is_stream_detection():
    assert _is_stream("rtsp://user:pass@192.168.1.1/stream") is True
    assert _is_stream("rtmp://example.com/live") is True
    assert _is_stream("http://example.com/video.m3u8") is True
    assert _is_stream("0") is True
    assert _is_stream("1") is True
    assert _is_stream("assets/sample.mp4") is False
    assert _is_stream("/tmp/video.mp4") is False

def test_video_source_stream_mock():
    # without real server, opening rtsp should fail gracefully or succeed if url is bogus?
    # we test that trying to open bogus rtsp raises RuntimeError
    with pytest.raises((RuntimeError, FileNotFoundError)):
        # bogus rtsp should fail to open
        VideoSource("rtsp://127.0.0.1:8554/bogus", max_frames=5)

def test_video_source_file_still_works(tmp_path):
    import cv2, numpy as np, pathlib
    p = tmp_path / "tmp.mp4"
    w,h,fps=64,48,10
    writer = cv2.VideoWriter(str(p), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w,h))
    for i in range(5):
        writer.write(np.zeros((h,w,3), dtype=np.uint8))
    writer.release()
    vs = VideoSource(str(p))
    assert vs.width == 64
    assert vs.is_stream is False
    frames = list(vs)
    assert len(frames) == 5

def test_stream_max_frames_limit():
    # simulate stream by using numeric source? but numeric 0 may try to open camera and fail if no camera
    # instead test max_frames logic via file with max_frames
    import cv2, numpy as np, pathlib, tempfile
    from pathlib import Path
    import os
    # create temp file and open with max_frames=2
    tmp = Path("/tmp/test_stream_limit.mp4")
    w,h=32,32
    writer = cv2.VideoWriter(str(tmp), cv2.VideoWriter_fourcc(*"mp4v"), 10, (w,h))
    for i in range(10):
        writer.write(np.zeros((h,w,3), dtype=np.uint8))
    writer.release()
    vs = VideoSource(str(tmp), max_frames=2)
    frames = list(vs)
    assert len(frames) == 2
    tmp.unlink(missing_ok=True)
