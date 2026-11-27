"""Compose the background track from code.

Warm lo-fi / chill-hop, built on the IV-V-iii-vi "royal road" progression with a recurring pluck motif
(the audio hook). Default D major, 96 BPM; plan["bpm"] and plan["transpose"] (semitones) give each video
its own track. The arrangement is driven by a plan (bars -> section style), so music changes land on
edit beats.
"""
import json
import sys

import numpy as np

import audio_engine as ae
from audio_engine import SR, hz, note_num as N

# chord: (bass note, [voicing])
PROG_MAIN = [
    ("G1", ["B3", "D4", "F#4", "A4"]),     # Gmaj9
    ("A1", ["B3", "D4", "E4", "G4"]),      # A9sus4
    ("F#1", ["A3", "C#4", "E4", "G#4"]),   # F#m9
    ("B1", ["A3", "C#4", "D4", "F#4"]),    # Bm9
]
PROG_CALM = [
    ("D2", ["F#3", "A3", "C#4", "E4"]),    # Dmaj9
    ("B1", ["F#3", "A3", "C#4", "D4"]),    # Bm9
    ("G1", ["F#3", "A3", "B3", "D4"]),     # Gmaj9 (rootless)
    ("A1", ["E3", "G3", "A3", "C#4"]),     # A7
]
PROG_TENSE = [
    ("B1", ["F#3", "B3", "C#4", "D4"]),     # Bm(add9) - close cluster, uneasy
    ("G1", ["F#3", "B3", "C#4", "D4"]),     # Gmaj7(#11)-ish over G
    ("B1", ["F#3", "B3", "C#4", "D4"]),
    ("G1", ["F#3", "B3", "C#4", "D4"]),
]
# pluck motif over 4 bars: (beat offset within 4-bar phrase, note, vel)
MOTIF = [
    (0.0, "F#5", 0.9), (1.5, "A5", 0.7), (2.5, "B5", 0.8), (3.5, "A5", 0.6),
    (4.5, "F#5", 0.8), (5.5, "E5", 0.6), (6.5, "D5", 0.7),
    (8.0, "E5", 0.85), (9.5, "F#5", 0.7), (10.5, "A5", 0.8), (11.5, "C#6", 0.7),
    (12.5, "B5", 0.8), (13.5, "A5", 0.6), (14.0, "F#5", 0.65),
]
MOTIF_B = [  # answer phrase
    (0.0, "D6", 0.8), (1.0, "B5", 0.6), (2.0, "A5", 0.7), (3.0, "F#5", 0.6),
    (4.5, "A5", 0.75), (6.0, "E5", 0.6),
    (8.0, "F#5", 0.8), (9.0, "A5", 0.6), (10.0, "B5", 0.75), (11.0, "D6", 0.6),
    (12.0, "C#6", 0.8), (13.5, "A5", 0.6),
]

# section styles -> which layers play
STYLES = {
    #            ep    pad   bass  kick  snare hat   shaker pluck  lp(Hz)
    "intro":    (0.0, 1.0, 0.6, 0.0, 0.0, 0.45, 0.0, 0.0, 1900),
    "build":    (0.8, 0.9, 0.6, 0.0, 0.0, 0.5, 0.6, 0.6, 3200),
    "light":    (0.9, 0.7, 0.8, 0.7, 0.0, 0.0, 0.8, 0.0, 9000),
    "groove":   (1.0, 0.6, 1.0, 1.0, 1.0, 0.8, 0.7, 0.0, 12000),
    "lift":     (1.0, 0.7, 1.0, 1.0, 1.0, 1.0, 0.9, 0.8, 15000),
    "break":    (0.9, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.7, 2600),
    "outro":    (0.9, 1.0, 0.5, 0.0, 0.0, 0.0, 0.4, 1.0, 5000),
}


def humanize(t, amt=0.006):
    return t + ae.RNG.uniform(-amt, amt)


# ----------------------------------------------------------------------------
# the mixing chain, shared with vlog_music.py (the order of the calls is part of the sound: make_ir draws from the
# shared random generator)
# ----------------------------------------------------------------------------
def bus_chain(buses, kicks, n, beat, sc_depth, trem, drums_lp):
    """the buses' effects: side-chain pumping from the kicks, one room for all, the electric piano's tremolo (trem(tt)
    -> depth per sample), filters and the pluck's dotted-eighth echo -> (sc, ir, ep, pad, bass, drums, pluck)"""
    sc = ae.sidechain_gain(n, kicks, depth=sc_depth, release=0.15)[:, None]
    ir = ae.make_ir(2.4, 0.02, 0.45)
    ep = ae.reverb(buses["ep"], ir, 0.28)
    ep = ae.butter(ep, "highpass", 140)
    tt = np.arange(n) / SR
    tr = trem(tt)
    ep[:, 0] *= 1 + tr
    ep[:, 1] *= 1 - tr
    pad = ae.reverb(buses["pad"], ir, 0.45)
    pad = ae.butter(pad, "highpass", 160)
    pad = ae.butter(pad, "lowpass", 5200)
    bass = ae.butter(buses["bass"], "lowpass", 900)
    drums = buses["drums"]
    drums = drums * 0.9 + ae.reverb(drums, ir, 1.0) * 0.08
    drums = ae.butter(drums, "lowpass", drums_lp)
    pluck = ae.reverb(buses["pluck"], ir, 0.38)
    d = int(beat * 0.75 * SR)                                       # dotted-eighth echo: it answers in time
    echo = np.zeros_like(pluck)
    echo[d:, 1] += pluck[:-d, 0] * 0.33
    echo[2 * d:, 0] += pluck[:-2 * d, 1] * 0.2
    pluck = pluck + ae.butter(echo, "lowpass", 4500)
    return sc, ir, ep, pad, bass, drums, pluck


def vinyl(mix, rate, crack_gain, hiss_gain):
    """vinyl warmth, added in place: a faint crackle (about `rate` clicks a second) and hiss"""
    n = len(mix)
    crack = np.zeros(n)
    k = ae.RNG.random(n) < (rate / SR)
    crack[k] = ae.RNG.uniform(-1, 1, k.sum()) * ae.RNG.uniform(0.2, 1.0, k.sum())
    crack = ae.butter(crack, "bandpass", [1200, 7000]) * crack_gain
    hiss = ae.butter(ae.RNG.standard_normal(n), "bandpass", [3000, 9000]) * hiss_gain
    mix += np.stack([crack + hiss, np.roll(crack, 17) + hiss], axis=1)


def glide(lp_points, n, bar):
    """the master low-pass cutoff per sample from [(time, Hz)]: it glides over the half bar before each point"""
    lp_points.sort()
    cut = np.full(n, 16000.0)
    if lp_points:
        cur = lp_points[0][1]
        cut[:] = cur
        for (t0, v) in lp_points:
            s = max(0, int((t0 - bar * 0.5) * SR))
            e = min(n, int((t0 + bar * 0.05) * SR))
            if e > s:
                cut[s:e] = np.geomspace(max(cur, 50), v, e - s)
            cut[e:] = v
            cur = v
    return cut


def sweep_lowpass(mix, cut):
    """the mix through a 2-pole low-pass whose cutoff follows `cut`, block by block"""
    from scipy import signal as sg
    out = np.zeros_like(mix)
    blk = 512
    zi = np.zeros((1, 2, 2))
    for s in range(0, len(mix), blk):
        c = float(min(cut[s], SR / 2 * 0.9))
        sos = sg.butter(2, c, btype="lowpass", fs=SR, output="sos")
        seg = mix[s:s + blk]
        y0, zi[:, :, 0] = sg.sosfilt(sos, seg[:, 0], zi=zi[:, :, 0])
        y1, zi[:, :, 1] = sg.sosfilt(sos, seg[:, 1], zi=zi[:, :, 1])
        out[s:s + blk, 0] = y0
        out[s:s + blk, 1] = y1
    return out


def glue(mix):
    """gentle saturation, then the peak normalised to 0.89"""
    mix = ae.soft_clip(mix * 1.1, 1.2)
    mix /= np.abs(mix).max() + 1e-9
    return (mix * 0.89).astype(np.float32)


def render(plan):
    BPM = float(plan.get("bpm", 96.0))
    BEAT = 60.0 / BPM
    BAR = 4 * BEAT
    tr = int(plan.get("transpose", 0))

    def note(name):
        return hz(N(name) + tr)

    dur = plan["duration"]
    bar0 = plan.get("bar0", 0.0)          # video time (s) of bar 0, may be negative
    n_total = int((dur + 4.0) * SR)
    sections = plan["sections"]           # list of [start_bar, end_bar, style, prog]
    stops = plan.get("stops", [])         # list of video times: music drops out for ~1 beat
    tail = plan.get("tail", 3.0)

    buses = {k: np.zeros((n_total, 2), np.float32) for k in
             ("ep", "pad", "bass", "drums", "pluck")}
    kicks = []
    lp_points = []  # (time, cutoff) for the master low-pass automation

    def t_of(bar, beat=0.0):
        return bar0 + bar * BAR + beat * BEAT

    for (b_start, b_end, style, prog_name) in sections:
        ep_l, pad_l, bass_l, kick_l, sn_l, hat_l, sh_l, pl_l, lp = STYLES[style]
        prog = {"main": PROG_MAIN, "calm": PROG_CALM, "tense": PROG_TENSE}[prog_name]
        lp_points.append((t_of(b_start), lp))
        for bar in range(b_start, b_end):
            ci = bar % 4
            bass_name, voicing = prog[ci]
            freqs = [note(v) for v in voicing]
            t_bar = t_of(bar)
            if t_bar > dur + 1:
                break
            # --- pad: whole bar
            if pad_l > 0:
                x = ae.pad_chord(freqs + [note(bass_name) * 2], BAR * 1.02, 0.9 * pad_l)
                ae.add(buses["pad"], x, t_bar * SR)
            # --- electric piano: comp pattern (beat offsets, length, vel)
            if ep_l > 0:
                pattern = [(0.0, 1.4, 0.75), (1.5, 0.45, 0.45), (2.5, 1.2, 0.6)]
                if bar % 2 == 1:
                    pattern = [(0.0, 1.9, 0.7), (2.75, 1.0, 0.5)]
                for (bt, ln, vel) in pattern:
                    for k, f in enumerate(freqs):
                        st = humanize(t_bar + bt * BEAT + k * 0.009)  # slight strum
                        x = ae.ep_note(f, ln * BEAT, vel * ep_l * (0.92 + 0.08 * ae.RNG.uniform()))
                        ae.add(buses["ep"], ae.pan(x, -0.25 + 0.17 * k), st * SR)
            # --- bass
            if bass_l > 0:
                fb = note(bass_name)
                for (bt, ln, vel) in [(0.0, 1.6, 0.95), (1.75, 0.25, 0.5), (2.5, 1.3, 0.8)]:
                    x = ae.bass_note(fb, ln * BEAT, vel * bass_l)
                    ae.add(buses["bass"], x, humanize(t_bar + bt * BEAT, 0.003) * SR)
            # --- drums (16th grid with swing)
            swing = 0.18
            for step in range(16):
                bt = step / 4.0
                if step % 2 == 1:
                    bt += swing / 4.0
                ts = t_bar + bt * BEAT
                if kick_l > 0 and step in ((0, 10) if bar % 2 == 0 else (0, 7, 10)):
                    v = (1.0 if step == 0 else 0.75) * kick_l
                    ae.add(buses["drums"], ae.kick(v), humanize(ts, 0.002) * SR)
                    kicks.append(ts * SR)
                if sn_l > 0 and step in (4, 12):
                    c_, s_ = ae.clap(0.8 * sn_l), ae.snare(0.5 * sn_l)
                    x = np.zeros(max(len(c_), len(s_)), np.float32)
                    x[: len(c_)] += c_
                    x[: len(s_)] += s_
                    ae.add(buses["drums"], ae.pan(x, 0.05), humanize(ts, 0.004) * SR)
                if hat_l > 0 and step % 2 == 0:
                    open_ = (step == 14 and bar % 4 == 3)
                    v = (0.55 if step % 4 == 0 else 0.85) * hat_l * ae.RNG.uniform(0.8, 1.0)
                    ae.add(buses["drums"], ae.pan(ae.hat(v, open_), 0.3), humanize(ts, 0.003) * SR)
                if sh_l > 0:
                    v = (0.9 if step % 4 == 2 else 0.45) * sh_l * ae.RNG.uniform(0.7, 1.0)
                    ae.add(buses["drums"], ae.pan(ae.shaker(v), -0.35), humanize(ts, 0.004) * SR)
            # --- pluck motif (4-bar phrases)
            if pl_l > 0 and bar % 4 == 0:
                motif = MOTIF if (bar // 4) % 2 == 0 else MOTIF_B
                for (bt, nm, vel) in motif:
                    st = humanize(t_bar + bt * BEAT, 0.004)
                    x = ae.pluck_note(note(nm), vel * pl_l, 1.8)
                    ae.add(buses["pluck"], ae.pan(x, 0.35 if int(bt) % 2 else -0.15), st * SR)

    # ---------------- mixing ----------------
    n = n_total
    # tremolo / auto-pan on the EP for movement
    sc, ir, ep, pad, bass, drums, pluck = bus_chain(buses, kicks, n, BEAT, 0.32,
                                                    lambda tt: 0.18 * np.sin(2 * np.pi * 4.2 * tt), 11000)
    mix = (ep * 0.62 + pad * 0.5) * sc + bass * 0.40 * sc + drums * 0.58 + pluck * 0.42
    mix = ae.butter(mix, "highpass", 32)
    vinyl(mix, 22.0, 0.05, 0.0025)
    # master low-pass automation (block-wise, smooth cutoff glide)
    mix = sweep_lowpass(mix, glide(lp_points, n, BAR))

    # stops: music cuts out for ~1 beat (gain dip with fast fades), for punchlines
    g = np.ones(n, np.float32)
    for st in stops:
        a = int((st - 0.03) * SR)
        b = int((st + BEAT * 1.0) * SR)
        f1 = int(0.025 * SR)
        f2 = int(0.12 * SR)
        if a < 0 or b >= n:
            continue
        g[a:b] = 0.0
        g[max(0, a - f1):a] = np.minimum(g[max(0, a - f1):a], np.linspace(1, 0, a - max(0, a - f1)))
        g[b:b + f2] = np.minimum(g[b:b + f2], np.linspace(0, 1, f2))
    mix *= g[:, None]

    # fade in / out
    fi = int(0.05 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]
    end = int(dur * SR)
    fo = int(tail * SR)
    mix[end - fo:end] *= np.linspace(1, 0, fo)[:, None] ** 1.5
    mix[end:] = 0
    mix = mix[:end]
    return glue(mix)


def write_wav(path, x):
    from scipy.io import wavfile
    wavfile.write(path, SR, np.clip(x, -1, 1).astype(np.float32))


if __name__ == "__main__":
    plan_path, out_path = sys.argv[1], sys.argv[2]
    with open(plan_path, encoding="utf-8") as f:
        plan = json.load(f)
    write_wav(out_path, render(plan))
    print("wrote", out_path)
