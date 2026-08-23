# HANDOFF

Goal: M3 ROI/Occupancy/Dwell
Done:
- Config roi polygon/dwell/classes 归一化
- ROIAnalytics point_in_polygon + occupancy max/by_class + dwell 30f触发 + 去抖 (enter_frame连续)
- Visualizer ROI半透明+occupancy/dwell文本+红框, Pipeline集成 line+roi 并行
- Demo roi_demo 80f 滑入停留 (前16滑入 中40停留 后24滑出) 704KB
- Tests 9 roi (内外/边/占用/阈值/重置/过滤/归一化/by_class) + 13 prior =22 passed
- 验证: sample occ4 dwell4@30, roi_demo occ4 dwell4@30/33/38/42 line5, result 1.89MB, --no-* 回归
Verified:
- 端到端 80f一致, 可视化绿ROI+黄线, MPS 5-7fps, 22 tests
Rejected: —
Open: 无
Active: 待 commit/push
Next:
1. commit → push
2. M4 JSON+截图 (事件持久化)
