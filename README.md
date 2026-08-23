# Real-Time Video Analytics (M1+M2)

小型可交付视频分析系统 — MP4 → YOLO检测 → ByteTrack跟踪 → 稳定ID → 事件统计 → 可视化视频。

## 技术栈
- Python 3.11
- OpenCV 5.x
- Ultralytics YOLO 8.4 (内置 ByteTrack `bytetrack.yaml`)
- PyTorch (MPS / CUDA / CPU)

## 结构
```
config/config.yaml          # 配置: 模型/视频/conf/输出/device + line_crossing
src/source/                 # 视频输入 (VideoSource)
src/vision/                 # 检测+跟踪 (YOLOTracker, Track, visualizer)
src/analytics/              # 业务分析 (line_crossing.py — M2)
src/events/                 # 事件记录 (M4 占位)
src/pipeline.py             # 串联 source→vision→analytics→writer
main.py                     # 入口
assets/sample.mp4           # M1 样例 (80f 618KB, 5目标)
assets/line_demo.mp4        # M2 滑移 demo (80f 763KB, 保证越线)
outputs/result.mp4          # M1/M2 输出 (带框+ID+计数线)
outputs/line_result.mp4     # M2 滑动 demo 输出 (4次越线)
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

推荐使用 conda:

```bash
conda create -n yolo-portfolio python=3.11 -y
conda activate yolo-portfolio
pip install -r requirements.txt
```

或直接复用现有环境 `yolo-portfolio` (已验证: torch 2.13 + mps).

首次运行会自动下载 `yolov8n.pt` (~6MB) 到当前目录或 ultralytics 缓存。

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
  line: [[320, 0], [320, 480]]  # p1->p2, 支持 0-1 归一化
  mode: both   # both | a_to_b | b_to_a
  classes: null
```

- `line`: 虚拟线两端点, 归一化 `[[0.5,0],[0.5,1]]` 自动转为像素
- `mode`: 越线方向过滤
- `classes`: 仅统计特定类别, null=全部
- `device: auto` 会自动选择 `cuda` > `mps` > `cpu`

## 运行

```bash
# M2 默认 (带越线)
conda run -n yolo-portfolio python main.py --config config/config.yaml
# 输出 line_crossing total/a_to_b/b_to_a, 可视化含黄线与计数

# 纯 M1 回归
conda run -n yolo-portfolio python main.py --config config/config.yaml --no-line

# 自定义线与视频
conda run -n yolo-portfolio python main.py --source assets/line_demo.mp4 --output outputs/my.mp4 --device mps

# 归一化线示例
# line: [[0.5, 0], [0.5, 1]]  # 垂直中心线, 自适应分辨率
```

输出: `outputs/*.mp4` (带框、类别、ID、计数线与实时计数)

## 验证

已在 M1 Mac (MPS) 验证:

- **M1**: `bus.jpg` 单帧 5 目标 ID 1..5 稳定; `sample.mp4` 80帧 357检测, 无越线时 0 计数 (抖动过滤 via movement>3px + cooldown 10)
- **M2**: `line_demo.mp4` 80帧 303检测, 越线 4 次 (person 3 + bus 1, 均为 a_to_b), 输出 1.9MB, 日志 `[cross] frame=18/41/50/59`
- **归一化**: `[[0.5,0],[0.5,1]]` 正确转为 320px 线, 计数一致
- **性能**: line_demo MPS ~10.6fps, sample MPS ~8.9fps (含跟踪+分析)
- **测试**: 13 passed — `test_line_crossing` 10 (含方向/去抖/归一化) + `test_track_conversion` 2 + `test_video_source` 1

```bash
conda run -n yolo-portfolio python -m pytest tests/ -v
conda run -n yolo-portfolio python main.py --source assets/line_demo.mp4 --output outputs/line_result.mp4
```

## 下一步 (M3)

- ROI 区域检测
- Occupancy 人数统计
- Dwell Time 停留检测

## License

MIT (代码) / Ultralytics AGPL-3.0 (模型)
