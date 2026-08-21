# STATE

## Current Phase
M1 — Completed & Verified (2026-08-21)

## Verified
- 环境: macOS Darwin 25.2.0 arm64, Apple M1 8GB, Python 3.11.15 (conda env yolo-portfolio)
- 依赖: opencv-python 5.0.0.93, ultralytics 8.4.121, torch 2.13.0, torchvision 0.28.0, lap 0.5.13, mps=True, cuda=False
- 接口: YOLO.track(source=ndarray, persist=True, conf, iou, device, tracker="bytetrack.yaml") -> List[Results]; Boxes 7 cols [x1,y1,x2,y2,track_id,conf,cls], id tensor, is_track
- 样例视频: assets/sample.mp4 — 80 frames, 640x480, 20fps, 618KB, 由 bus.jpg 合成, 含 5 目标可检测
- 端到端: `conda run -n yolo-portfolio python main.py --config config/config.yaml` → outputs/result.mp4 80 frames 1.4MB, 18.87fps MPS / 11.6fps CPU, 357 detections, unique_ids [1,2,3,4,5,7,11] 稳定, 日志每30帧打印
- 设备: auto→mps (M1), 手动 --device cpu 覆盖验证通过, 输出一致
- 测试: pytest 3 passed (test_video_source, test_tracks_from_results_with_bus_image 5 tracks ID stable, test_tracks_empty)
- 审查: reviewer 5 issues → 已修复 P1-01/P1-02/P2-03/P2-05, P2-04 部分改进 (ASSETS 常量)

## In Progress
- 无 (M1 交付完成)

## Open Issues
- 无阻塞; outputs/*.mp4 被 .gitignore 忽略, 需本地保留或 releases 分发

## Risks
- M1 MPS 速度波动 (11-18fps), 需 M2 后持续监控

## Next
- M2: Line Crossing 越线统计 (待用户确认后启动)
