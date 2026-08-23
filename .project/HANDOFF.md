# HANDOFF

Goal: M2 Line Crossing 越线统计
Done:
- Config 扩展 line_crossing (enabled/line/mode/classes, 归一化支持)
- Analytics LineCrossingCounter (side+segment相交, movement>3px 去抖, cooldown 10, 方向 both/a_to_b/b_to_a, by_class)
- Visualizer draw_line_and_counts + Pipeline 集成 (frame30日志, stats 含 line_crossing/line_events)
- Demo: assets/line_demo.mp4 80f 滑移 bus 763KB, 生成 scripts/generate_line_demo.py
- Tests: 10 line_crossing 单元 + 归回, 13 total passed
- 验证: line_demo 4次 (18/41/50/59) person3 bus1, sample 0次 (抖动过滤), 归一化 0.5 线一致, --no-line 回归 1.44MB
Verified:
- 端到端 80f 输出一致, 可视化含黄线+计数, MPS 8-10fps, CPU 1.4fps
- 去抖生效: sample 6→0, line_demo 保持 4
Rejected: —
Open: 无
Active: 待 review/commit
Next:
1. review → commit → push
2. 启动 M3 (ROI/Occupancy/Dwell) 需定义区域配置
