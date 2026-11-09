"""Locate the people in a static shot, fill project.json (speakers, matte crop) and draw an overlay to verify.

python find_faces.py PROJECT [--names M,W] [--samples 6]

Runs person matting on a few low-res frames from the source; each person blob gives a head top, a face
centre and a head box. Names go left to right. Open faces_check.jpg and correct project.json by hand if a
marker is off: everything that sits "behind the head" uses these numbers.
"""
import argparse
import json
import os
import subprocess
import sys

import cv2
import numpy as np
import torch

from imgio import imwrite

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument("project")
ap.add_argument("--names", default="")
ap.add_argument("--samples", type=int, default=6)
args = ap.parse_args()

cfg_path = os.path.join(args.project, "project.json")
cfg = json.load(open(cfg_path, encoding="utf-8"))
SW, SH = cfg["src_w"], cfg["src_h"]
LW = 640
LH = int(round(SH * LW / SW / 2) * 2)
scale = SW / LW
torch.set_num_threads(8)
torch._C._jit_set_profiling_executor(False)
model = torch.jit.load(os.path.join(SKILL_DIR, "assets", "rvm", "rvm_mobilenetv3_fp32.torchscript")).eval()

dur = cfg["duration"]
heads, last_rgb, acc = [], None, None
for k in range(args.samples):
    t = dur * (k + 0.5) / args.samples
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", cfg["source"], "-frames:v", "10", "-vf",
                        f"scale={LW}:{LH}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    fr = np.frombuffer(b, np.uint8)
    n = len(fr) // (LW * LH * 3)
    rec = [None] * 4
    pha = None
    with torch.no_grad():
        for i in range(n):
            img = fr[i * LW * LH * 3:(i + 1) * LW * LH * 3].reshape(LH, LW, 3)
            src = torch.from_numpy(img.copy()).permute(2, 0, 1).float().div_(255).unsqueeze_(0)
            fgr, pha, *rec = model(src, *rec, 1.0)
    m = (pha[0, 0].numpy() * 255).astype(np.uint8)
    last_rgb = img
    acc = m.astype(np.float32) if acc is None else np.maximum(acc, m)
    num, lab, stats, _ = cv2.connectedComponentsWithStats((m > 128).astype(np.uint8))
    blobs = [i for i in range(1, num) if stats[i, cv2.CC_STAT_AREA] > 0.012 * LW * LH]
    blobs.sort(key=lambda i: stats[i, cv2.CC_STAT_LEFT])
    row = []
    for i in blobs:
        ys, xs = np.nonzero(lab == i)
        top = ys.min()
        band = ys < top + 0.09 * LH          # the head, roughly
        x0, x1 = xs[band].min(), xs[band].max()
        hw = x1 - x0 + 1
        row.append(((x0 + x1) / 2 * scale, top * scale, hw * scale))
    heads.append(row)

counts = [len(r) for r in heads]
np_people = max(set(counts), key=counts.count)
rows = [r for r in heads if len(r) == np_people]
med = np.median(np.array(rows), axis=0) if np_people else np.zeros((0, 3))
if not np_people:
    sys.exit("no person found in the sampled frames: fill speakers and matte in project.json by hand")
names = [n for n in args.names.split(",") if n] or [chr(ord("A") + i) for i in range(np_people)]
if len(names) != np_people:
    print(f"warning: found {np_people} people but got {len(names)} names; check faces_check.jpg")
speakers = {}
for nm, (x, top, hw) in zip(names, med):
    speakers[nm] = {"face": [round(float(x)), round(float(top + 0.52 * hw))], "head_top": round(float(top)),
                    "box": [round(float(x - hw * 0.75)), round(float(top - 0.03 * hw)), round(float(x + hw * 0.75)),
                            round(float(top + 1.35 * hw))]}
cfg["speakers"] = speakers
ys, xs = np.nonzero(acc > 64)
if len(xs):
    pad = int(0.04 * LW)
    x0, x1 = max(0, xs.min() - pad), min(LW, xs.max() + pad)
    y0, y1 = max(0, ys.min() - pad), LH
    base = 2.0 * max(1.0, min(SW, SH) / 1080.0)
    cx0, cy0 = int(x0 * scale) // 2 * 2, int(y0 * scale) // 2 * 2
    cw, ch = int((x1 - x0) * scale) // 8 * 8, int((y1 - y0) * scale) // 8 * 8
    cfg["matte"] = {"crop": [cx0, cy0, min(cw, SW - cx0), min(ch, SH - cy0)], "scale": base}
json.dump(cfg, open(cfg_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

vis = cv2.cvtColor(last_rgb, cv2.COLOR_RGB2BGR)
vis = cv2.resize(vis, (LW * 2, LH * 2))
k = 2 / scale
for nm, s in speakers.items():
    fx, fy = s["face"]
    cv2.circle(vis, (int(fx * k), int(fy * k)), 8, (0, 255, 255), 2)
    cv2.line(vis, (int(fx * k) - 40, int(s["head_top"] * k)), (int(fx * k) + 40, int(s["head_top"] * k)), (0, 255, 0), 2)
    bx = [int(v * k) for v in s["box"]]
    cv2.rectangle(vis, (bx[0], bx[1]), (bx[2], bx[3]), (255, 160, 0), 1)
    cv2.putText(vis, nm, (int(fx * k) - 12, int(s["head_top"] * k) - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
imwrite(os.path.join(args.project, "faces_check.jpg"), vis)
print(json.dumps({"speakers": speakers, "matte": cfg.get("matte")}, indent=1))
print("verify the markers in faces_check.jpg")
