# STATE

## Current Phase
M3 — Completed & Verified (2026-08-23)

## Verified (M1+M2+M3)
- 环境 M1 yolo-portfolio 8.4.121 mps, 22 tests (10 line +9 roi +2 track +1 video)
- M1: sample 80f 357 det, outputs/result 1.44MB m1-only
- M2: line_demo 4 cross (a_to_b 4), sample 0 (movement3+cooldown10), line_result 1.99MB
- M3: roi polygon [[0.25,0.25]..]→160,120-480,360, dwell 1.5s=30f
  - sample: occ 4 max4 by_class person3 bus1, dwell 4 @30f (全员)
  - roi_demo 80f 350det: occ max4, dwell 4 @30/33/38/42 (各ID分时), line 5
  - result (sample+line+roi): occ4 dwell4 line0 1.89MB, roi_result 1.73MB
- 可视化: 黄线+计数, 绿ROI半透明+边框+ Occupancy/Dwell 叠加, dwell红框
- 归一化: 线与多边形 0-1→像素验证, --no-line/--no-roi 回归通过
- 性能: sample 7.4fps MPS (line+roi), 10.6fps line-only

## In Progress
- 无 (M3交付完成)

## Open Issues
- 无阻塞

## Risks
- 阈值固定, 极慢速目标 dwell 需 30f 连续, 丢失1帧会重置计时, 可后续增加容忍帧

## Next
- M4: Event JSON + 自动截图
