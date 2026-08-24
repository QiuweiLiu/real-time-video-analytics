# Real-Time Video Analytics (M1+M2+M3+M4)

小型可交付视频分析系统 — MP4 → YOLO检测 → ByteTrack跟踪 → 稳定ID → 业务分析 (越线/ROI/驻留) → 事件持久化 (JSON+截图) → 可视化视频。

## 技术栈
- Python 3.11
- OpenCV 5.x
- Ultralytics YOLO 8.4 (内置 ByteTrack `bytetrack.yaml`)
- PyTorch (MPS / CUDA / CPU)

## 结构
```
config/config.yaml              # 配置: 模型/视频/conf/输出/device + line_crossing + roi + events
src/source/                     # 视频输入 (VideoSource)
src/vision/                     # 检测+跟踪 (YOLOTracker, Track, visualizer)
src/analytics/                  # 业务分析 (line_crossing.py, roi.py)
src/events/                     # 事件持久化 (logger.py, snapshot.py)
src/pipeline.py                 # 串联 source→vision→analytics→events→writer
main.py                         # 入口
assets/sample.mp4               # M1 样例 (80f 618KB, 5目标)
assets/line_demo.mp4            # M2 滑移 demo (80f, 4越线)
assets/roi_demo.mp4             # M3 停留 demo (80f, dwell触发)
outputs/result.mp4              # 默认输出 (带框+ID+计数线+ROI)
outputs/events.jsonl            # M4 事件记录 (JSONL)
outputs/snapshots/*.jpg         # M4 自动截图
```

### Track 数据结构
```python
Track:
  track_id: int
  class_id: int
  class_name: str
  confidence: float
  bbox: (x1,y1,x2,y2)
  center: (cx,cy)
```

下游不直接依赖 `ultralytics.engine.results.Results`。

## 安装

```bash
conda create -n yolo-portfolio python=3.11 -y
conda activate yolo-portfolio
pip install -r requirements.txt
```

首次运行自动下载 `yolov8n.pt` (~6MB)。

## 配置

`config/config.yaml`:

```yaml
model: yolov8n.pt
source: assets/sample.mp4
output: outputs/result.mp4
device: auto
conf: 0.25
iou: 0.5
imgsz: 640
tracker: bytetrack.yaml

line_crossing:
  enabled: true
  line: [[320, 0], [320, 480]]
  mode: both
  classes: null

roi:
  enabled: true
  polygon: [[0.25,0.25],[0.75,0.25],[0.75,0.75],[0.25,0.75]]
  dwell_sec: 1.5
  classes: null

events:
  enabled: true
  json_path: outputs/events.jsonl
  snapshot_dir: outputs/snapshots
  snapshot_expand: 0.2
  snapshot_max: 100
```

- `line`: 虚拟线, 归一化 0-1 自动转像素
- `roi`: 多边形≥3点 + dwell阈值
- `events`: JSONL路径 + 截图目录 + 外扩比例 + 上限
- `device: auto` → cuda > mps > cpu

## 运行

```bash
# M4 默认 (越线+ROI+事件)
conda run -n yolo-portfolio python main.py --config config/config.yaml
# → outputs/events.jsonl 4行 + outputs/snapshots/4图

# 单独开关
conda run -n yolo-portfolio python main.py --no-line
conda run -n yolo-portfolio python main.py --no-roi
conda run -n yolo-portfolio python main.py --no-events

# 自定义视频
conda run -n yolo-portfolio python main.py --source assets/line_demo.mp4 --output outputs/line_result.mp4  # 8事件 (4line+4dwell)
conda run -n yolo-portfolio python main.py --source assets/roi_demo.mp4 --output outputs/roi_result.mp4
```

事件示例 (`events.jsonl`):
```json
{"event_id":"dwell_1_30_8371","type":"dwell","timestamp":1.5,"frame_idx":30,"track_id":1,"class_name":"person","center":[202.6,291.5],"bbox":[158,178,246,404],"enter_frame":1,"duration_sec":1.5,"snapshot":"outputs/snapshots/dwell_1_30_8371.jpg"}
{"event_id":"line_3_18_14e8","type":"line_cross","timestamp":0.9,"frame_idx":18,"track_id":3,"center":[326,281],"bbox":[295,175,357,386],"direction":"a_to_b","snapshot":"..."}
```

## 验证

已在 M1 Mac (MPS) 验证:

- **M1**: bus.jpg 5目标 ID稳定; sample 80f 357检测
- **M2**: line_demo 4越线 @18/41/50/59 (movement>3去抖), sample 0
- **M3**: sample occ4 dwell4@30f; roi_demo occ max4 dwell4@30/33/38/42
- **M4**: 
  - sample: `events.jsonl` 4 dwell + 4 snapshots (27KB/75KB/14KB/16KB), 时间戳1.5s, bbox可溯
  - line_demo: 8事件 (4 line+4 dwell) 8截图, clip含bus/person
  - --no-events: 无文件, 回归 M3 行为
  - 边界: 超框/小框 snapshot clamp≥10px, expand 0-1 校验
- **性能**: sample MPS 18.9fps (line+roi+events 4 snapshots), line_demo 13.6fps
- **测试**: 28 passed — line 10 + roi 9 + events 6 + track 2 + video 1
```bash
conda run -n yolo-portfolio python -m pytest tests/ -v
conda run -n yolo-portfolio python main.py --source assets/sample.mp4
cat outputs/events.jsonl | head
ls outputs/snapshots/
```

## 下一步 (M5)

- FastAPI 接口
- 简单 Dashboard
- RTSP 支持

## License

MIT (代码) / Ultralytics AGPL-3.0 (模型)
