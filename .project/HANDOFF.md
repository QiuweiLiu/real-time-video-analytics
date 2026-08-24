# HANDOFF

Goal: M4 Event JSON + Snapshot
Done:
- Config events enabled/json/snapshot_expand/max
- EventLogger JSONL + save_snapshot clamp/expand/min10
- Pipeline 集成 line/dwell → logger+snapshot (uuid, timestamp=frame/fps, snapshot路径), stats events_json/snapshots
- Tests 6 events (logger读写, 正常/边界/小框/0expand, disabled)
- 验证: sample 4 dwell 4截图 1.7KB json, line_demo 8事件 8图 3.3KB, --no-events 无文件回归, 22→28 tests
Verified:
- 端到端 80f, MPS 13-18fps, json字段完整, 截图可读 (14-75KB), 事件去重
Rejected: —
Open: 无
Active: 待 commit/push
Next:
1. commit → push
2. M5 FastAPI/Dashboard/RTSP
