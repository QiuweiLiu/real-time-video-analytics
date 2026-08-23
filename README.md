# Real-Time Video Analytics (M1+M2+M3)

小型可交付视频分析系统 — MP4 → YOLO检测 → ByteTrack跟踪 → 稳定ID → 事件统计 (越线/ROI/驻留) → 可视化视频。

## 技术栈
- Python 3.11
- OpenCV 5.x
- Ultralytics YOLO 8.4 (内置 ByteTrack `bytetrack.yaml`)
- PyTorch (MPS / CUDA / CPU)

## 结构
```
config/config.yaml              # 配置: 模型/视频/conf/输出/device + line_crossing + roi
src/source/                     # 视频输入 (VideoSource)
src/vision/                     # 检测+跟踪 (YOLOTracker, Track, visualizer)
src/analytics/                  # 业务分析 (line_crossing.py, roi.py)
src/events/                     # 事件记录 (M4 占位)
src/pipeline.py                 # 串联 source→vision→analytics→writer
main.py                         # 入口
assets/sample.mp4               # M1 样例 (80f 618KB, 5目标)
assets/line_demo.mp4            # M2 滑移 demo (80f 763KB, 4越线)
assets/roi_demo.mp4             # M3 停留 demo (80f 688KB, dwell触发)
outputs/result.mp4              # 默认输出 (带框+ID+计数线+ROI)
outputs/line_result.mp4         # M2 输出 (4越线)
outputs/roi_result.mp4          # M3 输出 (占用4, dwell4)
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

或复用 `yolo-portfolio` (已验证 torch 2.13 + mps). 首次运行自动下载 `yolov8n.pt` (~6MB)。

## 配置

`config/config.yaml`:

```yaml
model: yolov8n.pt
source: assets/sample.mp4
output: outputs/result.mp4
device: auto   # auto | cpu | mps | cuda | 0
conf: 0.25
iou: 0.5
imgsz: 640
tracker: bytetrack.yaml

line_crossing:
  enabled: true
  line: [[320, 0], [320, 480]]  # 支持 0-1 归一化
  mode: both
  classes: null

roi:
  enabled: true
  polygon: [[0.25,0.25],[0.75,0.25],[0.75,0.75],[0.25,0.75]]  # 中央矩形, 归一化
  dwell_sec: 1.5
  classes: null
```

- `line`: 虚拟线, `mode` 方向过滤, `polygon`: ROI多边形 (≥3点), `dwell_sec`: 停留秒数
- 归一化 `0-1` 自动转像素, 适配任意分辨率
- `device: auto` → cuda > mps > cpu

## 运行

```bash
# M3 默认 (越线+ROI)
conda run -n yolo-portfolio python main.py --config config/config.yaml
# 日志: [cross] / [dwell] / frame occupancy, 输出带黄线+绿ROI+计数

# 单独开关
conda run -n yolo-portfolio python main.py --no-line   # 仅ROI
conda run -n yolo-portfolio python main.py --no-roi    # 仅越线
conda run -n yolo-portfolio python main.py --no-line --no-roi  # 纯M1

# 自定义视频
conda run -n yolo-portfolio python main.py --source assets/roi_demo.mp4 --output outputs/my.mp4
conda run -n yolo-portfolio python main.py --source assets/line_demo.mp4 --output outputs/my2.mp4
```

输出: `outputs/*.mp4` 带框/ID/计数线/ROI/占用数, dwell 红框警告

## 验证

已在 M1 Mac (MPS) 验证:

- **M1**: bus.jpg 5目标 ID稳定; sample 80f 357检测
- **M2**: line_demo 80f 303检测 越线4 (a_to_b 4, person3 bus1 @18/41/50/59), sample 0 (movement>3去抖)
- **M3**: 
  - sample 80f → 占用4 (max4, by_class person3 bus1), dwell 4 @30帧 (1.5s, 30f) 全员触发
  - roi_demo 80f 350检测 → 占用 max4, dwell4 @30/33/38/42 (滑入停留, 各ID分时触发), 越线5
  - 归一化: [[0.25,0.25]...] → 160,120-480,360 正确, [[0.5,0],[0.5,1]] 线亦通过
- **性能**: sample MPS 7.4fps (line+roi), line_demo 10.6fps, roi_demo 5.5fps
- **测试**: 22 passed — line_crossing 10 + roi 9 + track 2 + video 1
```bash
conda run -n yolo-portfolio python -m pytest tests/ -v
```

## 下一步 (M4)

- Event JSON 记录
- 自动截图 (事件帧保存)

## License

MIT (代码) / Ultralytics AGPL-3.0 (模型)
