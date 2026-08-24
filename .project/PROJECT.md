# PROJECT: Real-Time Video Analytics

## Goal
交付一个从 MP4 → YOLO检测 → ByteTrack跟踪 → 事件分析 → 可视化输出 的小型可交付视频分析系统，展示从模型到应用的 CV 工程能力。

## Scope
- 输入: MP4 视频 (M1), 后续 RTSP (M5)
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

## Architecture Overview (M5)
```
config.yaml → VideoSource (+RTSP) → YOLOTracker → Line/ROI Analytics → EventLogger+Snapshot → Visualizer → VideoWriter → output.mp4
                                          ↘ FastAPI (/process,/events,/video) → Dashboard (HTML) + RTSP
```
- `source/video_source.py`: VideoCapture + RTSP (max_frames, fps fallback)
- `vision/types.py`: Track dataclass
- `vision/detector.py`: YOLO.track + ByteTrack
- `analytics/line_crossing.py` & `roi.py`: 越线/占用/停留
- `events/logger.py` & `snapshot.py`: JSONL + 截图
- `api/app.py` + `api/static/dashboard.html`: FastAPI + 极简前端
- `pipeline.py` + `main.py`: 串联 + CLI

## Milestones
- M1: MP4 + YOLO + ByteTrack + Stable ID + 输出带框视频 ✅ 2026-08-21
- M2: Line Crossing 越线统计 ✅ 2026-08-22
- M3: ROI / Occupancy / Dwell ✅ 2026-08-23
- M4: Event JSON + 截图 ✅ 2026-08-24
- M5: FastAPI + Dashboard + RTSP ✅ 2026-08-24

## Key Decisions
- 使用 ultralytics 内置 ByteTrack (`bytetrack.yaml`) 而非独立仓库
- Device: auto → mps > cpu, 透传给 YOLO; API 允许 --device cpu 回退
- 去抖: movement>3px + cooldown 10, dwell 30f=1.5s
- 事件: JSONL + snapshot expand 0.2, uuid 避免覆盖
- 服务: FastAPI 同步 pipeline, 限制上传50MB, RTSP max_frames 300

## Risks
- MPS 在子进程可能冲突 → API 提供 cpu 选项
- RTSP 无真实服务器 → mock 测试, 文档说明
