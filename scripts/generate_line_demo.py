#!/usr/bin/env python3
"""Generate line_demo video with horizontal sliding bus to ensure line crossing."""

import cv2
from pathlib import Path
import numpy as np

src_img = Path("/opt/miniconda3/envs/yolo-portfolio/lib/python3.11/site-packages/ultralytics/assets/bus.jpg")
out = Path("assets/line_demo.mp4")
out.parent.mkdir(parents=True, exist_ok=True)

img = cv2.imread(str(src_img))
assert img is not None, f"not found {src_img}"

# target canvas 640x480, letterbox resized bus
target_w, target_h = 640, 480
h, w = img.shape[:2]
scale = min(target_w / w, target_h / h)  # ~0.44
nw, nh = int(w*scale), int(h*scale)
resized = cv2.resize(img, (nw, nh))
pad_top = (target_h - nh)//2
pad_left = (target_w - nw)//2
base = np.full((target_h, target_w, 3), 114, dtype=np.uint8)
base[pad_top:pad_top+nh, pad_left:pad_left+nw] = resized

print(f"base {w}x{h} -> {nw}x{nh}, canvas {target_w}x{target_h}")

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
fps = 20
writer = cv2.VideoWriter(str(out), fourcc, fps, (target_w, target_h))

num_frames = 80
# slide from left off-screen to right off-screen: define offset range
# start offset -300, end +300, linear move across center line x=320
# At offset 0, bus center around 320. Let's compute: bus span approx [pad_left, pad_left+nw] = ~[140,500] at offset 0
# So we slide whole base? Instead slide the bus region within base by translating the patched area.
# Simpler: translate the whole base image horizontally.

for i in range(num_frames):
    # linear slide: dx from -250 to +250
    # ensure at least one crossing per object: initial left, final right
    dx = int(-250 + (500 * i / (num_frames-1)))  # -250 -> +250
    M = np.float32([[1,0,dx],[0,1,0]])
    shifted = cv2.warpAffine(base, M, (target_w, target_h), borderValue=(114,114,114))
    # annotate frame number and expected line
    cv2.putText(shifted, f"frame {i} dx={dx}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
    # draw expected counting line for reference (will also be drawn by pipeline, but add faint)
    cv2.line(shifted, (320,0), (320,480), (200,200,200), 1, cv2.LINE_AA)
    writer.write(shifted)

writer.release()
print(f"wrote {out.resolve()} exists={out.exists()} size={out.stat().st_size}")
# validate frames
cap = cv2.VideoCapture(str(out))
frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"frames={frames} fps={cap.get(cv2.CAP_PROP_FPS)}")
cap.release()
