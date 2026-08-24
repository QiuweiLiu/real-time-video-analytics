# PLAN — Milestone 3: ROI / Occupancy / Dwell

## Goal
在 M1/M2 基础上增加 ROI 区域感知：多边形 ROI 内外判定，实时 Occupancy 人数统计，Dwell 停留时长检测与事件触发，可视化叠加，配置驱动，不破坏既有管线。

## Boundary
- Inputs: config.yaml 新增 `roi` 段 (polygon + dwell_sec), 复用已有视频 (sample/line_demo) + 可选 roi_demo 滑移停留视频
- Allowed: 修改 config, 新建 analytics/roi.py, 扩展 pipeline/visualizer, 新增测试与 demo 生成脚本, 更新 README
- Forbidden: 改 Track 结构, 引入 FastAPI/RTSP, 二套状态, 改动 M2 line 逻辑
- Success:
  - `main.py` 同时支持 line+roi (可单独开关) 输出 `outputs/roi_result.mp4` 带 ROI 多边形+占用数
  - 单元: 点在多边形 5用例, 占用计数 per-frame, 停留 2sec 触发 (20fps → 40帧), 去抖 (进出只计一次), 归一化 0-1 转换
  - 集成: sample (中心矩形) 占用 2-3, dwell 在 4sec 视频内触发 ≥1 (阈值 1.5s); line_demo 占用 1-3, dwell 阈值 1.0s 时触发
  - 可视化: ROI 半透明填充+边框+ `Occupancy: N / Dwell: M` 叠加, dwell 超阈值红框警告
  - 回归: 关闭 roi 时 M1/M2 行为一致, 13→18 tests 均通过
- Escalation: 若 YOLO 中心点判定导致边缘抖动误触发 dwell → 增加进入/离开滞回或时间阈值调参
- Compute: <20s 80f, 无配额

## Tasks
1. **Config 设计** (20min) — ✅ done
   - roi polygon + dwell_sec + classes, 归一化

2. **Analytics 核心** (60min) — ✅ done
   - point_in_polygon, ROIAnalytics, DwellEvent, 30f阈值, 去抖

3. **Pipeline & Visualizer 集成** (40min) — ✅ done
   - draw_roi + highlight, pipeline 双 analytics, stats

4. **Demo 视频与测试** (40min) — ✅ done
   - roi_demo 滑入停留, 9 tests, 22 total

5. **Verification** (30min) — ✅ done
   - sample occ4 dwell4, roi_demo occ4 dwell4, 归一化, --no-* 回归, MPS 7fps

## Verification Plan
- 最小先测: synthetic polygon → synthetic Track 序列 → 真实 YOLO roi_demo → full pipeline
- 证据: 输出视频帧数/大小, 日志 occupancy/dwell, 截图, pytest 22
- Gate: not_required

## Deliverable Checklist
- [x] 修改文件清单
- [x] 运行命令
- [x] 测试结果
- [x] 输出视频
- [x] 下一步 M4
