"""Build the soundtrack: edited dialogue + music + synthesised SFX, mixed to -14 LUFS.

python audio_mix.py --project P --fmt tiktok|youtube [--preset NAME] [--reuse-music]
Outputs in P/audio_<fmt>/: voice_raw.wav voice.wav music.wav sfx.wav mix_pre.wav final_audio.wav (-14 LUFS)

The preset is --preset, else MIX in design.py, else the one a style kit set (vlog.setup() sets "vlog"), else
score_solo for a design with score() events and SOLO_WINDOWS, else score for one with score() events, else standard:
  standard     code-composed music (compose.py, from story.music_plan()) at -23.5 LUFS, ducked 9 dB under the voice;
               -14 LUFS, -1.2 dBTP
  score        a trailer: the score registered with story.score() (trailer_score.py, and the kinds of modern_score.py
               and track_music.py) in three stems: music -21 LUFS, ducked 9 dB (5.5 dB under a drive), hits -17.5,
               perc -27; a limiter, then -14 LUFS, -1.5 dBTP. Also hits.wav, perc.wav, mix_lim.wav
  score_solo   score with the music split in two before it is levelled (references/motion.md): the bed under the voice
               as in score; each voiceless stretch (design.SOLO_WINDOWS, else the end card from design.T_END) levelled
               on its own to -14.8 LUFS, so a licensed track carries the end card without lowering the bed under every
               line. Hits 2 dB lower (the first word is often under the boom), -2.0 dBTP, a 20 ms fade-in
  vlog         the vlog style (references/vlog.md): vlog_music.py on the cut's beat grid; the clip's own sound fades
               out over B-roll, the holds after a last word, the end and vlog.QUIET; music -21 LUFS, ducked 6.5 dB,
               3.5 dB up over B-roll; -14 LUFS, -1.5 dBTP, a 20 ms fade-in. --reuse-music keeps the music.wav already
               rendered (the music takes a few minutes): use it after changing only cues

A project script can import this module, call setup(project, fmt) and use its helpers (build_voice, render_sfx, wr,
lufs, loudnorm...). Older project scripts set sys.argv to ["audio_mix.py", "--project", P, "--fmt", F] before importing
it, and that still loads the project the same way.
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio_engine as ae  # noqa: E402
import compose  # noqa: E402

SR = 48000
PRESETS = ("standard", "score", "score_solo", "vlog")
ARGS = D = E = FPS = OUT = IR = None      # set by setup()


def parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--fmt", choices=["youtube", "tiktok"], required=True)
    ap.add_argument("--preset", choices=PRESETS)
    ap.add_argument("--reuse-music", action="store_true", help="vlog: keep the music.wav already rendered")
    return ap


def setup(project, fmt):
    """load the project's design for this format; every helper below needs it. Once per process: engine and story
    read the project when they are first imported."""
    global ARGS, D, E, FPS, OUT, IR
    ARGS = argparse.Namespace(project=project, fmt=fmt)
    os.environ["EDIT_PROJECT"] = os.path.abspath(project)
    os.environ["EDIT_FMT"] = fmt
    os.environ["EDIT_SS"] = "1"
    import engine
    import story
    story.load_design()
    D, E, FPS = story, engine, engine.FPS
    OUT = os.path.join(E.PROJECT, f"audio_{fmt}")
    os.makedirs(OUT, exist_ok=True)
    # made after the design is loaded, as it always was: the shared random generator's order of draws is part of the sound
    IR = ae.make_ir(1.8, 0.015, 0.5)


def wr(path, x):
    wavfile.write(path, SR, np.clip(x, -1, 1).astype(np.float32))


def rd(path):
    sr, x = wavfile.read(path)
    assert sr == SR
    if x.dtype == np.int32:
        x = x.astype(np.float32) / 2147483648.0
    elif x.dtype == np.int16:
        x = x.astype(np.float32) / 32768.0
    return x.astype(np.float32)


def db_to_gain(d):
    return 10 ** (d / 20)


# ----------------------------------------------------------------------------
# 1. dialogue edit (sample-accurate to the video frames)
# ----------------------------------------------------------------------------
def build_voice():
    src = rd(os.path.join(E.PROJECT, "audio48k.wav"))
    if src.ndim > 1:
        src = src.mean(1)
    total = int(round(D.TOTAL * SR))
    out = np.zeros(total, np.float32)
    fade = int(0.006 * SR)
    for c in D.CLIPS:
        f0 = int(round(c["src_in"] * FPS))
        o0 = int(round(c["out_in"] * FPS))
        n = c["frames"]
        s0 = int(round(f0 / FPS * SR))
        s1 = int(round((f0 + n) / FPS * SR))
        seg = src[s0:s1].copy()
        if len(seg) > 2 * fade:
            seg[:fade] *= np.linspace(0, 1, fade) ** 0.5
            seg[-fade:] *= np.linspace(1, 0, fade) ** 0.5
        p0 = int(round(o0 / FPS * SR))
        e = min(total, p0 + len(seg))
        out[p0:e] += seg[: e - p0]
    wr(os.path.join(OUT, "voice_raw.wav"), out)
    # processing chain (ffmpeg): HPF, gentle denoise, de-mud, presence, compression, limiter
    af = ("highpass=f=80:poles=2,"
          "afftdn=nr=9:nf=-48:tn=1,"
          "equalizer=f=250:t=q:w=1.0:g=-2.5,"
          "equalizer=f=3300:t=q:w=1.1:g=2.5,"
          "equalizer=f=9000:t=h:w=0.7:g=1.5,"
          "acompressor=threshold=-24dB:ratio=3.2:attack=6:release=140:makeup=5:knee=6,"
          "deesser=i=0.35,"
          "alimiter=limit=0.89:attack=3:release=60")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(OUT, "voice_raw.wav"), "-af", af,
                    "-c:a", "pcm_f32le", os.path.join(OUT, "voice.wav")], check=True)
    return rd(os.path.join(OUT, "voice.wav"))


# ----------------------------------------------------------------------------
# 2. SFX
# ----------------------------------------------------------------------------
def sfx_shimmer(vel=1.0):
    notes = [86, 90, 93, 98]  # D6 F#6 A6 D7
    n = int(1.6 * SR)
    y = np.zeros(n, np.float32)
    for i, m in enumerate(notes):
        s = int(i * 0.045 * SR)
        x = ae.bell_note(ae.hz(m), 0.55 - i * 0.08, 1.4)
        y[s:s + len(x)] += x[: n - s]
    st = np.stack([y, np.roll(y, int(0.011 * SR))], axis=1)
    return st * 0.55 * vel


def sfx_rewind(vel=1.0, length=0.55):
    n = int(length * SR)
    t = np.linspace(0, 1, n)
    f = 1500 * (1 - t) ** 1.6 + 220
    ph = 2 * np.pi * np.cumsum(f) / SR
    flutter = 1 + 0.25 * np.sin(2 * np.pi * 38 * t)
    saw = 2 * ((ph / (2 * np.pi)) % 1) - 1
    tone = ae.butter(saw * flutter, "lowpass", 3500) * 0.35
    nz = ae.butter(ae.RNG.standard_normal(n), "bandpass", [800, 5000]) * 0.25
    env = np.sin(np.pi * t) ** 0.7
    y = (tone + nz * (1 - t)) * env
    st = np.stack([y, np.roll(y, 40)], axis=1)
    return (st * 0.6 * vel).astype(np.float32)


def sfx_connect(vel=1.0):
    a = ae.sfx_tick(0.8, 2400)
    b = ae.bell_note(880.0, 0.5, 0.5)
    c = ae.bell_note(1318.5, 0.6, 0.8)
    n = int(1.0 * SR)
    y = np.zeros(n, np.float32)
    y[:len(a)] += a
    s = int(0.06 * SR)
    y[s:s + len(b)] += b[: n - s]
    s = int(0.16 * SR)
    y[s:s + len(c)] += c[: n - s]
    return y * vel


def sfx_click(vel=1.0):
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    y = ae.sfx_tick(1.0, 3200)
    thump = np.sin(2 * np.pi * 140 * t) * np.exp(-t / 0.02) * 0.5
    out = thump.copy()
    out[:len(y)] += y
    return (out * 0.8 * vel).astype(np.float32)


def sfx_beep(vel=1.0):
    n = int(0.42 * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for d in (0.0, 0.2):
        tt = t - d
        m = (tt >= 0) & (tt < 0.09)
        y[m] += np.sin(2 * np.pi * 2093 * tt[m]) * np.minimum(1, tt[m] / 0.004) * np.minimum(1, (0.09 - tt[m]) / 0.01)
    return (y * 0.22 * vel).astype(np.float32)


def sfx_swipe(vel=1.0):
    return ae.sfx_whoosh(length=0.3, direction=1, vel=vel, low=1800, high=9500)


def sfx_typing(length):
    """fast keystrokes for `length` s (a prompt typing itself)."""
    rng = np.random.default_rng(5)
    n = int((length + 0.1) * SR)
    y = np.zeros(n, np.float32)
    t = 0.0
    while t < length:
        k = ae.sfx_tick(rng.uniform(0.45, 0.9), rng.uniform(1700, 3100))
        s = int(t * SR)
        y[s:s + len(k)] += k[: n - s]
        t += rng.uniform(0.035, 0.075)
    return y


def render_sfx(total):
    buf = np.zeros((total, 2), np.float32)
    base = {"whoosh": -15, "pop": -17, "tick": -21, "impact": -11, "swipe": -16, "shimmer": -20,
            "ding": -21, "glitch": -21, "rewind": -14, "connect": -17, "click": -15, "beep": -17,
            "shutter": -16, "pluck": -14, "swell": -17, "typing": -12}
    for (t, kind, gain, kw) in D.CUES:
        if kind == "whoosh":
            x = ae.sfx_whoosh(length=kw.get("length", 0.5), direction=kw.get("direction", 1))
            t = t - kw.get("length", 0.5) * 0.55  # peak lands on the cue
        elif kind == "pop":
            x = ae.sfx_pop(1.0, kw.get("f0", 520), kw.get("f1", 1100))
        elif kind == "tick":
            x = ae.sfx_tick(1.0, kw.get("f", 2600))
        elif kind == "impact":
            x = ae.sfx_impact(1.0, kw.get("length", 2.0))
        elif kind == "swipe":
            x = sfx_swipe()
            t -= 0.12
        elif kind == "shimmer":
            x = sfx_shimmer()
        elif kind == "ding":
            x = ae.sfx_ding(1.0, kw.get("f", 1318.5))
        elif kind == "glitch":
            x = ae.sfx_glitch(1.0)
        elif kind == "rewind":
            x = sfx_rewind()
        elif kind == "connect":
            x = sfx_connect()
        elif kind == "click":
            x = sfx_click()
        elif kind == "beep":
            x = sfx_beep()
        elif kind == "shutter":
            x = ae.sfx_shutter()
        elif kind == "swell":
            x = ae.sfx_reverse_swell(kw.get("length", 1.0))
        elif kind == "pluck":
            x = ae.pluck_note(ae.hz(kw.get("note", 74)), 1.0, 1.6)
            x = ae.reverb(x, IR, 0.3)
        elif kind == "typing":
            x = sfx_typing(kw.get("until", t + 1.5) - t)
        else:
            continue
        g = db_to_gain(base[kind]) * gain / max(1e-6, np.abs(x).max())
        ae.add(buf, x * g, int(t * SR))
    return buf



# ----------------------------------------------------------------------------
# 3. mix
# ----------------------------------------------------------------------------
def envelope_db(x, win=0.05):
    n = int(win * SR)
    p = np.convolve(x ** 2, np.ones(n) / n, mode="same")
    return 10 * np.log10(p + 1e-12)


def smooth(a, att, rel):
    out = np.zeros_like(a)
    ca = np.exp(-1 / (att * SR))
    cr = np.exp(-1 / (rel * SR))
    v = 0.0
    from numba import njit

    @njit(cache=False)
    def run(a, out, ca, cr):
        v = 0.0
        for i in range(len(a)):
            x = a[i]
            c = ca if x > v else cr
            v = c * v + (1 - c) * x
            out[i] = v
        return out
    return run(a.astype(np.float64), out.astype(np.float64), ca, cr)


def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
                       capture_output=True, text=True)
    for line in r.stderr.splitlines()[::-1]:
        if "I:" in line and "LUFS" in line:
            return float(line.split("I:")[1].split("LUFS")[0])
    return None


def loudnorm(src, dst, tp=-1.2, lra=11):
    """two-pass loudnorm to -14 LUFS."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", f"loudnorm=I=-14:TP={tp}:LRA={lra}:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    js = r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1]
    m = json.loads(js)
    af = (f"loudnorm=I=-14:TP={tp}:LRA={lra}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
          f"linear=true:print_format=summary")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", af, "-ar", "48000", "-c:a", "pcm_s24le", dst], check=True)


def fit(x, total):
    """a stereo stem cut or padded to `total` samples"""
    x = x[:total]
    if len(x) < total:
        x = np.pad(x, ((0, total - len(x)), (0, 0)))
    return x


def fade_in(src, dst):
    """a 20 ms fade-in: a boom or a first word on frame 0 made the AAC encode overshoot the true peak (tập 14: the wav
    was -2.0 dBTP, the AAC +0.2)"""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", "afade=t=in:st=0:d=0.02", "-c:a", "pcm_s24le", dst],
                   check=True)


# ----------------------------------------------------------------------------
# 4. presets
# ----------------------------------------------------------------------------
def mix_standard():
    """code-composed music under the voice"""
    total = int(round(D.TOTAL * SR))
    voice = build_voice()[:total]
    if len(voice) < total:
        voice = np.pad(voice, (0, total - len(voice)))
    # music
    plan = D.music_plan()
    json.dump(plan, open(os.path.join(OUT, "music_plan.json"), "w"), indent=1)
    music = compose.render(plan)
    music = music[:total]
    if len(music) < total:
        music = np.pad(music, ((0, total - len(music)), (0, 0)))
    wr(os.path.join(OUT, "music.wav"), music)
    sfx = render_sfx(total)
    wr(os.path.join(OUT, "sfx.wav"), sfx)

    # loudness-normalise stems
    lv = lufs(os.path.join(OUT, "voice.wav"))
    lm = lufs(os.path.join(OUT, "music.wav"))
    voice = voice * db_to_gain(-16.0 - lv)
    music = music * db_to_gain(-23.5 - lm)
    print(f"voice {lv:.1f} LUFS -> -16, music {lm:.1f} LUFS -> -23.5")

    # ducking from the voice envelope
    edb = envelope_db(voice)
    act = np.clip((edb + 46) / 16, 0, 1)
    act = smooth(act, 0.045, 0.45)
    duck_db = -9.0 * act
    # lift the music a little in the intro / pauses / end card
    g = db_to_gain(duck_db)[:, None]
    music_d = music * g
    vox = np.stack([voice, voice], axis=1)
    mix = vox + music_d + sfx
    pre = os.path.join(OUT, "mix_pre.wav")
    wr(pre, mix * 0.9)
    loudnorm(pre, os.path.join(OUT, "final_audio.wav"))     # -14 LUFS, -1.2 dBTP
    print("final", lufs(os.path.join(OUT, "final_audio.wav")), "LUFS")


SOLO_LUFS = -14.8           # score_solo: a voiceless stretch, about 1 LU under the spoken parts in the final mix
SOLO_RAMP = 0.35


def solo_windows():
    """score_solo: design.SOLO_WINDOWS [(t0, t1)], else the end card / the tag after the last word (design.T_END)"""
    design = sys.modules.get("design")
    if hasattr(design, "SOLO_WINDOWS"):
        return list(design.SOLO_WINDOWS)
    if hasattr(design, "T_END"):
        return [(design.T_END - 0.05, D.TOTAL)]
    return []


def mix_score(solo=False):
    """the score registered with story.score() replaces the composed music (trailer_score.py); solo: score_solo"""
    import trailer_score
    total = int(round(D.TOTAL * SR))
    voice = build_voice()[:total]
    if len(voice) < total:
        voice = np.pad(voice, (0, total - len(voice)))
    sfx = render_sfx(total)
    wr(os.path.join(OUT, "sfx.wav"), sfx)
    music, hits, perc, light = trailer_score.render(D.SCORE, D.TOTAL)
    if solo:
        tt = np.arange(total) / SR
        music = fit(music, total)
        parts = {"hits": hits, "perc": perc}
        rest = np.ones(total, np.float32)
        plan = [("music", -21.0)]
        for i, (a, b) in enumerate(solo_windows()):        # each voiceless stretch is levelled on its own
            w = np.clip(np.minimum((tt - a) / SOLO_RAMP + 0.5, (b - tt) / SOLO_RAMP + 0.5), 0, 1)
            m = (0.5 - 0.5 * np.cos(np.pi * w)).astype(np.float32)
            parts[f"music_solo{i}"] = music * m[:, None]
            rest = rest * (1 - m)
            plan.append((f"music_solo{i}", SOLO_LUFS))
        parts["music"] = music * rest[:, None]
        plan += [("hits", -19.5), ("perc", -27.0)]
    else:
        parts = {"music": music, "hits": hits, "perc": perc}
        plan = [("music", -21.0), ("hits", -17.5), ("perc", -27.0)]
    stems = {}
    for name, target in plan:
        x = fit(parts[name], total)
        p = os.path.join(OUT, f"{name}.wav")
        wr(p, x)
        lv_ = lufs(p) if np.abs(x).max() > 0 else None
        stems[name] = x * db_to_gain(target - lv_) if lv_ is not None else x
        print(f"{name} {lv_ if lv_ is None else round(lv_, 1)} -> {target} LUFS")
    lv = lufs(os.path.join(OUT, "voice.wav"))
    voice = voice * db_to_gain(-16.0 - lv)
    print(f"voice {lv:.1f} -> -16 LUFS")
    # the music dips under the voice, less while a drive plays (it has to be felt); hits and perc stay whole
    act = smooth(np.clip((envelope_db(voice) + 46) / 16, 0, 1), 0.04, 0.4)
    depth = np.full(total, -9.0)
    for (a, b) in light:
        depth[int(a * SR):int(b * SR)] = -5.5
    mix = np.stack([voice, voice], axis=1) + stems["music"] * db_to_gain(depth * act)[:, None]
    if solo:
        mix = mix + sum(v for k, v in stems.items() if k.startswith("music_solo"))
    mix = mix + stems["hits"] + stems["perc"] + sfx
    pre = os.path.join(OUT, "mix_pre.wav")
    wr(pre, mix * 0.8)
    # braams and booms are far above the speech peaks: limit them first, so loudnorm can stay linear
    lim = os.path.join(OUT, "mix_lim.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pre, "-af", "alimiter=limit=0.7:attack=3:release=90:level=false",
                    "-c:a", "pcm_f32le", lim], check=True)
    final = os.path.join(OUT, "final_audio.wav")
    if solo:
        loudnorm(lim, os.path.join(OUT, "final_audio_nofade.wav"), tp=-2.0, lra=14)
        fade_in(os.path.join(OUT, "final_audio_nofade.wav"), final)
    else:
        loudnorm(lim, final, tp=-1.5, lra=14)
    print("final", lufs(final), "LUFS")


VLOG_MUSIC_LUFS, VLOG_DUCK_DB = -21.0, -6.5
VLOG_SOLO_DB = 3.5          # where the picture is B-roll the music steps forward: the swell lands with the cut
VLOG_FADE = 0.18            # the clip's own sound fades out / in over this at a quiet window's edges
VLOG_RAMP = 0.10


def vlog_quiet_windows():
    """(t0, t1) where the clip's own sound is not wanted: B-roll, the holds after a last word, the end, vlog.QUIET"""
    import vlog
    broll = set(b["beat"] for b in vlog.BT.get("broll", []))
    out = [(c["out_in"], c["out_out"]) for c in D.CLIPS if c["beat"] in broll]
    for h in vlog.BT.get("holds", []):
        c = next(c for c in D.CLIPS if c["beat"] == h["beat"])
        ws = [w["e"] for w in D.WORDS if c["out_in"] <= w["s"] < c["out_out"]]
        last = max(ws) if ws else h["from"] / vlog.FPS
        out.append((last + 0.12, c["out_out"]))
    out.append((D.DUR, D.TOTAL))
    out += [tuple(q) for q in vlog.QUIET]
    return sorted(out)


def mix_vlog(reuse_music=False):
    """the vlog style: music on the beat grid, the clip's own sound out over B-roll and the holds"""
    import vlog
    import vlog_music
    total = int(round(D.TOTAL * SR))
    voice = build_voice()[:total]
    if len(voice) < total:
        voice = np.pad(voice, (0, total - len(voice)))
    tt = np.arange(total) / SR
    keep = np.ones(total, np.float32)
    for (a, b) in vlog_quiet_windows():
        w = np.clip(np.minimum((tt - a) / VLOG_FADE, (b - tt) / VLOG_FADE), 0, 1)
        if b >= D.DUR - 1e-3:                               # nothing comes back after the last window
            w = np.clip((tt - a) / VLOG_FADE, 0, 1)
        keep *= (1 - (0.5 - 0.5 * np.cos(np.pi * w))).astype(np.float32)
    voice = voice * keep
    wr(os.path.join(OUT, "voice.wav"), voice)

    mpath = os.path.join(OUT, "music.wav")
    if reuse_music and os.path.exists(mpath):
        music = rd(mpath)
    else:
        vlog_music.load(E.PROJECT, vlog.ARRANGE)
        music = vlog_music.render()
    music = music[:total]
    if len(music) < total:
        music = np.pad(music, ((0, total - len(music)), (0, 0)))
    wr(mpath, music)
    sfx = render_sfx(total)
    wr(os.path.join(OUT, "sfx.wav"), sfx)

    lv = lufs(os.path.join(OUT, "voice.wav"))
    lm = lufs(os.path.join(OUT, "music.wav"))
    voice = voice * db_to_gain(-16.0 - lv)
    music = music * db_to_gain(VLOG_MUSIC_LUFS - lm)
    print(f"voice {lv:.1f} LUFS -> -16, music {lm:.1f} LUFS -> {VLOG_MUSIC_LUFS}")
    act = smooth(np.clip((envelope_db(voice) + 46) / 16, 0, 1), 0.045, 0.45)
    solo = np.zeros(total, np.float32)
    for (a, b) in vlog_quiet_windows():
        w = np.clip(np.minimum((tt - a) / VLOG_RAMP + 0.5, (b - tt) / VLOG_RAMP + 0.5), 0, 1)
        if b >= D.DUR - 1e-3:
            w = np.clip((tt - a) / VLOG_RAMP + 0.5, 0, 1)
        solo = np.maximum(solo, (0.5 - 0.5 * np.cos(np.pi * w)).astype(np.float32))
    music_d = music * db_to_gain(VLOG_DUCK_DB * act * (1 - solo) + VLOG_SOLO_DB * solo)[:, None]
    mix = np.stack([voice, voice], axis=1) + music_d + sfx
    pre = os.path.join(OUT, "mix_pre.wav")
    wr(pre, mix * 0.9)
    loudnorm(pre, os.path.join(OUT, "final_audio_nofade.wav"), tp=-1.5)
    fade_in(os.path.join(OUT, "final_audio_nofade.wav"), os.path.join(OUT, "final_audio.wav"))
    print("final", lufs(os.path.join(OUT, "final_audio.wav")), "LUFS")
    for (a, b) in vlog_quiet_windows():
        print(f"  quiet {a:7.2f}-{b:7.2f}")


def preset_of(args):
    """--preset, else MIX in design.py, else a kit's story.MIX, else from the design's score"""
    if args.preset:
        return args.preset
    design = sys.modules.get("design")
    for p in (getattr(design, "MIX", None), getattr(D, "MIX", None)):
        if p:
            if p not in PRESETS:
                sys.exit(f"MIX = {p!r} is not a preset ({', '.join(PRESETS)})")
            return p
    if D.SCORE:
        return "score_solo" if hasattr(design, "SOLO_WINDOWS") else "score"
    return "standard"


def main():
    args = parser().parse_args()
    setup(args.project, args.fmt)
    preset = preset_of(args)
    print(f"preset {preset}", flush=True)
    if preset == "standard":
        mix_standard()
    elif preset in ("score", "score_solo"):
        mix_score(solo=preset == "score_solo")
    else:
        mix_vlog(args.reuse_music)


if __name__ == "__main__":
    main()
elif "--project" in sys.argv and D is None:
    # an older project script set sys.argv and imported this module for its helpers: load the project as before
    _a = parser().parse_known_args()[0]
    setup(_a.project, _a.fmt)
