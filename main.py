#!/usr/bin/env python3
"""Entry point for Real-Time Video Analytics M1."""

import argparse
from pathlib import Path
import sys

# ensure src on path when run as script
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config import load_config
from src.utils.device import resolve_device
from src.pipeline import VideoPipeline


def parse_args():
    p = argparse.ArgumentParser(description="Real-Time Video Analytics — M1/M2")
    p.add_argument("--config", type=str, default="config/config.yaml", help="path to config yaml")
    p.add_argument("--source", type=str, default=None, help="override video source path")
    p.add_argument("--output", type=str, default=None, help="override output path")
    p.add_argument("--device", type=str, default=None, help="override device (auto/cpu/mps/cuda/0)")
    p.add_argument("--conf", type=float, default=None, help="override confidence threshold")
    p.add_argument("--no-line", action="store_true", help="disable line crossing for this run")
    return p.parse_args()


def main():
    args = parse_args()
    cfg = load_config(args.config)

    # apply overrides
    overrides = {}
    if args.source:
        overrides["source"] = args.source
    if args.output:
        overrides["output"] = args.output
    if args.device:
        overrides["device"] = args.device
    if args.conf is not None:
        overrides["conf"] = args.conf

    if args.no_line:
        # disable line crossing override
        from dataclasses import replace
        from src.utils.config import LineCrossingConfig
        lc = LineCrossingConfig(enabled=False, p1=(320,0), p2=(320,480), mode="both", classes=None)
        cfg = replace(cfg, line_crossing=lc)
        print("[override] line_crossing disabled via --no-line")

    if overrides:
        # validate overrides before applying (P2-05)
        if "conf" in overrides:
            c = overrides["conf"]
            if not 0 < c <= 1:
                print(f"[error] conf must be in (0,1], got {c}", file=sys.stderr)
                sys.exit(2)
        # reconstruct config with overrides (dataclass is frozen)
        from dataclasses import replace
        # need to resolve device if overridden separately? keep as-is, pipeline will resolve
        cfg = replace(cfg, **overrides)
        print(f"[override] {overrides}")

    # resolve device for logging (actual resolution inside tracker too)
    print(f"[config] {cfg}")
    print(f"[device] resolved={resolve_device(cfg.device)} (raw={cfg.device})")

    pipeline = VideoPipeline(cfg)
    stats = pipeline.run()

    print("\n=== Summary ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    # line crossing summary highlight
    if stats.get("line_enabled"):
        lc = stats.get("line_crossing", {})
        print(f"\n[line] total={lc.get('total')} a_to_b={lc.get('a_to_b')} b_to_a={lc.get('b_to_a')} by_class={lc.get('by_class')}")
        if lc.get("total", 0) == 0:
            print("[line] note: no crossings detected — try line_demo.mp4 or adjust line position")

    if not Path(stats["output"]).exists() or stats["output_bytes"] == 0:
        print("[error] output video missing or empty!", file=sys.stderr)
        sys.exit(1)
    if stats.get("total_frames", 0) == 0:
        print("[error] no frames processed — check source video!", file=sys.stderr)
        sys.exit(1)
    print(f"\n[ok] output video: {stats['output']}")


if __name__ == "__main__":
    main()
