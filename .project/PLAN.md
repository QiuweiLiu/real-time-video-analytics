# PLAN — Milestone 5: FastAPI + Dashboard + RTSP

## Goal
将本地管道服务化：提供 FastAPI HTTP 接口上传/处理视频、查询事件/回放，提供极简可交互 Dashboard (上传+播放+事件表格)，并扩展 VideoSource 支持 RTSP 流输入（带帧数/时长限制），保持 M1-4 配置与管道兼容。

## Boundary
- Inputs: 已有 pipeline/config, 新增 HTTP 层与 RTSP 扩展
- Allowed: 新建 `api/` (FastAPI app, static), 扩展 `src/source/video_source.py` 支持 rtsp://, 更新 requirements, 配置新增 server/rtsp 段, 更新 README, 新增测试
- Forbidden: 改 Track/Analytics/Events 核心, 引入认证/数据库, 二套状态
- Success:
  - `uvicorn api.app:app --port 8000` 启动, `GET /health` 200, `GET /` 返回 dashboard html
  - `POST /process` 上传 mp4 (sample 618KB) 同步处理返回 stats JSON (80f, events 4) 并生成 outputs/result.mp4 + events.jsonl + snapshots, 可通过 `GET /video` 回放
  - `GET /events` 返回 jsonl 解析, `GET /snapshots/{id}.jpg` 可访问
  - `GET /api/config` 返回当前配置
  - `VideoSource("rtsp://...")` 打开失败时报错清晰 (无真实rtsp服务器时 mock via sample.mp4 模拟)
  - Dashboard: 拖拽上传, 处理后自动播放视频 + 事件表格刷新, 无需手动刷新
  - 测试: `tests/test_api.py` 3用例 (health, upload->process, events) + `tests/test_rtsp.py` 1用例 (rtsp URL 识别)
  - 回归: 28→32 tests passed, 本地 `main.py` 仍工作
- Escalation: 若 uvicorn 端口占用或 torch mps 在子进程冲突 → 报告并建议 --device cpu
- Compute: FastAPI 处理 80f <20s, 无长时守护

## Tasks
1. **Config & Source 扩展** (20min) — ✅ done (server/rtsp, _is_stream, max_frames)
2. **FastAPI 核心** (60min) — ✅ done (5 endpoints, CORS, static)
3. **Dashboard** (30min) — ✅ done (拖拽, KPI, 表格)
4. **RTSP 扩展** (20min) — ✅ done (VideoSource rtsp, pipeline max_frames)
5. **Tests & Verification** (30min) — ✅ done (api5+rtsp4, 37 total, curl upload)

## Verification Plan
- 最小先: TestClient health → upload sample → 事件/视频 → 浏览器 dashboard → RTSP URL 识别
- 证据: `curl /health` 200, `POST /process` 80f 4, `GET /events` 4, 截图, dashboard, pytest 37
- Gate: not_required

## Deliverable Checklist
- [x] 修改文件清单
- [x] 运行命令 (uvicorn + curl + dashboard)
- [x] 测试结果 (37)
- [x] 输出视频+服务地址
- [x] 下一步 (归档/发布)
