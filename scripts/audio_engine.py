"""Code-synthesised background music + sound effects.

Everything here is generated from oscillators and noise with numpy/scipy:
no samples, no external audio. Output is float32 stereo at 48 kHz.
"""
import numpy as np
from scipy import signal

SR = 48000
RNG = np.random.default_rng(7)


def hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def note_num(name):
    """'F#4' -> midi number."""
    names = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    n = names[name[0]]
    i = 1
    while i < len(name) and name[i] in "#b":
        n += 1 if name[i] == "#" else -1
        i += 1
    return n + 12 * (int(name[i:]) + 1)


def add(buf, x, start):
    """Mix x (n,) or (n,2) into buf (N,2) at sample offset start (clipped)."""
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    s = int(start)
    if s >= len(buf):
        return
    if s < 0:
        x = x[-s:]
        s = 0
    e = min(len(buf), s + len(x))
    buf[s:e] += x[: e - s]


def pan(x, p):
    """Equal-power pan, p in [-1, 1]."""
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1)


def butter(x, kind, f, order=2):
    sos = signal.butter(order, f, btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def soft_clip(x, drive=1.0):
    return np.tanh(x * drive) / np.tanh(drive)


# ----------------------------------------------------------------------------
# Instruments
# ----------------------------------------------------------------------------

def ep_note(f, dur, vel):
    """FM electric piano (Rhodes-like): bark on attack, tine ping, warm decay."""
    rel = 0.45
    n = int((dur + rel) * SR)
    t = np.arange(n) / SR
    decay = 1.9 * (220.0 / f) ** 0.4
    env = np.exp(-t / decay) * np.minimum(1.0, t / 0.003)
    env *= np.where(t < dur, 1.0, np.clip(1 - (t - dur) / rel, 0, 1) ** 2)
    idx = (0.55 + 1.3 * vel) * np.exp(-t / 0.22) + 0.18
    y = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * t))
    y += 0.10 * vel * np.exp(-t / 0.05) * np.sin(2 * np.pi * f * 13.9 * t)
    y += 0.22 * np.exp(-t / (decay * 1.4)) * np.sin(2 * np.pi * f * 2.0 * t + 0.4)
    return (y * env * vel * 0.55).astype(np.float32)


_TABLE_N = 4096


def _saw_table(bright):
    k = np.arange(1, 80)
    ph = np.arange(_TABLE_N) / _TABLE_N
    amp = (1.0 / k) * np.exp(-k / bright)
    tab = (amp[:, None] * np.sin(2 * np.pi * k[:, None] * ph[None, :])).sum(0)
    return (tab / np.abs(tab).max()).astype(np.float32)


TAB_DARK = _saw_table(3.5)
TAB_BRIGHT = _saw_table(9.0)


def _wt(freq, n, table, phase0=0.0):
    ph = (phase0 + np.cumsum(np.full(n, freq / SR))) % 1.0
    pos = ph * _TABLE_N
    i0 = pos.astype(np.int64)
    fr = pos - i0
    return table[i0 % _TABLE_N] * (1 - fr) + table[(i0 + 1) % _TABLE_N] * fr


def pad_chord(freqs, dur, vel, bright=0.35, att=0.9, rel=1.8):
    """Detuned wavetable-saw pad, slow attack, stereo spread."""
    n = int((dur + rel) * SR)
    t = np.arange(n) / SR
    env = np.minimum(1.0, t / att) ** 1.5
    env *= np.where(t < dur, 1.0, np.clip(1 - (t - dur) / rel, 0, 1) ** 1.6)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * t + RNG.uniform(0, 6))
    mix = np.clip(bright * (0.7 + 0.6 * lfo), 0, 1)
    out = np.zeros((n, 2), np.float32)
    for j, f in enumerate(freqs):
        for d, p in ((-0.0045, -0.7), (0.0, 0.0), (0.0052, 0.7)):
            ff = f * (1 + d)
            ph0 = RNG.uniform()
            y = _wt(ff, n, TAB_DARK, ph0) * (1 - mix) + _wt(ff, n, TAB_BRIGHT, ph0) * mix
            out += pan(y * env, p * 0.8)
    return out * (vel * 0.11 / max(1, len(freqs)) ** 0.5)


def bass_note(f, dur, vel):
    rel = 0.09
    n = int((dur + rel) * SR)
    t = np.arange(n) / SR
    env = np.minimum(1.0, t / 0.006) * np.where(t < dur, 1.0, np.clip(1 - (t - dur) / rel, 0, 1))
    env *= 0.82 + 0.18 * np.exp(-t / 0.18)
    y = np.sin(2 * np.pi * f * t) + 0.28 * np.sin(4 * np.pi * f * t) + 0.08 * np.sin(6 * np.pi * f * t)
    return (soft_clip(y * env, 1.4) * vel * 0.5).astype(np.float32)


def pluck_note(f, vel, length=1.6, bright=1.0):
    """Glassy additive pluck (harp/kalimba-ish), exactly in tune."""
    n = int(length * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for k in range(1, 9):
        if f * k > 15000:
            break
        a = (1.0 / k ** 1.35) * (bright if k > 1 else 1.0)
        tau = 0.9 / (1 + 0.55 * (k - 1))
        y += a * np.exp(-t / tau) * np.sin(2 * np.pi * f * k * t + RNG.uniform(0, 0.3))
    y += 0.25 * np.exp(-t / 0.012) * RNG.standard_normal(n) * 0.2  # pick noise
    y *= np.minimum(1.0, t / 0.0015)
    return (y * vel * 0.32).astype(np.float32)


def bell_note(f, vel, length=2.6):
    n = int(length * SR)
    t = np.arange(n) / SR
    idx = 2.2 * np.exp(-t / 0.5)
    y = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * 3.5 * t))
    y *= np.exp(-t / 0.9) * np.minimum(1.0, t / 0.002)
    return (y * vel * 0.25).astype(np.float32)


# ----------------------------------------------------------------------------
# Drums (one-shots)
# ----------------------------------------------------------------------------

def kick(vel=1.0):
    n = int(0.55 * SR)
    t = np.arange(n) / SR
    f = 46 + 95 * np.exp(-t / 0.028)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / 0.21)
    click = butter(RNG.standard_normal(n) * np.exp(-t / 0.0025), "highpass", 1500) * 0.35
    return (soft_clip((body + click) * 1.25, 1.6) * vel * 0.85).astype(np.float32)


def snare(vel=1.0):
    n = int(0.4 * SR)
    t = np.arange(n) / SR
    nz = butter(RNG.standard_normal(n), "bandpass", [900, 7000]) * np.exp(-t / 0.085)
    tone = np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.045) * 0.6
    y = nz * 0.9 + tone
    y = butter(y, "lowpass", 7500)
    return (y * vel * 0.42).astype(np.float32)


def clap(vel=1.0):
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    env = np.zeros(n)
    for d in (0.0, 0.011, 0.022):
        tt = t - d
        env += np.where(tt >= 0, np.exp(-np.clip(tt, 0, None) / 0.008), 0) * 0.6
    env += np.where(t >= 0.03, np.exp(-np.clip(t - 0.03, 0, None) / 0.11), 0)
    y = butter(RNG.standard_normal(n), "bandpass", [1100, 6500]) * env
    return (y * vel * 0.36).astype(np.float32)


def hat(vel=1.0, open_=False):
    n = int((0.35 if open_ else 0.09) * SR)
    t = np.arange(n) / SR
    y = butter(RNG.standard_normal(n), "highpass", 7200, 3)
    y *= np.exp(-t / (0.11 if open_ else 0.022)) * np.minimum(1, t / 0.0008)
    y = butter(y, "lowpass", 14000)
    return (y * vel * 0.20).astype(np.float32)


def shaker(vel=1.0):
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    env = np.minimum(1, t / 0.012) * np.exp(-t / 0.035)
    y = butter(RNG.standard_normal(n), "bandpass", [4500, 11000]) * env
    return (y * vel * 0.12).astype(np.float32)


# ----------------------------------------------------------------------------
# Sound effects (all synthesised)
# ----------------------------------------------------------------------------

def sfx_whoosh(length=0.55, direction=1, vel=1.0, low=500, high=5200):
    """Band-passed noise sweep with doppler-ish pan. direction=1 -> left to right."""
    n = int(length * SR)
    t = np.linspace(0, 1, n)
    nz = RNG.standard_normal(n)
    env = np.sin(np.pi * np.clip(t, 0, 1)) ** 2.2
    env *= (t < 0.62) * (t / 0.62) ** 1.4 + (t >= 0.62) * np.exp(-(t - 0.62) * 6)
    # time-varying band: process in blocks
    out = np.zeros(n)
    blk = 1024
    zi = None
    centers = low * (high / low) ** np.sin(np.pi * t * 0.5 + 0.0) ** 1.2
    for s in range(0, n, blk):
        c = float(centers[min(n - 1, s + blk // 2)])
        sos = signal.butter(2, [c / 1.6, min(c * 1.6, 20000)], btype="bandpass", fs=SR, output="sos")
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        out[s:s + blk], zi = signal.sosfilt(sos, nz[s:s + blk], zi=zi)
    y = out * env
    p = np.clip((t - 0.5) * 1.6 * direction, -0.85, 0.85)
    a = (p + 1) * np.pi / 4
    st = np.stack([y * np.cos(a), y * np.sin(a)], axis=1)
    return (st / (np.abs(st).max() + 1e-9) * 0.5 * vel).astype(np.float32)


def sfx_pop(vel=1.0, f0=520, f1=1100):
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    f = f0 + (f1 - f0) * (1 - np.exp(-t / 0.012))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.022) * np.minimum(1, t / 0.0015)
    return (y * 0.42 * vel).astype(np.float32)


def sfx_tick(vel=1.0, f=2600):
    n = int(0.035 * SR)
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.004)
    y += butter(RNG.standard_normal(n), "highpass", 4000) * np.exp(-t / 0.002) * 0.4
    return (y * 0.3 * vel).astype(np.float32)


def sfx_ding(vel=1.0, f=1318.5):
    y = bell_note(f, 1.0, 1.8) + bell_note(f * 2.0, 0.35, 1.8)
    return (y * 0.8 * vel).astype(np.float32)


def sfx_impact(vel=1.0, length=2.2):
    """Cinematic sub boom + noise burst."""
    n = int(length * SR)
    t = np.arange(n) / SR
    f = 32 + 48 * np.exp(-t / 0.09)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.55)
    nz = butter(RNG.standard_normal(n), "lowpass", 900) * np.exp(-t / 0.12) * 0.7
    crack = butter(RNG.standard_normal(n), "highpass", 2500) * np.exp(-t / 0.015) * 0.25
    y = soft_clip(sub * 1.1 + nz + crack, 1.3)
    return (y * 0.7 * vel).astype(np.float32)


def sfx_riser(length=2.0, vel=1.0):
    """Rising filtered noise + pitch-rising tone; ends abruptly (for cut-on-hit)."""
    n = int(length * SR)
    t = np.linspace(0, 1, n)
    nz = RNG.standard_normal(n)
    out = np.zeros(n)
    blk = 1024
    zi = None
    for s in range(0, n, blk):
        c = 300 * (9000 / 300) ** (t[min(n - 1, s + blk // 2)] ** 1.6)
        sos = signal.butter(2, [c / 1.4, min(c * 1.4, 21000)], btype="bandpass", fs=SR, output="sos")
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        out[s:s + blk], zi = signal.sosfilt(sos, nz[s:s + blk], zi=zi)
    f = 180 * 2 ** (t * 2.5)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.15
    env = t ** 2.4
    y = (out / (np.abs(out).max() + 1e-9) + tone) * env
    y[-int(0.004 * SR):] *= np.linspace(1, 0, int(0.004 * SR))
    st = np.stack([y, np.roll(y, 37)], axis=1)
    return (st * 0.33 * vel).astype(np.float32)


def sfx_reverse_swell(length=1.2, vel=1.0):
    n = int(length * SR)
    t = np.linspace(0, 1, n)
    y = butter(RNG.standard_normal(n), "bandpass", [2500, 12000]) * t ** 3
    y[-200:] *= np.linspace(1, 0, 200)
    st = np.stack([y, np.roll(y, 53)], axis=1)
    return (st * 0.18 * vel).astype(np.float32)


def sfx_shutter(vel=1.0):
    n = int(0.16 * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for d, a in ((0.0, 1.0), (0.055, 0.7)):
        tt = t - d
        y += np.where(tt >= 0, np.exp(-np.clip(tt, 0, None) / 0.006), 0) * a * RNG.standard_normal(n)
    y = butter(y, "bandpass", [1500, 9000])
    return (y * 0.35 * vel).astype(np.float32)


def sfx_glitch(vel=1.0, length=0.25):
    n = int(length * SR)
    y = np.zeros(n)
    pos = 0
    while pos < n:
        seg = int(RNG.uniform(0.008, 0.03) * SR)
        f = RNG.uniform(300, 3000)
        tt = np.arange(seg) / SR
        y[pos:pos + seg] = np.sign(np.sin(2 * np.pi * f * tt))[: n - pos] * RNG.uniform(0.2, 0.6)
        pos += seg
    y = butter(y, "bandpass", [400, 6000])
    y *= np.linspace(1, 0.3, n)
    return (y * 0.2 * vel).astype(np.float32)


# ----------------------------------------------------------------------------
# Effects
# ----------------------------------------------------------------------------

def use_sfx(**fns):
    """swap a sound for every caller that reaches it through this module (audio_mix's cues, the effects built from
    pops and ticks): use_sfx(pop=fn, tick=fn). modern_sfx.py does this when a design imports it."""
    for name, fn in fns.items():
        if "sfx_" + name not in globals():
            raise KeyError(f"no sound sfx_{name} to replace")
        globals()["sfx_" + name] = fn


def make_ir(rt60=2.2, predelay=0.018, damp=0.5):
    n = int(rt60 * 1.15 * SR)
    t = np.arange(n) / SR
    chans = []
    for _ in range(2):
        nz = RNG.standard_normal(n)
        dark = butter(nz, "lowpass", 2600) * 10 ** (-3 * t / rt60)
        bright = nz * 10 ** (-3 * t / (rt60 * damp))
        ir = dark * 0.85 + bright * 0.25
        ir *= np.minimum(1, t / 0.006)
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        chans.append(ir)
    ir = np.stack(chans, axis=1)
    return (ir / np.sqrt((ir ** 2).sum(0, keepdims=True)) * 0.9).astype(np.float32)


def reverb(x, ir, wet=0.3):
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    out = np.zeros((len(x) + len(ir) - 1, 2), np.float32)
    for c in range(2):
        out[:, c] = signal.oaconvolve(x[:, c], ir[:, c])
    y = out[: len(x)]
    return x * (1 - wet) + y * wet


def sidechain_gain(n, kick_samples, depth=0.35, release=0.16):
    g = np.ones(n, np.float32)
    rel = int(release * 4 * SR)
    curve = 1 - depth * np.exp(-np.arange(rel) / (release * SR))
    att = int(0.004 * SR)
    curve[:att] = 1 - depth * np.linspace(0, 1, att)
    for s in kick_samples:
        s = int(s)
        if s >= n:
            continue
        e = min(n, s + rel)
        g[s:e] = np.minimum(g[s:e], curve[: e - s])
    return g
