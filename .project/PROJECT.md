# PROJECT: Real-Time Video Analytics

## Goal
交付一个从 MP4 → YOLO检测 → ByteTrack跟踪 → 事件分析 → 可视化输出 的小型可交付视频分析系统，展示从模型到应用的 CV 工程能力。

## Scope
- 输入: MP4 视频 (M1), 后续 RTSP
- 核心: YOLO + ByteTrack 稳定 Track ID + 可视化视频
- 事件: 越线/ROI/驻留/截图/JSON (M2-M4), API/Dashboard (M5)
- 非目标: 自研检测/跟踪算法、复杂前端

## Constraints
- Python + OpenCV + Ultralytics YOLO + ByteTrack (via ultralytics tracker)
- 结构: source / vision / analytics / events
- 自定义 Track 结构, 不泄漏 Ultralytics 格式
- 配置文件管理 (model/video/conf/output/device)
- 支持 CUDA / MPS / CPU 自动选择
- 代码最小完整、可运行、可验证

## Architecture Overview (M1)
```
config.yaml → VideoSource (source/) → VisionPipeline (vision/: YOLO.track + Track 转换) → VideoWriter → output.mp4
                ↑                                                              |
            DeviceResolver (utils/device)                                  Visualizer
```
- `source/video_source.py`: OpenCV VideoCapture 封装, 帧迭代、元信息、释放
- `vision/types.py`: Track dataclass (track_id, class_name, confidence, bbox[x1,y1,x2,y2], center)
- `vision/detector.py`: YOLO model 加载, device 解析, track(frame) -> List[Track]
- `vision/visualizer.py`: 绘制 bbox/class/ID (可选)
- `analytics/` , `events/`: M1 占位, 不引入逻辑
- `pipeline.py` / `main.py`: 串联 source→vision→writer, 配置驱动

## Milestones
- M1: MP4 + YOLO + ByteTrack + Stable ID + 输出带框视频 ✅ 当前
- M2: Line Crossing 越线统计
- M3: ROI / Occupancy / Dwell Time
- M4: Event JSON + 截图
- M5: FastAPI + Dashboard + RTSP

## Key Decisions
- 使用 ultralytics 内置 ByteTrack (`bytetrack.yaml`) 而非独立仓库, 最小依赖、官方维护
- Device: torch.backends.mps.is_available() 优先, 回落 cpu; 透传 device 字符串给 YOLO

## Risks
- M1 M芯片上 MPS 可能慢于 CPU, 需实测对比, 提供 --device 手动覆盖
- Ultralytics 版本差异导致 API 漂移, 已基于 8.4.121 验证
