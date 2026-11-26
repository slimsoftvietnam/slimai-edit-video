"""Modern blockbuster trailer sounds (the motion style, references/motion.md; first made for the Agent Skill series,
approved on tập 16). A design imports this module; it wraps trailer_score.render so that the new kinds below
render into the same three stems, and every existing kind still goes through the skill's own code.

New score kinds (t in output seconds; gain defaults to 1):
  hits   hit(length=3.0, metal=1.0)     hybrid impact: sub thump, punch, metallic ring, crack, big tail
         subdrop(length=1.6)            808-style sub sweep down, for under a slam
         shepard(length=4.0)            Shepard-tone riser (endless rise) with an accelerating pulse; t = its end
         whoosh_up(length=1.2)          rising filtered noise into a hit; t = its end
         stutter(length=0.5, rate=16)   gated noise and chord chops, the glitch before a drop
         rev_hit(length=0.8)            reversed swell into a hit at t
  music  pulse(until, bpm=124, root=38, open_from=None)   16th saw arpeggio + sub, side-chain pumped; filter opens
         beat(until, bpm=124, fill=True)                  808 kick, roomy clap, 16th hats, tom fill on the 4th bar
         drone(dur, root=26)                              dark detuned saws and sub with a slow swell
  perc   ticks(until, bpm=124)          fast metallic 16th ticks (watch-like tension)
"""
import numpy as np

import audio_engine as ae
import trailer_score as TS

SR = ae.SR
_R = np.random.default_rng(23)
_KNOWN = {"boom", "braam", "taiko", "riser", "swell", "crash", "heartbeat", "clock", "pad", "ostinato", "drive",
          "bells", "piano"}


def S(t):
    return int(round(t * SR))


def st(x):
    return x if x.ndim == 2 else np.stack([x, x], axis=1)


def _env(n, att, dec):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(att, 1e-4)) * np.exp(-t / dec)


# ----------------------------------------------------------------------------
# hits
# ----------------------------------------------------------------------------
def hit(vel=1.0, length=3.0, metal=1.0):
    n = S(length)
    t = np.arange(n) / SR
    sub = np.sin(2 * np.pi * np.cumsum(32 + 58 * np.exp(-t / 0.07)) / SR) * np.exp(-t / 0.9)
    punch = ae.butter(_R.standard_normal(n), "lowpass", 1400) * np.exp(-t / 0.06) * 0.9
    body = ae.butter(_R.standard_normal(n), "bandpass", [180, 900]) * np.exp(-t / 0.25) * 0.35
    crack = ae.butter(_R.standard_normal(n), "highpass", 3200) * np.exp(-t / 0.012) * 0.5
    ring = np.zeros(n)
    for f, d in ((233.1, 1.4), (523.0, 1.0), (1187.0, 0.7), (1873.0, 0.5), (2711.0, 0.35), (3529.0, 0.25)):
        ring += np.sin(2 * np.pi * f * (1 + _R.uniform(-0.004, 0.004)) * t + _R.uniform(0, 6.28)) * np.exp(-t / d)
    ring *= 0.16 * metal * np.minimum(1, t / 0.002)
    y = ae.soft_clip(sub * 1.25 + punch + body + crack + ring, 1.6)
    y = st(y.astype(np.float32))
    y[:, 1] = np.roll(y[:, 1], 37)
    return ae.reverb(y, TS.ir("big"), 0.32) * 0.8 * vel


def subdrop(vel=1.0, length=1.6):
    n = S(length)
    t = np.arange(n) / SR
    f = 28 + 92 * np.exp(-t / (length * 0.28))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, t / 0.004) * np.exp(-t / (length * 0.55))
    y = np.tanh(y * 2.2) / np.tanh(2.2)
    return st(ae.butter(y, "lowpass", 220).astype(np.float32)) * 0.9 * vel


def shepard(vel=1.0, length=4.0):
    """an endlessly rising tone: octave-spaced partials glide up one octave, faded in and out across the range."""
    n = S(length)
    t = np.arange(n) / SR
    prog = t / length
    y = np.zeros(n)
    for k in range(7):
        pos = (k + prog) / 7.0                     # 0..1 across the band, each partial climbs one slot
        f = 55 * 2 ** (pos * 7)
        amp = 0.5 - 0.5 * np.cos(2 * np.pi * np.clip(pos, 0, 1))
        y += amp * np.sin(2 * np.pi * np.cumsum(f) / SR)
    rate = 4 + 18 * prog ** 2                      # the pulse speeds up into the end
    puls = 0.55 + 0.45 * np.sin(2 * np.pi * np.cumsum(rate) / SR)
    nz = ae.butter(_R.standard_normal(n), "bandpass", [900, 7000]) * prog ** 2 * 0.25
    y = (y / 3.0 * puls + nz) * (0.15 + 0.85 * prog ** 1.6)
    return st(ae.butter(y, "highpass", 60).astype(np.float32)) * 0.7 * vel


def whoosh_up(vel=1.0, length=1.2):
    n = S(length)
    t = np.arange(n) / SR
    prog = t / length
    nz = _R.standard_normal(n)
    out = np.zeros(n)
    edges = np.linspace(0, n, 13).astype(int)
    for a, b in zip(edges[:-1], edges[1:]):        # a band-pass that climbs in steps, smoothed by the envelope
        fc = 400 * 2 ** (4.2 * (a / n))
        out[a:b] = ae.butter(nz, "bandpass", [fc * 0.6, min(fc * 1.8, 20000)])[a:b]
    y = out * prog ** 2.2
    y = st(y.astype(np.float32))
    y[:, 0] *= 1 - 0.4 * prog
    y[:, 1] *= 0.6 + 0.4 * prog
    return y * 0.8 * vel


def stutter(vel=1.0, length=0.5, rate=16):
    n = S(length)
    t = np.arange(n) / SR
    src = ae.butter(_R.standard_normal(n), "bandpass", [300, 4000]) * 0.6
    for m in (38, 45, 50, 57):
        src += 0.25 * TS.ae._wt(ae.hz(m), n, ae.TAB_BRIGHT, _R.uniform())
    gate = (np.floor(t * rate) % 2 == 0).astype(float)
    gate = np.convolve(gate, np.ones(48) / 48, mode="same")
    return st((ae.soft_clip(src * gate, 1.4)).astype(np.float32)) * 0.7 * vel


def rev_hit(vel=1.0, length=0.8):
    return ae.sfx_reverse_swell(length, 1.0) * vel


# ----------------------------------------------------------------------------
# music beds
# ----------------------------------------------------------------------------
def pulse(mu, t0, until, bpm=124, root=38, open_from=None, gain=1.0):
    s16 = 60 / bpm / 4
    pattern = [0, 12, 7, 12, 0, 12, 10, 12, 0, 12, 7, 12, 3, 12, 10, 15]
    k = 0
    tt = t0
    while tt < until - 0.02:
        m = root + pattern[k % 16]
        n = S(s16 * 1.4)
        tn = np.arange(n) / SR
        f = ae.hz(m)
        y = ae._wt(f, n, ae.TAB_BRIGHT, _R.uniform()) + 0.6 * ae._wt(f * 1.006, n, ae.TAB_DARK, _R.uniform())
        prog = 0.0 if open_from is None else np.clip((tt - open_from) / max(0.5, until - open_from), 0, 1)
        cutoff = 500 + 3200 * prog
        y = ae.butter(y * np.minimum(1, tn / 0.003) * np.exp(-tn / (s16 * 0.9)), "lowpass", cutoff)
        beat_pos = (k % 4) / 4.0                      # side-chain: quiet on the beat, back by the next 16th
        sc = 0.35 + 0.65 * min(1.0, beat_pos * 4 / 1.5 + 0.15)
        ae.add(mu, st((y * 0.32 * sc * gain).astype(np.float32)), S(tt))
        if k % 4 == 0:                                 # a sub note on every beat
            nb = S(60 / bpm)
            tb = np.arange(nb) / SR
            sb = np.sin(2 * np.pi * ae.hz(root - 12) * tb) * np.minimum(1, tb / 0.01) * np.exp(-tb / 0.32)
            ae.add(mu, st((sb * 0.5 * gain).astype(np.float32)), S(tt))
        k += 1
        tt = t0 + k * s16


def kick808(vel=1.0):
    n = S(0.6)
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * np.cumsum(45 + 110 * np.exp(-t / 0.03)) / SR) * np.exp(-t / 0.32)
    y += ae.butter(_R.standard_normal(n), "highpass", 2000) * np.exp(-t / 0.004) * 0.3
    return st((np.tanh(y * 1.8) * 0.9 * vel).astype(np.float32))


def clap_big(vel=1.0):
    x = st(ae.clap(1.0)) if ae.clap(1.0).ndim == 1 else ae.clap(1.0)
    return ae.reverb(x.astype(np.float32), TS.ir("big"), 0.4) * vel


def beat(mu, t0, until, bpm=124, fill=True, gain=1.0):
    s16 = 60 / bpm / 4
    bar = 16 * s16
    kicks = {0: 1.0, 8: 0.9, 10: 0.6}
    b = 0
    while t0 + b * bar < until - 0.05:
        tb = t0 + b * bar
        last = fill and b % 4 == 3
        for k in range(16):
            tn = tb + k * s16
            if tn >= until - 0.03:
                break
            if k in kicks:
                ae.add(mu, kick808(kicks[k] * gain), S(tn))
            if k in (4, 12):
                ae.add(mu, clap_big(0.7 * gain), S(tn))
            ae.add(mu, st(ae.hat(0.35 if k % 2 == 0 else 0.18)) * gain, S(tn))
            if last and k >= 12:
                ae.add(mu, TS.taiko(0.55 * gain, 160 - 12 * (k - 12), 70, 0.5), S(tn))
        b += 1


def drone(dur, root=26, vel=1.0):
    n = S(dur)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for d in (-0.006, 0.0, 0.005):
        y += ae._wt(ae.hz(root) * (1 + d), n, ae.TAB_DARK, _R.uniform())
    y = ae.butter(y, "lowpass", 320) * 0.4 + 0.5 * np.sin(2 * np.pi * ae.hz(root) / 2 * t)
    swell = np.minimum(1, t / max(0.3, dur * 0.35)) * np.minimum(1, (dur - t) / 0.4).clip(0, 1)
    lfo = 0.8 + 0.2 * np.sin(2 * np.pi * 0.25 * t)
    return st((y * swell * lfo * 0.6 * vel).astype(np.float32))


def ticks(pc, t0, until, bpm=124, gain=1.0):
    s16 = 60 / bpm / 4
    k = 0
    while t0 + k * s16 < until:
        n = S(0.03)
        tn = np.arange(n) / SR
        f = 5200 if k % 4 == 0 else 4100
        y = np.sin(2 * np.pi * f * tn) * np.exp(-tn / 0.004) + ae.butter(_R.standard_normal(n), "highpass", 6000) * \
            np.exp(-tn / 0.002) * 0.5
        ae.add(pc, st((y * (0.5 if k % 4 == 0 else 0.3) * gain).astype(np.float32)), S(t0 + k * s16))
        k += 1


# ----------------------------------------------------------------------------
# the wrapper: new kinds here, the rest through the skill's own render
# ----------------------------------------------------------------------------
def _render(events, total):
    std = [e for e in events if e[1] in _KNOWN]
    mine = [e for e in events if e[1] not in _KNOWN]
    mu, hi, pc, light = _ORIG(std, total)
    for (t, kind, kw) in sorted(mine, key=lambda e: e[0]):
        g = kw.get("gain", 1.0)
        if kind == "hit":
            ae.add(hi, hit(g, kw.get("length", 3.0), kw.get("metal", 1.0)), S(t))
        elif kind == "subdrop":
            ae.add(hi, subdrop(g, kw.get("length", 1.6)), S(t))
        elif kind == "shepard":
            ln = kw.get("length", 4.0)
            ae.add(hi, shepard(g, ln), S(t - ln))
        elif kind == "whoosh_up":
            ln = kw.get("length", 1.2)
            ae.add(hi, whoosh_up(g, ln), S(t - ln))
        elif kind == "stutter":
            ae.add(hi, stutter(g, kw.get("length", 0.5), kw.get("rate", 16)), S(t))
        elif kind == "rev_hit":
            ln = kw.get("length", 0.8)
            ae.add(hi, rev_hit(g, ln), S(t - ln))
        elif kind == "pulse":
            pulse(mu, t, kw["until"], kw.get("bpm", 124), kw.get("root", 38), kw.get("open_from"), g)
            light.append((t, kw["until"]))
        elif kind == "beat":
            beat(mu, t, kw["until"], kw.get("bpm", 124), kw.get("fill", True), g)
            light.append((t, kw["until"]))
        elif kind == "drone":
            ae.add(mu, drone(kw["dur"], kw.get("root", 26), g), S(t))
        elif kind == "ticks":
            ticks(pc, t, kw["until"], kw.get("bpm", 124), g)
        else:
            raise ValueError(f"unknown score event: {kind}")
    return mu, hi, pc, light


if not getattr(TS.render, "_modern", False):
    _ORIG = TS.render
    TS.render = _render
    TS.render._modern = True
else:
    _ORIG = TS.render.__globals__["_ORIG"]
