"""VideoPipeline — orchestrates source → vision → writer + analytics."""

import time
from pathlib import Path
import cv2

from .source.video_source import VideoSource
from .vision.detector import YOLOTracker
from .vision.visualizer import draw_tracks, draw_line_and_counts
from .utils.config import PipelineConfig
from .analytics.line_crossing import LineCrossingCounter


class VideoPipeline:
    def __init__(self, config: PipelineConfig):
        self.config = config

    def run(self) -> dict:
        src = self.config.source
        out = Path(self.config.output)
        out.parent.mkdir(parents=True, exist_ok=True)

        # P1-01: guard against overwriting the source file
        try:
            if Path(src).resolve() == out.resolve():
                raise ValueError(f"source and output must be different files: {src}")
        except FileNotFoundError:
            # output may not exist yet — compare absolute paths
            if Path(src).absolute() == out.absolute():
                raise ValueError(f"source and output must be different files: {src}")

        print(f"[pipeline] model={self.config.model} device={self.config.device} conf={self.config.conf} iou={self.config.iou}")
        print(f"[pipeline] source={src}")
        print(f"[pipeline] output={out.resolve()}")
        if self.config.line_crossing.enabled:
            lc = self.config.line_crossing
            print(f"[line] enabled p1={lc.p1} p2={lc.p2} mode={lc.mode} classes={lc.classes}")

        source = None
        tracker = None
        writer = None
        counter = None
        total_frames = 0
        total_tracks = 0
        max_tracks_in_frame = 0
        unique_ids = set()
        t0 = time.time()

        try:
            source = VideoSource(src)
            print(f"[source] {source.info()}")

            tracker = YOLOTracker(
                model_path=self.config.model,
                device=self.config.device,
                conf=self.config.conf,
                iou=self.config.iou,
                tracker=self.config.tracker,
                imgsz=self.config.imgsz,
                classes=self.config.classes,
            )
            print(f"[vision] {tracker}")

            # init line crossing counter after source size known (for normalized handling)
            if self.config.line_crossing.enabled:
                lc = self.config.line_crossing
                counter = LineCrossingCounter(
                    p1=lc.p1, p2=lc.p2, mode=lc.mode, classes=lc.classes,
                    frame_width=source.width, frame_height=source.height
                )
                print(f"[line] counter {counter}")

            # writer setup — use source fps/size, fourcc from config
            fourcc_str = self.config.fourcc
            # ensure 4 chars
            if len(fourcc_str) != 4:
                fourcc_str = "mp4v"
            fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
            writer = cv2.VideoWriter(str(out), fourcc, source.fps, (source.width, source.height))
            if not writer.isOpened():
                # fallback to mp4v
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(str(out), fourcc, source.fps, (source.width, source.height))
                if not writer.isOpened():
                    raise RuntimeError(f"failed to open VideoWriter: {out}")

            for frame in source:
                total_frames += 1
                tracks = tracker.track(frame)
                total_tracks += len(tracks)
                max_tracks_in_frame = max(max_tracks_in_frame, len(tracks))
                for tr in tracks:
                    unique_ids.add(tr.track_id)

                # analytics: line crossing
                if counter is not None:
                    events = counter.update(tracks, total_frames)
                    for ev in events:
                        print(f"[cross] frame={ev.frame_idx} id={ev.track_id} {ev.class_name} dir={ev.direction} center={ev.center}")

                vis = draw_tracks(frame, tracks)
                if counter is not None:
                    vis = draw_line_and_counts(vis, counter.p1, counter.p2, counter.get_counts(), counter.mode)
                writer.write(vis)

                if total_frames % 30 == 0 or total_frames == 1:
                    lc_str = ""
                    if counter is not None:
                        lc_str = f" | line_total={counter.get_counts()['total']}"
                    print(f"[frame {total_frames}] tracks={len(tracks)} ids={[t.track_id for t in tracks]}{lc_str}")
        finally:
            if writer is not None:
                writer.release()
            if source is not None:
                source.release()
            if tracker is not None:
                tracker.close()

        elapsed = time.time() - t0
        fps_proc = total_frames / elapsed if elapsed > 0 else 0

        line_stats = counter.get_counts() if counter is not None else {"total": 0, "a_to_b": 0, "b_to_a": 0, "by_class": {}}
        line_events = [e.__dict__ for e in counter.get_events()] if counter is not None else []

        stats = {
            "total_frames": total_frames,
            "total_detections": total_tracks,
            "max_tracks_in_frame": max_tracks_in_frame,
            "unique_ids": sorted(list(unique_ids)),
            "unique_count": len(unique_ids),
            "elapsed_sec": round(elapsed, 2),
            "proc_fps": round(fps_proc, 2),
            "output": str(out.resolve()),
            "output_exists": out.exists(),
            "output_bytes": out.stat().st_size if out.exists() else 0,
            "line_crossing": line_stats,
            "line_events": line_events,
            "line_enabled": counter is not None,
        }
        print(f"[done] {stats}")
        return stats
