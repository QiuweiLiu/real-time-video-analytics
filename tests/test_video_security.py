"""Tests for /video path security (M5 hardening)."""

from pathlib import Path
from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


def test_video_default():
    # default without param should serve outputs/result.mp4 if exists; ensure 200
    # ensure file exists first (create dummy if needed)
    p = Path("outputs/result.mp4")
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00"*100)
    r = client.get("/video")
    assert r.status_code == 200
    assert r.headers["content-type"] == "video/mp4"


def test_video_allows_outputs_file():
    p = Path("outputs/result.mp4")
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"\x00"*100)
    r = client.get("/video", params={"path": "outputs/result.mp4"})
    assert r.status_code == 200


def test_video_blocks_traversal():
    for bad in [
        "../../config/config.yaml",
        "../main.py",
        "outputs/../../config/config.yaml",
        "%2e%2e%2fconfig/config.yaml",
    ]:
        r = client.get("/video", params={"path": bad})
        # should be 403 or 404, never 200 nor leak
        assert r.status_code in (400, 403, 404), f"{bad} -> {r.status_code}"


def test_video_blocks_outside_outputs():
    for bad in [
        "main.py",
        "config/config.yaml",
        "src/pipeline.py",
        ".project/STATE.md",
        "assets/sample.mp4",
    ]:
        r = client.get("/video", params={"path": bad})
        assert r.status_code in (400, 403, 404), f"{bad} -> {r.status_code}"


def test_video_blocks_bad_extension():
    for bad in [
        "outputs/events.jsonl",
        "outputs/result.txt",
        "outputs/.gitignore",
        "outputs/result",
    ]:
        r = client.get("/video", params={"path": bad})
        assert r.status_code in (400, 403, 404), f"{bad} -> {r.status_code}"


def test_video_404_for_missing():
    r = client.get("/video", params={"path": "outputs/nonexistent_12345.mp4"})
    assert r.status_code == 404


def test_video_blocks_directory():
    r = client.get("/video", params={"path": "outputs/"})
    assert r.status_code in (400, 403, 404)

    r = client.get("/video", params={"path": "outputs"})
    assert r.status_code in (400, 403, 404)


def test_snapshot_still_blocks_traversal():
    r = client.get("/snapshots/../../config/config.yaml")
    assert r.status_code in (400, 404)
