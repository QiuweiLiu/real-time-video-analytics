# STATE

## Current Phase
M2 — Completed & Verified (2026-08-22)

## Verified (M1+M2)
- 环境: M1, yolo-portfolio, 8.4.121, mps=True, 13 tests passed
- M1: sample 80f 357 detections, 0 line-cross (jitter filtered), outputs/result.mp4 80f 1.65MB MPS 8.9fps
- M2: line_demo 80f 303 detections, 4 crossings (a_to_b 4, person 3 bus 1) at frames 18/41/50/59, outputs/line_result.mp4 1.99MB 10.6fps
- 去抖: movement>3px + cooldown 10 frames, 归一化线 [[0.5,0],[0.5,1]]→320px 验证通过
- 单元: 10 line_crossing (方向/去抖/多ID/归一化) + 2 track +1 video + 归回 --no-line 80f 1.44MB

## In Progress
- 无 (M2 交付完成, 待 review)

## Open Issues
- 无阻塞

## Risks
- 阈值 3px 对极慢速目标可能漏计数, 可通过 config 暴露 min_distance 调参

## Next
- M3: ROI / Occupancy / Dwell (待确认)
