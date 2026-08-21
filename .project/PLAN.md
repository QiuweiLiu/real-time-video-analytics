# PLAN — Milestone 1

## Goal
完成 MP4 → YOLO → ByteTrack → 稳定 Track ID → 输出带框/类别/ID 视频, 配置文件驱动, 支持 MPS/CUDA/CPU。

## Boundary
- Inputs: config.yaml, MP4 文件
- Allowed: 新建 src/, config/, assets/, outputs/; 创建 pipeline/main; 安装/声明依赖; 轻量验证视频
- Forbidden: 修改 M2-M5 需求、引入 FastAPI/RTSP、改变 Track 定义范围外、二套状态系统
- Success: `python main.py --config config/config.yaml` 生成 outputs/result.mp4, 帧内 bbox+label+ID 稳定, 无崩溃, 支持 device auto
- Escalation: 若 YOLO track API 在实测中与 8.4.121 不一致 → 停并报告

## Tasks
1. **Config & Device** (30min) — ✅ done
   - config/config.yaml, src/utils/config.py, src/utils/device.py

2. **Core Types & Modules** (60min) — ✅ done
   - src/vision/types.py, src/source/video_source.py, src/vision/detector.py, src/vision/visualizer.py, analytics/events 占位

3. **Pipeline & Entry** (45min) — ✅ done
   - src/pipeline.py, main.py

4. **Dependencies & Assets** (20min) — ✅ done
   - requirements.txt, .gitignore, README.md, assets/sample.mp4 (80f, 640x480, bus合成), yolov8n.pt auto-download

5. **Verification** (30min) — ✅ done
   - pytest 3 passed; 端到端 MPS 18.87fps CPU 11.6fps, 80帧输出 1.4MB, ID 稳定, 抽帧验证; 修复 reviewer P1/P2 后复验通过

## Verification Plan
- Smallest first: 单帧 track 转换单元测试 → 合成视频 pipeline smoke → 真实 MP4 全量
- 证据: outputs/result.mp4 (80f), /tmp/thumb.jpg, 日志 device/model/conf, pytest
- Gate: not_required (local engineering)

## Deliverable Checklist (for handoff)
- [x] 修改文件清单
- [x] 运行命令
- [x] 测试结果
- [x] 输出视频位置
- [x] 下一步计划 (M2)
