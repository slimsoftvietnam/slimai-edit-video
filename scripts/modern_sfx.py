"""Modern UI sounds (user, 2026-11-17: "hiệu ứng sound click hiện đại hơn chút"; the motion style, references/motion.md). The skill's pop is
a 90 ms sine sweep (a cartoon "bloop") and its tick a plain ping; these are tight, crisp UI sounds instead: a bright
transient, a short plucked body tuned to the episode's key, a soft low thump for weight, a tiny room. A design imports
this module; it swaps in its pop and tick with audio_engine.use_sfx(), and audio_mix's render_sfx calls them at mix
time (each cue is then peak-normalised there). set_key(root, minor) tunes them to the music (default Bb minor, the Trap Banger track).

Pitch: the cue's f1 (pop) or f (tick) is snapped to the nearest D natural minor note, so design.py passes notes.
"""
import numpy as np

import audio_engine as ae

SR = ae.SR
_R = np.random.default_rng(57)
_DMIN = sorted({58 + 12 * o + s for o in range(-2, 5) for s in (0, 2, 3, 5, 7, 8, 10)})   # Bb natural minor: the pitch set of the Trap Banger track (chroma, 2026-11-24)


def set_key(root=58, minor=True):
    """snap the UI sounds to this key: root = MIDI note of the tonic (58 = Bb), minor or major scale"""
    steps = (0, 2, 3, 5, 7, 8, 10) if minor else (0, 2, 4, 5, 7, 9, 11)
    _DMIN[:] = sorted({root + 12 * o + s for o in range(-2, 5) for s in steps})
_ROOM = []


def note(m):
    return ae.hz(m)


def _snap(f):
    m = 69 + 12 * np.log2(max(f, 20.0) / 440.0)
    return ae.hz(min(_DMIN, key=lambda k: abs(k - m)))


def _space(y, wet):
    """a tiny room, mono: the skill's own effects (audio_mix.sfx_connect) mix these into mono buffers."""
    if not _ROOM:
        _ROOM.append(ae.make_ir(0.35, 0.004, 0.6))
    return ae.reverb(y.astype(np.float32), _ROOM[0], wet)[:, 0]


def pop(vel=1.0, f0=520, f1=1100):
    """an element snapping in: crisp transient, a plucked 'tock' that settles on its note in 4 ms, a low thump."""
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    fc = _snap(f1)
    ph = np.cumsum(fc * (1 + 0.5 * np.exp(-t / 0.004)) / SR)
    body = (np.sin(2 * np.pi * ph) + 0.22 * np.sin(4 * np.pi * ph)) * np.exp(-t / 0.03)
    thump = np.sin(2 * np.pi * 170 * t) * np.exp(-t / 0.014) * 0.55
    click = ae.butter(_R.standard_normal(n), "bandpass", [3000, 9000]) * np.exp(-t / 0.0009) * 0.6
    y = (body + thump + click) * np.minimum(1, t / 0.0004)
    return (_space(y, 0.14) * 0.5 * vel).astype(np.float32)


def tick(vel=1.0, f=2600):
    """a row checking in: a very short bright click with a tiny pitched 'tik' on its note and a mid knock."""
    n = int(0.07 * SR)
    t = np.arange(n) / SR
    fc = _snap(f)
    tik = np.sin(2 * np.pi * np.cumsum(fc * (1 + 0.15 * np.exp(-t / 0.003)) / SR)) * np.exp(-t / 0.012)
    knock = ae.butter(_R.standard_normal(n), "bandpass", [900, 2800]) * np.exp(-t / 0.0035) * 0.5
    air = ae.butter(_R.standard_normal(n), "highpass", 6000) * np.exp(-t / 0.0007) * 0.45
    y = (0.8 * tik + knock + air) * np.minimum(1, t / 0.0003)
    return (_space(y, 0.1) * 0.5 * vel).astype(np.float32)


ae.use_sfx(pop=pop, tick=tick)
