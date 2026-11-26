"""The mix of a trailer or motion edit scored with score() events, licensed tracks included (references/motion.md).

python trailer_mix.py PROJECT [--fmt tiktok]

It is audio_mix.py's trailer mix (main_score) with one change: the music stem is split in two before it is
loudness-normalised. The bed under the voice is normalised to -21 LUFS and ducked, as audio_mix does. The stretches with
no voice at all (the end card, a tag) are normalised on their own to SOLO_LUFS. With one stem, raising those also
lowered the bed under every spoken line, so a licensed track was either inaudible under the voice or too quiet alone.
The voiceless stretches are design.SOLO_WINDOWS [(t0, t1)], else the end card from design.T_END, else none.
The hits sit 2 dB under audio_mix's level, and a 20 ms fade-in keeps a boom on frame 0 from overshooting in AAC.
"""
import os
import subprocess
import sys

SKILL = os.path.dirname(os.path.abspath(__file__))
proj = os.path.abspath(sys.argv[1])
fmt = sys.argv[sys.argv.index("--fmt") + 1] if "--fmt" in sys.argv else "tiktok"
sys.argv = ["audio_mix.py", "--project", proj, "--fmt", fmt]
sys.path.insert(0, SKILL)
import numpy as np  # noqa: E402

import audio_mix as AM  # noqa: E402  (parses the argv above, loads design.py; main() does not run)

SOLO_LUFS = -14.8           # the guide and the end card: about 1 LU under the spoken parts in the final mix
RAMP = 0.35


def solo_windows():
    import design
    if hasattr(design, "SOLO_WINDOWS"):
        return list(design.SOLO_WINDOWS)
    if hasattr(design, "T_END"):
        return [(design.T_END - 0.05, AM.D.TOTAL)]      # the end card / the tag after the last word
    return []


def main():
    import trailer_score
    SR, D, OUT = AM.SR, AM.D, AM.OUT
    total = int(round(D.TOTAL * SR))
    voice = AM.build_voice()[:total]
    if len(voice) < total:
        voice = np.pad(voice, (0, total - len(voice)))
    sfx = AM.render_sfx(total)
    AM.wr(os.path.join(OUT, "sfx.wav"), sfx)
    music, hits, perc, light = trailer_score.render(D.SCORE, D.TOTAL)
    tt = np.arange(total) / SR
    music = music[:total]
    if len(music) < total:
        music = np.pad(music, ((0, total - len(music)), (0, 0)))
    parts = {"hits": hits, "perc": perc}
    rest = np.ones(total, np.float32)
    plan = [("music", -21.0)]
    for i, (a, b) in enumerate(solo_windows()):        # each voiceless stretch is levelled on its own
        w = np.clip(np.minimum((tt - a) / RAMP + 0.5, (b - tt) / RAMP + 0.5), 0, 1)
        m = (0.5 - 0.5 * np.cos(np.pi * w)).astype(np.float32)
        parts[f"music_solo{i}"] = music * m[:, None]
        rest = rest * (1 - m)
        plan.append((f"music_solo{i}", SOLO_LUFS))
    parts["music"] = music * rest[:, None]
    plan += [("hits", -19.5), ("perc", -27.0)]      # the hits sit 2 dB lower: the first word is often under the boom
    stems = {}
    for name, target in plan:
        x = parts[name][:total]
        if len(x) < total:
            x = np.pad(x, ((0, total - len(x)), (0, 0)))
        p = os.path.join(OUT, f"{name}.wav")
        AM.wr(p, x)
        lv_ = AM.lufs(p) if np.abs(x).max() > 0 else None
        stems[name] = x * AM.db_to_gain(target - lv_) if lv_ is not None else x
        print(f"{name} {lv_ if lv_ is None else round(lv_, 1)} -> {target} LUFS")
    lv = AM.lufs(os.path.join(OUT, "voice.wav"))
    voice = voice * AM.db_to_gain(-16.0 - lv)
    print(f"voice {lv:.1f} -> -16 LUFS")
    act = AM.smooth(np.clip((AM.envelope_db(voice) + 46) / 16, 0, 1), 0.04, 0.4)
    depth = np.full(total, -9.0)
    for (a, b) in light:
        depth[int(a * SR):int(b * SR)] = -5.5
    mix = np.stack([voice, voice], axis=1) + stems["music"] * AM.db_to_gain(depth * act)[:, None] \
        + sum(v for k, v in stems.items() if k.startswith("music_solo")) + stems["hits"] + stems["perc"] + sfx
    pre = os.path.join(OUT, "mix_pre.wav")
    AM.wr(pre, mix * 0.8)
    lim = os.path.join(OUT, "mix_lim.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pre, "-af", "alimiter=limit=0.7:attack=3:release=90:level=false",
                    "-c:a", "pcm_f32le", lim], check=True)
    AM.loudnorm(lim, os.path.join(OUT, "final_audio_nofade.wav"), tp=-2.0, lra=14)
    # the boom and the first word start on frame 0; without a 20 ms fade-in the AAC encode overshot to +0.2 dBTP in
    # the first second (tập 14: the wav was -2.0)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(OUT, "final_audio_nofade.wav"), "-af",
                    "afade=t=in:st=0:d=0.02", "-c:a", "pcm_s24le", os.path.join(OUT, "final_audio.wav")], check=True)
    print("final", AM.lufs(os.path.join(OUT, "final_audio.wav")), "LUFS")


if __name__ == "__main__":
    main()
