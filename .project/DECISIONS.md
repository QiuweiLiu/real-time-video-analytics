# DECISIONS

## 2026-08-21 — M1 architecture: use ultralytics built-in ByteTrack
- Context: 需求要求成熟库不重复实现; 存在独立 BoxMOT/ByteTrack 仓库与 ultralytics 内置 tracker 两种路径
- Decision: 采用 ultralytics YOLO.track + bytetrack.yaml, 不单独引入 boxmot
- Reason: 官方维护、依赖最少、API 已验证 (8.4.121), 避免双重检测/跟踪实现复杂度
- Alternatives rejected: 独立 ByteTrack 实现 (增加依赖与对齐成本)
- Evidence: /opt/miniconda3/envs/yolo-portfolio/lib/python3.11/site-packages/ultralytics/cfg/trackers/bytetrack.yaml, YOLO.track signature

## 2026-08-21 — Python env: reuse yolo-portfolio
- Context: base/ pip3 无 cv2/ultralytics; yolo-portfolio 已满足全部依赖且 mps=True
- Decision: 复用 conda env yolo-portfolio 作为开发/验证环境, requirements.txt 锁定版本
- Reason: 避免重复安装、M1 MPS 已可用、已验证版本一致性

## 2026-08-21 — Review fixes (P1-01, P1-02, P2-03, P2-05)
- Context: reviewer 指出 source==output 覆盖、空输出误报、资源泄漏、CLI conf 绕过校验
- Decision: pipeline 新增同路径 ValueError 保护与前置 try 资源管理; main 新增 total_frames==0 校验与 conf 范围校验; 测试改用 ASSETS 常量
- Reason: 最小完整修复, 不引入复杂架构, 保持 M1 可交付性
- Evidence: pipeline.py:19-26, 31-60; main.py:30-38, 59-62; tests/test_track_conversion.py:6-15
