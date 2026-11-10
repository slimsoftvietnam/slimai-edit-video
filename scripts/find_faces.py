"""Locate the people in a static shot, fill project.json (speakers, matte crop) and draw an overlay to verify.

python find_faces.py PROJECT [--names M,W] [--samples 6] [--cut 0.3]

Runs person matting on a few low-res frames from the source; each person blob gives a head top, a face
centre and a head box. Names go left to right. Open faces_check.jpg and correct project.json by hand if a
marker is off: everything that sits "behind the head" uses these numbers.

A source joined from several recordings often has the camera nudged between them. Hard cuts are found first,
and each take gets its own positions in project.json "takes" (top-level "speakers" = the longest take).
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
ap.add_argument("--cut", type=float, default=0.15, help="scene-change score worth checking for a new take")
args = ap.parse_args()

cfg_path = os.path.join(args.project, "project.json")
cfg = json.load(open(cfg_path, encoding="utf-8"))
SW, SH = cfg["src_w"], cfg["src_h"]
LW = 640
LH = int(round(SH * LW / SW / 2) * 2)
scale = SW / LW
dur = cfg["duration"]
torch.set_num_threads(8)
torch._C._jit_set_profiling_executor(False)
model = torch.jit.load(os.path.join(SKILL_DIR, "assets", "rvm", "rvm_mobilenetv3_fp32.torchscript")).eval()


def gray_at(t):
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0, t):.3f}", "-i", cfg["source"], "-frames:v", "1", "-vf",
                        f"scale={LW}:{LH},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    return np.frombuffer(b, np.uint8).reshape(LH, LW).astype(np.float32) if len(b) == LW * LH else None


def hard_cuts():
    """times where a new recording starts. Two takes of the same set-up differ only slightly, so the scene score
    of the join is low (0.25 here); candidates are confirmed by a moved background instead, which people moving
    in a static shot never produce."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", cfg["source"], "-an", "-vf",
                        f"scale=320:-2,select='gt(scene,{args.cut})',showinfo", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    times = [float(x.split("pts_time:")[1].split()[0]) for x in r.splitlines() if "pts_time:" in x]
    out = []
    for t in times:
        if t <= 3 or dur - t <= 3 or (out and t - out[-1] <= 3):    # a flash or a fade, not a new camera position
            continue
        a, b = gray_at(t - 0.15), gray_at(t + 0.1)
        if a is None or b is None:
            continue
        top = slice(0, int(LH * 0.45))                                # background above the heads
        (dx, dy), resp = cv2.phaseCorrelate(a[top], b[top])
        moved = np.hypot(dx, dy) * scale
        if moved >= 3 or resp < 0.1:
            out.append(t)
            print(f"new take at {t:.2f} s: background moved {moved:.0f} px")
    return out


def locate(times):
    """people seen in frames at `times` -> (rows of (x, head_top, head_width) per sample, matte max, last frame)."""
    heads, last_rgb, acc = [], None, None
    for t in times:
        b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", cfg["source"], "-frames:v", "10", "-vf",
                            f"scale={LW}:{LH}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        fr = np.frombuffer(b, np.uint8)
        n = len(fr) // (LW * LH * 3)
        if n == 0:
            continue
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
            row.append(((x0 + x1) / 2 * scale, top * scale, (x1 - x0 + 1) * scale))
        heads.append(row)
    return heads, acc, last_rgb


def speakers_from(heads, names):
    counts = [len(r) for r in heads]
    if not counts or max(counts) == 0:
        return {}
    n_people = max(set(counts), key=counts.count)
    rows = [r for r in heads if len(r) == n_people]
    med = np.median(np.array(rows), axis=0)
    names = names or [chr(ord("A") + i) for i in range(n_people)]
    if len(names) != n_people:
        print(f"warning: found {n_people} people but got {len(names)} names; check faces_check.jpg")
    out = {}
    for nm, (x, top, hw) in zip(names, med):
        out[nm] = {"face": [round(float(x)), round(float(top + 0.52 * hw))], "head_top": round(float(top)),
                   "box": [round(float(x - hw * 0.75)), round(float(top - 0.03 * hw)), round(float(x + hw * 0.75)),
                           round(float(top + 1.35 * hw))]}
    return out


names = [n for n in args.names.split(",") if n]
bounds = [0.0] + hard_cuts() + [dur]
takes, acc_all, panels = [], None, []
for a, b in zip(bounds[:-1], bounds[1:]):
    k = max(3, round(args.samples * (b - a) / dur))
    times = [a + (b - a) * (j + 0.5) / k for j in range(k)]
    heads, acc, last_rgb = locate(times)
    sp = speakers_from(heads, names)
    if acc is not None:
        acc_all = acc if acc_all is None else np.maximum(acc_all, acc)
    takes.append({"start": round(a, 3), "end": round(b, 3), "speakers": sp})
    panels.append((a, b, sp, last_rgb))

takes = [t for t in takes if t["speakers"]]
if not takes:
    sys.exit("no person found in the sampled frames: fill speakers and matte in project.json by hand")
longest = max(takes, key=lambda t: t["end"] - t["start"])
cfg["speakers"] = longest["speakers"]
if len(takes) > 1:
    cfg["takes"] = takes
    print(f"{len(takes)} takes (camera position changes at " + ", ".join(f"{t['start']:.2f} s" for t in takes[1:]) + ")")
else:
    cfg.pop("takes", None)
ys, xs = np.nonzero(acc_all > 64)
if len(xs):
    pad = int(0.04 * LW)
    x0, x1 = max(0, xs.min() - pad), min(LW, xs.max() + pad)
    y0 = max(0, ys.min() - pad)
    base = 2.0 * max(1.0, min(SW, SH) / 1080.0)
    cx0, cy0 = int(x0 * scale) // 2 * 2, int(y0 * scale) // 2 * 2
    cw, ch = int((x1 - x0) * scale) // 8 * 8, int((LH - y0) * scale) // 8 * 8
    cfg["matte"] = {"crop": [cx0, cy0, min(cw, SW - cx0), min(ch, SH - cy0)], "scale": base}
json.dump(cfg, open(cfg_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# one panel per take, stacked: the markers must sit on each person's face in every take
k = 2 / scale
tiles = []
for a, b, sp, rgb in panels:
    if rgb is None:
        continue
    vis = cv2.resize(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), (LW * 2, LH * 2))
    for nm, s in sp.items():
        fx, fy = s["face"]
        cv2.circle(vis, (int(fx * k), int(fy * k)), 8, (0, 255, 255), 2)
        cv2.line(vis, (int(fx * k) - 40, int(s["head_top"] * k)), (int(fx * k) + 40, int(s["head_top"] * k)), (0, 255, 0), 2)
        bx = [int(v * k) for v in s["box"]]
        cv2.rectangle(vis, (bx[0], bx[1]), (bx[2], bx[3]), (255, 160, 0), 1)
        cv2.putText(vis, nm, (int(fx * k) - 12, int(s["head_top"] * k) - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
    if len(panels) > 1:
        cv2.putText(vis, f"take {a:.1f}-{b:.1f} s", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 255), 2)
    tiles.append(vis)
imwrite(os.path.join(args.project, "faces_check.jpg"), np.vstack(tiles))
print(json.dumps({"speakers": cfg["speakers"], "takes": len(takes), "matte": cfg.get("matte")}, indent=1))
print("verify the markers in faces_check.jpg")
