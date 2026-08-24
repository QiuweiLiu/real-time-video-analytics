"""VideoPipeline — orchestrates source → vision → writer + analytics + events."""

import time
import uuid
from pathlib import Path
import cv2

from .source.video_source import VideoSource
from .vision.detector import YOLOTracker
from .vision.visualizer import draw_tracks, draw_line_and_counts, draw_roi, highlight_dwell_tracks
from .utils.config import PipelineConfig
from .analytics.line_crossing import LineCrossingCounter
from .analytics.roi import ROIAnalytics
from .events.logger import EventLogger
from .events.snapshot import save_snapshot


class VideoPipeline:
    def __init__(self, config: PipelineConfig):
        self.config = config

    def run(self) -> dict:
        src = self.config.source
        out = Path(self.config.output)
        out.parent.mkdir(parents=True, exist_ok=True)

        try:
            if Path(src).resolve() == out.resolve():
                raise ValueError(f"source and output must be different files: {src}")
        except FileNotFoundError:
            if Path(src).absolute() == out.absolute():
                raise ValueError(f"source and output must be different files: {src}")

        print(f"[pipeline] model={self.config.model} device={self.config.device} conf={self.config.conf} iou={self.config.iou}")
        print(f"[pipeline] source={src}")
        print(f"[pipeline] output={out.resolve()}")
        if self.config.line_crossing.enabled:
            lc = self.config.line_crossing
            print(f"[line] enabled p1={lc.p1} p2={lc.p2} mode={lc.mode} classes={lc.classes}")
        if self.config.roi.enabled:
            rc = self.config.roi
            print(f"[roi] enabled polygon={rc.polygon} dwell={rc.dwell_sec}s classes={rc.classes}")
        if self.config.events.enabled:
            ec = self.config.events
            print(f"[events] enabled json={ec.json_path} snapshots={ec.snapshot_dir} expand={ec.snapshot_expand} max={ec.snapshot_max}")

        source = None
        tracker = None
        writer = None
        counter = None
        roi_analytics = None
        logger = None
        total_frames = 0
        total_tracks = 0
        max_tracks_in_frame = 0
        unique_ids = set()
        snapshot_paths = []
        t0 = time.time()

        try:
            from .source.video_source import _is_stream
            max_frames = None
            reconnect_attempts = 0
            reconnect_delay = 0.5
            if _is_stream(str(src)):
                rtsp = getattr(self.config, "rtsp", None)
                max_frames = getattr(rtsp, "max_frames", 300) if rtsp else 300
                reconnect_attempts = getattr(rtsp, "reconnect_attempts", 3) if rtsp else 3
                reconnect_delay = getattr(rtsp, "reconnect_delay", 0.5) if rtsp else 0.5
            source = VideoSource(src, max_frames=max_frames, reconnect_attempts=reconnect_attempts, reconnect_delay=reconnect_delay)
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

            if self.config.line_crossing.enabled:
                lc = self.config.line_crossing
                counter = LineCrossingCounter(
                    p1=lc.p1, p2=lc.p2, mode=lc.mode, classes=lc.classes,
                    frame_width=source.width, frame_height=source.height
                )
                print(f"[line] counter {counter}")

            if self.config.roi.enabled:
                rc = self.config.roi
                roi_analytics = ROIAnalytics(
                    polygon=list(rc.polygon),
                    dwell_sec=rc.dwell_sec,
                    fps=source.fps,
                    classes=rc.classes,
                    frame_width=source.width,
                    frame_height=source.height,
                )
                print(f"[roi] analytics {roi_analytics}")

            if self.config.events.enabled:
                ec = self.config.events
                logger = EventLogger(ec.json_path)
                # ensure snapshot dir exists (even if no snapshots)
                Path(ec.snapshot_dir).mkdir(parents=True, exist_ok=True)
                # clean old snapshots for fresh run? keep but truncate logger already
                print(f"[events] logger {logger.path} snapshot_dir {ec.snapshot_dir}")

            fourcc_str = self.config.fourcc
            if len(fourcc_str) != 4:
                fourcc_str = "mp4v"
            fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
            writer = cv2.VideoWriter(str(out), fourcc, source.fps, (source.width, source.height))
            if not writer.isOpened():
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

                # map track_id -> track for snapshot lookup
                track_by_id = {t.track_id: t for t in tracks}

                if counter is not None:
                    events = counter.update(tracks, total_frames)
                    for ev in events:
                        print(f"[cross] frame={ev.frame_idx} id={ev.track_id} {ev.class_name} dir={ev.direction} center={ev.center}")
                        if logger is not None:
                            tr = track_by_id.get(ev.track_id)
                            bbox = tr.bbox if tr else (ev.center[0]-10, ev.center[1]-10, ev.center[0]+10, ev.center[1]+10)
                            event_id = f"line_{ev.track_id}_{ev.frame_idx}_{uuid.uuid4().hex[:4]}"
                            # snapshot with expand
                            snap_path = None
                            if len(snapshot_paths) < self.config.events.snapshot_max:
                                snap_path = save_snapshot(frame, bbox, self.config.events.snapshot_dir, event_id, self.config.events.snapshot_expand)
                                if snap_path:
                                    snapshot_paths.append(str(snap_path))
                            log_dict = {
                                "event_id": event_id,
                                "type": "line_cross",
                                "timestamp": round(ev.frame_idx / source.fps, 3),
                                "frame_idx": ev.frame_idx,
                                "track_id": ev.track_id,
                                "class_id": ev.class_id,
                                "class_name": ev.class_name,
                                "center": [ev.center[0], ev.center[1]],
                                "bbox": [bbox[0], bbox[1], bbox[2], bbox[3]],
                                "direction": ev.direction,
                                "p1": [ev.p1[0], ev.p1[1]],
                                "p2": [ev.p2[0], ev.p2[1]],
                                "snapshot": str(snap_path) if snap_path else None,
                            }
                            logger.log(log_dict)

                roi_info = None
                if roi_analytics is not None:
                    roi_info = roi_analytics.update(tracks, total_frames)
                    for ev in roi_info["dwell_events"]:
                        print(f"[dwell] frame={ev.frame_idx} id={ev.track_id} {ev.class_name} enter={ev.enter_frame} dur={ev.duration_sec}s center={ev.center}")
                        if logger is not None:
                            tr = track_by_id.get(ev.track_id)
                            bbox = tr.bbox if tr else (ev.center[0]-10, ev.center[1]-10, ev.center[0]+10, ev.center[1]+10)
                            event_id = f"dwell_{ev.track_id}_{ev.frame_idx}_{uuid.uuid4().hex[:4]}"
                            snap_path = None
                            if len(snapshot_paths) < self.config.events.snapshot_max:
                                snap_path = save_snapshot(frame, bbox, self.config.events.snapshot_dir, event_id, self.config.events.snapshot_expand)
                                if snap_path:
                                    snapshot_paths.append(str(snap_path))
                            log_dict = {
                                "event_id": event_id,
                                "type": "dwell",
                                "timestamp": round(ev.frame_idx / source.fps, 3),
                                "frame_idx": ev.frame_idx,
                                "track_id": ev.track_id,
                                "class_id": ev.class_id,
                                "class_name": ev.class_name,
                                "center": [ev.center[0], ev.center[1]],
                                "bbox": [bbox[0], bbox[1], bbox[2], bbox[3]],
                                "enter_frame": ev.enter_frame,
                                "duration_sec": ev.duration_sec,
                                "polygon": [list(p) for p in ev.polygon],
                                "snapshot": str(snap_path) if snap_path else None,
                            }
                            logger.log(log_dict)

                vis = draw_tracks(frame, tracks)
                if counter is not None:
                    vis = draw_line_and_counts(vis, counter.p1, counter.p2, counter.get_counts(), counter.mode)
                if roi_analytics is not None:
                    occ = roi_info["occupancy"] if roi_info else 0
                    max_occ = roi_analytics._max_occupancy
                    dwell_total = roi_info["total_dwell"] if roi_info else len(roi_analytics.get_events())
                    vis = draw_roi(vis, roi_analytics.get_polygon(), occ, max_occ, dwell_total, roi_analytics.dwell_sec)
                    vis = highlight_dwell_tracks(vis, tracks, roi_analytics)
                writer.write(vis)

                if total_frames % 30 == 0 or total_frames == 1:
                    parts = []
                    if counter is not None:
                        parts.append(f"line_total={counter.get_counts()['total']}")
                    if roi_analytics is not None and roi_info is not None:
                        parts.append(f"roi_occ={roi_info['occupancy']} dwell={roi_info['total_dwell']}")
                    suffix = " | ".join(parts) if parts else ""
                    print(f"[frame {total_frames}] tracks={len(tracks)} ids={[t.track_id for t in tracks]}" + (f" | {suffix}" if suffix else ""))
        finally:
            if writer is not None:
                writer.release()
            if source is not None:
                source.release()
            if tracker is not None:
                tracker.close()
            if logger is not None:
                logger.close()

        elapsed = time.time() - t0
        fps_proc = total_frames / elapsed if elapsed > 0 else 0

        line_stats = counter.get_counts() if counter is not None else {"total": 0, "a_to_b": 0, "b_to_a": 0, "by_class": {}}
        line_events = [e.__dict__ for e in counter.get_events()] if counter is not None else []

        if roi_analytics is not None:
            roi_events = [e.__dict__ for e in roi_analytics.get_events()]
            roi_stats = {
                "occupancy_current": roi_info["occupancy"] if 'roi_info' in locals() and roi_info else 0,
                "max_occupancy": roi_analytics._max_occupancy,
                "total_dwell": len(roi_analytics.get_events()),
                "by_class": roi_info["by_class"] if 'roi_info' in locals() and roi_info else {},
                "events": roi_events,
            }
        else:
            roi_stats = {"occupancy_current": 0, "max_occupancy": 0, "total_dwell": 0, "by_class": {}, "events": []}

        events_enabled = logger is not None
        events_count = logger.count() if logger else 0
        events_json = str(Path(self.config.events.json_path).resolve()) if events_enabled else None

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
            "roi": roi_stats,
            "roi_enabled": roi_analytics is not None,
            "events_enabled": events_enabled,
            "events_count": events_count,
            "events_json": events_json,
            "snapshots": snapshot_paths,
            "snapshots_count": len(snapshot_paths),
        }
        print(f"[done] {stats}")
        return stats
