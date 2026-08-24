# HANDOFF

Goal: M5 FastAPI+Dashboard+RTSP (最终)
Done:
- Config server/port + rtsp.max_frames/timeout + events/server/rtsp 解析
- VideoSource _is_stream + max_frames + fps fallback 25 + is_stream flag
- FastAPI api/app.py (health/config/process/events/video/snapshots + CORS + static), dashboard.html 极简上传+视频+KPI+事件表
- Tests 5 api (health/config/events/dashboard/upload) +4 rtsp, 28→37 passed
- 验证: uvicorn :8001 health200 config dashboard, curl POST sample 80f 4 dwell, GET /events 4, VideoSource 4, dashboard 拖拽
Verified:
- 端到端 80f 1.89MB + json 4 + snapshots 4, API 11.5fps, RTSP识别, 37 tests
Rejected: —
Open: 无
Active: 待 commit/push
Next:
1. commit → push
2. 发布: git tag M5, README 最终, 可选 Docker/Pages
