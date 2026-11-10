"""Show the colour choices on a frame of the user's own video, before asking which one they want.

python look_preview.py PROJECT OUT.jpg [--t SECONDS]

Writes a 2x2 sheet of one frame: the camera's own colour (iphone, the default) and the three film looks,
labelled in Vietnamese. Film grain, halation and vignette are added at render time, so they are not shown.
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("project")
ap.add_argument("out")
ap.add_argument("--t", type=float, default=None, help="source second to show (default: 40 % into the video)")
args = ap.parse_args()

proj = os.path.abspath(args.project)
cfg = json.load(open(os.path.join(proj, "project.json"), encoding="utf-8"))
portrait = cfg["src_h"] > cfg["src_w"]
os.environ["EDIT_PROJECT"] = proj
os.environ["EDIT_FMT"] = "tiktok" if portrait else "youtube"
os.environ["EDIT_SS"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine as E  # noqa: E402
import film_look as F  # noqa: E402
from imgio import imwrite  # noqa: E402

# the default first, then at most three alternatives
CHOICES = [("iphone", "1 · Màu gốc iPhone (mặc định)"), ("cine_warm", "2 · Màu phim ấm"),
           ("teal_orange", "3 · Màu phim tương phản"), ("neutral", "4 · Màu trung tính")]

TW, TH = E.W // 2, E.H // 2            # each tile is a quarter of the layout frame
t = args.t if args.t is not None else cfg["duration"] * 0.4
transfer = cfg["transfer"]
matrix = "2020_ncl" if transfer in ("hlg", "pq") else "709"
rin = "full" if cfg.get("color_range") == "pc" else "limited"
# the camera signal in float, scaled, exactly as build_master.py feeds it to the LUT
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", cfg["source"], "-frames:v", "1", "-vf",
                      f"zscale=w={TW}:h={TH}:filter=lanczos:min={matrix}:rin={rin}:r=full,format=gbrpf32le",
                      "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
planes = np.frombuffer(raw, np.float32).reshape(3, TH, TW)          # planar G, B, R
signal = np.stack([planes[2], planes[0], planes[1]], -1)

sheet = np.zeros((E.H, E.W, 3), np.uint8)
for k, (look, _label) in enumerate(CHOICES):
    rgb = F.apply_look(signal.reshape(-1, 3), look, transfer).reshape(TH, TW, 3)
    tile = (np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1]
    y0, x0 = (k // 2) * TH, (k % 2) * TW
    sheet[y0:y0 + TH, x0:x0 + TW] = tile

L = E.Layer()
L.begin()
f = E.font("bold", 30 if not portrait else 28)
for k, (_look, label) in enumerate(CHOICES):
    x0, y0 = (k % 2) * TW + 20, (k // 2) * TH + 20
    w = E.text_width(label, f) + 40
    L.c.drawRRect(E.rrect(x0, y0, x0 + w, y0 + 56, 28), E.fill(E.INK, 200))
    E.draw_text(L, label, f, x0 + 20, y0 + 39, rgb=E.AMBER if k == 0 else E.WHITE, align="left")
L.c.drawLine(TW, 0, TW, E.H, E.stroke((0, 0, 0), 255, width=4))
L.c.drawLine(0, TH, E.W, TH, E.stroke((0, 0, 0), 255, width=4))
L.mark(0, 0, E.W, E.H)
E.over_premul(sheet, L.arr)
imwrite(os.path.abspath(args.out), sheet, [1, 92])     # cv2.IMWRITE_JPEG_QUALITY = 1
print("wrote", os.path.abspath(args.out), f"(frame at {t:.1f} s)")
