"""Cut on the music's beat, for the vlog style (references/vlog.md).

python beat_fit.py PROJECT          reads PROJECT/vlog_cut.json -> select.json, beats.json, project.json end_hold

The music of a vlog edit is written in code (vlog_music.py), so its beat is known before anything is cut: one beat is
`beat_frames` frames, the first beat sits on frame 0, and every chapter starts on a downbeat. This script turns the
story (speech clips and silent B-roll shots, in source seconds) into select.json so that every cut lands on a beat, or
on a half beat where the source has no silence to spare. It never stretches or clips speech: it only chooses how much
of the natural silence before a clip's first sound (lead) and after its last sound (tail) is kept. A small dynamic
programme does the choosing for the whole video at once, so that chapter cards fall on beats 3-4 of a bar and every
chapter begins on the downbeat after them.

vlog_cut.json:
  {"beat_frames": 22, "card_beats": 2, "end_hold_beats": 4,
   "clips": [
     {"beat": "open", "spk": "W", "a": 14.40, "b": 26.26, "chapter": 1, "cut_in": 14.3667},
     {"beat": "modes", "spk": "M", "a": 28.26, "b": 47.88},
     {"beat": "card2", "broll": 334.72, "card": true},
     {"beat": "lib", "spk": "M", "a": 48.46, "b": 50.96, "chapter": 2},
     ...
     {"beat": "laugh", "spk": "M", "a": 374.32, "b": 376.31, "hold_beats": 4},
     {"beat": "leave", "broll": 389.5, "beats": 6}],
   "overlays": [{"src": 1.9, "at": "open", "beats": 4}],
   "fixes": [[78.3, "biết", "biên"]]}

  Speech clip: beat (unique name), spk, a / b = first word's start and last word's end from the transcript.
    The script reads the clip's first and last sound (s, e) from the audio near a and b, and the silence available
    around them. Check them in the table it prints, and pin any of them in the clip when they are wrong:
    s, e (seconds), lead_av, tail_av (seconds of silence that may be kept), adj (true: the next clip follows in the
    same take and both share one pause). cut_in / cut_out: an exact cut inside speech (no silence is added there),
    for a line that starts or ends mid-sentence. chapter: n on the first clip of chapter n. hold_beats: the picture
    stays this many beats after the last word (a reaction, a laugh); its own sound is muted in the mix.
    shot: wide | med (vlog.setup() reframes on bar lines anyway).
  B-roll: broll = source second of a silent shot (the speaker's sound is muted under it). card: true makes it the
    chapter card before the next chapter (card_beats long); otherwise beats = its length. The last B-roll is the
    ending: it starts on a downbeat.
  overlays: B-roll drawn over a speaking clip while its sound plays (a J-cut): src (source second), at (clip name, or
    a frame number), from_beat (beats into that clip), beats. vlog.py draws it; build_master.py adds its frames.
  fixes: as in select.json (passed through).

beats.json lists every cut (frame), the chapters with their downbeats, the cards, all B-roll, the overlays and the
muted holds. vlog.py, vlog_music.py and vlog_mix.py read it, so picture, music and sound share one clock.
"""
import json
import os
import sys

import numpy as np
from scipy.io import wavfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
proj = os.path.abspath(sys.argv[1])
plan = json.load(open(os.path.join(proj, "vlog_cut.json"), encoding="utf-8"))
cfg_path = os.path.join(proj, "project.json")
cfg = json.load(open(cfg_path, encoding="utf-8"))
FPS = int(cfg["fps"])
BEAT = int(plan.get("beat_frames", 22))      # 22 frames at 30 fps = 81.82 BPM: an unhurried lo-fi pulse
HALF = BEAT // 2
BAR = 4 * BEAT
CARD = int(plan.get("card_beats", 2)) * BEAT
LEAD_MIN, TAIL_MIN = 2, 3                    # frames of silence always kept before the first / after the last sound
if BEAT % 2:
    sys.exit("beat_frames must be even, so that a half beat is a whole frame")

# ----------------------------------------------------------------------------
# sound runs: 10 ms power, averaged over 30 ms, above a threshold set from the recording's noise and speech levels
# ----------------------------------------------------------------------------
sr, audio = wavfile.read(os.path.join(proj, "audio48k_orig.wav" if os.path.exists(os.path.join(proj, "audio48k_orig.wav"))
                                      else "audio48k.wav"))
audio = audio.astype(np.float64)
if audio.ndim > 1:
    audio = audio.mean(1)
audio /= max(1e-9, np.abs(audio).max())
HOP = sr // 100
nfr = len(audio) // HOP
p10 = (audio[:nfr * HOP].reshape(nfr, HOP) ** 2).mean(1)
db10 = 10 * np.log10(p10 + 1e-12)
db30 = 10 * np.log10(np.convolve(p10, np.ones(3) / 3, mode="same") + 1e-12)
THR = plan.get("threshold_db")
if THR is None:
    THR = max(np.percentile(db10, 8) + 9.0, np.percentile(db10, 75) - 24.0) + 4.0
snd = db30 > THR
RUNS = []
i = 0
while i < nfr:
    if snd[i]:
        j = i
        while j < nfr and snd[j]:
            j += 1
        RUNS.append((i / 100.0, j / 100.0))
        i = j
    else:
        i += 1
REAL = [r for r in RUNS if r[1] - r[0] >= 0.06]       # shorter runs are clicks and breaths


def runs_near(t0, t1):
    return [r for r in RUNS if r[1] > t0 and r[0] < t1]


def low_point(t0, t1):
    i0, i1 = int(t0 * 100), max(int(t0 * 100) + 1, int(t1 * 100))
    return (i0 + int(np.argmin(db10[i0:i1]))) / 100.0


def measure_start(a):
    """first sound of a clip whose first word starts near a; (s, how)"""
    c = [r for r in REAL if r[1] > a - 0.15 and r[0] < a + 0.30]
    if not c:
        return a, "no sound near a"
    r = c[0]
    if r[0] < a - 0.30:                         # the run began before the word: the clip starts mid-speech
        return low_point(a - 0.15, a + 0.03), "mid-speech: check, or set cut_in"
    return r[0], "auto"


def measure_end(b):
    c = [r for r in REAL if r[0] < b + 0.05 and r[1] > b - 0.30]
    if not c:
        return b, "no sound near b"
    r = c[-1]
    if r[1] > b + 0.40:
        return low_point(b - 0.03, b + 0.15), "mid-speech: check, or set cut_out"
    return r[1], "auto"


def silence_before(s):
    prev = [r[1] for r in RUNS if r[1] <= s - 0.005]
    return max(0.0, s - (max(prev) if prev else 0.0) - 0.04)


def silence_after(e):
    nxt = [r[0] for r in RUNS if r[0] >= e + 0.005]
    return max(0.0, (min(nxt) if nxt else len(audio) / sr) - e - 0.04)


# ----------------------------------------------------------------------------
# the plan
# ----------------------------------------------------------------------------
BASE = []
for c0 in plan["clips"]:
    c = dict(c0)
    if "broll" in c:
        c["kind"] = "broll"
        c["src"] = float(c["broll"])
        c["frames"] = CARD if c.get("card") else int(round(float(c.get("beats", 2)) * BEAT))
        c.setdefault("spk", "M")
        c["shot"] = "wide"
    else:
        c["kind"] = "speech"
        c.setdefault("shot", "wide")
        c["how"] = []
        if "cut_in" in c:
            c["s"], c["fix_a"] = float(c["cut_in"]), True
            c["how"].append("cut_in")
        elif "s" not in c:
            c["s"], how = measure_start(float(c["a"]))
            c["how"].append(f"s {how}")
        if "cut_out" in c:
            c["e"], c["fix_b"] = float(c["cut_out"]), True
            c["how"].append("cut_out")
        elif "e" not in c:
            c["e"], how = measure_end(float(c["b"]))
            c["how"].append(f"e {how}")
        if "lead_av" not in c:
            c["lead_av"] = 0.0 if c.get("fix_a") else round(silence_before(c["s"]), 2)
        if "tail_av" not in c:
            c["tail_av"] = 0.0 if c.get("fix_b") else round(silence_after(c["e"]), 2)
    BASE.append(c)
names = [c["beat"] for c in BASE]
if len(set(names)) != len(names):
    sys.exit("every clip needs its own beat name")
for k, c in enumerate(BASE):                       # adjacency: the next clip continues the same take after one pause
    nxt = BASE[k + 1] if k + 1 < len(BASE) else None
    if c["kind"] == "speech" and "adj" not in c:
        c["adj"] = bool(nxt is not None and nxt["kind"] == "speech" and 0 < nxt["s"] - c["e"] < 4.0
                        and not [r for r in REAL if r[0] < nxt["s"] - 0.005 and r[1] > c["e"] + 0.005])
for c in BASE:
    if c["kind"] != "speech":
        continue
    c["sf"] = int(np.floor(c["s"] * FPS + 1e-6))             # frame that holds the first sound
    c["ef"] = int(np.ceil(c["e"] * FPS - 1e-6))              # first frame after the last sound
    c["lead_fr"] = 0 if c.get("fix_a") else int(c["lead_av"] * FPS)
    c["tail_fr"] = 0 if c.get("fix_b") else int(c["tail_av"] * FPS)
    if "hold_beats" in c:
        c["tail_fixed"] = int(round(float(c["hold_beats"]) * BEAT))

# ----------------------------------------------------------------------------
# the fit: a dynamic programme over the cut's position inside the bar. Each speech clip may keep x extra frames of
# its own silence (tail first, then lead). Cuts want the beat, accept the half beat; a chapter card wants beats 3-4
# of a bar, so that its chapter starts on the next downbeat; pauses stay natural for who speaks next.
# ----------------------------------------------------------------------------
for k, c in enumerate(BASE):
    if c["kind"] != "speech":
        continue
    prev = BASE[k - 1] if k > 0 else None
    nxt = BASE[k + 1] if k + 1 < len(BASE) else None
    c["lead0"] = 0 if c.get("fix_a") else min(LEAD_MIN, c["lead_fr"])
    c["tmin"] = 0 if c.get("fix_b") else min(TAIL_MIN, c["tail_fr"])
    c["after_adj"] = prev is not None and prev["kind"] == "speech" and bool(prev.get("adj"))
    c["adj_next"] = bool(c.get("adj")) and nxt is not None and nxt["kind"] == "speech"
    tc = max(0, c["tail_fr"] - c["tmin"])
    if c["adj_next"]:            # one shared natural pause of N frames: tail + the next clip's lead may not exceed it
        c["N"] = nxt["sf"] - c["ef"]
        tc = max(0, min(tc, c["N"] - min(LEAD_MIN, nxt["lead_fr"]) - c["tmin"]))
    c["tail_cap"] = tc
    c["body"] = c["ef"] - c["sf"]
    if nxt is None:
        c["want"] = (0.2, 0.5, 1.2)
    elif nxt["kind"] == "broll":
        c["want"] = (0.17, 0.37, 0.9)
    elif nxt["spk"] != c["spk"]:
        c["want"] = (0.25, 0.47, 1.1)
    else:
        c["want"] = (0.15, 0.33, 0.8)


def phase_cost(ph, kind):
    """cost of a cut that falls ph frames into a bar. kind: "cut" (any cut), "card" (a chapter card: beats 3-4 of a
    bar), "bar" (the ending: a downbeat)."""
    on_beat, on_half = ph % BEAT == 0, ph % BEAT == HALF
    if kind == "card":
        if ph == 2 * BEAT:
            return 0.0
        return 9.0 if ph == 0 else (14.0 if on_beat else 70.0)
    if kind == "bar":
        if ph == 0:
            return 0.0
        return 4.0 if ph == 2 * BEAT else (8.0 if on_beat else 70.0)
    if on_beat:
        return -0.15 if ph % (2 * BEAT) == 0 else 0.0
    if on_half:
        return 1.2
    return 6.0 + 0.1 * min(ph % BEAT, BEAT - ph % BEAT)


last_broll = max([k for k, c in enumerate(BASE) if c["kind"] == "broll" and not c.get("card")], default=None)
for k, c in enumerate(BASE):
    nxt = BASE[k + 1] if k + 1 < len(BASE) else None
    if nxt is None:
        c["next_kind"] = "cut"
    elif nxt["kind"] == "broll" and nxt.get("card"):
        c["next_kind"] = "card"
    elif last_broll is not None and k + 1 == last_broll and last_broll == len(BASE) - 1:
        c["next_kind"] = "bar"
    else:
        c["next_kind"] = "cut"

best = {(0, 0): (0.0, [])}          # (frames into the bar, frames of a shared pause left for this clip's lead) -> (cost, xs)
for k, c in enumerate(BASE):
    new = {}
    for (ph, r), (cost, xs) in best.items():
        if c.get("chapter"):
            ph = 0                  # a chapter's first frame is a downbeat: the music is written from here
        if c["kind"] == "broll":
            cand = [(0, 0.0, 0)]
            step = c["frames"]
        elif "tail_fixed" in c:
            step = c["lead0"] + c["body"] + c["tail_fixed"]
            x0 = (-(ph + step)) % BEAT
            cand = [(x0 + j * BEAT, 0.05 * j, 0) for j in range(4)]
        else:
            step = c["lead0"] + c["body"] + c["tmin"]
            if c.get("fix_a"):
                lead_cap = 0
            elif c["after_adj"]:
                lead_cap = max(0, min(c["lead_fr"], r) - c["lead0"])
            else:
                lead_cap = max(0, c["lead_fr"] - c["lead0"])
            nxt = BASE[k + 1] if k + 1 < len(BASE) else None
            cand = []
            for xk in range(0, c["tail_cap"] + lead_cap + 1):
                t_add = min(xk, c["tail_cap"])
                l_add = xk - t_add
                pause = (c["tmin"] + t_add + (LEAD_MIN if nxt is not None and nxt["kind"] == "speech" else 0)) / FPS
                pc = 0.9 * l_add / FPS + abs(pause - c["want"][1]) * 0.8
                if pause < c["want"][0]:
                    pc += (c["want"][0] - pause) * 6
                elif pause > c["want"][2]:
                    pc += (pause - c["want"][2]) * 4
                r2 = (c["N"] - c["tmin"] - t_add) if c["adj_next"] else 0
                cand.append((xk, pc, r2))
        for xk, pc, r2 in cand:
            ph2 = (ph + step + xk) % BAR
            c2 = cost + pc + (phase_cost(ph2, c["next_kind"]) if c["kind"] == "speech" else 0.0)
            key = (ph2, r2)
            if key not in new or c2 < new[key][0]:
                new[key] = (c2, xs + [xk])
    best = new
cost, xs = min(best.values(), key=lambda v: v[0])

F = 0
down = 0
warn = []
for k, c in enumerate(BASE):
    c["cut"] = F
    if c.get("chapter"):
        down = F
    c["bar_pos"] = (F - down) / BEAT        # beats since the chapter's downbeat
    xk = xs[k]
    if c["kind"] == "broll":
        F += c["frames"]
        continue
    if "tail_fixed" in c:
        c["lead"], c["tail"] = c["lead0"], c["tail_fixed"] + xk
    else:
        t_add = min(xk, c["tail_cap"])
        c["lead"], c["tail"] = c["lead0"] + (xk - t_add), c["tmin"] + t_add
    F += c["lead"] + c["body"] + c["tail"]
    ph = (F - down) % BEAT
    c["grid"] = "beat" if ph == 0 else ("half" if ph == HALF else "OFF")
    if c["grid"] == "OFF":
        warn.append(c["beat"])
total = F

# ----------------------------------------------------------------------------
# outputs
# ----------------------------------------------------------------------------
clips = []
for c in BASE:
    if c["kind"] == "broll":
        a = round(round(c["src"] * FPS) / FPS, 4)
        b = round(a + c["frames"] / FPS, 4)
        clips.append({"a": a, "b": b, "spk": c["spk"], "beat": c["beat"], "shot": c["shot"], "hard": {"a": a, "b": b}})
    else:
        a = round((c["sf"] - c["lead"]) / FPS, 4)
        b = round((c["ef"] + c["tail"]) / FPS, 4)
        clips.append({"a": c["s"], "b": c["e"], "spk": c["spk"], "beat": c["beat"], "shot": c["shot"], "hard": {"a": a, "b": b}})
cut_of = {c["beat"]: c["cut"] for c in BASE}
overlays, extra = [], []
for o in plan.get("overlays", []):
    at = o.get("at", 0)
    f0 = (cut_of[at] if isinstance(at, str) else int(at)) + int(round(float(o.get("from_beat", 0)) * BEAT))
    n = int(round(float(o.get("beats", 4)) * BEAT))
    ov = {"src": float(o["src"]), "at": f0, "frames": n}
    ov.update({k: o[k] for k in ("zoom", "focus") if k in o})      # the slow push-in over it
    overlays.append(ov)
    extra.append([round(round(float(o["src"]) * FPS) / FPS, 4), n])
sel = {"clips": clips, "fixes": plan.get("fixes", []), "keep_pauses": True}
if extra:
    sel["extra"] = extra
json.dump(sel, open(os.path.join(proj, "select.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

chapters = [{"n": c["chapter"], "beat": c["beat"], "down": c["cut"]} for c in BASE if c.get("chapter")]
nxt_chapter = {}
for k, c in enumerate(BASE):
    if c["kind"] == "broll" and c.get("card"):
        later = [d for d in BASE[k + 1:] if d.get("chapter")]
        nxt_chapter[c["beat"]] = later[0]["chapter"] if later else None
cards = [{"beat": c["beat"], "cut": c["cut"], "frames": c["frames"], "chapter": nxt_chapter[c["beat"]]}
         for c in BASE if c["kind"] == "broll" and c.get("card")]
broll = [{"beat": c["beat"], "cut": c["cut"], "frames": c["frames"], "src": c["src"], "card": bool(c.get("card"))}
         for c in BASE if c["kind"] == "broll"]
holds = [{"beat": c["beat"], "from": c["cut"] + c["lead"] + c["body"], "to": c["cut"] + c["lead"] + c["body"] + c["tail"]}
         for c in BASE if "tail_fixed" in c]
end_hold = int(round(float(plan.get("end_hold_beats", 4)) * BEAT))
json.dump({"fps": FPS, "beat": BEAT, "total": total, "end_hold": end_hold, "chapters": chapters, "cards": cards,
           "broll": broll, "overlays": overlays, "holds": holds,
           "cuts": [{"beat": c["beat"], "cut": c["cut"]} for c in BASE]},
          open(os.path.join(proj, "beats.json"), "w", encoding="utf-8"), indent=1)
cfg.setdefault("end_hold", {})["youtube"] = round(end_hold / FPS, 4)
json.dump(cfg, open(cfg_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ----------------------------------------------------------------------------
# the table: check every measured edge (words from the transcript, sound runs around the edge)
# ----------------------------------------------------------------------------
tr = json.load(open(os.path.join(proj, "transcript.json"), encoding="utf-8"))
allw = sorted([(float(w["start"]), float(w["end"]), w["word"].strip()) for s_ in tr["segments"] for w in s_.get("words", [])])


def words_in(t0, t1):
    return " ".join(w for (s, e, w) in allw if t0 - 0.02 <= s < t1)


def fmt_runs(t0, t1):
    return " ".join(f"{a:.2f}-{b:.2f}" for a, b in runs_near(t0, t1)) or "-"


print(f"threshold {THR:.1f} dB · beat {BEAT} frames = {60 * FPS / BEAT:.2f} BPM · bar {BAR / FPS:.3f} s · "
      f"{total} frames = {total / FPS:.2f} s + end hold {end_hold / FPS:.2f} s")
print(f"{'clip':10s} {'cut':>6s} {'t':>7s} {'bar.beat':>8s} {'lead':>4s} {'tail':>4s}  end on   source s..e")
for c in BASE:
    bp = c["bar_pos"]
    pos = f"{int(bp // 4) + 1}.{bp % 4 + 1:.1f}"
    if c["kind"] == "broll":
        kind = "card" if c.get("card") else "B-roll"
        print(f"{c['beat']:10s} {c['cut']:6d} {c['cut'] / FPS:7.2f} {pos:>8s}   ({kind} {c['frames']} frames from {c['src']})")
        continue
    ch = f"   <- chapter {c['chapter']}" if c.get("chapter") else ""
    print(f"{c['beat']:10s} {c['cut']:6d} {c['cut'] / FPS:7.2f} {pos:>8s} {c['lead']:4d} {c['tail']:4d}  {c['grid']:6s} "
          f"{c['s']:8.2f}..{c['e']:.2f}  adj {str(c.get('adj', False))[0]}{ch}")
    if any("auto" not in h for h in c["how"]) or "--show" in sys.argv:
        print(f"{'':12s}{'; '.join(c['how'])}")
    if "--show" in sys.argv:
        print(f"{'':12s}start: [{words_in(c['s'] - 0.4, c['s'] + 0.6)}]  runs {fmt_runs(c['s'] - 0.9, c['s'] + 0.4)}")
        print(f"{'':12s}end:   [{words_in(c['e'] - 0.8, c['e'] + 0.1)}]  runs {fmt_runs(c['e'] - 0.4, c['e'] + 1.0)}")
for o in overlays:
    print(f"overlay    {o['at']:6d} {o['at'] / FPS:7.2f}   B-roll over speech: {o['frames']} frames from {o['src']}")
if warn:
    print("OFF THE GRID (no silence to reach a half beat):", ", ".join(warn))
print("wrote select.json, beats.json; project.json end_hold youtube", round(end_hold / FPS, 4))
