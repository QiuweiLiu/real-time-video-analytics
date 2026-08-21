"""VideoPipeline — orchestrates source → vision → writer."""

import time
from pathlib import Path
import cv2

from .source.video_source import VideoSource
from .vision.detector import YOLOTracker
from .vision.visualizer import draw_tracks
from .utils.config import PipelineConfig


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

        source = None
        tracker = None
        writer = None
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

                vis = draw_tracks(frame, tracks)
                writer.write(vis)

                if total_frames % 30 == 0 or total_frames == 1:
                    print(f"[frame {total_frames}] tracks={len(tracks)} ids={[t.track_id for t in tracks]}")
        finally:
            if writer is not None:
                writer.release()
            if source is not None:
                source.release()
            if tracker is not None:
                tracker.close()

        elapsed = time.time() - t0
        fps_proc = total_frames / elapsed if elapsed > 0 else 0

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
        }
        print(f"[done] {stats}")
        return stats
