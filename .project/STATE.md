# STATE

## Current Phase
M5 — Completed & Verified (2026-08-24)

## Verified (M1-M5)
- 37 tests (10 line +9 roi +6 events +2 track +1 video +5 api +4 rtsp)
- M1: sample 80f 357 detections, 1.44MB m1-only, bus.jpg 5 ID stable
- M2: line_demo 4 cross @18/41/50/59, sample 0 (movement3+cooldown10), line_result 1.99MB
- M3: sample occ4 dwell4@30f=1.5s, roi_demo occ max4 dwell4@30/33/38/42, roi_result 1.73MB, 归一化通过
- M4: sample events.jsonl 4 dwell +4 snapshots (14-75KB), line_demo 8 events 8 snaps, --no-events 回归
- M5: FastAPI health/config/dashboard/process(80f) ok, curl upload sample 80f 4 dwell, GET /events 4, VideoSource rtsp识别4, Dashboard 拖拽+KPI+表格, RTSP max_frames 300
- 性能: CLI sample 18.9fps MPS, API sync 11.5fps cpu, rtsp fallback 25fps

## In Progress
- 无 (M5交付完成, 全项目闭环)

## Open Issues
- 无阻塞

## Risks
- 已缓解

## Next
- 归档发布: git push, README 展示, 可选 Docker
