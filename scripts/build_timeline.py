"""Turn the editor's choices (select.json) into timeline.json: refine cut points on the audio, tighten
pauses, quantise to frames, map every word to output time.

python build_timeline.py PROJECT

select.json:
  {"clips": [{"a": 348.50, "b": 351.62, "spk": "M", "beat": "hook", "shot": "close", "hard": {"a": 348.22}}, ...],
   "fixes": [[52.80, "biết", "viết"], [348.14, "nã", ""], ...]}
  a / b: first word start and last word end (source seconds, from transcript.json), order = story order.
  shot: wide | med | close. hard: exact in/out overriding the automatic refinement.
  gap_after: seconds of silence after the clip, for a black title card in a trailer cut (references/trailer.md);
  timeline.json lists them under "gaps" as [t0, t1, beat].
  fixes: (approx source time, heard word, correct word); "" deletes a word from the captions.
  keep_pauses: true (for the whole file, or on one clip) keeps every pause inside a clip as cut; by default pauses of
  0.3 s or more are shortened to 0.12 s. The vlog style sets it: beat_fit.py has already timed each pause to the beat.
  extra: [[source second, frames], ...] source ranges the master must hold although no clip plays them, such as B-roll
  that the design draws over a speaking clip (vlog.py overlays); timeline.json passes them on to build_master.py.
"""
import json
import os
import sys

import numpy as np
from scipy.io import wavfile

proj = sys.argv[1]
cfg = json.load(open(os.path.join(proj, "project.json"), encoding="utf-8"))
sel = json.load(open(os.path.join(proj, "select.json"), encoding="utf-8"))
FPS = cfg["fps"]
FIX = {(float(t), w): new for (t, w, new) in sel.get("fixes", [])}

sr, audio = wavfile.read(os.path.join(proj, "audio48k.wav"))
audio = audio.astype(np.float64)
audio /= np.abs(audio).max()
HOP = sr // 100  # 10 ms
nfr = len(audio) // HOP
fr = audio[: nfr * HOP].reshape(nfr, HOP)
db = 10 * np.log10((fr ** 2).mean(1) + 1e-12)
noise = np.percentile(db, 8)
speech = np.percentile(db, 75)
THR = max(noise + 9.0, speech - 24.0)
print(f"noise {noise:.1f} dB, speech {speech:.1f} dB, thr {THR:.1f} dB")


def refine_start(t, prev_end):
    """Move start to just before speech onset; never before prev word end."""
    lo = max(prev_end + 0.01, t - 0.30)
    hi = t + 0.08
    i0, i1 = int(lo * 100), int(hi * 100)
    seg = db[i0:i1]
    if len(seg) == 0:
        return t
    onset_idx = None
    for i in range(int((t - 0.06) * 100) - i0, len(seg)):
        if i >= 0 and seg[i] > THR:
            onset_idx = i
            break
    if onset_idx is None:
        return t
    j = onset_idx
    while j > 0 and seg[j - 1] > THR:
        j -= 1
    return max(lo, (i0 + j) / 100.0 - 0.07)


def refine_end(t, next_start):
    hi = min(next_start - 0.01, t + 0.40)
    i0 = int((t - 0.05) * 100)
    i1 = int(hi * 100)
    k = i0
    while k < i1 and db[k] > THR:
        k += 1
    return min(hi, k / 100.0 + 0.10)


def split_pauses(a, b, min_gap=0.30, keep=0.12):
    """Sub-ranges with long internal silences shortened."""
    i0, i1 = int(a * 100), int(b * 100)
    sil = db[i0:i1] < THR
    out = []
    cur = a
    i = 0
    n = len(sil)
    while i < n:
        if sil[i]:
            j = i
            while j < n and sil[j]:
                j += 1
            if (j - i) / 100.0 >= min_gap and i > 5 and j < n - 5:
                g0, g1 = (i0 + i) / 100.0, (i0 + j) / 100.0
                out.append((cur, g0 + keep / 2))
                cur = g1 - keep / 2
            i = j
        else:
            i += 1
    out.append((cur, b))
    return [(x, y) for (x, y) in out if y - x > 0.12]


tr = json.load(open(os.path.join(proj, "transcript.json"), encoding="utf-8"))
allw = []
for s in tr["segments"]:
    for w in s.get("words", []):
        txt = w["word"].strip()
        for (ft, fw), new in FIX.items():
            if abs(w["start"] - ft) < 0.03 and fw == txt:
                txt = new
        allw.append({"w": txt, "s": float(w["start"]), "e": float(w["end"])})
allw.sort(key=lambda d: d["s"])


def word_bounds(t, side):
    if side == "prev":
        c = [w["e"] for w in allw if w["e"] <= t + 0.02 and w["s"] < t - 0.02]
        return max(c) if c else t - 1
    c = [w["s"] for w in allw if w["s"] >= t - 0.02 and w["e"] > t + 0.02]
    return min(c) if c else t + 1


clips = []
for c_ in sel["clips"]:
    a, b = c_["a"], c_["b"]
    hard = c_.get("hard", {})
    ra = hard.get("a", refine_start(a, word_bounds(a, "prev")))
    rb = hard.get("b", refine_end(b, word_bounds(b, "next")))
    n0 = len(clips)
    keep = sel.get("keep_pauses") or c_.get("keep_pauses")
    for k, (x, y) in enumerate([(ra, rb)] if keep else split_pauses(ra, rb)):
        clips.append({"src_in": round(x, 3), "src_out": round(y, 3), "spk": c_["spk"], "beat": c_.get("beat", ""),
                      "shot": f"{c_['spk']}_{c_.get('shot', 'med')}", "first_of_sel": k == 0})
    if c_.get("gap_after") and len(clips) > n0:
        clips[-1]["gap_after"] = float(c_["gap_after"])

t_out = 0.0
gaps = []
for c in clips:
    nfrm = max(3, int(round((c["src_out"] - c["src_in"]) * FPS)))
    c["src_out"] = round(c["src_in"] + nfrm / FPS, 4)
    c["out_in"] = round(t_out, 4)
    c["frames"] = nfrm
    t_out += nfrm / FPS
    c["out_out"] = round(t_out, 4)
    g = c.pop("gap_after", 0.0)
    if g:     # silence for a title card; words after it move along, since they are mapped through the clips
        n = int(round(g * FPS))
        gaps.append([c["out_out"], round(t_out + n / FPS, 4), c["beat"]])
        t_out += n / FPS


def src_to_out(t):
    for c in clips:
        if c["src_in"] - 1e-3 <= t <= c["src_out"] + 1e-3:
            return c["out_in"] + (t - c["src_in"])
    return None


def snap(t, mode):
    """Times inside removed gaps snap to the next kept frame (s) or the previous kept frame (e)."""
    o = src_to_out(t)
    if o is not None:
        return o
    if mode == "s":
        nxt = [c for c in clips if c["src_in"] > t]
        return min(nxt, key=lambda c: c["src_in"])["out_in"] if nxt else None
    prv = [c for c in clips if c["src_out"] < t]
    return max(prv, key=lambda c: c["src_out"])["out_out"] if prv else None


words = []
seen = set()
for c in clips:
    for w in allw:
        if not w["w"] or id(w) in seen:
            continue
        # a word belongs here if it overlaps this clip by >= 40 % of its length or 80 ms
        ov = min(w["e"], c["src_out"]) - max(w["s"], c["src_in"])
        zero_len = (w["e"] - w["s"]) < 0.05 and c["src_in"] <= w["s"] <= c["src_out"]
        if not zero_len and (ov <= 0 or (ov < 0.08 and ov < 0.4 * (w["e"] - w["s"]))):
            continue
        seen.add(id(w))
        s_ = snap(max(w["s"], c["src_in"]), "s")
        e_ = snap(min(w["e"], c["src_out"]), "e")
        if s_ is None or e_ is None:
            continue
        words.append({"w": w["w"], "src_s": w["s"], "src_e": w["e"], "s": round(s_, 3),
                      "e": round(max(e_, s_ + 0.06), 3), "spk": c["spk"], "beat": c["beat"]})
words.sort(key=lambda d: d["s"])

out = {"fps": FPS, "duration": round(t_out, 4), "clips": clips, "words": words, "gaps": gaps}
if sel.get("extra"):
    out["extra"] = [[float(t), int(n)] for (t, n) in sel["extra"]]
json.dump(out, open(os.path.join(proj, "timeline.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(clips)} sub-clips, duration {t_out:.2f}s")
for g in gaps:
    print(f"  gap after {g[2]}: {g[0]:.2f} - {g[1]:.2f}")
beats = {}
for c in clips:
    beats.setdefault(c["beat"], [c["out_in"], c["out_out"]])
    beats[c["beat"]][1] = c["out_out"]
for k, v in beats.items():
    print(f"  {k:10s} {v[0]:7.2f} - {v[1]:7.2f}  ({v[1] - v[0]:.1f}s)")
with open(os.path.join(proj, "words.txt"), "w", encoding="utf-8") as f:
    for w in words:
        f.write(f"{w['s']:8.2f} {w['e']:8.2f} {w['spk']} {w['w']}\n")
print("wrote timeline.json, words.txt (output-time word list: use it to write anchors in design.py)")
