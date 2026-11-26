"""A licensed track as the score of a trailer or motion edit, cut on its own bars (references/motion.md).

The design registers each track it uses, decoded to a 48 kHz wav inside the project (download it into a folder of its
own first, and only from the licence page the user chose):

    import track_music as TM
    TM.add_track("banger", "music_work/trapbanger.wav", bar0=2.282, bpm=96.69)   # first downbeat (s), tempo
    score("track", t, track="banger", src_t=TM.bar_of("banger", 36), dur=4.0, fade_in=0.004, fade_out=0.04)

music_analyse.py prints a track's tempo, its bars and their energy, to find the downbeat and the sections (intro,
build, drop, break). Score kinds (t in output seconds), into the music stem (ducked under the voice like any music):
  track(src_t, dur, gain=1.0, fade_in=0.02, fade_out=0.08, track=..., hp=None, boost=(), light=False)
        one piece of the track from src_t (source s); hp=(f0, f1[, curve]) a rising high-pass over it (a build);
        boost=[(t0, t1, gain)] a lift inside it; light=True lets it duck less under the voice
  roll(length=4.0, bpm=86.99, gain=1.0)   a snare roll that accelerates into t (the stop before a drop)
"""
import os
import wave

import numpy as np

import audio_engine as ae
import trailer_score as TS

SR = ae.SR
_CACHE = {}
TRACKS = {}      # name -> (wav path, first downbeat in s, bar length in s)


def add_track(name, path, bar0, bpm, beats_per_bar=4):
    """register a decoded 48 kHz wav (absolute, or relative to the project folder)"""
    import engine as E
    p = path if os.path.isabs(path) else os.path.join(E.PROJECT, path)
    TRACKS[name] = (p, float(bar0), beats_per_bar * 60.0 / float(bpm))
    return TRACKS[name]


def bar_of(track, n):
    path, b0, bar = TRACKS[track]
    return b0 + n * bar


def _load(track):
    if track not in _CACHE:
        w = wave.open(TRACKS[track][0])
        assert w.getframerate() == SR, "decode the track at 48 kHz (ffmpeg -ar 48000)"
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32).reshape(-1, w.getnchannels())
        _CACHE[track] = (x / 32768.0) if x.shape[1] == 2 else np.repeat(x / 32768.0, 2, axis=1)
    return _CACHE[track]


def hp_sweep(y, f0, f1, curve=2.0):
    """a rising high-pass across y (the build: the bass drains away so the drop lands harder), by crossfading six
    fixed high-pass versions; f0/f1 in Hz, curve > 1 keeps most of the rise for the end"""
    n = len(y)
    cuts = np.geomspace(max(f0, 15.0), f1, 6)
    ys = [ae.butter(y, "highpass", c).astype(np.float32) for c in cuts]
    pos = (np.linspace(0, 1, n) ** curve) * 5
    out = np.zeros_like(y)
    for i in range(6):
        w = np.clip(1 - np.abs(pos - i), 0, 1)[:, None]
        out += ys[i] * w
    return out


def roll(length=4.0, bpm=86.99, vel=1.0):
    """a snare roll that accelerates (eighths, sixteenths, then thirty-seconds) and swells into its end"""
    beat = 60.0 / bpm
    n = int(length * SR) + SR
    out = np.zeros((n, 2), np.float32)
    t = 0.0
    while t < length - 0.01:
        u = t / length
        step = beat / 2 if u < 0.4 else (beat / 4 if u < 0.75 else beat / 8)
        v = (0.35 + 0.65 * u ** 1.5) * vel
        hit = ae.snare(v)
        ae.add(out, np.stack([hit * (1 - 0.15 * np.sin(9 * t)), hit * (1 + 0.15 * np.sin(9 * t))], axis=1), int(t * SR))
        t += step
    room = ae.make_ir(1.2, 0.01, 0.5)
    y = ae.reverb(out, room, 0.22)[:int(length * SR)]
    y[-int(0.015 * SR):] *= np.linspace(1, 0, int(0.015 * SR))[:, None]     # dead stop: the silence stays silent
    return y


def piece(src_t, dur, gain=1.0, fade_in=0.02, fade_out=0.08, track=None, hp=None):
    x = _load(track)
    s0 = int(round(src_t * SR))
    n = int(round(dur * SR))
    y = x[s0:s0 + n].copy()
    if len(y) < n:
        y = np.pad(y, ((0, n - len(y)), (0, 0)))
    if hp:
        y = hp_sweep(y, hp[0], hp[1], hp[2] if len(hp) > 2 else 2.0)
    env = np.ones(n, np.float32)
    fi, fo = int(fade_in * SR), int(fade_out * SR)
    if fi > 0:
        env[:fi] = np.sin(0.5 * np.pi * np.linspace(0, 1, fi)) ** 2       # equal-power ramps for crossfades
    if fo > 0:
        env[-fo:] *= np.cos(0.5 * np.pi * np.linspace(0, 1, fo)) ** 2
    return (y * env[:, None] * gain).astype(np.float32)


def _render(events, total):
    mine = [e for e in events if e[1] == "track"]
    rolls = [e for e in events if e[1] == "roll"]
    rest = [e for e in events if e[1] not in ("track", "roll")]
    mu, hi, pc, light = _PREV(rest, total)
    for (t, _k, kw) in rolls:                          # t = where the roll ends (on the stop before a drop)
        ln = kw.get("length", 4.0)
        ae.add(hi, (roll(ln, kw.get("bpm", 86.99), 1.0) * kw.get("gain", 1.0)).astype(np.float32), int(round((t - ln) * SR)))
    for (t, _k, kw) in sorted(mine, key=lambda e: e[0]):
        y = piece(kw["src_t"], kw["dur"], kw.get("gain", 1.0), kw.get("fade_in", 0.02), kw.get("fade_out", 0.08),
                  kw["track"], kw.get("hp"))
        for (ba, bb, bg) in kw.get("boost", ()):
            tt = t + np.arange(len(y)) / SR
            w_ = np.clip(np.minimum((tt - ba) / 0.3 + 0.5, (bb - tt) / 0.3 + 0.5), 0, 1)
            y *= (1 + (bg - 1) * (0.5 - 0.5 * np.cos(np.pi * w_)))[:, None].astype(np.float32)
        ae.add(mu, y, int(round(t * SR)))
        if kw.get("light"):
            light.append((t, t + kw["dur"]))
    return mu, hi, pc, light


if not getattr(TS.render, "_track", False):
    _PREV = TS.render
    TS.render = _render
    TS.render._track = True
else:
    _PREV = TS.render.__globals__["_PREV"]
