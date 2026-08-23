# PLAN — Milestone 2: Line Crossing 越线统计

## Goal
在 M1 管道基础上增加虚拟线越线统计：检测 Track 中心轨迹与虚拟线的相交，统计越线次数（总数 + 方向），在输出视频上可视化计数线与实时计数，并通过配置文件驱动。

## Boundary
- Inputs: config.yaml 新增 `line_crossing` 段, MP4 视频 (复用 M1 sample + 新增 line_demo 滑移视频)
- Allowed: 修改 config/utils/config、pipeline、visualizer; 新增 analytics/line_crossing.py; 新增测试与 demo 视频生成脚本; 更新 README
- Forbidden: 修改 Track 定义、引入 ROI/RTSP/FastAPI、二套状态系统、改动 M1 的 device/model 逻辑
- Success:
  - `conda run -n yolo-portfolio python main.py --config config/config.yaml` (line_crossing enabled) 生成 `outputs/result.mp4` 带线与计数 overlay
  - 合成轨迹单元测试: 左右穿越各计 1, 往返计 2, 未穿越 0, 方向 both/a_to_b/b_to_a 符合预期
  - 滑移 demo `assets/line_demo.mp4` (bus 水平滑移) 越线数 ≥1, 输出 `outputs/line_result.mp4` 80帧 1.4MB+
  - M1 回归: 关闭 `enabled: false` 时 pipeline 行为与 M1 一致, 无回归
- Escalation: 若检测抖动导致同一 ID 往复误计数 → 增加 side 稳定阈值或去抖逻辑, 需报告并调整
- Compute: <10s 80帧, 无需 GPU quota

## Tasks
1. **Config 设计** (20min)
   - `config.yaml`: 新增
     ```yaml
     line_crossing:
       enabled: true
       line: [[320, 0], [320, 480]]  # p1->p2, 适配 640x480; 支持 0-1 归一化自动转换
       mode: both  # both | a_to_b | b_to_a
       classes: null  # null=全部, e.g. [0] 仅人
     ```
   - `src/utils/config.py`: 新增 `LineCrossingConfig` dataclass, 解析 line/mode/classes/enabled, 校验 line 为 2 点
   - `PipelineConfig` 新增 `line_crossing: LineCrossingConfig | None`

2. **Analytics 核心** (60min)
   - `src/analytics/line_crossing.py`: `LineCrossingCounter`
     - `__init__(p1, p2, mode="both", classes=None)`
     - `update(tracks: List[Track], frame_idx: int) -> List[CrossingEvent]` — 维护 `last_pos/side` per track_id, 用 cross product 判断侧, 用 segment intersection 判断穿越
     - `get_counts() -> {total, a_to_b, b_to_a, by_class}`
     - `get_events() -> List[dict]`
     - 去抖: 仅当 side 变化且线段相交时计数, 避免同帧重复
   - 辅助: `_side(point)`, `_segments_intersect`, `_is_valid_cross`

3. **Pipeline & Visualizer 集成** (40min)
   - `src/vision/visualizer.py`: 新增 `draw_line_and_counts(frame, p1,p2, counts, mode)` 绘制线 (2px) + 箭头 + 计数文本
   - `src/pipeline.py`: 初始化 counter (若 enabled), 每帧 `counter.update(tracks, frame_idx)`, 统计 `line_crossing_counts`, 传递给 visualizer, 在 `stats` 返回 `line_crossing`
   - `main.py`: 打印越线统计

4. **Demo 视频与测试** (40min)
   - `scripts/generate_line_demo.py`: 640x480 bus 水平滑移 `x = -200 + frame*8`, 生成 `assets/line_demo.mp4` (80帧) 确保中心跨 `x=320`
   - `tests/test_line_crossing.py`: 6 用例 — 左右穿越、往返、未穿越、方向过滤、抖动不误计数、归一化坐标
   - `tests/test_pipeline_line.py`: 集成 smoke (mock tracks 跨线)

5. **Verification** (30min)
   - 单元: `pytest tests/test_line_crossing.py tests/test_line_crossing*.py -v`
   - 集成: `main.py` 在 `assets/sample.mp4` (可能 0 次) 与 `assets/line_demo.mp4` (≥1 次) 各跑一次, 检查 `outputs/*.mp4` 帧数与 overlay
   - 回归: `enabled: false` 时与 M1 输出一致
   - 性能: MPS vs CPU 对比保留

## Verification Plan
- 最小先测: synthetic Track 轨迹 → line_demo YOLO 真实检测 → full pipeline
- 证据: 输出视频路径/帧数/大小, 日志 `line_crossing_counts`, 单帧截图带线, pytest 数
- Gate: not_required (local engineering, 无 formal experiment)

## Deliverable Checklist
- [x] 修改文件清单
- [x] 运行命令
- [x] 测试结果
- [x] 输出视频位置与截图
- [x] 下一步 (M3)
