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


def test_stream_reconnect_mock():
    import cv2, numpy as np
    from unittest.mock import Mock, patch

    fake_frame = np.zeros((10, 10, 3), dtype=np.uint8)

    # First capture: read fails once, then after reconnect a new capture succeeds
    mock_first = Mock()
    mock_first.isOpened.return_value = True
    mock_first.get.side_effect = lambda prop: {0: 10, 1: 10, 5: 25.0, 7: -1}.get(prop, 0)
    mock_first.read.return_value = (False, None)

    mock_second = Mock()
    mock_second.isOpened.return_value = True
    mock_second.get.side_effect = mock_first.get.side_effect
    mock_second.read.return_value = (True, fake_frame)

    # VideoSource will call cv2.VideoCapture twice: once in __init__, once in _reopen
    with patch("src.source.video_source.cv2.VideoCapture", side_effect=[mock_first, mock_second]) as mock_cap:
        vs = VideoSource("rtsp://test/stream", max_frames=1, reconnect_attempts=1, reconnect_delay=0.01)
        frames = list(vs)
        assert len(frames) == 1
        assert mock_cap.call_count == 2  # init + one reconnect

    # file source should not enable reconnect even if passed (outside patch)
    import pathlib
    tmp2 = pathlib.Path("/tmp/reconnect_file2.mp4")
    w2 = cv2.VideoWriter(str(tmp2), cv2.VideoWriter_fourcc(*"mp4v"), 10, (10, 10))
    w2.write(np.zeros((10,10,3), dtype=np.uint8))
    w2.release()
    vs2 = VideoSource(str(tmp2), max_frames=1, reconnect_attempts=3)
    assert vs2.is_stream is False
    assert vs2.reconnect_attempts == 0
    tmp2.unlink(missing_ok=True)
