# Real-Time Video Analytics (M1)

小型可交付视频分析系统 — MP4 → YOLO检测 → ByteTrack跟踪 → 稳定ID → 可视化视频。

## 技术栈
- Python 3.11
- OpenCV 5.x
- Ultralytics YOLO 8.4 (内置 ByteTrack `bytetrack.yaml`)
- PyTorch (MPS / CUDA / CPU)

## 结构
```
config/config.yaml      # 配置: 模型/视频/conf/输出/device
src/source/             # 视频输入 (VideoSource)
src/vision/             # 检测+跟踪 (YOLOTracker, Track, visualizer)
src/analytics/          # 业务分析 (M2/M3 占位)
src/events/             # 事件记录 (M4 占位)
src/pipeline.py         # 串联 source→vision→writer
main.py                 # 入口
assets/sample.mp4       # 输入视频
outputs/result.mp4      # 输出视频
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
```

`device: auto` 会自动选择 `cuda` > `mps` > `cpu`。

## 运行

```bash
# 使用配置文件
conda run -n yolo-portfolio python main.py --config config/config.yaml

# 覆盖参数
conda run -n yolo-portfolio python main.py --source assets/my.mp4 --output outputs/my_out.mp4 --device cpu --conf 0.3
```

输出: `outputs/result.mp4` (带框、类别、ID)

## 验证

已在 M1 Mac (MPS) 验证:

- `bus.jpg` 单帧跟踪: 5 目标, ID 稳定 1..5, 第二帧 persist 保持一致
- `mp4` 全量: 帧数与输入一致, 文件非空, 日志打印每30帧跟踪情况

## 下一步 (M2)

- Line Crossing 越线统计
- 计数可视化与日志

## License

MIT (代码) / Ultralytics AGPL-3.0 (模型)
