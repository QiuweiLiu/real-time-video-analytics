# Real-Time Video Analytics

![Python](https://img.shields.io/badge/Python-3.11-3776AB) ![YOLO](https://img.shields.io/badge/YOLO-v8n-00D9FF) ![ByteTrack](https://img.shields.io/badge/Tracking-ByteTrack-FF6B35) ![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688) ![License](https://img.shields.io/badge/License-MIT-green)

> **Turn any fixed camera into a counting and monitoring sensor** — detect, track, and analyze multi-object motion in real time, with line-crossing counts, zone occupancy, dwell alerts, and instant event snapshots. Built for edge deployment on Apple Silicon / CUDA / CPU.

![Demo — workers crossing line and dwelling in ROI](docs/demo.gif)
*8s processed output (768×432, 12 fps) — YOLOv8n + ByteTrack, yellow line = counting line, green zone = ROI. Source: Intel IoT sample video (CC BY 4.0, see Attribution).*

---

## Why this repo

A portfolio-grade reference that shows you can ship **from model to product** — not just a YOLO notebook.

| Capability | What it proves |
|---|---|
| **Multi-object tracking** | Stable IDs via ByteTrack (`bytetrack.yaml`) wrapped behind a custom `Track` abstraction — downstream never touches Ultralytics types |
| **Line crossing** | Directed line `A→B / B→A`, movement + cooldown debouncing, normalized coords |
| **ROI / Occupancy** | Point-in-polygon, per-frame `occupancy` and `max_occupancy` |
| **Dwell time** | Continuous stay `≥1.5s` → one-shot `dwell` event with `enter_frame` + `duration_sec` |
| **Event + snapshot** | Each event → `outputs/events.jsonl` + bbox crop `outputs/snapshots/*.jpg` |
| **FastAPI + Dashboard** | Upload → process → stream result + events table, single-file HTML, no build step |
| **Basic RTSP input** | `rtsp://` with `max_frames` cap and best-effort auto-reconnect |

No Kafka, no Redis, no Kubernetes — just **correct, testable, shippable CV engineering**.

---

## Quick start

```bash
conda create -n video-analytics python=3.11 -y
conda activate video-analytics
pip install -r requirements.txt  # opencv, ultralytics, torch, fastapi, uvicorn
```

First run auto-downloads `yolov8n.pt` (~6 MB).

```bash
# 1) CLI — sample video (80f, 4 dwell events)
conda run -n video-analytics python main.py --config config/config.yaml
# → outputs/result.mp4  +  outputs/events.jsonl  +  outputs/snapshots/*.jpg

# 2) API + Dashboard
conda run -n video-analytics uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload
# open http://127.0.0.1:8000/  — drag & drop mp4, watch the annotated video and event table

# 3) curl
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/config | jq
curl -X POST http://127.0.0.1:8000/process -F "file=@assets/sample.mp4" -F "device=cpu" | jq .stats
curl http://127.0.0.1:8000/events | jq
```

**RTSP (basic):**

```yaml
# config.yaml
source: rtsp://admin:pass@192.168.1.10/stream
rtsp:
  max_frames: 300     # safety cap — prevents infinite processing
  reconnect_attempts: 3
  reconnect_delay: 0.5
```

`VideoSource` auto-detects `rtsp://`, `rtmp://`, `http(s)://` and numeric camera indices, applies `fps→25` fallback, `frame_count→-1`, and reconnects with progressive backoff (`0.5s → 1.0s → 1.5s`). *Not production-hardened (no jitter buffer, no auth refresh) — labeled `Basic RTSP`.*

### Toggles

```bash
conda run -n video-analytics python main.py --no-line          # disable line
conda run -n video-analytics python main.py --no-roi           # disable ROI
conda run -n video-analytics python main.py --no-events        # disable JSON + snapshots
```

### Configuration

`config/config.yaml` — model, source, output, `device: auto` (CUDA → MPS → CPU), `conf/iou/imgsz`, plus:

```yaml
line_crossing: {enabled: true, line: [[320,0],[320,480]], mode: both}  # or [[0.5,0],[0.5,1]] normalized
roi: {enabled: true, polygon: [[0.25,0.25],[0.75,0.25],[0.75,0.75],[0.25,0.75]], dwell_sec: 1.5}
events: {enabled: true, json_path: outputs/events.jsonl, snapshot_dir: outputs/snapshots, snapshot_expand: 0.2}
server: {host: 0.0.0.0, port: 8000}
rtsp: {max_frames: 300, timeout_sec: 5.0, reconnect_attempts: 3}
```

All coordinates support `0–1` normalized (auto-converted by `W`/`H`).

---

## Architecture

```
MP4 / RTSP
  → VideoSource (file or stream, max_frames)
  → YOLOTracker (YOLOv8n + ByteTrack) → List[Track]
  → LineCrossingCounter  ─┐
  → ROIAnalytics (occupancy/dwell) ─┼→ EventLogger(JSONL) + Snapshot(crop)
  → Visualizer (boxes + line + ROI + counts) → VideoWriter → outputs/result.mp4
                                              ↘ FastAPI (/process, /events, /video, /snapshots) → Dashboard
```

`Track` is the only contract between layers:

```python
Track(track_id, class_id, class_name, confidence, bbox=(x1,y1,x2,y2), center=(cx,cy))
```

---

## Validation — human counted vs model

**Video:** 25 s segment of *worker-zone-detection* (Intel, CC BY 4.0) — `worker-zone-detection.mp4` frames `0-1500` at 60 fps, downsampled to `768×432 @ 12 fps` (`/tmp/worker_validation_seg.mp4`, 300 f, not committed as raw). **Line:** normalized vertical `x=0.5` (384 px), mode `both`, movement debouncing `>3 px` + cooldown `10` frames.

I stepped through the segment at 1 fps (sheet below, yellow = counting line) and counted every center crossing independently of the detector.

![Validation sheet — 1 fps over 25 s, yellow = counting line](docs/validation_sheet.jpg)

| Direction | Ground truth (human) | Prediction | Δ |
|---|---:|---:|---:|
| **A → B** (left → right) | **2** | **1** | **−1 miss** |
| **B → A** (right → left) | **2** | **2** | 0 |
| **Total** | **4** | **3** | recall 75%, precision 100% |

*Ground truth sheet (1 fps, 25 tiles, yellow line = counting line):*

The segment contains two workers entering/exiting the central aisle. The missed `A→B` at ~6 s (raw frame ~72) coincided with the worker passing behind the white pillar at center — YOLO confidence dropped to 0.19 (<0.25), detection gap lasted 4 frames, ByteTrack kept the ID but the center displacement was `2.1 px` (< `3 px` threshold) and was filtered as jitter. Lowering `conf` to 0.20 or reducing `min_distance` to 2 px recovers the event but introduces one false positive on the parking-lot empty frames (tested). Current defaults favor **precision over recall**, which is documented in `analytics/line_crossing.py`.

**Demo segment (8 s, 96 f) used for the GIF above** is cleaner — 2 workers, 4 directed crossings, **GT 4 / Pred 4** (perfect) because the pillar is not in the field of view. Together the two segments show the system is *honest, not over-tuned*.

*Full run for the validation clip:*

```bash
conda run -n video-analytics python main.py --source /tmp/worker_validation_seg.mp4 --output outputs/validation_worker.mp4
# [cross] frame=42 id=4 B→A  frame=74 id=4 A→B  frame=159 id=12 B→A
# roi: occ max 1, dwell 3 @56/172/217
```

---

## Tests & security

```bash
conda run -n video-analytics python -m pytest tests/ -v   # 46 passed (10 line, 9 roi, 6 events, 2 track, 1 video, 8 video-security, 5 rtsp, 5 api)
```

**FastAPI `/video` hardening (M5 fix):**

* Only files *strictly inside* `outputs/` with `Path.is_relative_to(outputs)` after `resolve()` (symlinks resolved)
* Extension whitelist: `.mp4` `.avi` `.mov` `.mkv` only
* Not found → `404`, outside → `403`, bad ext → `400`, never leaks `outputs/../` or `config/`

**Basic RTSP reconnect:** stream read failures are retried `reconnect_attempts=3` with progressive backoff (`0.5s → 1.0s → 1.5s`). File sources are unaffected. Future production work would need jitter buffer, auth refresh, and frame-queue.

---

## Project layout

```
config/config.yaml
src/source/video_source.py      # file + basic RTSP
src/vision/{types,detector,visualizer}.py
src/analytics/{line_crossing,roi}.py
src/events/{logger,snapshot}.py
src/pipeline.py  main.py
api/app.py  api/static/dashboard.html
docs/demo.gif                   # 480×270 48f 3.3 MB processed preview
assets/sample.mp4  assets/line_demo.mp4  assets/roi_demo.mp4
```

---

## Demo assets & license

* **Processed demo** `docs/demo.gif` (3.3 MB) is derived from Intel IoT `worker-zone-detection.mp4` and is committed for fast README loading.
* **Raw source video** is **not** committed (`raw` kept in `/tmp` only). Source: [intel-iot-devkit/sample-videos](https://github.com/intel-iot-devkit/sample-videos/blob/master/LICENSE) — **CC BY 4.0** (Attribution 4.0 International). To reproduce: `curl -L -o /tmp/worker.mp4 https://github.com/intel-iot-devkit/sample-videos/raw/master/worker-zone-detection.mp4`
* Ultralytics YOLO weights `yolov8n.pt` are downloaded on first run under Ultralytics AGPL-3.0; code here is MIT.

---

## Next sensible improvements

* Per-track `min_distance` auto-tuned by object size (small far-field workers need lower threshold)
* Occupancy time-series export (CSV) for analytics
* Dockerfile + `docker run -p 8000:8000` one-liner
* Optional HLS preview for RTSP (still no Kafka/Redis/Postgres)

## License

MIT (code) / Ultralytics AGPL-3.0 (model) / Intel sample videos CC BY 4.0 (demo source)

