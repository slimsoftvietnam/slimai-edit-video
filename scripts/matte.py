"""Person matte (Robust Video Matting) for every frame of the master -> matte/{source_frame:06d}.png

python matte.py PROJECT            (about 4 fps on an i5 laptop CPU; frames already present are skipped)
"""
import json
import os
import subprocess
import sys
import time

import cv2
import numpy as np
import torch

from imgio import imwrite

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
proj = os.path.abspath(sys.argv[1])
cfg = json.load(open(os.path.join(proj, "project.json"), encoding="utf-8"))
index = json.load(open(os.path.join(proj, "master_index.json")))
OUT = os.path.join(proj, "matte")
os.makedirs(OUT, exist_ok=True)
CX, CY, CW, CH = cfg["matte"]["crop"]
SCALE = float(cfg["matte"]["scale"])
w, h = int(CW / SCALE), int(CH / SCALE)
DSR = 0.6
torch.set_num_threads(int(os.environ.get("RVM_THREADS", "8")))
torch._C._jit_set_profiling_executor(False)
model = torch.jit.load(os.path.join(SKILL_DIR, "assets", "rvm", "rvm_mobilenetv3_fp32.torchscript")).eval()

frames = [f0 + i for (f0, n, _p) in index for i in range(n)]
missing = sum(1 for f in frames if not os.path.exists(os.path.join(OUT, f"{f:06d}.png")))
if not missing:
    print("all mattes present")
    sys.exit()
cmd = ["ffmpeg", "-v", "error", "-i", os.path.join(proj, "master.mkv"), "-vf",
       f"crop={CW}:{CH}:{CX}:{CY},scale={w}:{h}:flags=area,format=rgb24", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
rec = [None] * 4
t0 = time.time()
first = True
with torch.no_grad():
    for i, f in enumerate(frames):
        buf = p.stdout.read(w * h * 3)
        if len(buf) < w * h * 3:
            break
        src = torch.from_numpy(np.frombuffer(buf, np.uint8).reshape(h, w, 3).copy()).permute(2, 0, 1).float().div_(255).unsqueeze_(0)
        if first:     # let the recurrent state settle on the first frame
            for _ in range(6):
                fgr, pha, *rec = model(src, *rec, DSR)
            first = False
        fgr, pha, *rec = model(src, *rec, DSR)
        path = os.path.join(OUT, f"{f:06d}.png")
        if not os.path.exists(path):
            imwrite(path, (pha[0, 0].clamp(0, 1).numpy() * 255 + 0.5).astype(np.uint8), [cv2.IMWRITE_PNG_COMPRESSION, 3])
        if i % 300 == 0:
            print(f"{i}/{len(frames)}  {time.time() - t0:.0f}s", flush=True)
p.wait()
print(f"done {len(frames)} frames in {time.time() - t0:.0f}s")
