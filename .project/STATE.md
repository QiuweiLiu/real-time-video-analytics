# STATE

## Current Phase
M4 — Completed & Verified (2026-08-24)

## Verified (M1+M2+M3+M4)
- 28 tests (10 line +9 roi +6 events +2 track +1 video)
- M1: sample 80f 357 det, 1.44MB m1-only
- M2: line_demo 4 cross @18/41/50/59, sample 0
- M3: sample occ4 dwell4@30f=1.5s, roi_demo occ max4 dwell4@30/33/38/42
- M4: sample events.jsonl 4 dwell +4 snapshots (14-75KB), line_demo 8 events (4+4) 8 snapshots, json 字段 event_id/type/timestamp/frame/track/bbox/center/direction/polygon/duration/snapshot, --no-events 回归
- 性能: sample 18.9fps MPS, line_demo 13.6fps (含截图)

## In Progress
- 无 (M4交付完成)

## Open Issues
- 无阻塞

## Risks
- Snapshot 多事件同帧同ID已用 uuid 避免覆盖, 但连续帧快速事件可能超 snapshot_max 100 (未触达)

## Next
- M5: FastAPI + Dashboard + RTSP
