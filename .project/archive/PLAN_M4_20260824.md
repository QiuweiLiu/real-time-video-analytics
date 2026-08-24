# PLAN — Milestone 4: Event JSON + 自动截图

## Goal
为已有的越线/ROI/dwell 事件增加持久化：每事件写入 JSON 记录（含帧号/时间戳/track/类型/位置）并自动保存事件发生时的目标截图 (bbox crop)，配置驱动，可选开关。

## Boundary
- Inputs: 已有 analytics 事件 (line_crossing, dwell), 原始帧 + Track bbox, config 新增 events 段
- Allowed: 新建 src/events/logger.py + snapshot.py, 修改 config、pipeline、main, 更新 README, 新增测试
- Forbidden: 改 Track/ROI/Line 核心逻辑, 引入 RTSP/FastAPI, 二套状态
- Success:
  - 运行 `main.py` 后生成 `outputs/events.jsonl` (每行一 event, 含 event_id/type/timestamp/frame/track/class/center/bbox, line/dwell 特有字段) 且 `outputs/snapshots/*.jpg` (事件裁剪)
  - sample 80f → json 4 dwell + 0 line 计数, snapshots 4 张; line_demo 4 line + 0 dwell? (roi disabled) 或 roi_demo 4+3 混合; 截图文件对应 event_id
  - 关闭 events.enabled 时无文件且 M3 行为一致 (回归)
  - 单元: logger 写入/读取, snapshot 边界裁剪 (超框, 小框), 去重命名
  - 总 tests 22→26 passed
- Escalation: 若 bbox 裁剪超帧边界导致空图 → clamp 并保证 1x1 最小
- Compute: <25s 80f, 截图 4-8 张 <2MB

## Tasks
1. **Config 设计** (15min) — ✅ done
2. **Events 核心** (60min) — ✅ done (logger JSONL + snapshot clamp/expand)
3. **Pipeline 集成** (40min) — ✅ done (uuid, timestamp, snapshot并行)
4. **Tests & Demo** (30min) — ✅ done (6 tests, 28 total)
5. **Verification** (30min) — ✅ done (sample 4 dwell/4snap, line_demo 8/8, --no-events 回归)

## Verification Plan
- 最小先: 合成 logger + 假 frame snapshot → 真实视频 pipeline
- 证据: jsonl行数/首行内容, snapshot 数量/大小/可读, 截图与 bbox 对应, pytest 28, 日志 EventLogger

## Deliverable Checklist
- [x] 修改文件清单
- [x] 运行命令
- [x] 测试结果
- [x] 输出视频+JSON+截图路径
- [x] 下一步 M5
