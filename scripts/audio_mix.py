"""Build the soundtrack: edited dialogue + code-composed music (ducked) + synthesised SFX.

python audio_mix.py --project P --fmt tiktok|youtube
Outputs in P/audio_<fmt>/: voice_raw.wav voice.wav music.wav sfx.wav mix_pre.wav final_audio.wav (-14 LUFS)
A design that registers story.score() events gets that trailer score (trailer_score.py) instead of the
composed music, mixed as three stems (also hits.wav, perc.wav) with a limiter before the loudness pass.
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np
from scipy import signal
from scipy.io import wavfile

ap = argparse.ArgumentParser()
ap.add_argument("--project", required=True)
ap.add_argument("--fmt", choices=["youtube", "tiktok"], required=True)
ARGS = ap.parse_args()
os.environ["EDIT_PROJECT"] = os.path.abspath(ARGS.project)
os.environ["EDIT_FMT"] = ARGS.fmt
os.environ["EDIT_SS"] = "1"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio_engine as ae  # noqa: E402
import compose  # noqa: E402
import engine as E  # noqa: E402
import story as D  # noqa: E402

D.load_design()
SR = 48000
FPS = E.FPS
OUT = os.path.join(E.PROJECT, f"audio_{ARGS.fmt}")
os.makedirs(OUT, exist_ok=True)


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


IR = ae.make_ir(1.8, 0.015, 0.5)


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


def main_score():
    """trailer cut: the score registered with story.score() replaces the composed music (trailer_score.py)."""
    import trailer_score
    total = int(round(D.TOTAL * SR))
    voice = build_voice()[:total]
    if len(voice) < total:
        voice = np.pad(voice, (0, total - len(voice)))
    sfx = render_sfx(total)
    wr(os.path.join(OUT, "sfx.wav"), sfx)
    music, hits, perc, light = trailer_score.render(D.SCORE, D.TOTAL)
    stems = {}
    for name, x, target in (("music", music, -21.0), ("hits", hits, -17.5), ("perc", perc, -27.0)):
        x = x[:total]
        if len(x) < total:
            x = np.pad(x, ((0, total - len(x)), (0, 0)))
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
    mix = np.stack([voice, voice], axis=1) + stems["music"] * db_to_gain(depth * act)[:, None] + stems["hits"] \
        + stems["perc"] + sfx
    pre = os.path.join(OUT, "mix_pre.wav")
    wr(pre, mix * 0.8)
    # braams and booms are far above the speech peaks: limit them first, so loudnorm can stay linear
    lim = os.path.join(OUT, "mix_lim.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pre, "-af", "alimiter=limit=0.7:attack=3:release=90:level=false",
                    "-c:a", "pcm_f32le", lim], check=True)
    loudnorm(lim, os.path.join(OUT, "final_audio.wav"), tp=-1.5, lra=14)
    print("final", lufs(os.path.join(OUT, "final_audio.wav")), "LUFS")


def main():
    if D.SCORE:
        return main_score()
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


if __name__ == "__main__":
    main()
