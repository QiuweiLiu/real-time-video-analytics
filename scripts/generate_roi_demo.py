#!/usr/bin/env python3
"""Generate roi_demo video: bus slides in, stays centered 40 frames, then slides out — to trigger dwell."""

import cv2
from pathlib import Path
import numpy as np

src_img = Path("/opt/miniconda3/envs/yolo-portfolio/lib/python3.11/site-packages/ultralytics/assets/bus.jpg")
out = Path("assets/roi_demo.mp4")
out.parent.mkdir(parents=True, exist_ok=True)

img = cv2.imread(str(src_img))
assert img is not None

target_w, target_h = 640, 480
h, w = img.shape[:2]
scale = min(target_w / w, target_h / h)
nw, nh = int(w*scale), int(h*scale)
resized = cv2.resize(img, (nw, nh))
base = np.full((target_h, target_w, 3), 114, dtype=np.uint8)
pad_top = (target_h - nh)//2
pad_left = (target_w - nw)//2
base[pad_top:pad_top+nh, pad_left:pad_left+nw] = resized

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
fps = 20
writer = cv2.VideoWriter(str(out), fourcc, fps, (target_w, target_h))

num_frames = 80
# phase 0-15: slide in from left -200 -> 0
# phase 16-55: stay centered (40 frames → 2 sec, dwell 1.5s should trigger)
# phase 56-79: slide out 0 -> +200
for i in range(num_frames):
    if i < 16:
        # -200 to 0
        prog = i / 15
        dx = int(-200 + 200*prog)
    elif i < 56:
        dx = 0
    else:
        prog = (i-56)/23
        dx = int(0 + 200*prog)
    M = np.float32([[1,0,dx],[0,1,0]])
    shifted = cv2.warpAffine(base, M, (target_w, target_h), borderValue=(114,114,114))
    cv2.putText(shifted, f"frame {i} dx={dx}", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
    # draw ROI for reference
    cv2.rectangle(shifted, (160,120), (480,360), (0,255,0), 1)
    writer.write(shifted)

writer.release()
print(f"wrote {out.resolve()} size={out.stat().st_size}")
cap = cv2.VideoCapture(str(out))
print(f"frames {cap.get(cv2.CAP_PROP_FRAME_COUNT)} fps {cap.get(cv2.CAP_PROP_FPS)}")
cap.release()
