"""Graded master holding only the frames the edit uses (source order) + master_index.json.

python build_master.py PROJECT [--crf 6] [--no-denoise] [--look iphone]

Quality path: 10-bit source -> float RGB -> film LUT (float, tetrahedral) -> near-lossless 4:4:4.
There is no 8-bit step before the grade, which is where the old pipeline lost gradients and detail.
Temporal denoise runs first: a static shot has no real frame-to-frame change, so removing the codec's
"boil" costs no detail and gives the sharpening pass and the platform encoder cleaner input.
"""
import argparse
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import film_look  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("project")
ap.add_argument("--crf", type=float, default=6)
ap.add_argument("--no-denoise", action="store_true")
ap.add_argument("--look", default=None)
args = ap.parse_args()

proj = os.path.abspath(args.project)
cfg_path = os.path.join(proj, "project.json")
cfg = json.load(open(cfg_path, encoding="utf-8"))
tl = json.load(open(os.path.join(proj, "timeline.json"), encoding="utf-8"))
FPS = cfg["fps"]
look = args.look or cfg.get("look", "iphone")
if args.look:
    cfg["look"] = look
    json.dump(cfg, open(cfg_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
transfer = cfg["transfer"]
lut = f"look_{look}_{transfer}.cube"
film_look.write_cube(os.path.join(proj, lut), look, transfer)

ranges = sorted((int(round(c["src_in"] * FPS)), int(round(c["src_in"] * FPS)) + c["frames"]) for c in tl["clips"])
merged = []
for a, b in ranges:
    if merged and a <= merged[-1][1] + 2:
        merged[-1][1] = max(merged[-1][1], b)
    else:
        merged.append([a, b])
index, pos = [], 0
for a, b in merged:
    index.append([a, b - a, pos])
    pos += b - a
sel = "+".join(f"between(n,{a},{b - 1})" for a, b in merged)

matrix = "2020_ncl" if transfer in ("hlg", "pq") else "709"
rin = "full" if cfg.get("color_range") == "pc" else "limited"
den = "" if args.no_denoise else "atadenoise=0a=0.015:0b=0.03:1a=0.015:1b=0.03:2a=0.015:2b=0.03:s=7,"
vf = (f"fps={FPS},select='{sel}',setpts=N/{FPS}/TB,{den}"
      f"zscale=filter=lanczos:min={matrix}:rin={rin}:r=full,format=gbrpf32le,"
      f"lut3d=file={lut}:interp=tetrahedral,"
      "zscale=m=709:r=limited:d=error_diffusion,format=yuv444p,"
      "setparams=range=tv:color_primaries=bt709:color_trc=bt709:colorspace=bt709")
t0 = time.time()
cmd = ["ffmpeg", "-v", "error", "-stats", "-y", "-i", cfg["source"], "-an", "-vf", vf, "-fps_mode", "passthrough",
       "-c:v", "libx264", "-preset", "medium", "-crf", str(args.crf), "-g", "15", "-colorspace", "bt709",
       "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", "master.mkv"]
subprocess.run(cmd, cwd=proj, check=True)
n = int(subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                        "stream=nb_read_packets", "-of", "csv=p=0", os.path.join(proj, "master.mkv")],
                       capture_output=True, text=True).stdout.strip().split(",")[0])
if n != pos:
    sys.exit(f"master has {n} frames, expected {pos}")
json.dump(index, open(os.path.join(proj, "master_index.json"), "w"))
size = os.path.getsize(os.path.join(proj, "master.mkv"))
print(f"master.mkv: {pos} frames in {len(index)} ranges, {size / 1e9:.2f} GB, {time.time() - t0:.0f} s, look {look}/{transfer}")
