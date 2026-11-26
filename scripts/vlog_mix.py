"""The soundtrack of a vlog-style edit (references/vlog.md): use it instead of audio_mix.py.

python vlog_mix.py --project P [--reuse-music]     -> P/audio_youtube/final_audio.wav (-14 LUFS) + voice, music, sfx

It is the skill's standard mix (audio_mix.py) with three changes:
1. The music is vlog_music.py: the lo-fi recipe played on the cut's beat grid (beats.json), arranged per chapter
   (vlog.ARRANGE).
2. B-roll is silent picture. Under the chapter cards, the ending, every hold after a last word (hold_beats) and the
   end card, the clip's own sound (steps, laughter, off-script words) is faded out and the music carries the moment.
   vlog.QUIET adds windows of your own.
3. The beat is felt under the voice, as in a vlog: the bed sits at -21 LUFS and ducks 6.5 dB under speech (the
   standard mix: -23.5 and 9 dB); over B-roll it steps up 3.5 dB, so every card swells with its fill.

--reuse-music keeps the music.wav already rendered (the music takes a few minutes): use it after changing only cues.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REUSE = "--reuse-music" in sys.argv
if "--project" not in sys.argv:
    sys.exit("usage: vlog_mix.py --project P [--reuse-music]")
proj = os.path.abspath(sys.argv[sys.argv.index("--project") + 1])
sys.argv = ["audio_mix.py", "--project", proj, "--fmt", "youtube"]
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

import audio_mix as AM  # noqa: E402  (parses the argv above and loads design.py; its main() does not run)
import vlog  # noqa: E402
import vlog_music  # noqa: E402

MUSIC_LUFS, DUCK_DB = -21.0, -6.5
SOLO_DB = 3.5              # where the picture is B-roll the music steps forward: the swell lands with the cut
FADE = 0.18                # the clip's own sound fades out / in over this at a quiet window's edges
RAMP = 0.10


def quiet_windows():
    """(t0, t1) where the clip's own sound is not wanted: B-roll, the holds after a last word, the end, vlog.QUIET"""
    D = AM.D
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


def main():
    SR, D, OUT = AM.SR, AM.D, AM.OUT
    total = int(round(D.TOTAL * SR))
    voice = AM.build_voice()[:total]
    if len(voice) < total:
        voice = np.pad(voice, (0, total - len(voice)))
    tt = np.arange(total) / SR
    keep = np.ones(total, np.float32)
    for (a, b) in quiet_windows():
        w = np.clip(np.minimum((tt - a) / FADE, (b - tt) / FADE), 0, 1)
        if b >= D.DUR - 1e-3:                               # nothing comes back after the last window
            w = np.clip((tt - a) / FADE, 0, 1)
        keep *= (1 - (0.5 - 0.5 * np.cos(np.pi * w))).astype(np.float32)
    voice = voice * keep
    AM.wr(os.path.join(OUT, "voice.wav"), voice)

    mpath = os.path.join(OUT, "music.wav")
    if REUSE and os.path.exists(mpath):
        music = AM.rd(mpath)
    else:
        vlog_music.load(proj, vlog.ARRANGE)
        music = vlog_music.render()
    music = music[:total]
    if len(music) < total:
        music = np.pad(music, ((0, total - len(music)), (0, 0)))
    AM.wr(mpath, music)
    sfx = AM.render_sfx(total)
    AM.wr(os.path.join(OUT, "sfx.wav"), sfx)

    lv = AM.lufs(os.path.join(OUT, "voice.wav"))
    lm = AM.lufs(os.path.join(OUT, "music.wav"))
    voice = voice * AM.db_to_gain(-16.0 - lv)
    music = music * AM.db_to_gain(MUSIC_LUFS - lm)
    print(f"voice {lv:.1f} LUFS -> -16, music {lm:.1f} LUFS -> {MUSIC_LUFS}")
    act = AM.smooth(np.clip((AM.envelope_db(voice) + 46) / 16, 0, 1), 0.045, 0.45)
    solo = np.zeros(total, np.float32)
    for (a, b) in quiet_windows():
        w = np.clip(np.minimum((tt - a) / RAMP + 0.5, (b - tt) / RAMP + 0.5), 0, 1)
        if b >= D.DUR - 1e-3:
            w = np.clip((tt - a) / RAMP + 0.5, 0, 1)
        solo = np.maximum(solo, (0.5 - 0.5 * np.cos(np.pi * w)).astype(np.float32))
    music_d = music * AM.db_to_gain(DUCK_DB * act * (1 - solo) + SOLO_DB * solo)[:, None]
    mix = np.stack([voice, voice], axis=1) + music_d + sfx
    pre = os.path.join(OUT, "mix_pre.wav")
    AM.wr(pre, mix * 0.9)
    AM.loudnorm(pre, os.path.join(OUT, "final_audio_nofade.wav"), tp=-1.5)
    # a 20 ms fade-in: a first word on the first frame can make an AAC encode overshoot the true peak
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(OUT, "final_audio_nofade.wav"), "-af",
                    "afade=t=in:st=0:d=0.02", "-c:a", "pcm_s24le", os.path.join(OUT, "final_audio.wav")], check=True)
    print("final", AM.lufs(os.path.join(OUT, "final_audio.wav")), "LUFS")
    for (a, b) in quiet_windows():
        print(f"  quiet {a:7.2f}-{b:7.2f}")


if __name__ == "__main__":
    main()
