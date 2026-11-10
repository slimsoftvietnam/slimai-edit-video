"""Who is talking? Mouth-motion energy per transcript segment (static camera, needs project.json speakers).

python speaker_hints.py PROJECT     -> speakers.txt: [start-end] guess (score) text

Pitch-based labels failed on real footage (an excited male guest reads as female), mouth motion holds up.
Treat the output as a draft: look at frames for any segment with a score below about 1.3.
"""
import json
import os
import subprocess
import sys

import numpy as np

proj = sys.argv[1]
cfg = json.load(open(os.path.join(proj, "project.json"), encoding="utf-8"))
tr = json.load(open(os.path.join(proj, "transcript.json"), encoding="utf-8"))
SW, SH = cfg["src_w"], cfg["src_h"]
LW, LH = SW // 2, SH // 2
names = list(cfg["speakers"])


def mouth_boxes(speakers):
    out = []
    for k in names:
        s = speakers[k]
        fx, fy = s["face"]
        hw = (s["box"][2] - s["box"][0]) / 2
        out.append((int((fx - hw * 0.6) / 2), int(fy / 2), int((fx + hw * 0.6) / 2), int((fy + hw * 0.75) / 2)))
    return out


# per take when the camera moved between recordings (project.json "takes", from find_faces.py)
takes = [(t["start"], t["end"], mouth_boxes(dict(cfg["speakers"], **t["speakers"]))) for t in cfg.get("takes", [])]
takes = takes or [(0.0, 1e9, mouth_boxes(cfg["speakers"]))]
step = 3      # analyse every 3rd frame
p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", cfg["source"], "-vf", f"fps={cfg['fps']},scale={LW}:{LH},format=gray",
                      "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
prev = None
rows = []
i = 0
while True:
    buf = p.stdout.read(LW * LH)
    if len(buf) < LW * LH:
        break
    if i % step == 0:
        f = np.frombuffer(buf, np.uint8).reshape(LH, LW).astype(np.int16)
        if prev is not None:
            d = np.abs(f - prev)
            t_now = i / cfg["fps"]
            boxes = next((bx for (a, b, bx) in takes if a <= t_now < b), takes[-1][2])
            rows.append([float(d[y0:y1, x0:x1].mean()) for (x0, y0, x1, y1) in boxes])
        prev = f
    i += 1
# No per-person normalisation: it erases how much the talker moves. Checked by eye on 38 + 17 clips, raw motion got
# all of them right; dividing by each person's median got 22 of 38. People at very different distances may need care.
arr = np.array(rows)
fps = cfg["fps"] / step
with open(os.path.join(proj, "speakers.txt"), "w", encoding="utf-8") as out:
    for s in tr["segments"]:
        a, b = int(s["start"] * fps), max(int(s["end"] * fps), int(s["start"] * fps) + 1)
        e = arr[a:b].mean(axis=0) if b <= len(arr) and b > a else np.zeros(len(names))
        order = np.argsort(e)[::-1]
        score = e[order[0]] / (e[order[1]] + 1e-3) if len(names) > 1 else 9.9
        out.write(f"[{s['start']:7.2f}-{s['end']:7.2f}] {names[order[0]]} ({score:.2f}) {s['text'].strip()}\n")
print("wrote speakers.txt")
