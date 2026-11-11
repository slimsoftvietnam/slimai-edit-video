"""Trailer score, synthesised in code (no samples). design.py registers events with story.score(kind, t, **kw);
audio_mix.py calls render() and mixes the three stems it returns: music (ducked under the voice), hits and perc
(kept whole, so place hits between lines or on a word onset). See references/trailer.md.

Kinds, by stem (t in output seconds; gain defaults to 1):
  hits   boom(length=2.6)              sub boom + crack
         braam(chord, length=3.0, bright=0.95)   detuned low brass cluster, the trailer "BWAAM"
         taiko(f0=118, f1=54, length=1.0)        drum hit, a cut or a step
         riser(length=2.0)             t = where it ENDS: lands on a hit or a hard cut
         swell(length=0.5)             reversed noise swell, t = where it ends
         crash(length=3.0)
  perc   heartbeat(until, bpm=72)      clock(until, bpm=100, fast_from=None, loud_from=None): 8ths, 16ths from fast_from
  music  pad(notes, dur, bright=0.22, att=0.5, rel=1.4, trem=0)        trem = 11 Hz tremolo depth
         ostinato(until, bpm=100, prog, pattern, fast_from=None)  spiccato strings, one chord per bar, plus a pad
         drive(until, bpm=120, chords)  taiko pattern, hats, 16th strings, a brass stab per bar; ducking is
                                        lighter while it plays
         bells(notes, step=0.09)       piano(notes=[(dt, midi), ...])
Chords and notes are MIDI numbers; prog / chords are [(root, [chord notes]), ...] (D_MIN, BB_MAJ, D_MAJ below).
"""
import numpy as np

import audio_engine as ae

SR = ae.SR
RNG = np.random.default_rng(11)
_IR = {}


def ir(name):
    """reverb impulses, built on first use (design.py imports the chord names below while rendering pictures)."""
    if name not in _IR:
        _IR[name] = ae.make_ir(3.0, 0.025, 0.45) if name == "big" else ae.make_ir(1.1, 0.010, 0.55)
    return _IR[name]


D_MIN = [26, 33, 38, 41, 45]       # D1 A1 D2 F2 A2
BB_MAJ = [22, 29, 34, 38, 41]      # Bb0 F1 Bb1 D2 F2
D_MAJ = [26, 33, 38, 42, 45]       # D1 A1 D2 F#2 A2
PROG_OLD = [(38, [26, 33, 38, 41]), (34, [22, 29, 34, 38]), (31, [19, 26, 31, 34]), (33, [21, 28, 33, 37])]  # i VI iv V
PROG_EPIC = [(38, [26, 33, 38, 45]), (34, [22, 29, 34, 41]), (36, [24, 31, 36, 43]), (38, [26, 33, 38, 45])]  # I bVI bVII I
PATTERN = [0, 0, 12, 0, 7, 0, 12, 10]


def S(t):
    return int(round(t * SR))


def st(x):
    return x if x.ndim == 2 else np.stack([x, x], axis=1)


# ----------------------------------------------------------------------------
# instruments
# ----------------------------------------------------------------------------
def braam(midis, length=3.0, vel=1.0, bright_peak=0.95):
    n = S(length)
    t = np.arange(n) / SR
    bright = (0.2 + (bright_peak - 0.2) * np.exp(-t / 0.75)) * np.minimum(1, t / 0.035)
    amp = np.minimum(1, t / 0.02) * np.exp(-t / (length * 0.45))
    out = np.zeros((n, 2))
    for m in midis:
        f = ae.hz(m)
        for d, p in ((-0.007, -0.7), (-0.002, -0.2), (0.003, 0.25), (0.008, 0.7)):
            ph = RNG.uniform()
            y = ae._wt(f * (1 + d), n, ae.TAB_DARK, ph) * (1 - bright) + ae._wt(f * (1 + d), n, ae.TAB_BRIGHT, ph) * bright
            out += ae.pan(y * amp, p)
    sub = np.sin(2 * np.pi * ae.hz(midis[0]) * t) * np.minimum(1, t / 0.015) * np.exp(-t / (length * 0.4))
    # level from the RMS of the attack, not the peak: with random phases the peak of twenty detuned saws swings,
    # and peak-normalised braams came out up to 6 dB apart
    head = out[: S(min(0.5, length))]
    out = out * (0.28 / (np.sqrt(np.mean(head ** 2)) + 1e-9)) + 0.7 * sub[:, None]
    out = ae.soft_clip(out * 1.4, 2.4)
    out = ae.butter(out, "lowpass", 4200)
    return ae.reverb(out.astype(np.float32), ir("big"), 0.3) * vel


def boom(vel=1.0, length=2.6):
    x = ae.sfx_impact(1.0, length)
    t = np.arange(len(x)) / SR
    sub = np.sin(2 * np.pi * np.cumsum(30 + 40 * np.exp(-t / 0.12)) / SR) * np.exp(-t / 0.9)
    return ae.reverb(st((x + 0.6 * sub).astype(np.float32)), ir("big"), 0.22) * vel


def taiko(vel=1.0, f0=118, f1=54, length=1.0):
    n = S(length)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t / 0.035)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.3)
    skin = ae.butter(RNG.standard_normal(n), "bandpass", [140, 1400]) * np.exp(-t / 0.028) * 0.55
    y = ae.soft_clip((body + skin) * 1.3, 1.6)
    return ae.reverb(st(y.astype(np.float32)), ir("room"), 0.3) * vel


def heartbeat(vel=1.0):
    n = S(0.7)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for d, a in ((0.0, 1.0), (0.18, 0.72)):
        tt = t - d
        m = tt >= 0
        y[m] += a * np.sin(2 * np.pi * np.cumsum(46 + 34 * np.exp(-tt[m] / 0.02)) / SR) * np.exp(-tt[m] / 0.1)
    return st(ae.butter(y, "lowpass", 180).astype(np.float32)) * vel


def clock_tick(hi=True, vel=1.0):
    n = S(0.07)
    t = np.arange(n) / SR
    f, body = (3300, 950) if hi else (2500, 720)
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.005)
    y += ae.butter(RNG.standard_normal(n), "bandpass", [2000, 7500]) * np.exp(-t / 0.003) * 0.6
    y += 0.45 * np.sin(2 * np.pi * body * t) * np.exp(-t / 0.014)
    return st((y * 0.5).astype(np.float32)) * vel


def spic(m, vel=1.0, length=0.15):
    n = S(length + 0.1)
    t = np.arange(n) / SR
    env = np.minimum(1, t / 0.005) * np.exp(-t / (length * 0.55))
    f = ae.hz(m)
    y = ae._wt(f, n, ae.TAB_BRIGHT, RNG.uniform()) * 0.6 + ae._wt(f * 1.004, n, ae.TAB_DARK, RNG.uniform()) * 0.5
    y += 0.5 * ae._wt(f / 2, n, ae.TAB_DARK, RNG.uniform())
    return st(ae.butter(y * env, "lowpass", 2400).astype(np.float32)) * vel


def pad(midis, dur, vel=1.0, bright=0.22, att=0.5, rel=1.4, trem=0.0):
    x = ae.pad_chord([ae.hz(m) for m in midis], dur, vel, bright=bright, att=att, rel=rel)
    if trem:
        t = np.arange(len(x)) / SR
        x = x * (1 - trem + trem * (0.5 + 0.5 * np.sin(2 * np.pi * 11 * t)))[:, None]
    return x


def crash(vel=1.0, length=3.0):
    n = S(length)
    t = np.arange(n) / SR
    y = ae.butter(RNG.standard_normal(n), "highpass", 3000) * np.exp(-t / 0.9) * np.minimum(1, t / 0.002)
    return ae.reverb(np.stack([y, np.roll(y, 61)], axis=1).astype(np.float32) * 0.25, ir("big"), 0.3) * vel


# ----------------------------------------------------------------------------
# patterns
# ----------------------------------------------------------------------------
def ostinato(mu, t0, until, bpm=100, prog=PROG_OLD, pattern=PATTERN, fast_from=None, gain=1.0):
    e8 = 60 / bpm / 2
    bar = 4 * 60 / bpm
    for b in range(int(np.ceil((until - t0) / bar))):
        root, chord = prog[b % len(prog)]
        ae.add(mu, pad(chord, bar, 0.75 * gain, bright=0.18, att=0.3, rel=0.4), S(t0 + b * bar))
        for k, iv in enumerate(pattern):
            tn = t0 + b * bar + k * e8
            if tn >= until:
                break
            ae.add(mu, spic(root + iv, (0.55 + (0.15 if k % 4 == 0 else 0.0)) * gain), S(tn))
            if fast_from is not None and tn >= fast_from:     # density doubles as the montage speeds up
                ae.add(mu, spic(root + iv + 12, 0.3 * gain), S(tn + e8 / 2))


def drive(mu, t0, until, bpm=120, chords=PROG_EPIC, gain=1.0):
    s16 = 60 / bpm / 4
    bar = 16 * s16
    low = {0: 1.0, 6: 0.7, 8: 0.9, 11: 0.7}
    high = {4: 0.6, 12: 0.6, 14: 0.5}
    b = 0
    while t0 + b * bar < until - 0.05:
        root, chord = chords[b % len(chords)]
        tb = t0 + b * bar
        ae.add(mu, braam(chord, min(1.4, until - tb), 0.35 * gain, bright_peak=0.7), S(tb))
        for k in range(16):
            tn = tb + k * s16
            if tn >= until - 0.03:
                break
            if k in low:
                ae.add(mu, taiko(0.55 * low[k] * gain, 110, 52, 0.6), S(tn))
            if k in high:
                ae.add(mu, taiko(0.4 * high[k] * gain, 210, 130, 0.4), S(tn))
            ae.add(mu, st(ae.hat(0.5 if k % 2 == 0 else 0.25)) * gain, S(tn))
            ae.add(mu, spic(root + (12 if k % 4 == 2 else (7 if k % 4 == 3 else 0)), 0.45 * gain, 0.1), S(tn))
        b += 1


def render(events, total):
    """events: story.SCORE. -> music, hits, perc (float32 stereo, `total` s) and the windows of lighter ducking."""
    n = S(total)
    mu, hi, pc = (np.zeros((n, 2), np.float32) for _ in range(3))
    light = []
    for (t, kind, kw) in sorted(events, key=lambda e: e[0]):
        g = kw.get("gain", 1.0)
        if kind == "boom":
            ae.add(hi, boom(g, kw.get("length", 2.6)), S(t))
        elif kind == "braam":
            ae.add(hi, braam(kw["chord"], kw.get("length", 3.0), g, kw.get("bright", 0.95)), S(t))
        elif kind == "taiko":
            ae.add(hi, taiko(g, kw.get("f0", 118), kw.get("f1", 54), kw.get("length", 1.0)), S(t))
        elif kind == "riser":
            ln = kw.get("length", 2.0)
            ae.add(hi, ae.sfx_riser(ln, 1.0) * g, S(t - ln))
        elif kind == "swell":
            ln = kw.get("length", 0.5)
            ae.add(hi, ae.sfx_reverse_swell(ln, 1.0) * g, S(t - ln))
        elif kind == "crash":
            ae.add(hi, crash(g, kw.get("length", 3.0)), S(t))
        elif kind == "heartbeat":
            tt = t
            while tt < kw["until"]:
                ae.add(pc, heartbeat(0.9 * g), S(tt))
                tt += 60 / kw.get("bpm", 72)
        elif kind == "clock":
            e8 = 60 / kw.get("bpm", 100) / 2
            fast, loud = kw.get("fast_from"), kw.get("loud_from")
            tt, i = t, 0
            while tt < kw["until"]:
                ae.add(pc, clock_tick(i % 2 == 0, (1.0 if loud is not None and tt >= loud else 0.75) * g), S(tt))
                i += 1
                tt += e8 / 2 if fast is not None and tt >= fast else e8
        elif kind == "pad":
            ae.add(mu, pad(kw["notes"], kw["dur"], g, kw.get("bright", 0.22), kw.get("att", 0.5), kw.get("rel", 1.4),
                           kw.get("trem", 0.0)), S(t))
        elif kind == "ostinato":
            ostinato(mu, t, kw["until"], kw.get("bpm", 100), kw.get("prog", PROG_OLD), kw.get("pattern", PATTERN),
                     kw.get("fast_from"), g)
        elif kind == "drive":
            drive(mu, t, kw["until"], kw.get("bpm", 120), kw.get("chords", PROG_EPIC), g)
            light.append((t, kw["until"]))
        elif kind == "bells":
            for k, m in enumerate(kw["notes"]):
                ae.add(mu, st(ae.bell_note(ae.hz(m), 0.5 * g, 1.6)), S(t + kw.get("step", 0.09) * k))
        elif kind == "piano":
            for (dt, m) in kw["notes"]:
                ae.add(mu, st(ae.ep_note(ae.hz(m), 1.4, 0.55 * g)), S(t + dt))
        else:
            raise ValueError(f"unknown score event: {kind}")
    return ae.reverb(mu, ir("room"), 0.16)[:n], hi, pc, light
