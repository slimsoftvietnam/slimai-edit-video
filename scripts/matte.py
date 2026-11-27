"""Person matte (Robust Video Matting) for every frame of the master -> matte/{source_frame:06d}.png

python matte.py PROJECT            (about 4 fps on an i5 laptop CPU)

Only frames without a matte are computed. Each missing stretch is decoded from its own place in the master, after a
second of frames that lets the network's recurrent state settle, so a run after a recut (or after an interruption)
costs only the new frames. A stretch that starts the master comes out exactly as in a full run; one further in is close
to it, not identical (the network remembers every frame before; tested: a mean difference of about 3/255, at the hair
and shoulder edges, in the middle of a shot). The run ends with a count: every frame of the master must have its
matte, else it exits with an error.
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
MODEL = os.path.join(SKILL_DIR, "assets", "rvm", "rvm_mobilenetv3_fp32.torchscript")
DSR = 0.6
WARM = 30          # frames before a missing stretch that the network sees first, so its recurrent state settles


def load_model():
    """the RVM network, on the CPU, with the thread count of RVM_THREADS (default 8)"""
    torch.set_num_threads(int(os.environ.get("RVM_THREADS", "8")))
    torch._C._jit_set_profiling_executor(False)
    return torch.jit.load(MODEL).eval()


def stretches(positions):
    """sorted master positions -> [(first, last + 1)] of consecutive runs"""
    out = []
    for p in positions:
        if out and p == out[-1][1]:
            out[-1][1] = p + 1
        else:
            out.append([p, p + 1])
    return out


def main():
    proj = os.path.abspath(sys.argv[1])
    cfg = json.load(open(os.path.join(proj, "project.json"), encoding="utf-8"))
    index = json.load(open(os.path.join(proj, "master_index.json")))
    out_dir = os.path.join(proj, "matte")
    os.makedirs(out_dir, exist_ok=True)
    cx, cy, cw, ch = cfg["matte"]["crop"]
    scale = float(cfg["matte"]["scale"])
    w, h = int(cw / scale), int(ch / scale)
    fps = cfg.get("fps", 30)

    def path_of(f):
        return os.path.join(out_dir, f"{f:06d}.png")

    frames = [f0 + i for (f0, n, _p) in index for i in range(n)]       # master position -> source frame
    missing = [i for i, f in enumerate(frames) if not os.path.exists(path_of(f))]
    if not missing:
        print("all mattes present")
        return
    runs = stretches(missing)
    print(f"{len(missing)} of {len(frames)} frames need a matte, in {len(runs)} stretches", flush=True)
    model = load_model()
    t0, done = time.time(), 0
    with torch.no_grad():
        for (p0, p1) in runs:
            start = max(0, p0 - WARM)
            # the master's frame k sits at k / fps, rounded to the millisecond: seek half a millisecond early, as
            # engine.ClipReader does, or ffmpeg starts one frame late
            seek = ["-ss", f"{max(0, start / fps - 0.0005):.4f}"] if start else []
            cmd = ["ffmpeg", "-v", "error"] + seek + ["-i", os.path.join(proj, "master.mkv"), "-frames:v", str(p1 - start),
                                                      "-vf", f"crop={cw}:{ch}:{cx}:{cy},scale={w}:{h}:flags=area,format=rgb24",
                                                      "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            rec = [None] * 4
            first = True
            for i in range(start, p1):
                buf = p.stdout.read(w * h * 3)
                if len(buf) < w * h * 3:
                    break
                src = torch.from_numpy(np.frombuffer(buf, np.uint8).reshape(h, w, 3).copy()).permute(2, 0, 1).float().div_(255).unsqueeze_(0)
                if first:     # let the recurrent state settle on the first frame
                    for _ in range(6):
                        fgr, pha, *rec = model(src, *rec, DSR)
                    first = False
                fgr, pha, *rec = model(src, *rec, DSR)
                if i >= p0 and not os.path.exists(path_of(frames[i])):
                    imwrite(path_of(frames[i]), (pha[0, 0].clamp(0, 1).numpy() * 255 + 0.5).astype(np.uint8),
                            [cv2.IMWRITE_PNG_COMPRESSION, 3])
                    done += 1
                    if done % 300 == 0:
                        print(f"{done}/{len(missing)}  {time.time() - t0:.0f}s", flush=True)
            p.stdout.close()
            p.wait()
    still = [f for f in frames if not os.path.exists(path_of(f))]
    if still:
        sys.exit(f"{len(still)} frames still have no matte (first: source frame {still[0]}): is master.mkv complete? "
                 "Run build_master.py again, then matte.py")
    print(f"done: {done} mattes in {time.time() - t0:.0f}s, all {len(frames)} frames have one")


if __name__ == "__main__":
    main()
