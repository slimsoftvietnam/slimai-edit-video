"""Clamp the transcript's word times to the clips of select.json. Run it after beat_fit.py, before build_timeline.py.

Whisper stretches a word's end over the pause after it (and sometimes its start over the pause before it), so a
word at a clip's edge can fall outside the clip and vanish from words.txt. This clamps the words of transcript.json
to the clips of select.json: a word that overlaps a clip by any part is moved to lie inside it (the first-pass
transcript is kept as transcript_firstpass.json). It only nudges word edges into the clips, so it is safe to run
again after a recut.

python clamp_words.py PROJECT
"""
import json
import os
import shutil
import sys

proj = sys.argv[1]
tp = os.path.join(proj, "transcript.json")
keep = os.path.join(proj, "transcript_firstpass.json")
if not os.path.exists(keep):
    shutil.copy(tp, keep)
d = json.load(open(tp, encoding="utf-8"))
sel = json.load(open(os.path.join(proj, "select.json"), encoding="utf-8"))
clips = [(c.get("hard", {}).get("a", c["a"]), c.get("hard", {}).get("b", c["b"])) for c in sel["clips"]]
n = 0
for s in d["segments"]:
    for w in s.get("words", []):
        ws, we = w["start"], w["end"]
        mid = (ws + we) / 2
        best = None
        for (a, b) in clips:
            ov = min(we, b) - max(ws, a)
            if ov > 0.02 and (best is None or ov > best[0]):
                best = (ov, a, b)
        if best is None:
            continue
        _ov, a, b = best
        ns, ne = max(ws, a + 0.005), min(we, b - 0.01)
        if ne - ns < 0.04:
            continue
        if abs(ns - ws) > 1e-6 or abs(ne - we) > 1e-6:
            w["start"], w["end"] = round(ns, 3), round(ne, 3)
            n += 1
json.dump(d, open(tp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("clamped", n, "words")
