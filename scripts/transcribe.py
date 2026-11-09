"""Word-level transcript with Whisper (CPU; a 6.5 min file takes about 19 min with the medium model).

python transcribe.py PROJECT [--model medium] [--threads 10]     -> transcript.json, transcript.txt
python transcribe.py PROJECT --range 116 118.5 --prompt "rẽ nhánh"  re-hears one passage with beam search

Whisper can drop speech without any error: after a sentence that matches its prompt it may decide that the
rest of the 30 s window is silent. So the result is checked against the audio's own speech envelope, and any
stretch of speech with no words on it is transcribed again on its own, without the prompt.
"""
import argparse
import json
import os
import time

import numpy as np
import torch
import whisper

SR = 16000


def speech_regions(audio):
    """(start, end) seconds of speech from the energy envelope, the same thresholds as build_timeline.py."""
    hop = SR // 50
    n = len(audio) // hop
    db = 10 * np.log10((audio[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    thr = max(np.percentile(db, 8) + 9.0, np.percentile(db, 75) - 24.0)
    regions = []
    for i in np.nonzero(db > thr)[0]:
        t = i / 50.0
        if regions and t - regions[-1][1] < 0.4:
            regions[-1][1] = t + 0.02
        else:
            regions.append([t, t + 0.02])
    return [(a, b) for a, b in regions if b - a >= 0.25]


def missing_speech(segments, regions, min_len=1.0):
    """speech with no word within 0.4 s of it; pieces less than 1 s apart are merged so they keep their context."""
    spans = sorted((w["start"] - 0.4, w["end"] + 0.4) for s in segments for w in s.get("words", []))
    out = []
    for a, b in regions:
        cur = a
        for x, y in spans:
            if y <= cur:
                continue
            if x >= b:
                break
            if x > cur:
                out.append([cur, x])
            cur = max(cur, y)
        if cur < b:
            out.append([cur, b])
    merged = []
    for a, b in out:
        if merged and a - merged[-1][1] < 1.0:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    return [(a, b) for a, b in merged if b - a >= min_len]


def fill_gaps(model, audio, result, language):
    """re-hear what the first pass skipped, at most twice."""
    regions = speech_regions(audio)
    filled = 0.0
    for _ in range(2):
        gaps = missing_speech(result["segments"], regions)
        if not gaps:
            break
        for a, b in gaps:
            a0 = max(0.0, a - 0.3)
            r = model.transcribe(audio[int(a0 * SR):int((b + 0.3) * SR)], language=language, word_timestamps=True,
                                 condition_on_previous_text=False, fp16=False)
            for s in r["segments"]:
                s["start"] += a0
                s["end"] += a0
                for w in s.get("words", []):
                    w["start"] += a0
                    w["end"] += a0
                result["segments"].append(s)
            filled += b - a
    result["segments"].sort(key=lambda s: s["start"])
    left = missing_speech(result["segments"], regions)
    if filled:
        print(f"first pass skipped speech: re-heard {filled:.0f} s without the prompt; check names and jargon there")
    if left:
        print("no words on this speech, listen to it (could be noise, music or a skipped sentence):",
              ", ".join(f"{a:.1f}-{b:.1f}" for a, b in left))


ap = argparse.ArgumentParser()
ap.add_argument("project")
ap.add_argument("--model", default="medium")
ap.add_argument("--threads", type=int, default=10)
ap.add_argument("--range", nargs=2, type=float)
ap.add_argument("--prompt", default=None)
args = ap.parse_args()

cfg = json.load(open(os.path.join(args.project, "project.json"), encoding="utf-8"))
lang = cfg.get("language", "vi")
torch.set_num_threads(args.threads)
t0 = time.time()
model = whisper.load_model(args.model, device="cpu")
audio = whisper.load_audio(os.path.join(args.project, "audio16k.wav"))
if args.range:
    a, b = args.range
    r = model.transcribe(audio[int(a * SR):int(b * SR)], language=lang, word_timestamps=True, beam_size=5,
                         initial_prompt=args.prompt or cfg.get("whisper_prompt"), fp16=False)
    for s in r["segments"]:
        for w in s.get("words", []):
            print(f"{a + w['start']:8.2f} {a + w['end']:8.2f} {w['word']}")
else:
    r = model.transcribe(audio, language=lang, word_timestamps=True, verbose=None,
                         condition_on_previous_text=True, initial_prompt=cfg.get("whisper_prompt"), fp16=False)
    fill_gaps(model, audio, r, lang)
    with open(os.path.join(args.project, "transcript.json"), "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=1)
    with open(os.path.join(args.project, "transcript.txt"), "w", encoding="utf-8") as f:
        for s in r["segments"]:
            f.write(f"[{s['start']:7.2f}-{s['end']:7.2f}] {s['text'].strip()}\n")
print(f"done in {time.time() - t0:.0f} s")
