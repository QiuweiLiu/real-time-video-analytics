# Real-Time Video Analytics (M1+M2+M3+M4+M5)

小型可交付视频分析系统 — MP4 → YOLO检测 → ByteTrack跟踪 → 业务分析 (越线/ROI/驻留) → 事件持久化 → FastAPI服务 + Dashboard + RTSP。

## 技术栈
- Python 3.11, OpenCV 5.x, Ultralytics YOLO 8.4 (ByteTrack), PyTorch MPS/CUDA/CPU, FastAPI

## 结构
```
config/config.yaml              # 配置: 模型/视频/conf + line/roi/events/server/rtsp
src/source/                     # 视频输入 (VideoSource, RTSP流支持)
src/vision/                     # 检测+跟踪 (YOLOTracker, Track, visualizer)
src/analytics/                  # 业务分析 (line_crossing.py, roi.py)
src/events/                     # 事件持久化 (logger.py, snapshot.py)
src/pipeline.py                 # 串联 source→vision→analytics→events→writer
api/app.py                      # FastAPI 服务
api/static/dashboard.html       # 极简 Dashboard
main.py                         # CLI 入口
assets/sample.mp4               # M1 样例 (80f 618KB)
assets/line_demo.mp4            # M2 滑移 (4越线)
assets/roi_demo.mp4             # M3 停留 (dwell触发)
outputs/result.mp4              # 默认输出
outputs/events.jsonl            # 事件 JSONL
outputs/snapshots/*.jpg         # 自动截图
```

### Track 数据结构
```python
Track(track_id, class_id, class_name, confidence, bbox=(x1,y1,x2,y2), center=(cx,cy))
```

## 安装

```bash
conda create -n yolo-portfolio python=3.11 -y
conda activate yolo-portfolio
pip install -r requirements.txt  # 含 fastapi uvicorn python-multipart
```

首次运行自动下载 `yolov8n.pt` (~6MB)。

## 配置

`config/config.yaml` (M5):
```yaml
model: yolov8n.pt
source: assets/sample.mp4        # 或 rtsp://user:pass@ip/stream
output: outputs/result.mp4
device: auto
conf: 0.25
line_crossing: {enabled: true, line: [[320,0],[320,480]], mode: both}
roi: {enabled: true, polygon: [[0.25,0.25],[0.75,0.25],[0.75,0.75],[0.25,0.75]], dwell_sec: 1.5}
events: {enabled: true, json_path: outputs/events.jsonl, snapshot_dir: outputs/snapshots, snapshot_expand: 0.2}
server: {host: 0.0.0.0, port: 8000}
rtsp: {max_frames: 300, timeout_sec: 5.0}
```

## 运行

### CLI

```bash
# M5 默认 (越线+ROI+事件)
conda run -n yolo-portfolio python main.py --config config/config.yaml
# → outputs/result.mp4 + events.jsonl 4行 + snapshots/4图

# 开关
conda run -n yolo-portfolio python main.py --no-line --no-roi --no-events  # 纯检测跟踪

# RTSP 流 (限制 300帧)
conda run -n yolo-portfolio python main.py --config config/config.yaml --source rtsp://user:pass@192.168.1.64/stream --output outputs/rtsp_result.mp4

# 自定义
conda run -n yolo-portfolio python main.py --source assets/line_demo.mp4 --output outputs/line_result.mp4  # 8事件
```

### FastAPI 服务

```bash
conda run -n yolo-portfolio uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload
# 打开 http://127.0.0.1:8000/  Dashboard
# 拖拽上传 MP4 → 自动处理 → 播放视频 + 事件表格
```

```bash
# API 直调
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/config | jq
curl -X POST http://127.0.0.1:8000/process -F "file=@assets/sample.mp4" -F "device=cpu" | jq .stats
curl http://127.0.0.1:8000/events | jq
curl http://127.0.0.1:8000/video?path=outputs/result.mp4 --output out.mp4
curl http://127.0.0.1:8000/snapshots/dwell_1_30_8371.jpg --output snap.jpg
```

**Dashboard**: 顶部健康检查, 左上传区 (拖拽), 设备/conf选择, 右视频播放 + KPI (Frames/FPS/Line/MaxOcc/Dwell/Time), 下事件表 (badge LINE/DWELL, track/帧/时间/截图缩略), 自动刷新。

### RTSP

`VideoSource` 自动识别 `rtsp://`/`rtmp://`/`http(s)://` 前缀, 跳过文件存在检查, fps回退25, `max_frames` (默认300) 防无限流, `info()` 含 `is_stream`。

```python
from src.source.video_source import VideoSource
vs = VideoSource("rtsp://admin:pass@192.168.1.10/stream", max_frames=300)
for frame in vs: ...
```

示例配置 `source: rtsp://...` + `rtsp.max_frames: 300`。

## 验证

已在 M1 Mac (MPS) 验证:

- **M1**: bus.jpg 5目标 ID稳定; sample 80f 357检测
- **M2**: line_demo 4越线 @18/41/50/59 (movement>3), sample 0
- **M3**: sample occ4 dwell4@30f=1.5s; roi_demo occ max4 dwell4@30/33/38/42
- **M4**: sample 4 dwell +4 snapshots (14-75KB), line_demo 8事件 8截图, --no-events 回归
- **M5**: 
  - `GET /health` 200, `GET /api/config` 含 line/roi/events/rtsp, `GET /` dashboard 含 Real-Time, `POST /process` 80f 4 dwell +视频 1.8MB (curl & TestClient), `GET /events` 4行, `GET /snapshots` 可下载
  - `VideoSource` rtsp识别4用例, 文件仍5帧, max_frames截断2帧
  - 性能: sample CLI 18.9fps, API sync 11.5fps (cpu)
- **测试**: 37 passed — line10 +roi9 +events6 +track2 +video1 +api5 +rtsp4
```bash
conda run -n yolo-portfolio python -m pytest tests/ -v
conda run -n yolo-portfolio uvicorn api.app:app --port 8000
```

## License

MIT (代码) / Ultralytics AGPL-3.0 (模型)
