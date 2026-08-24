"""Tests for FastAPI M5."""

from pathlib import Path
from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ok"
    assert "version" in j

def test_config():
    r = client.get("/api/config")
    assert r.status_code == 200
    j = r.json()
    assert "model" in j
    assert "line_crossing" in j
    assert "roi" in j

def test_events_empty_or_list():
    r = client.get("/events")
    assert r.status_code == 200
    # should be list
    assert isinstance(r.json(), list)

def test_process_upload_sample():
    # upload sample.mp4 and expect stats json with 80 frames
    sample = Path("assets/sample.mp4")
    assert sample.exists(), "sample.mp4 missing"
    with open(sample, "rb") as f:
        files = {"file": ("sample.mp4", f, "video/mp4")}
        data = {"conf": "0.25", "device": "cpu"}  # cpu for test stability
        r = client.post("/process", files=files, data=data)
    # may take 10-20s
    assert r.status_code == 200, r.text[:500]
    j = r.json()
    assert "stats" in j
    stats = j["stats"]
    assert stats["total_frames"] == 80
    assert "line_crossing" in stats
    assert "roi" in stats
    assert "events_count" in stats
    # check video file exists
    # video_url like /video?path=outputs/api_result_xxx.mp4
    video_path = j.get("video_url", "")
    assert "api_result" in video_path
    # fetch video
    r2 = client.get(video_path)
    assert r2.status_code == 200
    assert r2.headers["content-type"] == "video/mp4"
    # events endpoint should now have events
    r3 = client.get("/events")
    assert isinstance(r3.json(), list)
    assert len(r3.json()) >= 4  # sample dwell 4

def test_dashboard():
    r = client.get("/")
    assert r.status_code == 200
    assert "Real-Time Video Analytics" in r.text
    assert "dashboard" in r.text.lower() or "Dashboard" in r.text
