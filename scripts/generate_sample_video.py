#!/usr/bin/env python3
"""Generate assets/sample.mp4 from ultralytics bus.jpg with slight motion to test tracking."""

import cv2
from pathlib import Path

try:
    from ultralytics.utils import ASSETS as ULTRALYTICS_ASSETS
    src_img = Path(ULTRALYTICS_ASSETS) / "bus.jpg"
except Exception:
    import ultralytics
    src_img = Path(ultralytics.__file__).parent / "assets" / "bus.jpg"
out = Path("assets/sample.mp4")
out.parent.mkdir(parents=True, exist_ok=True)

img = cv2.imread(str(src_img))
if img is None:
    raise FileNotFoundError(str(src_img))

# resize to 640x480ish to keep video manageable
target_w, target_h = 640, 480
# keep aspect, letterbox
h, w = img.shape[:2]
scale = min(target_w / w, target_h / h)
nw, nh = int(w*scale), int(h*scale)
resized = cv2.resize(img, (nw, nh))
# pad to target
canvas = cv2.copyMakeBorder(resized, (target_h-nh)//2, target_h-nh - (target_h-nh)//2,
                            (target_w-nw)//2, target_w-nw - (target_w-nw)//2,
                            cv2.BORDER_CONSTANT, value=(114,114,114))

print(f"input {w}x{h} -> {nw}x{nh} padded {target_w}x{target_h}")

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
fps = 20
writer = cv2.VideoWriter(str(out), fourcc, fps, (target_w, target_h))
# create 4 seconds (80 frames) with gentle pan + zoom
import numpy as np
for i in range(80):
    # slight translation: shift canvas by i%10
    dx = int(5 * np.sin(i * 0.2))
    dy = int(3 * np.cos(i * 0.2))
    M = np.float32([[1,0,dx],[0,1,dy]])
    shifted = cv2.warpAffine(canvas, M, (target_w, target_h), borderValue=(114,114,114))
    # add frame number overlay to see motion
    cv2.putText(shifted, f"frame {i}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
    writer.write(shifted)

writer.release()
print(f"wrote {out.resolve()} exists={out.exists()} size={out.stat().st_size}")

# also try download a real pedestrian sample if network allows
try:
    import urllib.request
    try:
        from ultralytics.utils import ASSETS as UA2
        zidane = Path(UA2) / "zidane.jpg"
    except Exception:
        import ultralytics
        zidane = Path(ultralytics.__file__).parent / "assets" / "zidane.jpg"
    if zidane.exists():
        print(f"zidane exists {zidane}")
except Exception as e:
    print(e)
