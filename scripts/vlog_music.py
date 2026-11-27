"""Music for the vlog style (references/vlog.md), written in code on the cut's own beat grid.

It is the skill's warm lo-fi recipe (compose.py: electric piano, pad, bass, soft drums, the pluck motif, vinyl hiss),
arranged so that the music and the edit share one clock:
- one beat = beats.json "beat" frames; beat_fit.py put every cut on that grid;
- every chapter starts on a downbeat: the bars are counted again from each chapter's first frame, with a small bell;
- the two beats of each chapter card are a fill (no drums, a pluck run that climbs into the downbeat);
- sections change on bar lines: calmer under questions and summaries, fuller under the worked examples, a lift for
  the last chapter and an outro under the ending.

The arrangement per chapter comes from vlog.ARRANGE (set in design.py), else from default_arrange().

python vlog_music.py PROJECT OUT.wav        (the music alone, and the bar map; audio_mix.py's vlog mix calls render())
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import audio_engine as ae  # noqa: E402
from audio_engine import SR, hz, note_num as N  # noqa: E402
from compose import MOTIF, MOTIF_B, PROG_CALM, PROG_MAIN, bus_chain, glide, glue, sweep_lowpass, vinyl  # noqa: E402

BT = FPS = BEAT = BAR = BPM = END_HOLD = TOTAL = None
ARRANGE = {}


def load(project, arrange=None):
    """read the project's beats.json (and the design's arrangement); call before render()"""
    global BT, FPS, BEAT, BAR, BPM, END_HOLD, TOTAL, ARRANGE
    BT = json.load(open(os.path.join(project, "beats.json")))
    FPS = BT["fps"]
    BEAT = BT["beat"] / FPS
    BAR = 4 * BEAT
    BPM = 60.0 / BEAT
    END_HOLD = BT.get("end_hold", 4 * BT["beat"]) / FPS
    TOTAL = BT["total"] / FPS + END_HOLD
    ARRANGE = dict(arrange or {})


#              ep    pad   bass  kick  snare hat   shaker pluck  lp(Hz)
STYLES = {
    "intro":   (0.8, 0.9, 0.6, 0.0, 0.0, 0.0, 0.4, 0.9, 7500),      # bar 1: she walks in; no kick yet, the motif leads
    "break":   (0.8, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.6, 3400),
    "light":   (0.9, 0.7, 0.75, 0.6, 0.0, 0.0, 0.6, 0.0, 8000),
    "stroll":  (0.9, 0.7, 0.8, 0.65, 0.0, 0.3, 0.65, 0.7, 10000),
    "groove":  (1.0, 0.6, 0.95, 0.85, 0.5, 0.55, 0.6, 0.0, 11000),
    "lift":    (1.0, 0.7, 1.0, 0.9, 0.6, 0.7, 0.7, 0.8, 13000),
    "outro":   (0.9, 1.0, 0.4, 0.0, 0.0, 0.0, 0.25, 1.0, 5200),
}
FILL_CHORD = ("A1", ["E3", "G3", "A3", "C#4"])           # the dominant: it leans into the next downbeat
FILL_RUN = [(0.0, "E5", 0.5), (0.5, "F#5", 0.6), (1.0, "A5", 0.72), (1.5, "B5", 0.85)]


def chapters():
    """[(number, downbeat s, end s)]: a chapter's music ends where the next chapter's card (its fill) starts."""
    card_of = {c["chapter"]: c["cut"] / FPS for c in BT["cards"] if c.get("chapter")}
    ch = BT["chapters"]
    out = []
    for i, c in enumerate(ch):
        if i + 1 < len(ch):
            nxt = ch[i + 1]
            end = card_of.get(nxt["n"], nxt["down"] / FPS)
        else:
            end = TOTAL
        out.append((c["n"], c["down"] / FPS, end))
    return out


def ending_start():
    """where the ending begins: the last B-roll when it closes the cut, else the end hold"""
    br = BT.get("broll", [])
    if br and br[-1]["cut"] + br[-1]["frames"] == BT["total"]:
        return br[-1]["cut"] / FPS
    return BT["total"] / FPS


def default_arrange(n, down, end, first, last):
    """a starting point for a chapter without an entry in vlog.ARRANGE: [(first bar, style, progression)]"""
    nb = int(np.ceil((end - down) / BAR - 1e-6))
    if first:
        return [(1, "intro", "main"), (2, "stroll", "main"), (5, "light", "main")]
    if last:
        out = [(1, "lift", "main")]
        k = int(round((ending_start() - down) / BAR)) + 1
        if 1 < k <= nb:
            out.append((k, "outro", "calm"))
        return out
    if nb <= 7:
        return [(1, "break", "calm"), (2, "stroll", "main")]
    return [(1, "break", "calm"), (2, "light", "main"), (max(3, nb // 2), "groove", "main"), (max(4, nb - 2), "light", "calm")]


def sections():
    """[(t0, t1, style, prog, first bar index)] in seconds, bar lines at t0 + k * BAR"""
    out = []
    chs = chapters()
    for i, (n, down, end) in enumerate(chs):
        arr = ARRANGE.get(n) or default_arrange(n, down, end, i == 0, i == len(chs) - 1)
        for j, (bar1, style, prog) in enumerate(arr):
            t0 = down + (bar1 - 1) * BAR
            t1 = down + (arr[j + 1][0] - 1) * BAR if j + 1 < len(arr) else end
            t1 = min(t1, end)
            if t1 > t0 + 1e-6:
                out.append((t0, t1, style, prog, bar1 - 1))
    return out


def fills():
    return [c["cut"] / FPS for c in BT["cards"]]


def humanize(t, amt=0.005):
    return t + ae.RNG.uniform(-amt, amt)


def render(verbose=False):
    n_total = int((TOTAL + 4.0) * SR)
    buses = {k: np.zeros((n_total, 2), np.float32) for k in ("ep", "pad", "bass", "drums", "pluck", "bell")}
    kicks = []
    lp_points = []

    def note(name):
        return hz(N(name))

    for (t0, t1, style, prog_name, bar_idx0) in sections():
        ep_l, pad_l, bass_l, kick_l, sn_l, hat_l, sh_l, pl_l, lp = STYLES[style]
        prog = {"main": PROG_MAIN, "calm": PROG_CALM}[prog_name]
        lp_points.append((t0, lp))
        nbars = int(np.ceil((t1 - t0) / BAR - 1e-6))
        if verbose:
            print(f"  {t0:7.2f}-{t1:7.2f}  bars {bar_idx0 + 1:2d}-{bar_idx0 + nbars:2d}  {style:7s} {prog_name}")
        for b in range(nbars):
            bar = bar_idx0 + b
            t_bar = t0 + b * BAR
            left = (t1 - t_bar) / BEAT                      # beats of this bar that belong to the section
            ci = bar % 4
            bass_name, voicing = prog[ci]
            freqs = [note(v) for v in voicing]
            if pad_l > 0:
                x = ae.pad_chord(freqs + [note(bass_name) * 2], min(BAR, left * BEAT) * 1.02, 0.9 * pad_l)
                ae.add(buses["pad"], x, t_bar * SR)
            if ep_l > 0:
                pattern = [(0.0, 1.4, 0.75), (1.5, 0.45, 0.45), (2.5, 1.2, 0.6)]
                if bar % 2 == 1:
                    pattern = [(0.0, 1.9, 0.7), (2.75, 1.0, 0.5)]
                for (bt, ln, vel) in pattern:
                    if bt >= left - 1e-6:
                        continue
                    for k, f in enumerate(freqs):
                        st = humanize(t_bar + bt * BEAT + k * 0.009)
                        x = ae.ep_note(f, ln * BEAT, vel * ep_l * (0.92 + 0.08 * ae.RNG.uniform()))
                        ae.add(buses["ep"], ae.pan(x, -0.25 + 0.17 * k), st * SR)
            if bass_l > 0:
                fb = note(bass_name)
                for (bt, ln, vel) in [(0.0, 1.6, 0.95), (1.75, 0.25, 0.5), (2.5, 1.3, 0.8)]:
                    if bt >= left - 1e-6:
                        continue
                    x = ae.bass_note(fb, ln * BEAT, vel * bass_l)
                    ae.add(buses["bass"], x, humanize(t_bar + bt * BEAT, 0.003) * SR)
            swing = 0.16
            for step in range(16):
                bt = step / 4.0
                if bt >= left - 1e-6:
                    break
                if step % 2 == 1:
                    bt += swing / 4.0
                ts = t_bar + bt * BEAT
                if kick_l > 0 and step in ((0, 10) if bar % 2 == 0 else (0, 7, 10)):
                    v = (1.0 if step == 0 else 0.7) * kick_l
                    ae.add(buses["drums"], ae.kick(v), (ts if step == 0 else humanize(ts, 0.002)) * SR)
                    kicks.append(ts * SR)
                if sn_l > 0 and step in (4, 12):
                    c_, s_ = ae.clap(0.7 * sn_l), ae.snare(0.45 * sn_l)
                    x = np.zeros(max(len(c_), len(s_)), np.float32)
                    x[: len(c_)] += c_
                    x[: len(s_)] += s_
                    ae.add(buses["drums"], ae.pan(x, 0.05), humanize(ts, 0.003) * SR)
                if hat_l > 0 and step % 2 == 0:
                    v = (0.5 if step % 4 == 0 else 0.8) * hat_l * ae.RNG.uniform(0.8, 1.0)
                    ae.add(buses["drums"], ae.pan(ae.hat(v, False), 0.3), humanize(ts, 0.003) * SR)
                if sh_l > 0:
                    v = (0.9 if step % 4 == 2 else 0.45) * sh_l * ae.RNG.uniform(0.7, 1.0)
                    ae.add(buses["drums"], ae.pan(ae.shaker(v), -0.35), humanize(ts, 0.004) * SR)
            if pl_l > 0 and bar % 4 == 0:
                motif = MOTIF if (bar // 4) % 2 == 0 else MOTIF_B
                for (bt, nm, vel) in motif:
                    if t_bar + bt * BEAT >= t1 - 1e-6:
                        continue
                    st = t_bar + bt * BEAT if bt == 0 else humanize(t_bar + bt * BEAT, 0.004)
                    x = ae.pluck_note(note(nm), vel * pl_l, 1.8)
                    ae.add(buses["pluck"], ae.pan(x, 0.35 if int(bt) % 2 else -0.15), st * SR)

    # the fill under each chapter card: two beats, no drums, a pluck run that climbs into the downbeat
    for tc in fills():
        bass_name, voicing = FILL_CHORD
        x = ae.pad_chord([note(v) for v in voicing] + [note(bass_name) * 2], 2 * BEAT * 1.02, 0.85)
        ae.add(buses["pad"], x, tc * SR)
        for k, v in enumerate(voicing):
            ae.add(buses["ep"], ae.pan(ae.ep_note(note(v), 1.8 * BEAT, 0.55), -0.25 + 0.17 * k), (tc + k * 0.012) * SR)
        for (bt, nm, vel) in FILL_RUN:
            ae.add(buses["pluck"], ae.pan(ae.pluck_note(note(nm), vel, 1.6), -0.2 + 0.25 * bt), (tc + bt * BEAT) * SR)
        for i in range(8):                                   # a shaker that swells through the second beat
            ae.add(buses["drums"], ae.pan(ae.shaker(0.25 + 0.07 * i), -0.3), (tc + BEAT + i * BEAT / 8) * SR)
    # a small bell on every chapter's downbeat: the ear learns that a chapter starts here
    for (n, down, _end) in chapters():
        ae.add(buses["bell"], ae.pan(ae.bell_note(note("D6"), 0.5, 2.4), 0.1), down * SR)
        ae.add(buses["bell"], ae.pan(ae.bell_note(note("A5"), 0.3, 2.0), -0.2), down * SR)

    # ---------------- mixing (the skill's chain, compose.py) ----------------
    n = n_total
    # a triplet-rate shimmer on the electric piano, tied to the tempo
    sc, ir, ep, pad, bass, drums, pluck = bus_chain(buses, kicks, n, BEAT, 0.26,
                                                    lambda tt: 0.16 * np.sin(2 * np.pi * (BPM / 60.0) * 3.0 * tt), 10500)
    bell = ae.reverb(buses["bell"], ir, 0.5)
    mix = (ep * 0.62 + pad * 0.5) * sc + bass * 0.38 * sc + drums * 0.50 + pluck * 0.46 + bell * 0.16
    mix = ae.butter(mix, "highpass", 32)
    vinyl(mix, 16.0, 0.04, 0.002)
    # master low-pass automation: glides over half a bar into each section; the fills open up
    cut = glide(lp_points, n, BAR)
    for tc in fills():
        s, e = int(tc * SR), int((tc + 2 * BEAT) * SR)
        cut[s:e] = np.maximum(cut[s:e], 9000.0)
    mix = sweep_lowpass(mix, cut)

    fi = int(0.03 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]
    end = int(TOTAL * SR)
    fo = int(END_HOLD * SR)
    mix[end - fo:end] *= np.linspace(1, 0, fo)[:, None] ** 1.5
    mix = mix[:end]
    return glue(mix)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    proj = os.path.abspath(sys.argv[1])
    os.environ["EDIT_PROJECT"] = proj
    os.environ["EDIT_FMT"] = "youtube"
    os.environ["EDIT_SS"] = "1"
    import story  # noqa: E402
    story.load_design()
    import vlog  # noqa: E402
    load(proj, vlog.ARRANGE)
    print(f"{BPM:.2f} BPM, beat {BEAT:.4f} s, bar {BAR:.4f} s, total {TOTAL:.2f} s")
    for (n, down, end) in chapters():
        print(f"chapter {n}: downbeat {down:7.2f} s, music to {end:7.2f} s = {(end - down) / BAR:.2f} bars")
    x = render(verbose=True)
    if len(sys.argv) > 2:
        from scipy.io import wavfile
        wavfile.write(sys.argv[2], SR, x)
        print("wrote", sys.argv[2], round(len(x) / SR, 2), "s")
