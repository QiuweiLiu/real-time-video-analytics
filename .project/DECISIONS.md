# DECISIONS

## 2026-08-21 — M1 architecture: use ultralytics built-in ByteTrack
- Context: 需求要求成熟库不重复实现; 存在独立 BoxMOT/ByteTrack 仓库与 ultralytics 内置 tracker 两种路径
- Decision: 采用 ultralytics YOLO.track + bytetrack.yaml, 不单独引入 boxmot
- Reason: 官方维护、依赖最少、API 已验证 (8.4.121), 避免双重检测/跟踪实现复杂度
- Alternatives rejected: 独立 ByteTrack 实现 (增加依赖与对齐成本)
- Evidence: /opt/miniconda3/envs/yolo-portfolio/lib/python3.11/site-packages/ultralytics/cfg/trackers/bytetrack.yaml, YOLO.track signature

## 2026-08-21 — Python env: reuse yolo-portfolio
- Context: base/ pip3 无 cv2/ultralytics; yolo-portfolio 已满足全部依赖且 mps=True
- Decision: 复用 conda env yolo-portfolio 作为开发/验证环境, requirements.txt 锁定版本
- Reason: 避免重复安装、M1 MPS 已可用、已验证版本一致性

## 2026-08-21 — Review fixes (P1-01, P1-02, P2-03, P2-05)
- Context: reviewer 指出 source==output 覆盖、空输出误报、资源泄漏、CLI conf 绕过校验
- Decision: pipeline 新增同路径 ValueError 保护与前置 try 资源管理; main 新增 total_frames==0 校验与 conf 范围校验; 测试改用 ASSETS 常量
- Reason: 最小完整修复, 不引入复杂架构, 保持 M1 可交付性
- Evidence: pipeline.py:19-26, 31-60; main.py:30-38, 59-62; tests/test_track_conversion.py:6-15

## 2026-08-22 — M2 line crossing 去抖设计
- Context: sample.mp4 静止抖动导致 6次误计数, line_demo 需稳定 4次
- Decision: movement>3px + cooldown 10帧 双重去抖, side+segment 相交校验, 归一化线自适应
- Reason: 1px 阈值无法区分 0.3抖动与 2px有效; 3px 可分离, 结合 cooldown 避免同ID反弹; 保留 synthetic 单元测试覆盖
- Evidence: analytics/line_crossing.py:87-98,182-195; pipeline 10.6fps, sample 0 vs line_demo 4

## 2026-08-22 — Demo 视频选择滑移而非下载
- Context: 公共视频下载 SSL 失败, 现有 sample 仅 5px 抖动无越线
- Decision: 生成 assets/line_demo.mp4 水平滑移 bus (-250->+250, 80f) 确保 4次越线, 比下载更可复现
- Reason: 保证确定性、离线可验证、与 M1 共享 bus 检测分布
- Evidence: scripts/generate_line_demo.py, outputs/line_result.mp4 1.99MB

## 2026-08-23 — M3 阈值与可视化
- Context: 需同时支持静态停留 (sample) 与滑移停留 (roi_demo) 的 dwell 检测, 避免边缘抖动误触发
- Decision: dwell 1.5s=30f@20fps (进入即计时, 仅首次触发, 离开重置), ROI中心点判定+绿色半透明, dwell红框告警, occupancy每帧统计
- Reason: 30f 在 80f 视频内保证 sample 4全员@30f 与 roi_demo 分时@30-42 两类场景均触发, 可视化区分 occupancy/dwell
- Evidence: roi.py:40-90, pipeline 7.4fps, sample occ4 dwell4, roi_demo dwell4

## 2026-08-23 — 归一化统一
- Context: 需适配不同分辨率视频, 硬编码像素不通用
- Decision: line/roi 均支持 0-1 归一化, 检测到全点 0-1 时按 frame W/H 转换, 绝对坐标保持原值
- Reason: 中央 ROI [[0.25,0.25]..] 在 640x480 正确映射 160-480, 便于 Portfolio 演示跨分辨率
- Evidence: config.py _parse, line_crossing/ROIAnalytics set_frame_size, test_normalized

## 2026-08-24 — M4 截图命名与 expand
- Context: 多事件同帧同ID需避免覆盖, bbox贴边需clamp
- Decision: event_id = f"{type}_{track}_{frame}_{uuid4[:4]}", snapshot按 bbox*expand(0.2) clamp至帧内, min10px, snapshot_max 100
- Reason: uuid保证唯一, expand保留上下文, clamp防空图, 统一 logger JSONL便于追加与流式读取
- Evidence: events/logger.py, snapshot.py save_snapshot, tests/test_events.py 6 passed, sample 4截图 line_demo 8截图

## 2026-08-24 — M5 服务与 RTSP
- Context: 需将本地管道服务化且支持流, 但保持同步简单与本地复用
- Decision: FastAPI 同步调用 VideoPipeline (非后台队列), 上传限50MB, VideoSource _is_stream 识别 rtsp/http/数字, max_frames 300 防无限, dashboard 纯静态 HTML 无构建
- Reason: 同步保证 Portfolio 可演示确定性 (10-20s), 避免 Celery/Redis 复杂度; _is_stream 统一文件与流, 复用现有 pipeline; 静态 dashboard 最小依赖
- Evidence: api/app.py 5 endpoints, api/static/dashboard.html, VideoSource 4 tests, api 5 tests, curl POST sample 80f
