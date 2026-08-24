"""FastAPI app — minimal service for video analytics."""

from pathlib import Path
import shutil
import uuid
import json

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# ensure project root on path for imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.config import load_config
from src.pipeline import VideoPipeline

app = FastAPI(title="Real-Time Video Analytics", version="M5")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config/config.yaml"
OUTPUTS = ROOT / "outputs"
SNAPSHOTS = OUTPUTS / "snapshots"
EVENTS_JSON = OUTPUTS / "events.jsonl"


@app.get("/health")
def health():
    return {"status": "ok", "version": "M5", "model": "yolov8n.pt"}


@app.get("/api/config")
def get_config():
    try:
        cfg = load_config(CONFIG_PATH)
        return {
            "model": cfg.model,
            "device": cfg.device,
            "conf": cfg.conf,
            "iou": cfg.iou,
            "line_crossing": {"enabled": cfg.line_crossing.enabled, "line": [cfg.line_crossing.p1, cfg.line_crossing.p2], "mode": cfg.line_crossing.mode},
            "roi": {"enabled": cfg.roi.enabled, "polygon": list(cfg.roi.polygon), "dwell_sec": cfg.roi.dwell_sec},
            "events": {"enabled": cfg.events.enabled, "json_path": cfg.events.json_path, "snapshot_dir": cfg.events.snapshot_dir},
            "rtsp": {"max_frames": cfg.rtsp.max_frames},
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/events")
def get_events(limit: int = 100):
    if not EVENTS_JSON.exists():
        return []
    lines = EVENTS_JSON.read_text(encoding="utf-8").strip().splitlines()
    events = []
    for line in lines[-limit:]:
        if line.strip():
            try:
                events.append(json.loads(line))
            except Exception:
                continue
    return events


@app.get("/video")
def get_video(path: str = "outputs/result.mp4"):
    # security: only allow outputs/ files
    p = (ROOT / path).resolve()
    if not str(p).startswith(str(ROOT.resolve())) or not p.exists():
        # fallback to default result
        p = OUTPUTS / "result.mp4"
        if not p.exists():
            raise HTTPException(404, "video not found")
    return FileResponse(str(p), media_type="video/mp4")


@app.get("/snapshots/{filename}")
def get_snapshot(filename: str):
    # prevent path traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(400, "invalid filename")
    p = SNAPSHOTS / filename
    if not p.exists():
        raise HTTPException(404, "snapshot not found")
    return FileResponse(str(p), media_type="image/jpeg")


@app.post("/process")
async def process_video(
    file: UploadFile = File(..., description="MP4 video"),
    conf: float = Form(0.25),
    device: str = Form("auto"),
):
    # validate file type
    if not file.filename.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
        raise HTTPException(400, "only mp4/avi/mov/mkv allowed, got " + file.filename)
    if file.size and file.size > 50 * 1024 * 1024:
        raise HTTPException(413, "file too large (>50MB)")

    uploads = OUTPUTS / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)
    uid = uuid.uuid4().hex[:6]
    save_name = f"upload_{uid}_{Path(file.filename).name}"
    save_path = uploads / save_name

    try:
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    finally:
        await file.close()

    # load base config and override
    try:
        base_cfg = load_config(CONFIG_PATH)
    except Exception as e:
        raise HTTPException(500, f"config load failed: {e}")

    from dataclasses import replace
    # override device/conf if provided
    cfg = base_cfg
    overrides = {}
    if conf != base_cfg.conf:
        if not 0 < conf <= 1:
            raise HTTPException(400, "conf must be 0-1")
        overrides["conf"] = conf
    if device != base_cfg.device:
        overrides["device"] = device
    # force source/output to uploaded file and api output
    api_output = OUTPUTS / f"api_result_{uid}.mp4"
    api_events = OUTPUTS / "events.jsonl"  # keep default, will be overwritten
    # keep snapshots default
    combined_overrides = {**overrides, "source": str(save_path), "output": str(api_output)}
    # need to replace events path? keep default
    try:
        cfg = replace(cfg, **combined_overrides)
    except Exception as e:
        raise HTTPException(500, f"config override failed: {e}")

    # run pipeline synchronously (could be slow 10-20s)
    try:
        pipeline = VideoPipeline(cfg)
        stats = pipeline.run()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"pipeline failed: {e}")

    # build response with reachable URLs
    return JSONResponse({
        "stats": stats,
        "video_url": f"/video?path={api_output.relative_to(ROOT)}",
        "events_url": "/events",
        "snapshots": stats.get("snapshots", [])[:5],
    })


# serve dashboard static (must be after api routes)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
def dashboard():
    html_path = static_dir / "dashboard.html"
    if not html_path.exists():
        return HTMLResponse("<h3>Dashboard not found. Check api/static/dashboard.html</h3>")
    return HTMLResponse(html_path.read_text(encoding="utf-8"))
